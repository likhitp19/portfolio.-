"""Legal PDF → citation-ready chunks (page + source preserved).

Used by ``backend/scripts/ingest_pdfs.py`` and offline RAG fallbacks.
Does not call Pinecone or embedding APIs.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_ARTICLE_LINE = re.compile(
    r"(?im)^(?P<header>(?:ARTICLE|Chapter|CHAPTER|Appendix|APPENDIX)\s+[A-Z0-9][^\n]{0,120})$"
)


def promote_legal_headers(text: str) -> str:
    """Turn ARTICLE / CHAPTER / APPENDIX lines into Markdown ``##`` headings."""

    def _repl(match: re.Match[str]) -> str:
        header = match.group("header").strip()
        if header.startswith("#"):
            return header
        return "## {0}".format(header)

    return _ARTICLE_LINE.sub(_repl, text or "")


def extract_pdf_pages(pdf_path: Path) -> List[Tuple[int, str]]:
    """Return ``(page_number, text)`` pairs (1-indexed) via PyMuPDF."""
    import fitz  # PyMuPDF

    document = fitz.open(pdf_path)
    pages: List[Tuple[int, str]] = []
    try:
        for index in range(len(document)):
            page = document.load_page(index)
            text = page.get_text("text") or ""
            pages.append((index + 1, text))
    finally:
        document.close()
    return pages


def _split_markdown_headers(markdown: str) -> List[Dict[str, str]]:
    """Split on ``##`` headers; prefer LangChain MarkdownHeaderTextSplitter when installed."""
    cleaned = (markdown or "").strip()
    if not cleaned:
        return []

    try:
        from langchain_text_splitters import MarkdownHeaderTextSplitter

        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("##", "article")],
            strip_headers=False,
        )
        docs = splitter.split_text(cleaned)
        out: List[Dict[str, str]] = []
        for doc in docs:
            meta = dict(doc.metadata or {})
            article = str(meta.get("article") or "").strip()
            body = (doc.page_content or "").strip()
            if len(body) < 40:
                continue
            if not article:
                first = body.splitlines()[0].lstrip("# ").strip() if body else ""
                article = first[:160]
            out.append({"article": article, "text": body})
        if out:
            return out
    except Exception:
        pass

    # Manual fallback: same semantics without LangChain.
    chunks: List[Dict[str, str]] = []
    current_article = "Preamble"
    current_lines: List[str] = []
    for line in cleaned.splitlines():
        if line.startswith("## "):
            if current_lines:
                body = "\n".join(current_lines).strip()
                if len(body) >= 40:
                    chunks.append({"article": current_article, "text": body})
            current_article = line[3:].strip()[:160] or "Section"
            current_lines = [line]
            continue
        current_lines.append(line)
    if current_lines:
        body = "\n".join(current_lines).strip()
        if len(body) >= 40:
            chunks.append({"article": current_article, "text": body})
    return chunks


def _recursive_legal_split(text: str, *, max_chars: int = 3500) -> List[str]:
    """Further split oversized clauses on Article/Chapter/paragraph boundaries only."""
    body = (text or "").strip()
    if len(body) <= max_chars:
        return [body] if body else []

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chars,
            chunk_overlap=200,
            separators=[
                "\n## ",
                "\nARTICLE ",
                "\nArticle ",
                "\nCHAPTER ",
                "\nChapter ",
                "\nAPPENDIX ",
                "\nAppendix ",
                "\n\n",
                "\n",
                " ",
            ],
            keep_separator=True,
            length_function=len,
        )
        parts = [part.strip() for part in splitter.split_text(body) if part.strip()]
        return parts or [body]
    except Exception:
        # Soft paragraph pack without mid-word cuts.
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        packed: List[str] = []
        current = ""
        for paragraph in paragraphs:
            candidate = "{0}\n\n{1}".format(current, paragraph).strip() if current else paragraph
            if len(candidate) <= max_chars:
                current = candidate
                continue
            if current:
                packed.append(current)
            current = paragraph
        if current:
            packed.append(current)
        return packed or [body]


def chunk_pdf(
    pdf_path: Path,
    *,
    source_document: Optional[str] = None,
    max_chars: int = 3500,
) -> List[Dict[str, Any]]:
    """Extract and chunk one PDF into citation-ready dicts."""
    path = Path(pdf_path)
    source = source_document or path.name
    pages = extract_pdf_pages(path)
    chunks: List[Dict[str, Any]] = []

    for page_number, raw_text in pages:
        if not (raw_text or "").strip():
            continue
        markdown = promote_legal_headers(raw_text)
        # Ensure at least one header so the splitter keeps page text.
        if "## " not in markdown:
            markdown = "## Page {0}\n\n{1}".format(page_number, markdown)
        for section in _split_markdown_headers(markdown):
            for part_index, part in enumerate(_recursive_legal_split(section["text"], max_chars=max_chars)):
                article = section.get("article") or "Page {0}".format(page_number)
                chunk_id = hashlib.sha1(
                    "{0}|{1}|{2}|{3}".format(source, page_number, article, part_index).encode("utf-8")
                ).hexdigest()[:16]
                chunks.append(
                    {
                        "id": "fia-{0}".format(chunk_id),
                        "text": part,
                        "article": article[:200],
                        "title": article[:200],
                        "page_number": int(page_number),
                        "source": source,
                        "source_document": source,
                    }
                )
    return chunks


def chunk_pdfs(
    pdf_dir: Path,
    *,
    patterns: Sequence[str] = ("*.pdf", "*.PDF"),
    max_chars: int = 3500,
) -> List[Dict[str, Any]]:
    """Chunk all PDFs under ``pdf_dir``."""
    root = Path(pdf_dir)
    paths: List[Path] = []
    for pattern in patterns:
        paths.extend(sorted(root.glob(pattern)))
    # De-dupe while preserving order.
    seen = set()
    unique: List[Path] = []
    for path in paths:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)

    all_chunks: List[Dict[str, Any]] = []
    for path in unique:
        all_chunks.extend(chunk_pdf(path, max_chars=max_chars))
    return all_chunks
