from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.config import settings

_CORPUS_PATH = Path(__file__).resolve().parents[1] / "data" / "fia_driving_standards.md"
COLLECTION_NAME = "fia_driving_standards"
EMBED_DIM_DEFAULT = 1536


def _tokenize(text: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(token) > 1]


def split_corpus(markdown: str) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    current_title = "Driving standards"
    current_lines: List[str] = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            if current_lines:
                chunks.append(
                    {
                        "title": current_title,
                        "text": "\n".join(current_lines).strip(),
                        "page_number": 0,
                        "source_document": "fia_driving_standards.md",
                        "source": "fia_driving_standards.md",
                        "article": current_title,
                    }
                )
            current_title = line[3:].strip()
            current_lines = [line]
            continue
        current_lines.append(line)
    if current_lines:
        chunks.append(
            {
                "title": current_title,
                "text": "\n".join(current_lines).strip(),
                "page_number": 0,
                "source_document": "fia_driving_standards.md",
                "source": "fia_driving_standards.md",
                "article": current_title,
            }
        )
    return [chunk for chunk in chunks if len(chunk["text"]) > 40]


def _overlap_score(query: str, document: str) -> float:
    query_tokens = set(_tokenize(query))
    doc_tokens = _tokenize(document)
    if not query_tokens or not doc_tokens:
        return 0.0
    hits = sum(1 for token in doc_tokens if token in query_tokens)
    return hits / math.sqrt(len(doc_tokens))


def _bm25_light(query: str, documents: Sequence[str]) -> List[float]:
    """Tiny BM25-ish scorer for hybrid merge (no external dependency)."""
    query_tokens = _tokenize(query)
    if not query_tokens or not documents:
        return [0.0] * len(documents)
    doc_tokens = [_tokenize(doc) for doc in documents]
    df: Dict[str, int] = {}
    for tokens in doc_tokens:
        for token in set(tokens):
            df[token] = df.get(token, 0) + 1
    n_docs = len(documents)
    avgdl = sum(len(tokens) for tokens in doc_tokens) / max(1, n_docs)
    k1 = 1.2
    b = 0.75
    scores: List[float] = []
    for tokens in doc_tokens:
        tf: Dict[str, int] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        score = 0.0
        dl = len(tokens) or 1
        for token in query_tokens:
            freq = tf.get(token, 0)
            if not freq:
                continue
            idf = math.log(1 + (n_docs - df.get(token, 0) + 0.5) / (df.get(token, 0) + 0.5))
            denom = freq + k1 * (1 - b + b * dl / avgdl)
            score += idf * (freq * (k1 + 1)) / denom
        scores.append(score)
    return scores


