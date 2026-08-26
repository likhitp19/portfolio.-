#!/usr/bin/env python3
"""Ingest FIA Sporting Regulations PDFs into Pinecone.

Usage (from ``backend/``)::

    python scripts/ingest_pdfs.py --dry-run
    python scripts/ingest_pdfs.py

Requires ``PINECONE_API_KEY`` for upsert. Embeddings use OpenRouter
(``OPENROUTER_API_KEY``) or OpenAI (``OPENAI_API_KEY``) with
``EMBEDDING_MODEL`` (default ``openai/text-embedding-3-small``).

Never commit API keys. Ask the operator for Pinecone credentials before a live run.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings  # noqa: E402
from app.services.embeddings import embed_texts  # noqa: E402
from app.services.legal_chunking import chunk_pdfs  # noqa: E402

UPSERT_BATCH = 64


def _pdf_dir(cli_path: str | None) -> Path:
    if cli_path:
        path = Path(cli_path)
        return path if path.is_absolute() else (BACKEND_ROOT / path)
    configured = Path(settings.fia_pdfs_dir)
    if not configured.is_absolute():
        configured = BACKEND_ROOT / configured
    return configured


def _resolve_index_dimension(pc: Any, index_name: str) -> int:
    """Use existing index dimension when present; else settings.embedding_dimensions."""
    existing = {item["name"] for item in pc.list_indexes()}
    if index_name in existing:
        desc = pc.describe_index(index_name)
        dim = getattr(desc, "dimension", None)
        if dim:
            return int(dim)
    configured = int(settings.embedding_dimensions or 512)
    return configured


def _ensure_index(pc: Any, index_name: str, dimension: int) -> Any:
    from pinecone import ServerlessSpec

    existing = {item["name"] for item in pc.list_indexes()}
    if index_name not in existing:
        print(
            "Creating Pinecone index {0!r} (dim={1}, cloud={2}, region={3})…".format(
                index_name, dimension, settings.pinecone_cloud, settings.pinecone_region
            )
        )
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
        )
        for _ in range(30):
            desc = pc.describe_index(index_name)
            status = getattr(desc, "status", None) or {}
            if isinstance(status, dict) and status.get("ready"):
                break
            if getattr(status, "ready", False):
                break
            time.sleep(2)
    return pc.Index(index_name)


def _upsert_pinecone(chunks: List[Dict[str, Any]]) -> None:
    api_key = settings.pinecone_key
    if not api_key:
        raise SystemExit(
            "PINECONE_API_KEY is empty. Paste your Pinecone key into backend/.env "
            "(never commit it), then re-run without --dry-run."
        )

    from pinecone import Pinecone

    pc = Pinecone(api_key=api_key)
    dimension = _resolve_index_dimension(pc, settings.pinecone_index)
    print(
        "Embedding {0} chunks at dimensions={1} for index={2!r}…".format(
            len(chunks), dimension, settings.pinecone_index
        )
    )
    try:
        vectors = embed_texts([chunk["text"] for chunk in chunks], dimensions=dimension)
    except Exception as exc:
        raise SystemExit(str(exc)) from exc

    if vectors and len(vectors[0]) != dimension:
        raise SystemExit(
            "Embedding dim {0} does not match index dim {1}. "
            "Set EMBEDDING_DIMENSIONS={1} or use a compatible model.".format(
                len(vectors[0]), dimension
            )
        )

    index = _ensure_index(pc, settings.pinecone_index, dimension)

    namespace = settings.pinecone_namespace or ""
    print(
        "Upserting to index={0!r} namespace={1!r}…".format(
            settings.pinecone_index, namespace or "(default)"
        )
    )
    total = 0
    for start in range(0, len(chunks), UPSERT_BATCH):
        batch_chunks = chunks[start : start + UPSERT_BATCH]
        batch_vectors = vectors[start : start + UPSERT_BATCH]
        payload = []
        for chunk, values in zip(batch_chunks, batch_vectors):
            metadata = {
                "source": chunk["source"],
                "source_document": chunk["source_document"],
                "page_number": int(chunk["page_number"]),
                "article": str(chunk.get("article") or "")[:500],
                "text": chunk["text"][:35000],
            }
            payload.append({"id": chunk["id"], "values": values, "metadata": metadata})
        kwargs: Dict[str, Any] = {"vectors": payload}
        if namespace:
            kwargs["namespace"] = namespace
        index.upsert(**kwargs)
        total += len(payload)
        print("  upserted {0}/{1}".format(total, len(chunks)))
    print("Done. Upserted {0} vectors.".format(total))


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest FIA PDFs into Pinecone")
    parser.add_argument(
        "--pdf-dir",
        default=None,
        help="Directory of PDFs (default: settings.fia_pdfs_dir → app/data/pdfs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chunk only; print metadata sample; do not embed or upsert",
    )
    parser.add_argument("--max-chars", type=int, default=3500)
    parser.add_argument("--sample", type=int, default=3, help="Sample chunks to print")
    args = parser.parse_args(argv)

    pdf_dir = _pdf_dir(args.pdf_dir)
    if not pdf_dir.is_dir():
        raise SystemExit("PDF directory not found: {0}".format(pdf_dir))

    pdfs = sorted(pdf_dir.glob("*.pdf")) + sorted(pdf_dir.glob("*.PDF"))
    if not pdfs:
        raise SystemExit("No PDFs found in {0}".format(pdf_dir))

    print("Chunking {0} PDF(s) from {1}…".format(len(set(p.resolve() for p in pdfs)), pdf_dir))
    chunks = chunk_pdfs(pdf_dir, max_chars=args.max_chars)
    if not chunks:
        raise SystemExit("No chunks produced — check PDF text extraction.")

    missing_meta = [
        chunk["id"]
        for chunk in chunks
        if chunk.get("page_number") is None or not chunk.get("source_document")
    ]
    if missing_meta:
        raise SystemExit("Chunks missing page_number/source_document: {0}".format(missing_meta[:5]))

    print("Produced {0} chunks.".format(len(chunks)))
    for chunk in chunks[: max(0, args.sample)]:
        preview = {
            "id": chunk["id"],
            "article": chunk.get("article"),
            "page_number": chunk.get("page_number"),
            "source_document": chunk.get("source_document"),
            "text_preview": (chunk.get("text") or "")[:180].replace("\n", " "),
        }
        print(json.dumps(preview, ensure_ascii=False, indent=2))

    if args.dry_run:
        print("Dry run complete — no Pinecone upsert.")
        return 0

    _upsert_pinecone(chunks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
