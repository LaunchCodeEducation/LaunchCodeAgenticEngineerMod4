#!/usr/bin/env python3
"""Sample storage MCP server with role-based allow-list enforcement."""

import datetime
import json
import os
from pathlib import Path
from typing import Any

try:
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError
except Exception:  # pragma: no cover - lets tests run without FastMCP installed
    class ToolError(Exception):
        pass
    class FastMCP:
        def __init__(self, name: str):
            self.name = name
        def tool(self, func=None):
            def decorate(fn):
                return fn
            return decorate(func) if func else decorate
        def run(self):
            print(f"FastMCP not installed; {self.name} functions are importable only.")

mcp = FastMCP("storage")
CALLING_ROLE = os.environ.get("AGENT_ROLE", "")
ALLOW_LIST_PATH = Path(__file__).parent / "allow-list.json"
ALLOW_LIST = json.loads(ALLOW_LIST_PATH.read_text(encoding="utf-8"))
AUDIT_LOG_PATH = Path(os.environ.get("STORAGE_AUDIT_LOG", "logs/storage-audit-log.jsonl"))
AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
STORE_PATH = Path(os.environ.get("STORAGE_STORE", str(AUDIT_LOG_PATH.parent / "storage-store.json")))
STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_store() -> dict[str, Any]:
    if STORE_PATH.exists():
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_store(data: dict[str, Any]) -> None:
    STORE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _record(event: str, operation: str, outcome: str, detail: str | None = None) -> dict[str, Any]:
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "event": event,
        "operation": operation,
        "role": CALLING_ROLE,
        "outcome": outcome,
        "detail": detail,
        "policy_reference": "docs/governance-policy.md",
    }
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as log:
        log.write(json.dumps(record) + "\n")
    return record


def _authorize(operation: str) -> None:
    allowed_roles = ALLOW_LIST.get(operation, [])
    if CALLING_ROLE not in allowed_roles:
        record = _record("authorization_denied", operation, "authorization_denied")
        raise ToolError(
            f"authorization_denied: role '{record['role']}' may not call "
            f"'{operation}'. See {record['policy_reference']}."
        )


@mcp.tool
def write_entry(key: str, value: str) -> dict:
    _authorize("write_entry")
    data = _load_store()
    data[key] = value
    _save_store(data)
    _record("storage_write", "write_entry", "success")
    return {"ok": True, "key": key}


@mcp.tool
def read_entry(key: str) -> dict:
    _authorize("read_entry")
    data = _load_store()
    _record("storage_read", "read_entry", "success")
    return {"key": key, "value": data.get(key)}


@mcp.tool
def list_entries() -> dict:
    _authorize("list_entries")
    data = _load_store()
    _record("storage_list", "list_entries", "success")
    return {"keys": sorted(data)}


@mcp.tool
def update_entry(key: str, value: str) -> dict:
    _authorize("update_entry")
    data = _load_store()
    data[key] = value
    _save_store(data)
    _record("storage_update", "update_entry", "success")
    return {"ok": True, "key": key}


@mcp.tool
def delete_entry(key: str) -> dict:
    _authorize("delete_entry")
    data = _load_store()
    existed = key in data
    data.pop(key, None)
    _save_store(data)
    _record("storage_delete", "delete_entry", "success")
    return {"ok": True, "deleted": existed}


@mcp.tool
def audit_read(limit: int = 50) -> dict:
    _authorize("audit_read")
    if not AUDIT_LOG_PATH.exists():
        return {"entries": []}
    lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()[-limit:]
    return {"entries": [json.loads(line) for line in lines if line.strip()]}


if __name__ == "__main__":
    mcp.run()
