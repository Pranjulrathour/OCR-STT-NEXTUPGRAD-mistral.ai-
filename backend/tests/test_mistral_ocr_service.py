import pytest

from app.core.config import Settings
from app.core.exceptions import MistralServiceError
from app.services.mistral_ocr import extract_text, extract_text_batched


def make_settings(**overrides) -> Settings:
    return Settings(mistral_api_key="test-key", **overrides)


async def test_extract_text_success(fake_ocr_client) -> None:
    result = await extract_text(
        filename="doc.png",
        content_type="image/png",
        content=b"fake-image-bytes",
        settings=make_settings(),
    )

    assert result.pages == 1
    assert result.page_contents[0].index == 0
    assert "content for page 0" in result.markdown
    assert result.model == "mistral-ocr-latest"


async def test_extract_text_raises_when_no_text_detected(fake_ocr_client) -> None:
    fake_ocr_client.ocr.process_async = lambda **kwargs: _empty_response()

    with pytest.raises(MistralServiceError, match="No text detected"):
        await extract_text(
            filename="blank.png",
            content_type="image/png",
            content=b"fake",
            settings=make_settings(),
        )


async def _empty_response():
    from types import SimpleNamespace

    return SimpleNamespace(pages=[])


async def test_extract_text_batched_multi_batch_preserves_order(
    fake_ocr_client,
) -> None:
    import io

    from pypdf import PdfWriter

    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=72, height=72)
    buffer = io.BytesIO()
    writer.write(buffer)

    settings = make_settings(ocr_batch_pages=2)

    events = [
        event
        async for event in extract_text_batched(
            filename="book.pdf",
            content_type="application/pdf",
            content=buffer.getvalue(),
            settings=settings,
        )
    ]

    assert events[0].kind == "total_pages"
    assert events[0].total_pages == 5

    progress_events = [e for e in events if e.kind == "progress"]
    assert [e.pages_done for e in progress_events] == [2, 4, 5]

    done_event = events[-1]
    assert done_event.kind == "done"
    assert done_event.result.pages == 5
    assert [p.index for p in done_event.result.page_contents] == [0, 1, 2, 3, 4]

    # Three batches of [0,1], [2,3], [4] pages each — verifies the batching
    # math actually drove three separate Mistral calls, not one call with
    # all pages. Each call now sends its own sliced sub-PDF rather than a
    # `pages` filter (see mistral_ocr.py), so `calls` records `None` for
    # each — the batch boundaries are verified via `progress_events` above.
    assert fake_ocr_client.calls == [None, None, None]


async def test_extract_text_batched_image_is_single_batch(fake_ocr_client) -> None:
    events = [
        event
        async for event in extract_text_batched(
            filename="photo.jpg",
            content_type="image/jpeg",
            content=b"fake-image",
            settings=make_settings(),
        )
    ]

    kinds = [e.kind for e in events]
    assert kinds == ["total_pages", "progress", "done"]
    assert events[0].total_pages == 1
    assert events[-1].result.pages == 1
