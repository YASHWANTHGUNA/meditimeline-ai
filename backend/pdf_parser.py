"""
pdf_parser.py — digital-PDF text extraction, chunking and source verification.

Pipeline (mirrors the aceresults flow: parse -> validate -> persist):
  1. parse_pdf()       deterministic text extraction per page (pdfplumber), tables kept as rows
  2. build_chunks()    page-aligned chunks that fit comfortably in one LLM call
  3. (services.py)     Gemini extracts structured events from each chunk
  4. locate_source()   deterministic check: does the quoted source text really exist in the PDF?
                       Also tells us which page it came from (we never trust the LLM for that).
"""
import io
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pdfplumber

MAX_PAGES = 40
MIN_CHARS_PER_PAGE = 25        # below this on average => probably a scanned PDF
CHUNK_CHAR_BUDGET = 12000      # approx. chars per LLM call
VERIFY_THRESHOLD = 0.85        # share of source-text tokens that must appear on a page


class PdfParseError(Exception):
    """Raised for unreadable, scanned or oversized PDFs. Message is safe to show to users."""


@dataclass
class ParsedPage:
    page: int
    text: str
    tokens: frozenset


@dataclass
class ParsedPdf:
    pages: List[ParsedPage]
    page_count: int
    char_count: int


_WS = re.compile(r"[ \t]+")
_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> frozenset:
    return frozenset(_TOKEN.findall((text or "").lower()))


def _clean(text: str) -> str:
    lines = [_WS.sub(" ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def _table_rows(table) -> List[str]:
    """Turn a pdfplumber table into 'cell | cell | cell' rows (lab reports are mostly tables)."""
    rows = []
    for row in table:
        cells = [_WS.sub(" ", (c or "").replace("\n", " ")).strip() for c in row]
        cells = [c for c in cells if c]
        if cells:
            rows.append(" | ".join(cells))
    return rows


def _extract_page_text(page) -> str:
    """Prose outside tables + table rows. Falls back to plain text if anything goes wrong."""
    # Use tighter x_tolerance (1 instead of default 3) to prevent squished words
    x_tol = 1
    
    try:
        tables = page.find_tables({"text_x_tolerance": x_tol})
        if tables:
            prose_page = page
            for t in tables:
                prose_page = prose_page.outside_bbox(t.bbox)
            prose = prose_page.extract_text(x_tolerance=x_tol) or ""
            rows: List[str] = []
            for t in tables:
                rows.extend(_table_rows(t.extract(x_tolerance=x_tol)))
            return _clean(prose + "\n" + "\n".join(rows))
    except Exception:
        pass
    return _clean(page.extract_text(x_tolerance=x_tol) or "")


def pages_from_text(text: str) -> List[ParsedPage]:
    """Wrap pasted text as a single 'page' so the same verification works for text input."""
    cleaned = _clean(text)
    return [ParsedPage(page=1, text=cleaned, tokens=_tokens(cleaned))]


def parse_pdf(data: bytes) -> ParsedPdf:
    """Synchronous + CPU bound: call via asyncio.to_thread() from async code."""
    if not data.startswith(b"%PDF"):
        raise PdfParseError("File is not a valid PDF.")

    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            n_pages = len(pdf.pages)
            if n_pages == 0:
                raise PdfParseError("The PDF has no pages.")
            if n_pages > MAX_PAGES:
                raise PdfParseError(f"PDF has {n_pages} pages; the limit is {MAX_PAGES}.")

            pages: List[ParsedPage] = []
            for i, page in enumerate(pdf.pages, start=1):
                text = _extract_page_text(page)
                pages.append(ParsedPage(page=i, text=text, tokens=_tokens(text)))
    except PdfParseError:
        raise
    except Exception as e:
        raise PdfParseError(
            "Could not read this PDF (it may be corrupted or password-protected)."
        ) from e

    total_chars = sum(len(p.text) for p in pages)
    if total_chars < MIN_CHARS_PER_PAGE * len(pages):
        raise PdfParseError(
            "This PDF has no selectable text (it looks scanned). "
            "Scanned/image reports are not supported yet - please upload a digital PDF."
        )

    return ParsedPdf(pages=pages, page_count=len(pages), char_count=total_chars)


def build_chunks(pages: List[ParsedPage], max_chars: int = CHUNK_CHAR_BUDGET) -> List[str]:
    """Group whole pages into chunks; page boundaries are never split."""
    chunks: List[str] = []
    current: List[str] = []
    size = 0
    for p in pages:
        if not p.text:
            continue
        block = f"--- PAGE {p.page} ---\n{p.text}"
        if current and size + len(block) > max_chars:
            chunks.append("\n\n".join(current))
            current, size = [], 0
        current.append(block)
        size += len(block)
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def locate_source(source_text: Optional[str], pages: List[ParsedPage]) -> Tuple[Optional[int], bool]:
    """
    Returns (page_number, verified).
    verified=True only if >= VERIFY_THRESHOLD of the quoted tokens appear on a single page.
    Token-overlap (not exact match) so table rows like 'Total Cholesterol | 240 | mg/dL'
    still match a quote like 'Total cholesterol 240 mg/dL'.
    """
    src = _tokens(source_text or "")
    if not src:
        return None, False

    best_page, best_score = None, 0.0
    for p in pages:
        score = len(src & p.tokens) / len(src)
        if score > best_score:
            best_score, best_page = score, p.page

    if best_score >= VERIFY_THRESHOLD:
        return best_page, True
    return None, False
