"""Pure-logic tests for chunking + provenance verification (no PDF needed)."""
import pytest
pytest.importorskip("pdfplumber")
from pdf_parser import pages_from_text, build_chunks, locate_source, ParsedPage, _tokens, parse_pdf, PdfParseError


def page(n, text):
    return ParsedPage(page=n, text=text, tokens=_tokens(text))


def test_locate_source_finds_correct_page():
    pages = [page(1, "Patient has hypertension"), page(2, "Total Cholesterol | 240 | mg/dL")]
    assert locate_source("Total cholesterol 240 mg/dL", pages) == (2, True)


def test_locate_source_rejects_hallucinated_quote():
    pages = [page(1, "Patient has hypertension")]
    assert locate_source("Patient suffers from severe diabetes mellitus", pages) == (None, False)


def test_locate_source_empty():
    assert locate_source(None, [page(1, "x")]) == (None, False)


def test_chunks_never_split_pages():
    pages = [page(i, "word " * 100) for i in range(1, 6)]
    chunks = build_chunks(pages, max_chars=700)
    assert len(chunks) > 1
    assert all(c.count("--- PAGE") >= 1 for c in chunks)
    assert sum(c.count("--- PAGE") for c in chunks) == 5


def test_pages_from_text_wraps_single_page():
    p = pages_from_text("  Hello   world \n\n")
    assert len(p) == 1 and p[0].text == "Hello world"


def test_parse_pdf_rejects_non_pdf():
    with pytest.raises(PdfParseError):
        parse_pdf(b"not a pdf")