class RuleRetriever:
    def __init__(
        self,
        corpus_path: Optional[Path] = None,
        persist_dir: Optional[Path] = None,
        use_chroma: bool = True,
        use_pinecone: Optional[bool] = None,
    ) -> None:
        self.corpus_path = corpus_path or _CORPUS_PATH
        persist = persist_dir
        if persist is None:
            persist = Path(settings.chroma_persist_dir)
            if not persist.is_absolute():
                persist = Path(__file__).resolve().parents[2] / persist
        self.persist_dir = persist
        self.chunks = split_corpus(self.corpus_path.read_text(encoding="utf-8"))
        self._collection = None
        self._use_pinecone = (
            bool(settings.pinecone_key) if use_pinecone is None else bool(use_pinecone)
        )
        if use_chroma and getattr(settings, "steward_use_chroma", True) and not self._use_pinecone:
            self._collection = self._try_chroma()

    def _try_chroma(self) -> Any:
        try:
            import chromadb
        except Exception:
            return None
        try:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(self.persist_dir))
            collection = client.get_or_create_collection(
                name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
            )
            if collection.count() < len(self.chunks):
                collection.upsert(
                    ids=["fia-{0}".format(index) for index, _ in enumerate(self.chunks)],
                    documents=[chunk["text"] for chunk in self.chunks],
                    metadatas=[
                        {
                            "title": chunk["title"],
                            "page_number": int(chunk.get("page_number") or 0),
                            "source_document": chunk.get("source_document") or "",
                            "article": chunk.get("article") or chunk["title"],
                        }
                        for chunk in self.chunks
                    ],
                )
            return collection
        except Exception:
            return None

    def retrieve_rules(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        cleaned = (query or "").strip()
        if not cleaned:
            return []

        pinecone_hits = self._pinecone_hits(cleaned, max(top_k * 2, top_k)) if self._use_pinecone else []
        keyword_hits = self._keyword_hits(cleaned, max(top_k * 2, top_k))
        chroma_hits = self._chroma_hits(cleaned, top_k) if not pinecone_hits else []

        merged = self._hybrid_merge(cleaned, pinecone_hits, keyword_hits, chroma_hits, top_k=top_k)
        return merged

    def _keyword_hits(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        bm25 = _bm25_light(query, [chunk["text"] for chunk in self.chunks])
        ranked = []
        for index, chunk in enumerate(self.chunks):
            overlap = _overlap_score(query, chunk["title"] + " " + chunk["text"])
            score = round(0.65 * bm25[index] + 0.35 * overlap, 4)
            ranked.append(
                {
                    "id": "fia-{0}".format(index),
                    "title": chunk["title"],
                    "text": chunk["text"],
                    "score": score,
                    "source": "keyword",
                    "page_number": int(chunk.get("page_number") or 0),
                    "source_document": chunk.get("source_document") or "fia_driving_standards.md",
                    "article": chunk.get("article") or chunk["title"],
                }
            )
        ranked.sort(key=lambda row: row["score"], reverse=True)
        return [row for row in ranked if row["score"] > 0][:top_k] or ranked[: min(top_k, len(ranked))]

    def _chroma_hits(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        if self._collection is None:
            return []
        try:
            result = self._collection.query(query_texts=[query], n_results=max(1, top_k))
        except Exception:
            return []
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        ids = (result.get("ids") or [[]])[0]
        hits: List[Dict[str, Any]] = []
        for index, text in enumerate(documents):
            distance = float(distances[index]) if index < len(distances) else 1.0
            meta = metadatas[index] if index < len(metadatas) else {}
            meta = meta or {}
            hits.append(
                {
                    "id": ids[index] if index < len(ids) else "fia-{0}".format(index),
                    "title": meta.get("title") or meta.get("article") or "",
                    "text": text,
                    "score": round(max(0.0, 1.0 - distance), 4),
                    "source": "chroma",
                    "page_number": int(meta.get("page_number") or 0),
                    "source_document": meta.get("source_document") or "fia_driving_standards.md",
                    "article": meta.get("article") or meta.get("title") or "",
                }
            )
        return hits

    def _embed_query(self, query: str) -> Optional[List[float]]:
        from app.services.embeddings import embed_query

        dim = int(getattr(settings, "embedding_dimensions", 0) or 0) or None
        # Prefer matching an existing Pinecone index dimension when available.
        if settings.pinecone_key:
            try:
                from pinecone import Pinecone

                pc = Pinecone(api_key=settings.pinecone_key)
                desc = pc.describe_index(settings.pinecone_index)
                index_dim = getattr(desc, "dimension", None)
                if index_dim:
                    dim = int(index_dim)
            except Exception:
                pass
        return embed_query(query, dimensions=dim)

    def _pinecone_hits(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        if not settings.pinecone_key:
            return []
        vector = self._embed_query(query)
        if not vector:
            return []
        try:
            from pinecone import Pinecone
        except Exception:
            return []
        try:
            pc = Pinecone(api_key=settings.pinecone_key)
            index = pc.Index(settings.pinecone_index)
            kwargs: Dict[str, Any] = {
                "vector": vector,
                "top_k": max(1, top_k),
                "include_metadata": True,
            }
            if settings.pinecone_namespace:
                kwargs["namespace"] = settings.pinecone_namespace
            result = index.query(**kwargs)
        except Exception:
            return []

        matches = getattr(result, "matches", None) or result.get("matches") or []
        hits: List[Dict[str, Any]] = []
        for match in matches:
            meta = getattr(match, "metadata", None) or match.get("metadata") or {}
            score = float(getattr(match, "score", None) or match.get("score") or 0.0)
            match_id = getattr(match, "id", None) or match.get("id") or ""
            article = str(meta.get("article") or "")
            hits.append(
                {
                    "id": match_id,
                    "title": article or str(meta.get("source_document") or ""),
                    "text": str(meta.get("text") or ""),
                    "score": round(score, 4),
                    "source": "pinecone",
                    "page_number": int(meta.get("page_number") or 0),
                    "source_document": str(
                        meta.get("source_document") or meta.get("source") or ""
                    ),
                    "article": article,
                }
            )
        return hits

    def _hybrid_merge(
        self,
        query: str,
        pinecone_hits: List[Dict[str, Any]],
        keyword_hits: List[Dict[str, Any]],
        chroma_hits: List[Dict[str, Any]],
        *,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Blend dense (Pinecone) with BM25/keyword via reciprocal rank fusion.

        When Pinecone returns hits, they are preferred so live legal PDF citations
        are not drowned out by teaching-corpus BM25 magnitudes.
        """

        def _key(row: Dict[str, Any]) -> str:
            return "{0}|{1}|{2}".format(
                row.get("source_document") or "",
                row.get("page_number") or 0,
                (row.get("id") or row.get("title") or "")[:80],
            )

        # Prefer Pinecone when available — still fuse ranks for diversity.
        ranked_lists: List[Tuple[float, List[Dict[str, Any]]]] = []
        if pinecone_hits:
            ranked_lists.append((1.35, pinecone_hits))
            ranked_lists.append((0.45, keyword_hits))
        else:
            if chroma_hits:
                ranked_lists.append((1.0, chroma_hits))
            ranked_lists.append((0.9, keyword_hits))

        rrf: Dict[str, float] = {}
        best_row: Dict[str, Dict[str, Any]] = {}
        for weight, rows in ranked_lists:
            for rank, row in enumerate(rows):
                key = _key(row)
                rrf[key] = rrf.get(key, 0.0) + weight * (1.0 / (60.0 + rank + 1.0))
                # Keep the denser / citation-complete row when keys collide.
                prior = best_row.get(key)
                if prior is None or (row.get("source") == "pinecone" and prior.get("source") != "pinecone"):
                    best_row[key] = row
                elif prior is None:
                    best_row[key] = row

        merged = []
        for key, score in sorted(rrf.items(), key=lambda item: item[1], reverse=True):
            row = dict(best_row[key])
            row["score"] = round(float(score), 4)
            # Soft boost when query tokens appear in article heading.
            article = str(row.get("article") or row.get("title") or "")
            if article and any(token.lower() in article.lower() for token in query.split() if len(token) > 3):
                row["score"] = round(float(row["score"]) + 0.02, 4)
            merged.append(row)
        if merged:
            return merged[:top_k]
        return keyword_hits[:top_k]


def get_rule_retriever() -> RuleRetriever:
    # Prefer Pinecone when keyed; otherwise Chroma/keyword teaching corpus (CI-safe).
    return RuleRetriever(use_chroma=bool(settings.steward_use_chroma))


def retrieve_rules(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    return get_rule_retriever().retrieve_rules(query, top_k=top_k)


def retrieve_regulations(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """Primary Phase 1 retrieve API — Pinecone when keyed, else offline markdown."""
    return retrieve_rules(query, top_k=top_k)
