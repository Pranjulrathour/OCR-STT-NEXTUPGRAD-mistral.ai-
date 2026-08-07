"""OCR service — the only module that talks to Mistral's OCR API (ADR 0001).

Verified against ``mistralai==2.9.1``'s actual SDK surface (not guessed):
``client.ocr.process_async(model=..., document=...)`` returns an
``OCRResponse`` whose ``.pages`` is a list of ``OCRPageObject``, each with a
``.markdown`` field. Documents are passed as a base64 data URI keyed
``document_url`` (PDF) or ``image_url`` (image) — see
``mistralai.client.models.ocrrequest`` for the full ``DocumentUnion`` if this
ever needs pagination/annotation options beyond what's used here.

Book-scale PDFs are OCR'd in page batches (``extract_text_batched``) instead
of one call, using ``process_async(..., pages=[...])`` — verified the SDK's
``Pages`` type is ``Union[str, list[int]]``, i.e. Mistral will happily OCR a
specific subset of page indices. This is what makes real "page 45 of 320"
progress possible; without it, a single call for the whole book would be an
opaque multi-minute black box. Mistral's response carries no "total pages in
the source document" field independent of what was requested (only
``usage_info.pages_processed``, which just reflects the current call) — so
total page count is read locally via ``pypdf`` before any Mistral call.
"""

from __future__ import annotations

import asyncio
import base64
import re
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from io import BytesIO
from typing import Literal

from mistralai.client import Mistral
from mistralai.client.models.documenturlchunk import DocumentURLChunk
from mistralai.client.models.imageurlchunk import ImageURLChunk
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

from app.core.config import Settings
from app.core.exceptions import MistralServiceError, MistralTimeoutError
from app.core.mistral_client import get_mistral_client

_MARKDOWN_NOISE = re.compile(
    r"(?:!\[[^\]]*\]\([^)]*\)|\[([^\]]*)\]\([^)]*\)|[#>*_`~-])"
)


def _markdown_to_plain_text(markdown: str) -> str:
    """Lightweight strip — good enough for a "Plain Text" tab, not a full parser."""
    without_links_and_images = _MARKDOWN_NOISE.sub(lambda m: m.group(1) or "", markdown)
    return re.sub(r"\n{3,}", "\n\n", without_links_and_images).strip()


@dataclass(frozen=True, slots=True)
class OcrPage:
    index: int
    markdown: str
    plain_text: str


@dataclass(frozen=True, slots=True)
class OcrResult:
    filename: str
    pages: int
    markdown: str
    plain_text: str
    processing_time: float
    model: str
    page_contents: list[OcrPage]


@dataclass(frozen=True, slots=True)
class OcrProgressEvent:
    kind: Literal["total_pages", "progress", "done"]
    total_pages: int | None = None
    pages_done: int | None = None
    # Sorted 0-based page indices completed so far -- a full snapshot each
    # time, not a delta, so the frontend can render a real page-by-page
    # status grid without needing to reconcile missed/out-of-order events
    # (batches complete concurrently, not strictly in page order).
    completed_pages: list[int] | None = None
    result: OcrResult | None = None


def compute_page_batches(total_pages: int, batch_size: int) -> list[list[int]]:
    """Splits ``[0, total_pages)`` into contiguous batches of ``batch_size``
    page indices — pure function, kept separate from any I/O so it's cheap
    to unit test.
    """
    return [
        list(range(start, min(start + batch_size, total_pages)))
        for start in range(0, total_pages, batch_size)
    ]


async def extract_text(
    *, filename: str, content_type: str, content: bytes, settings: Settings
) -> OcrResult:
    client = get_mistral_client()
    encoded = base64.b64encode(content).decode("ascii")

    data_uri = f"data:{content_type};base64,{encoded}"
    document: DocumentURLChunk | ImageURLChunk = (
        DocumentURLChunk(document_url=data_uri)
        if content_type == "application/pdf"
        else ImageURLChunk(image_url=data_uri)
    )

    start = time.perf_counter()
    try:
        response = await asyncio.wait_for(
            client.ocr.process_async(model=settings.ocr_model, document=document),
            timeout=settings.ocr_timeout_seconds,
        )
    except TimeoutError as exc:
        raise MistralTimeoutError("Processing timeout") from exc
    except Exception as exc:
        raise MistralServiceError(
            "Unable to process your file. Please try again."
        ) from exc
    processing_time = time.perf_counter() - start

    pages = response.pages or []
    markdown = "\n\n".join(page.markdown for page in pages)

    if not markdown.strip():
        raise MistralServiceError("No text detected in this document.")

    page_contents = [
        OcrPage(
            index=page.index,
            markdown=page.markdown,
            plain_text=_markdown_to_plain_text(page.markdown),
        )
        for page in pages
    ]

    return OcrResult(
        filename=filename,
        pages=len(pages),
        markdown=markdown,
        plain_text=_markdown_to_plain_text(markdown),
        processing_time=processing_time,
        model=settings.ocr_model,
        page_contents=page_contents,
    )


