from io import BytesIO

import pytest
from pypdf import PdfWriter

from app.core.config import get_settings
from app.core.exceptions import MistralServiceError
from app.services.mistral_ocr import compute_page_batches, extract_text_batched


def _make_pdf(num_pages: int) -> bytes:
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_splits_into_even_batches() -> None:
    assert compute_page_batches(40, 20) == [list(range(0, 20)), list(range(20, 40))]


def test_last_batch_is_partial() -> None:
    assert compute_page_batches(45, 20) == [
        list(range(0, 20)),
        list(range(20, 40)),
        list(range(40, 45)),
    ]


def test_fewer_pages_than_batch_size_is_one_batch() -> None:
    assert compute_page_batches(5, 20) == [list(range(0, 5))]


def test_zero_pages_is_no_batches() -> None:
    assert compute_page_batches(0, 20) == []


async def test_rejects_pdf_over_max_pages(monkeypatch) -> None:
    monkeypatch.setenv("OCR_MAX_PAGES", "1")
    monkeypatch.setenv("MISTRAL_API_KEY", "dummy-for-this-test")
    get_settings.cache_clear()
    settings = get_settings()

    two_page_pdf = _make_pdf(2)

    with pytest.raises(MistralServiceError, match="maximum is 1"):
        async for _ in extract_text_batched(
            filename="book.pdf",
            content_type="application/pdf",
            content=two_page_pdf,
            settings=settings,
        ):
            pass

    get_settings.cache_clear()


async def test_rejects_pdf_with_no_pages(monkeypatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "dummy-for-this-test")
    get_settings.cache_clear()
    settings = get_settings()

    empty_pdf = _make_pdf(0)

    with pytest.raises(MistralServiceError, match="no pages"):
        async for _ in extract_text_batched(
            filename="empty.pdf",
            content_type="application/pdf",
            content=empty_pdf,
            settings=settings,
        ):
            pass

    get_settings.cache_clear()
