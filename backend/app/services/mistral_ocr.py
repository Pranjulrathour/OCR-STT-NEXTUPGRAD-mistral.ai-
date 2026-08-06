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

from mistralai.client.models.documenturlchunk import DocumentURLChunk
from mistralai.client.models.imageurlchunk import ImageURLChunk
from pypdf import PdfReader
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
        yield OcrProgressEvent(kind="progress", pages_done=1, total_pages=1)
        yield OcrProgressEvent(kind="done", result=result)
        return

    try:
        total_pages = len(PdfReader(BytesIO(content)).pages)
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
    encoded = base64.b64encode(content).decode("ascii")
    data_uri = f"data:{content_type};base64,{encoded}"

    batches = compute_page_batches(total_pages, settings.ocr_batch_pages)
    all_pages: list[OcrPage] = []
    start = time.perf_counter()

    for batch_indices in batches:
        try:
            response = await asyncio.wait_for(
                client.ocr.process_async(
                    model=settings.ocr_model,
                    document=DocumentURLChunk(document_url=data_uri),
                    pages=batch_indices,
                ),
                timeout=settings.ocr_batch_timeout_seconds(len(batch_indices)),
            )
        except TimeoutError as exc:
            raise MistralTimeoutError("Processing timeout") from exc
        except Exception as exc:
            raise MistralServiceError(
                "Unable to process your file. Please try again."
            ) from exc

        for page in response.pages or []:
            all_pages.append(
                OcrPage(
                    index=page.index,
                    markdown=page.markdown,
                    plain_text=_markdown_to_plain_text(page.markdown),
                )
            )

        yield OcrProgressEvent(
            kind="progress", pages_done=len(all_pages), total_pages=total_pages
        )

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
