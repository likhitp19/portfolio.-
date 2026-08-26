from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

_CORPUS_PATH = Path(__file__).resolve().parents[1] / "data" / "fia_driving_standards.md"
COLLECTION_NAME = "fia_driving_standards"


def _tokenize(text: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(token) > 1]


def split_corpus(markdown: str) -> List[Dict[str, str]]:
    chunks: List[Dict[str, str]] = []
    current_title = "Driving standards"
    current_lines: List[str] = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            if current_lines:
                chunks.append({"title": current_title, "text": "\n".join(current_lines).strip()})
            current_title = line[3:].strip()
            current_lines = [line]
            continue
        current_lines.append(line)
    if current_lines:
        chunks.append({"title": current_title, "text": "\n".join(current_lines).strip()})
    return [chunk for chunk in chunks if len(chunk["text"]) > 40]


def _overlap_score(query: str, document: str) -> float:
    query_tokens = set(_tokenize(query))
    doc_tokens = _tokenize(document)
    if not query_tokens or not doc_tokens:
        return 0.0
    hits = sum(1 for token in doc_tokens if token in query_tokens)
    return hits / math.sqrt(len(doc_tokens))


class RuleRetriever:
    def __init__(
        self,
        corpus_path: Optional[Path] = None,
        persist_dir: Optional[Path] = None,
        use_chroma: bool = True,
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
        if use_chroma and getattr(settings, "steward_use_chroma", True):
            self._collection = self._try_chroma()

    def _try_chroma(self) -> Any:
        try:
            import chromadb
        except Exception:
            return None
        try:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(self.persist_dir))
            collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
            if collection.count() < len(self.chunks):
                collection.upsert(
                    ids=["fia-{0}".format(index) for index, _ in enumerate(self.chunks)],
                    documents=[chunk["text"] for chunk in self.chunks],
                    metadatas=[{"title": chunk["title"]} for chunk in self.chunks],
                )
            return collection
        except Exception:
            return None

    def retrieve_rules(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        cleaned = (query or "").strip()
        if not cleaned:
            return []
        chroma_hits = self._chroma_hits(cleaned, top_k)
        if chroma_hits:
            return chroma_hits
        ranked = sorted(
            (
                {
                    "id": "fia-{0}".format(index),
                    "title": chunk["title"],
                    "text": chunk["text"],
                    "score": round(_overlap_score(cleaned, chunk["title"] + " " + chunk["text"]), 4),
                    "source": "keyword",
                }
                for index, chunk in enumerate(self.chunks)
            ),
            key=lambda row: row["score"],
            reverse=True,
        )
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
            hits.append(
                {
                    "id": ids[index] if index < len(ids) else "fia-{0}".format(index),
                    "title": (meta or {}).get("title") or "",
                    "text": text,
                    "score": round(max(0.0, 1.0 - distance), 4),
                    "source": "chroma",
                }
            )
        return hits


def get_rule_retriever() -> RuleRetriever:
    return RuleRetriever(use_chroma=bool(settings.steward_use_chroma))


def retrieve_rules(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    return get_rule_retriever().retrieve_rules(query, top_k=top_k)
