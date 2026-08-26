#!/usr/bin/env python3
"""Scrape FIA Sporting / Appendix L PDFs into ``backend/app/data/pdfs/``.

Target: https://www.fia.com/regulation/category/110

Strict filter — download ONLY when title or filename contains ``sporting`` or
``appendix l``. Ignore Technical, Financial, Power Unit, and other packages.

If new PDFs land on disk, optionally re-run ``ingest_pdfs.py`` to refresh Pinecone.

Usage (from ``backend/``)::

    python scripts/scrape_fia_sporting.py --dry-run
    python scripts/scrape_fia_sporting.py
    python scripts/scrape_fia_sporting.py --no-ingest
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, unquote

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

CATEGORY_URL = "https://www.fia.com/regulation/category/110"
DEFAULT_PDF_DIR = BACKEND_ROOT / "app" / "data" / "pdfs"

ALLOW_RE = re.compile(r"(sporting|appendix\s*l\b|appendix-l|appendix_l)", re.I)
DENY_RE = re.compile(
    r"(technical|financial|power\s*unit|power-unit|\bpu\b|budget\s*cap|"
    r"homologation|tyre|tire\s*regulation)",
    re.I,
)

USER_AGENT = (
    "Mozilla/5.0 (compatible; ApexAnalyticsProtestEngine/1.0; "
    "+https://github.com/apex-analytics/protest-engine)"
)


def _soup(html: str):
    from bs4 import BeautifulSoup

    return BeautifulSoup(html, "html.parser")


def is_sporting_document(title: str, url: str) -> bool:
    """Return True only for Sporting / Appendix L documents."""
    blob = "{0} {1}".format(title or "", unquote(url or ""))
    if DENY_RE.search(blob) and not ALLOW_RE.search(blob):
        return False
    if DENY_RE.search(blob) and ALLOW_RE.search(blob):
        # e.g. "Sporting & Technical" — still allow if sporting/appendix l present,
        # but reject pure technical/financial/PU packages.
        if re.search(r"\btechnical\b", blob, re.I) and not re.search(r"sporting|appendix\s*l", blob, re.I):
            return False
    return bool(ALLOW_RE.search(blob))


def _filename_from_url(url: str, title: str) -> str:
    path_name = Path(urlparse(url).path).name
    if path_name.lower().endswith(".pdf"):
        safe = re.sub(r"[^\w.\-]+", "_", path_name)
        return safe
    base = re.sub(r"[^\w.\-]+", "_", (title or "fia_document").strip())[:120] or "fia_document"
    if not base.lower().endswith(".pdf"):
        base = "{0}.pdf".format(base)
    return base


def discover_pdf_candidates(html: str, base_url: str = CATEGORY_URL) -> List[Dict[str, str]]:
    """Parse category HTML for PDF links / document titles."""
    soup = _soup(html)
    found: Dict[str, Dict[str, str]] = {}

    for anchor in soup.find_all("a", href=True):
        href = (anchor.get("href") or "").strip()
        if not href:
            continue
        absolute = urljoin(base_url, href)
        text = " ".join(anchor.stripped_strings) or ""
        title_attr = (anchor.get("title") or "").strip()
        title = title_attr or text or Path(urlparse(absolute).path).name
        lowered = absolute.lower()
        looks_pdf = lowered.endswith(".pdf") or "pdf" in lowered or ".pdf?" in lowered
        if not looks_pdf and "document" not in lowered and "regulation" not in lowered:
            # Keep non-PDF anchors only when title clearly matches filter (follow later).
            if not is_sporting_document(title, absolute):
                continue
        if not is_sporting_document(title, absolute):
            continue
        if not looks_pdf:
            continue
        key = absolute.split("#", 1)[0]
        found[key] = {"url": key, "title": title}

    # Also scan plain text URLs ending in .pdf
    for match in re.finditer(r"https?://[^\s\"'<>]+\.pdf(?:\?[^\s\"'<>]*)?", html, flags=re.I):
        url = match.group(0)
        if not is_sporting_document(url, url):
            continue
        key = url.split("#", 1)[0]
        found.setdefault(key, {"url": key, "title": Path(urlparse(url).path).name})

    return list(found.values())


def fetch_category_html(session, url: str = CATEGORY_URL) -> str:
    response = session.get(url, timeout=60)
    response.raise_for_status()
    return response.text


def download_pdf(session, url: str, dest: Path) -> bool:
    """Download PDF to dest. Returns True if bytes were written (new/changed)."""
    response = session.get(url, timeout=120, stream=True)
    response.raise_for_status()
    content_type = (response.headers.get("content-type") or "").lower()
    payload = response.content
    if "html" in content_type and not payload.startswith(b"%PDF"):
        raise RuntimeError("Expected PDF, got HTML from {0}".format(url))
    if not payload.startswith(b"%PDF"):
        # Some FIA endpoints wrap PDFs; still write if large binary-ish.
        if len(payload) < 1000:
            raise RuntimeError("Response too small to be a PDF: {0}".format(url))

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file():
        existing = dest.read_bytes()
        if hashlib.sha256(existing).digest() == hashlib.sha256(payload).digest():
            return False
    dest.write_bytes(payload)
    return True


def run_ingest() -> int:
    ingest = BACKEND_ROOT / "scripts" / "ingest_pdfs.py"
    print("New PDFs detected — triggering Pinecone ingest…")
    completed = subprocess.run(
        [sys.executable, str(ingest)],
        cwd=str(BACKEND_ROOT),
        check=False,
    )
    return int(completed.returncode)


def scrape(
    *,
    pdf_dir: Path,
    dry_run: bool = False,
    ingest: bool = True,
    category_url: str = CATEGORY_URL,
) -> Tuple[int, int]:
    import requests

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,*/*"})

    print("Fetching {0}".format(category_url))
    html = fetch_category_html(session, category_url)
    candidates = discover_pdf_candidates(html, category_url)
    print("Matched Sporting / Appendix L PDF candidates: {0}".format(len(candidates)))
    for item in candidates:
        print("  - {0} | {1}".format(item["title"][:80], item["url"]))

    if dry_run:
        print("Dry run — no downloads.")
        return 0, len(candidates)

    downloaded = 0
    for item in candidates:
        name = _filename_from_url(item["url"], item["title"])
        dest = pdf_dir / name
        try:
            changed = download_pdf(session, item["url"], dest)
        except Exception as exc:
            print("  ! skip {0}: {1}".format(item["url"], exc))
            continue
        if changed:
            downloaded += 1
            print("  + saved {0}".format(dest.name))
        else:
            print("  = unchanged {0}".format(dest.name))
        time.sleep(0.4)

    if downloaded and ingest:
        code = run_ingest()
        if code != 0:
            raise SystemExit("ingest_pdfs.py failed with exit code {0}".format(code))
    elif downloaded:
        print("Skipped ingest (--no-ingest).")
    else:
        print("No new PDFs — ingest not required.")

    return downloaded, len(candidates)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Scrape FIA Sporting / Appendix L PDFs")
    parser.add_argument("--pdf-dir", type=Path, default=DEFAULT_PDF_DIR)
    parser.add_argument("--url", default=CATEGORY_URL)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-ingest", action="store_true")
    args = parser.parse_args(argv)

    try:
        scrape(
            pdf_dir=args.pdf_dir,
            dry_run=args.dry_run,
            ingest=not args.no_ingest,
            category_url=args.url,
        )
    except Exception as exc:
        print("Scrape failed: {0}".format(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
