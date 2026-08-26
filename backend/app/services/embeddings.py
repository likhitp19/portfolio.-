"""Shared embedding helpers for Pinecone ingest + retrieve."""

from __future__ import annotations

from typing import List, Optional, Sequence

import httpx

from app.config import settings


def embed_texts(texts: Sequence[str], *, dimensions: Optional[int] = None) -> List[List[float]]:
    """Embed texts via OpenRouter or OpenAI. Optionally truncate to ``dimensions``."""
    openrouter = settings.openrouter_key
    openai_key = (settings.openai_api_key or "").strip()
    if openrouter:
        base = settings.openrouter_base_url.rstrip("/")
        api_key = openrouter
        model = settings.embedding_model
    elif openai_key:
        base = "https://api.openai.com/v1"
        api_key = openai_key
        model = settings.embedding_model.split("/")[-1]
    else:
        raise RuntimeError(
            "Embedding key missing. Set OPENROUTER_API_KEY or OPENAI_API_KEY."
        )

    dim = dimensions if dimensions is not None else int(settings.embedding_dimensions or 0) or None
    vectors: List[List[float]] = []
    with httpx.Client(timeout=120.0) as client:
        for start in range(0, len(texts), 16):
            batch = list(texts[start : start + 16])
            body = {"model": model, "input": batch}
            if dim:
                body["dimensions"] = int(dim)
            response = client.post(
                "{0}/embeddings".format(base),
                headers={
                    "Authorization": "Bearer {0}".format(api_key),
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/apex-analytics/protest-engine",
                    "X-Title": "FIA Protest Engine",
                },
                json=body,
            )
            if response.status_code >= 400:
                raise RuntimeError(
                    "Embedding request failed ({0}): {1}".format(
                        response.status_code, response.text[:500]
                    )
                )
            payload = response.json()
            data = sorted(payload.get("data") or [], key=lambda row: row.get("index", 0))
            if len(data) != len(batch):
                raise RuntimeError("Embedding API returned unexpected batch size.")
            for row in data:
                vectors.append([float(value) for value in (row.get("embedding") or [])])
    return vectors


def embed_query(query: str, *, dimensions: Optional[int] = None) -> Optional[List[float]]:
    try:
        vectors = embed_texts([query], dimensions=dimensions)
    except Exception:
        return None
    return vectors[0] if vectors else None
