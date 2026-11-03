from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import Client

THRESHOLD = 0.65
SERVER_URL = "http://localhost:8002/mcp"

CASES: list[dict[str, Any]] = [
    {
        "id": "Q1",
        "kind": "precision",
        "query": "What should we verify before committing MarketRadar to a new marketplace source?",
        "project_id": "proj-lessons",
        "ceiling": "internal",
        "filters": {"doc_type": "lesson"},
        "expected": "lesson-marketplace-source-feasibility.md",
    },
    {
        "id": "Q2",
        "kind": "precision",
        "query": "How should MarketRadar be designed so Facebook could later be replaced by another marketplace?",
        "project_id": "proj-lessons",
        "ceiling": "internal",
        "filters": {"doc_type": "lesson"},
        "expected": "lesson-source-adapter-isolation.md",
    },
    {
        "id": "Q3",
        "kind": "precision",
        "query": "If Facebook login succeeds, does that prove MarketRadar can scrape listings?",
        "project_id": "proj-lessons",
        "ceiling": "internal",
        "filters": {"doc_type": "lesson"},
        "expected": "lesson-authentication-vs-scrape-access.md",
    },
    {
        "id": "Q4",
        "kind": "keyword",
        "query": "What evidence should we capture when a scraper unexpectedly returns zero listings?",
        "project_id": "proj-lessons",
        "ceiling": "internal",
        "filters": {"doc_type": "lesson"},
        "expected": "lesson-empty-scrape-diagnostics.md",
    },
    {
        "id": "Q5",
        "kind": "ceiling",
        "query": "How should reusable marketplace cookies, tokens, credentials, and session data be protected?",
        "project_id": "proj-lessons",
        "ceiling": "internal",
        "filters": {"doc_type": "lesson"},
        "forbidden": "lesson-session-data-security.md",
    },
    {
        "id": "Q6",
        "kind": "precision",
        "query": "Where should business logic live so the React web app and a future mobile client can share it?",
        "project_id": "proj-lessons",
        "ceiling": "internal",
        "filters": {"doc_type": "lesson"},
        "expected": "lesson-shared-backend-clients.md",
    },
]


def extract_hits(result: Any) -> list[dict[str, Any]]:
    if hasattr(result, "data") and result.data is not None:
        return result.data
    if hasattr(result, "structured_content") and result.structured_content is not None:
        return result.structured_content
    if hasattr(result, "structuredContent") and result.structuredContent is not None:
        return result.structuredContent
    if isinstance(result, list):
        return result
    raise RuntimeError(f"Could not extract structured hits from result: {result!r}")


def judge(case: dict[str, Any], hits: list[dict[str, Any]]) -> bool:
    docs = [hit["source_document"] for hit in hits]

    if case["kind"] == "ceiling":
        return case["forbidden"] not in docs

    if case["kind"] == "keyword":
        return case["expected"] in docs

    return any(
        hit["source_document"] == case["expected"]
        and (hit.get("similarity_score") or 0) >= THRESHOLD
        for hit in hits
    )


def summarize(hits: list[dict[str, Any]]) -> str:
    if not hits:
        return "(no results)"

    return ", ".join(
        f"{hit['source_document']}#{hit['chunk_index']}"
        f"({hit['retrieval_method']},{hit.get('similarity_score')})"
        for hit in hits
    )


async def main() -> None:
    passed = 0

    async with Client(SERVER_URL) as client:
        for case in CASES:
            result = await client.call_tool(
                "retrieve",
                {
                    "query": case["query"],
                    "project_id": case["project_id"],
                    "top_k": 3,
                    "classification_ceiling": case["ceiling"],
                    "metadata_filters": case.get("filters", {}),
                    "calling_role": "planner",
                },
            )

            hits = extract_hits(result)
            ok = judge(case, hits)
            passed += int(ok)

            print(
                f"{case['id']}: {'PASS' if ok else 'FAIL'} "
                f"[{summarize(hits)}]"
            )

    print(f"\n{passed}/{len(CASES)} passed")

    if passed / len(CASES) < 0.80:
        raise SystemExit("Retrieval pass rate is below the 80% floor")


if __name__ == "__main__":
    asyncio.run(main())