async def _ocr_one_batch(
    client: Mistral,
    reader: PdfReader,
    batch_indices: list[int],
    settings: Settings,
) -> list[OcrPage]:
    """OCRs one batch by slicing just its pages into their own small PDF
    instead of re-sending the entire document. Mistral's `pages` param
    only *selects* which pages of an uploaded document get OCR'd -- it
    still requires the whole document body on every call, so a book-scale
    PDF would otherwise be re-uploaded in full on every single batch (14
    times over for a 277-page book at the default batch size). That
    repeated ~100MB+ payload is what crashed the deployed backend on a
    real book in production (confirmed by calling Mistral directly with
    the same batch, which succeeded fine outside the memory-constrained
    container) even though each batch itself is well within Mistral's own
    limits.
    """
    writer = PdfWriter()
    for page_index in batch_indices:
        writer.add_page(reader.pages[page_index])
    batch_buffer = BytesIO()
    writer.write(batch_buffer)
    batch_encoded = base64.b64encode(batch_buffer.getvalue()).decode("ascii")
    batch_data_uri = f"data:application/pdf;base64,{batch_encoded}"

    try:
        response = await asyncio.wait_for(
            client.ocr.process_async(
                model=settings.ocr_model,
                document=DocumentURLChunk(document_url=batch_data_uri),
            ),
            timeout=settings.ocr_batch_timeout_seconds(len(batch_indices)),
        )
    except TimeoutError as exc:
        raise MistralTimeoutError("Processing timeout") from exc
    except Exception as exc:
        raise MistralServiceError(
            "Unable to process your file. Please try again."
        ) from exc

    return [
        OcrPage(
            index=batch_indices[page.index],
            markdown=page.markdown,
            plain_text=_markdown_to_plain_text(page.markdown),
        )
        for page in response.pages or []
    ]


async def extract_text_batched(
    *, filename: str, content_type: str, content: bytes, settings: Settings
) -> AsyncIterator[OcrProgressEvent]:
    """Yields progress as a multi-page PDF is OCR'd batch by batch. Images
    (never multi-page) take a single-shot fast path through ``extract_text``
    and just report "1 of 1" so callers don't need two code paths.
    """
    if content_type != "application/pdf":
        yield OcrProgressEvent(kind="total_pages", total_pages=1)
        result = await extract_text(
            filename=filename,
            content_type=content_type,
            content=content,
            settings=settings,
        )
        yield OcrProgressEvent(
            kind="progress", pages_done=1, total_pages=1, completed_pages=[0]
        )
        yield OcrProgressEvent(kind="done", result=result)
        return

    try:
        reader = PdfReader(BytesIO(content))
        total_pages = len(reader.pages)
    except PdfReadError as exc:
        raise MistralServiceError(
            "Unable to read this PDF. It may be corrupted or password protected."
        ) from exc

    if total_pages == 0:
        raise MistralServiceError("This PDF has no pages.")
    if total_pages > settings.ocr_max_pages:
        raise MistralServiceError(
            f"This PDF has {total_pages} pages; the maximum is "
            f"{settings.ocr_max_pages}."
        )

    yield OcrProgressEvent(kind="total_pages", total_pages=total_pages)

    client = get_mistral_client()
    batches = compute_page_batches(total_pages, settings.ocr_batch_pages)
    all_pages: list[OcrPage] = []
    start = time.perf_counter()

    semaphore = asyncio.Semaphore(max(1, settings.ocr_batch_concurrency))

    async def run_batch(batch_indices: list[int]) -> list[OcrPage]:
        async with semaphore:
            return await _ocr_one_batch(client, reader, batch_indices, settings)

    tasks = [asyncio.create_task(run_batch(batch)) for batch in batches]
    try:
        # as_completed yields whichever batch finishes first, not
        # necessarily in page order -- running up to
        # `ocr_batch_concurrency` Mistral calls at once (rather than one
        # strictly sequential call per batch) is what turns a few-hundred-
        # page book from a serial multi-minute queue into something that
        # finishes in roughly 1/N the time, and progress now reflects real
        # completions as they land instead of a fixed schedule.
        for coro in asyncio.as_completed(tasks):
            all_pages.extend(await coro)
            yield OcrProgressEvent(
                kind="progress",
                pages_done=len(all_pages),
                total_pages=total_pages,
                completed_pages=sorted(page.index for page in all_pages),
            )
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    processing_time = time.perf_counter() - start
    all_pages.sort(key=lambda page: page.index)
    markdown = "\n\n".join(page.markdown for page in all_pages)

    if not markdown.strip():
        raise MistralServiceError("No text detected in this document.")

    result = OcrResult(
        filename=filename,
        pages=len(all_pages),
        markdown=markdown,
        plain_text=_markdown_to_plain_text(markdown),
        processing_time=processing_time,
        model=settings.ocr_model,
        page_contents=all_pages,
    )
    yield OcrProgressEvent(kind="done", result=result)
