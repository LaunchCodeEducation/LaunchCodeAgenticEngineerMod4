#!/usr/bin/env python3
"""Sample retrieval MCP server with role and classification enforcement."""

import datetime
import json
import os
from pathlib import Path
from typing import Any

try:
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError
except Exception:  # pragma: no cover
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

mcp = FastMCP("retrieval")
CALLING_ROLE = os.environ.get("AGENT_ROLE", "")
ALLOW_LIST_PATH = Path(__file__).parent / "allow-list.json"
ALLOW_LIST = json.loads(ALLOW_LIST_PATH.read_text(encoding="utf-8"))
AUDIT_LOG_PATH = Path(os.environ.get("RETRIEVAL_AUDIT_LOG", "logs/retrieval-audit-log.jsonl"))
AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
CORPUS_PATH = Path(__file__).parent / "corpus.json"
CLASSIFICATION_ORDER = ["public", "internal", "confidential"]


def _record_audit(event: str, operation: str, detail: str) -> dict[str, Any]:
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "event": event,
        "operation": operation,
        "role": CALLING_ROLE,
        "outcome": event,
        "detail": detail,
        "policy_reference": "docs/governance-policy.md",
    }
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as log:
        log.write(json.dumps(record) + "\n")
    return record


def _retrieval_ceiling() -> str:
    rule = ALLOW_LIST.get("retrieve", {}).get(CALLING_ROLE)
    if not rule or not rule.get("granted"):
        reason = (rule or {}).get("denial_reason", "role is not granted retrieval")
        _record_audit("authorization_denied", "retrieve", reason)
        raise ToolError(
            f"authorization_denied: role '{CALLING_ROLE}' may not call 'retrieve': "
            f"{reason}. See docs/governance-policy.md."
        )
    return str(rule["classification_ceiling"])


def _vector_search(query: str, top_k: int) -> list[dict[str, Any]]:
    # Sample lexical search. Replace with sqlite-vec / embedding search from Module 4.
    docs = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    query_terms = set(query.lower().split())
    scored = []
    for doc in docs:
        text = f"{doc.get('title', '')} {doc.get('text', '')}".lower()
        score = sum(1 for term in query_terms if term in text)
        scored.append((score, doc))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for score, doc in scored[:top_k] if score > 0] or [doc for _, doc in scored[:top_k]]


@mcp.tool
def retrieve(query: str, top_k: int = 5) -> list:
    ceiling = _retrieval_ceiling()
    max_level = CLASSIFICATION_ORDER.index(ceiling)
    candidates = _vector_search(query, top_k)
    visible = []
    withheld = 0
    for doc in candidates:
        if CLASSIFICATION_ORDER.index(doc["classification"]) <= max_level:
            visible.append(doc)
        else:
            withheld += 1
    if withheld:
        _record_audit(
            "classification_withheld",
            "retrieve",
            f"{withheld} result(s) above the '{ceiling}' ceiling were withheld",
        )
    _record_audit(
        "retrieval_success",
        "retrieve",
        f"{len(visible)} result(s) returned at the '{ceiling}' ceiling",
    )
    return visible


if __name__ == "__main__":
    mcp.run()
