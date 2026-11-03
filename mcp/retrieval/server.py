from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Callable

import sqlite_vec
from fastmcp import FastMCP
from sentence_transformers import SentenceTransformer
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

REFERENCE_DIR = os.getenv("RETRIEVAL_REFERENCE_DIR", "/memory/reference")
EMBEDDING_MODEL = os.getenv("RETRIEVAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIM = 384
SIMILARITY_THRESHOLD = float(os.getenv("RETRIEVAL_SIMILARITY_THRESHOLD", "0.65"))
DEFAULT_CEILING = "internal"
PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
ROLE_ALLOWLIST_PATH = Path(__file__).resolve().parent.parent / "roles.allowlist.json"

# Ordered from least to most sensitive. A value's index is its sensitivity rank.
CLASSIFICATION_ORDER = ["public", "internal", "confidential", "secret"]
FALLBACK_CLASSIFICATION = "secret"
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

mcp = FastMCP("retrieval")


def validate_project_id(project_id: str) -> None:
    if not PROJECT_ID_PATTERN.match(project_id or ""):
        raise ValueError("project_id must contain only letters, numbers, and hyphens")


def rank(classification: str) -> int:
    """Sensitivity rank. Unknown document values rank above all known values."""
    if classification in CLASSIFICATION_ORDER:
        return CLASSIFICATION_ORDER.index(classification)
    return len(CLASSIFICATION_ORDER)


def validate_ceiling(classification_ceiling: str) -> None:
    if classification_ceiling not in CLASSIFICATION_ORDER:
        raise ValueError(
            f"classification_ceiling must be one of {CLASSIFICATION_ORDER}"
        )


def enforce_role_ceiling(calling_role: str, requested_ceiling: str) -> None:
    """Reject retrieval above the classification ceiling assigned to a role."""
    if not ROLE_ALLOWLIST_PATH.exists():
        raise ValueError("role allowlist is missing")

    allowlist = json.loads(ROLE_ALLOWLIST_PATH.read_text())
    role_config = allowlist.get(calling_role)

    if role_config is None:
        raise ValueError(f"retrieval is not allowed for role: {calling_role}")

    if "retrieve" not in role_config.get("retrieval", []):
        raise ValueError(f"retrieve is not allowed for role: {calling_role}")

    allowed_ceiling = role_config.get("classification_ceiling", "public")
    validate_ceiling(allowed_ceiling)

    if rank(requested_ceiling) > rank(allowed_ceiling):
        raise ValueError(
            f"{calling_role} may retrieve only up to {allowed_ceiling}"
        )


def validate_metadata_filters(filters: dict) -> None:
    allowed = {"doc_type"}
    unknown = set(filters) - allowed
    if unknown:
        raise ValueError(f"unsupported metadata_filters: {sorted(unknown)}")


def embed(text: str) -> list[float]:
    """Return a normalized 384-number embedding as a plain Python list."""
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Read a leading ---...--- block of `key: value` lines."""
    metadata: dict[str, str] = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            front = text[3:end].strip()
            for line in front.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
            return metadata, text[end + 4 :].strip()
    return metadata, text.strip()


def split_sentences(text: str) -> list[str]:
    """Rough sentence split on . ! or ? followed by whitespace."""
    flat = " ".join(text.split())
    return [s.strip() for s in SENTENCE_END.split(flat) if s.strip()]


def enforce_sizes(pieces: list[str], min_words: int, max_words: int) -> list[str]:
    """Merge small pieces and split over-large pieces."""
    merged: list[str] = []
    buffer = ""
    for piece in pieces:
        candidate = (buffer + " " + piece).strip() if buffer else piece
        if len(candidate.split()) < min_words:
            buffer = candidate
        else:
            merged.append(candidate)
            buffer = ""
    if buffer:
        merged.append(buffer)

    chunks: list[str] = []
    for piece in merged:
        words = piece.split()
        if len(words) <= max_words:
            chunks.append(piece)
        else:
            for i in range(0, len(words), max_words):
                chunks.append(" ".join(words[i : i + max_words]))
    return [chunk for chunk in chunks if chunk.strip()]


def chunk_paragraphs(body: str, min_words: int = 50, max_words: int = 300) -> list[str]:
    """Split on blank lines, then apply shared size guards."""
    pieces = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    return enforce_sizes(pieces, min_words, max_words)


def chunk_semantic(
    body: str,
    boundary_threshold: float = 0.75,
    min_words: int = 50,
    max_words: int = 300,
) -> list[str]:
    """Start a new chunk where adjacent sentence similarity drops."""
    sentences = split_sentences(body)
    if len(sentences) <= 1:
        return [body.strip()] if body.strip() else []

    embeddings = model.encode(sentences, normalize_embeddings=True)
    chunks: list[str] = []
    current = [sentences[0]]

    for i in range(1, len(sentences)):
        similarity = float(embeddings[i - 1] @ embeddings[i])
        if similarity < boundary_threshold:
            chunks.append(" ".join(current))
            current = [sentences[i]]
        else:
            current.append(sentences[i])

    chunks.append(" ".join(current))
    return enforce_sizes(chunks, min_words, max_words)


def load_sqlite_vec(conn: sqlite3.Connection) -> None:
    conn.enable_load_extension(True)
    try:
        sqlite_vec.load(conn)
    finally:
        conn.enable_load_extension(False)


def build_index(conn: sqlite3.Connection, chunker: Callable[[str], list[str]]) -> int:
    """Read the reference corpus and build vector and keyword indexes."""
    reference = Path(REFERENCE_DIR)
    if not reference.exists():
        raise FileNotFoundError(
            f"reference corpus not found at {REFERENCE_DIR}; create .memory/reference"
        )

    load_sqlite_vec(conn)
    conn.execute("DROP TABLE IF EXISTS chunks")
    conn.execute("DROP TABLE IF EXISTS fts_chunks")
    conn.execute("DROP TABLE IF EXISTS vec_chunks")
    conn.execute(
        f"CREATE VIRTUAL TABLE vec_chunks USING vec0("
        f"embedding float[{EMBEDDING_DIM}] distance_metric=cosine)"
    )
    conn.execute(
        "CREATE TABLE chunks ("
        " chunk_id INTEGER PRIMARY KEY,"
        " source_document TEXT NOT NULL,"
        " chunk_index INTEGER NOT NULL,"
        " project TEXT NOT NULL,"
        " classification TEXT NOT NULL,"
        " doc_type TEXT,"
        " excerpt TEXT NOT NULL)"
    )
    conn.execute("CREATE VIRTUAL TABLE fts_chunks USING fts5(excerpt)")

    next_id = 1
    for path in sorted(reference.glob("*.md")):
        metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
        classification = metadata.get("classification")
        if classification not in CLASSIFICATION_ORDER:
            print(
                f"WARNING: {path.name} has no valid classification; "
                f"indexing as '{FALLBACK_CLASSIFICATION}' "
                "(hidden under normal ceilings). Tag it and re-index.",
                flush=True,
            )
            classification = FALLBACK_CLASSIFICATION

        project = metadata.get("project", "unknown")
        doc_type = metadata.get("doc_type")

        for index, chunk in enumerate(chunker(body)):
            conn.execute(
                "INSERT INTO chunks (chunk_id, source_document, chunk_index, "
                "project, classification, doc_type, excerpt) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (next_id, path.name, index, project, classification, doc_type, chunk),
            )
            conn.execute(
                "INSERT INTO vec_chunks (rowid, embedding) VALUES (?, ?)",
                (next_id, sqlite_vec.serialize_float32(embed(chunk))),
            )
            conn.execute(
                "INSERT INTO fts_chunks (rowid, excerpt) VALUES (?, ?)",
                (next_id, chunk),
            )
            next_id += 1

    conn.commit()
    count = next_id - 1
    print(f"Indexed {count} chunks from {REFERENCE_DIR}", flush=True)
    return count


def fts_query(text: str) -> str:
    """Turn free text into a safe FTS5 query matching exact tokens and words."""
    tokens = re.findall(r"[A-Za-z0-9_]+", text)
    tokens.extend(re.findall(r"[A-Za-z0-9]+", text))
    unique = sorted(set(tokens), key=lambda token: (-len(token), token.lower()))
    return " OR ".join(f'"{token}"' for token in unique)


def keyword_search(
    query: str,
    project_id: str,
    top_k: int,
    ceiling_rank: int,
    filters: dict,
) -> list[dict]:
    query_expr = fts_query(query)
    if not query_expr:
        return []

    rows = conn.execute(
        "SELECT c.source_document, c.chunk_index, c.project, c.classification, "
        "c.doc_type, c.excerpt "
        "FROM fts_chunks f JOIN chunks c ON c.chunk_id = f.rowid "
        "WHERE fts_chunks MATCH ? AND c.project = ? ORDER BY bm25(fts_chunks)",
        (query_expr, project_id),
    ).fetchall()

    results: list[dict] = []
    for row in rows:
        if row["project"] != project_id:
            continue
        if rank(row["classification"]) > ceiling_rank:
            continue
        if "doc_type" in filters and row["doc_type"] != filters["doc_type"]:
            continue
        results.append(
            {
                "source_document": row["source_document"],
                "chunk_index": row["chunk_index"],
                "excerpt": row["excerpt"],
                "classification": row["classification"],
                "similarity_score": None,
                "retrieval_method": "keyword",
            }
        )
        if len(results) == top_k:
            break
    return results


@mcp.tool
def retrieve(
    query: str,
    project_id: str,
    top_k: int = 3,
    classification_ceiling: str = DEFAULT_CEILING,
    metadata_filters: dict | None = None,
    calling_role: str = "unknown",
) -> list[dict]:
    """Search the reference corpus by meaning within project and classification bounds."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    validate_project_id(project_id)
    validate_ceiling(classification_ceiling)
    enforce_role_ceiling(calling_role, classification_ceiling)
    if top_k < 1 or top_k > 20:
        raise ValueError("top_k must be between 1 and 20")

    filters = metadata_filters or {}
    validate_metadata_filters(filters)
    ceiling_rank = rank(classification_ceiling)
    pool_size = max(top_k * 5, 20)
    query_vector = sqlite_vec.serialize_float32(embed(query))

    candidates = conn.execute(
        "WITH matches AS ("
        " SELECT rowid AS chunk_id, distance FROM vec_chunks "
        " WHERE embedding MATCH ? AND k = ?"
        ") "
        "SELECT c.source_document, c.chunk_index, c.project, c.classification, "
        "c.doc_type, c.excerpt, m.distance "
        "FROM matches m JOIN chunks c ON c.chunk_id = m.chunk_id "
        "ORDER BY m.distance",
        (query_vector, pool_size),
    ).fetchall()

    results: list[dict] = []
    for row in candidates:
        if row["project"] != project_id:
            continue
        if rank(row["classification"]) > ceiling_rank:
            continue
        if "doc_type" in filters and row["doc_type"] != filters["doc_type"]:
            continue
        score = round(1.0 - float(row["distance"]), 3)
        if score < SIMILARITY_THRESHOLD:
            continue
        results.append(
            {
                "source_document": row["source_document"],
                "chunk_index": row["chunk_index"],
                "excerpt": row["excerpt"],
                "classification": row["classification"],
                "similarity_score": score,
                "retrieval_method": "vector",
            }
        )
        if len(results) == top_k:
            break

    if results:
        return results

    return keyword_search(query, project_id, top_k, ceiling_rank, filters)


model: SentenceTransformer
conn: sqlite3.Connection

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vector retrieval MCP server")
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--chunking", choices=["paragraph", "semantic"], default="paragraph"
    )
    parser.add_argument("--boundary-threshold", type=float, default=0.75)
    args = parser.parse_args()

    model = SentenceTransformer(EMBEDDING_MODEL)
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row

    if args.chunking == "semantic":
        chunker = lambda body: chunk_semantic(body, args.boundary_threshold)
    else:
        chunker = chunk_paragraphs

    build_index(conn, chunker)

    import uvicorn
    app = mcp.http_app(
        stateless_http=True,
        middleware=[
            Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        ],
    )
    uvicorn.run(app, host=args.host, port=args.port)
