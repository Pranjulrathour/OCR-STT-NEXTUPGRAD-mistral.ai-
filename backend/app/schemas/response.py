"""Response envelopes (PRD §85/§96) — every endpoint returns one of these shapes.

OCR and Speech success responses flatten their fields alongside ``success``
rather than nesting them under a ``data`` key (see the concrete examples in
PRD §79/§83) — the generic ``{success, data, message}`` wrapper in §85 is the
abstract shape; these models are its concrete, per-endpoint instantiations.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    success: bool = False
    message: str


class HealthResponse(BaseModel):
    """Deliberately bare — no success/message envelope (PRD §76)."""

    status: str = "healthy"
    version: str


class OcrPageResponse(BaseModel):
    index: int
    markdown: str
    plain_text: str


class OcrSuccessResponse(BaseModel):
    success: bool = True
    filename: str
    pages: int
    markdown: str
    plain_text: str
    processing_time: float
    model: str
    page_contents: list[OcrPageResponse]


class SpeechTranscribeSuccessResponse(BaseModel):
    success: bool = True
    transcript: str
    language: str
    duration: float
    processing_time: float
    model: str


class RagIndexResponse(BaseModel):
    success: bool = True
    document_id: str
    filename: str
    pages: int
    chunks: int


class RagSourceResponse(BaseModel):
    filename: str
    page: int
    score: float
    snippet: str


class RagChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class RagChatResponse(BaseModel):
    success: bool = True
    answer: str
    found: bool
    sources: list[RagSourceResponse]
