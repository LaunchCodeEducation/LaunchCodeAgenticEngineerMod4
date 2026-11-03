from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

DB_PATH = os.getenv("STORAGE_DB_PATH", "/memory/storage.db")
AUDIT_PATH = os.getenv("STORAGE_AUDIT_PATH", "/memory/storage-audit.log")

ALLOWED_CLASSIFICATIONS = {"public", "internal", "confidential", "secret"}
WRITE_CLASSIFICATIONS = {"public", "internal"}
PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
ROLE_ALLOWLIST_PATH = Path(__file__).resolve().parent.parent / "roles.allowlist.json"

mcp = FastMCP("storage")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_db() -> sqlite3.Connection:
    """Open the persistent SQLite database and ensure its schema exists."""
    ensure_parent(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            entry_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            entry_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            classification TEXT NOT NULL,
            deleted INTEGER NOT NULL DEFAULT 0,
            last_updated TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_entries_project_type "
        "ON entries(project_id, entry_type, deleted)"
    )
    return conn


def audit(
    operation: str,
    project_id: str,
    entry_id: str | None,
    classification: str | None,
    calling_role: str | None,
) -> None:
    """Append one JSON audit record. Agents have no tool that edits this file."""
    ensure_parent(AUDIT_PATH)
    record: dict[str, Any] = {
        "timestamp": utc_now(),
        "operation": operation,
        "project_id": project_id,
        "entry_id": entry_id,
        "classification": classification,
        "calling_role": calling_role or "unknown",
    }
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def validate_project_id(project_id: str) -> None:
    if not PROJECT_ID_PATTERN.match(project_id or ""):
        raise ValueError("project_id must contain only letters, numbers, and hyphens")


def enforce_storage_operation(calling_role: str, operation: str) -> None:
    """Enforce the storage operations granted to a role."""
    if not ROLE_ALLOWLIST_PATH.exists():
        raise ValueError("role allowlist is missing")

    allowlist = json.loads(ROLE_ALLOWLIST_PATH.read_text())
    role_config = allowlist.get(calling_role)

    if role_config is None:
        raise ValueError(f"storage is not allowed for role: {calling_role}")

    allowed_operations = role_config.get("storage", [])
    if operation not in allowed_operations:
        raise ValueError(
            f"{operation} is not allowed for role: {calling_role}"
        )


def validate_nonempty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def validate_classification(classification: str) -> None:
    if classification not in ALLOWED_CLASSIFICATIONS:
        raise ValueError(
            f"classification must be one of {sorted(ALLOWED_CLASSIFICATIONS)}"
        )
    if classification not in WRITE_CLASSIFICATIONS:
        raise ValueError(
            "this server does not accept writes classified confidential or secret"
        )


def get_live_entry(conn: sqlite3.Connection, project_id: str, entry_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM entries WHERE project_id = ? AND entry_id = ? AND deleted = 0",
        (project_id, entry_id),
    ).fetchone()


@mcp.tool
def write_entry(
    project_id: str,
    entry_type: str,
    title: str,
    content: str,
    classification: str,
    calling_role: str = "unknown",
) -> dict:
    """Write a new entry to the store. Requires a valid classification tag."""
    enforce_storage_operation(calling_role, "write_entry")
    validate_project_id(project_id)
    validate_nonempty(entry_type, "entry_type")
    validate_nonempty(title, "title")
    validate_nonempty(content, "content")
    validate_classification(classification)

    entry_id = str(uuid.uuid4())
    now = utc_now()
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO entries (entry_id, project_id, entry_type, title, content, "
            "classification, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (entry_id, project_id, entry_type, title, content, classification, now),
        )
        conn.commit()
    finally:
        conn.close()

    audit("write_entry", project_id, entry_id, classification, calling_role)
    return {"entry_id": entry_id}


@mcp.tool
def read_entry(
    project_id: str,
    entry_id: str,
    calling_role: str = "unknown",
) -> dict:
    """Read a single entry by ID, scoped to its project."""
    enforce_storage_operation(calling_role, "read_entry")
    validate_project_id(project_id)
    validate_nonempty(entry_id, "entry_id")

    conn = get_db()
    try:
        row = get_live_entry(conn, project_id, entry_id)
    finally:
        conn.close()

    if row is None:
        raise ValueError("no entry found for that project_id and entry_id")
    return dict(row)


@mcp.tool
def list_entries(
    project_id: str,
    entry_type: str | None = None,
    calling_role: str = "unknown",
) -> list[dict]:
    """List entries for a project. Metadata only; never returns full content."""
    enforce_storage_operation(calling_role, "list_entries")
    validate_project_id(project_id)

    conn = get_db()
    try:
        if entry_type is None:
            rows = conn.execute(
                "SELECT entry_id, title, entry_type, classification, last_updated "
                "FROM entries WHERE project_id = ? AND deleted = 0 "
                "ORDER BY last_updated DESC",
                (project_id,),
            ).fetchall()
        else:
            validate_nonempty(entry_type, "entry_type")
            rows = conn.execute(
                "SELECT entry_id, title, entry_type, classification, last_updated "
                "FROM entries WHERE project_id = ? AND entry_type = ? AND deleted = 0 "
                "ORDER BY last_updated DESC",
                (project_id, entry_type),
            ).fetchall()
    finally:
        conn.close()

    return [dict(row) for row in rows]


@mcp.tool
def update_entry(
    project_id: str,
    entry_id: str,
    content: str,
    calling_role: str = "unknown",
) -> dict:
    """Update the content of an existing entry. Classification is preserved."""
    enforce_storage_operation(calling_role, "update_entry")
    validate_project_id(project_id)
    validate_nonempty(entry_id, "entry_id")
    validate_nonempty(content, "content")

    now = utc_now()
    conn = get_db()
    try:
        row = get_live_entry(conn, project_id, entry_id)
        if row is None:
            raise ValueError("no entry found to update")
        conn.execute(
            "UPDATE entries SET content = ?, last_updated = ? "
            "WHERE project_id = ? AND entry_id = ? AND deleted = 0",
            (content, now, project_id, entry_id),
        )
        conn.commit()
        classification = row["classification"]
    finally:
        conn.close()

    audit("update_entry", project_id, entry_id, classification, calling_role)
    return {"success": True}


@mcp.tool
def delete_entry(
    project_id: str,
    entry_id: str,
    calling_role: str = "unknown",
) -> dict:
    """Soft-delete an entry. Marks deleted; does not remove backend evidence."""
    enforce_storage_operation(calling_role, "delete_entry")
    validate_project_id(project_id)
    validate_nonempty(entry_id, "entry_id")

    conn = get_db()
    try:
        row = get_live_entry(conn, project_id, entry_id)
        if row is None:
            raise ValueError("no entry found to delete")
        conn.execute(
            "UPDATE entries SET deleted = 1, last_updated = ? "
            "WHERE project_id = ? AND entry_id = ? AND deleted = 0",
            (utc_now(), project_id, entry_id),
        )
        conn.commit()
        classification = row["classification"]
    finally:
        conn.close()

    audit("delete_entry", project_id, entry_id, classification, calling_role)
    return {"success": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Persistent storage MCP server")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    import uvicorn
    app = mcp.http_app(
        stateless_http=True,
        middleware=[
            Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        ],
    )
    uvicorn.run(app, host=args.host, port=args.port)
