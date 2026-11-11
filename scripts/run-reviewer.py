#!/usr/bin/env python3
"""
Run an advisory agentic code review on changed files.

This script:
- Reads CHANGED_FILES from the environment.
- Reads OPENROUTER_API_KEY from the environment (OpenRouter's Anthropic-compatible endpoint).
- Reviews only text-like changed files.
- Writes /out/review-output.md.
- Writes /out/review-audit.json.
- Always exits 0 because this review is advisory.
"""

from __future__ import annotations

import json
import os
import subprocess
import textwrap
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/out")
MAX_FILE_CHARS = 20_000
MAX_TOTAL_CHARS = 60_000

TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml",
    ".md", ".txt", ".sh", ".toml", ".ini", ".cfg", ".html", ".css",
}


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()


def is_text_candidate(path: Path) -> bool:
    if path.name in {"Dockerfile", "Makefile"}:
        return True
    return path.suffix.lower() in TEXT_EXTENSIONS


def read_changed_files() -> list[str]:
    raw = os.environ.get("CHANGED_FILES", "").strip()
    if raw:
        return [p for p in raw.split() if p]

    # Fallback for local debugging.
    try:
        return run(["git", "diff", "--name-only", "HEAD~1", "HEAD"]).splitlines()
    except Exception:
        return []


def collect_file_context(paths: list[str]) -> tuple[str, list[dict]]:
    chunks: list[str] = []
    audit_files: list[dict] = []
    total = 0

    for name in paths:
        path = Path(name)

        record = {
            "path": name,
            "included": False,
            "reason": "",
            "chars": 0,
        }

        if not path.exists() or not path.is_file():
            record["reason"] = "missing_or_not_file"
            audit_files.append(record)
            continue

        if not is_text_candidate(path):
            record["reason"] = "skipped_non_text_extension"
            audit_files.append(record)
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            record["reason"] = f"read_error: {exc}"
            audit_files.append(record)
            continue

        if not text.strip():
            record["reason"] = "empty_file"
            audit_files.append(record)
            continue

        if len(text) > MAX_FILE_CHARS:
            text = text[:MAX_FILE_CHARS] + "\n\n[TRUNCATED]\n"

        if total + len(text) > MAX_TOTAL_CHARS:
            record["reason"] = "skipped_total_context_limit"
            audit_files.append(record)
            continue

        chunks.append(f"\n\n--- FILE: {name} ---\n{text}")
        total += len(text)

        record["included"] = True
        record["reason"] = "included"
        record["chars"] = len(text)
        audit_files.append(record)

    return "\n".join(chunks), audit_files


def call_anthropic(prompt: str) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return (
            "## Advisory Code Review\n\n"
            "No review was performed because `OPENROUTER_API_KEY` was not available. "
            "Confirm that the repository secret is configured and injected only into this step.\n"
        )

    model = os.environ.get("REVIEW_MODEL", "anthropic/claude-sonnet-4.6")

    payload = {
        "model": model,
        "max_tokens": 1200,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {api_key}",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return f"## Advisory Code Review\n\nOpenRouter API request failed: HTTP {exc.code}\n\n```text\n{detail[:2000]}\n```"
    except Exception as exc:
        return f"## Advisory Code Review\n\nOpenRouter API request failed: `{exc}`"

    blocks = data.get("content", [])
    text_parts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
    return "\n".join(text_parts).strip() or "No review text was returned."

 def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    changed_files = read_changed_files()
    file_context, audit_files = collect_file_context(changed_files)

    if not file_context.strip():
        review = (
            "## Advisory Code Review\n\n"
            "No reviewable text files were found in this change.\n"
        )
    else:
        prompt = textwrap.dedent(
            f"""
            You are performing an advisory code review for a CI/CD workflow.

            Review the changed files below. Focus on:
            - correctness bugs
            - security or secret-handling issues
            - brittle CI/CD or Docker behavior
            - governance-policy drift
            - missing tests or obvious regression risks

            Do not nitpick style. Keep the review concise.
            Use this format:

            ## Advisory Code Review
            ### High-priority findings
            - ...

            ### Medium-priority findings
            - ...

            ### Suggested follow-ups
            - ...

            If there are no meaningful issues, say so clearly.

            Changed files:
            {", ".join(changed_files)}

            File contents:
            {file_context}
            """
        ).strip()

        review = call_anthropic(prompt)

    (OUT_DIR / "review-output.md").write_text(review + "\n", encoding="utf-8")

    audit = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "advisory",
        "changed_files": changed_files,
        "files": audit_files,
        "openrouter_key_present": bool(os.environ.get("OPENROUTER_API_KEY", "").strip()),
        "output": "/out/review-output.md",
        "exit_behavior": "always_zero_advisory",
    }

    (OUT_DIR / "review-audit.json").write_text(
        json.dumps(audit, indent=2),
        encoding="utf-8",
    )

    # Advisory: a critical review is still a successful run.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
