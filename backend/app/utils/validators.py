"""Upload validation (PRD §78/§86) — reject before ever calling Mistral."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.constants import ALLOWED_OCR_CONTENT_TYPES, ALLOWED_OCR_EXTENSIONS
from app.utils.file import file_extension


def validate_ocr_upload(
    *, filename: str, content_type: str | None, size: int, max_bytes: int
) -> None:
    if size == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The uploaded file is empty.")

    if size > max_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, "File exceeds maximum size."
        )

    extension_ok = file_extension(filename) in ALLOWED_OCR_EXTENSIONS
    content_type_ok = content_type in ALLOWED_OCR_CONTENT_TYPES
    if not (extension_ok and content_type_ok):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Only PDF, JPG, PNG are supported.",
        )


def validate_audio_upload(*, size: int, max_bytes: int) -> None:
    if size == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No audio was received.")

    if size > max_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, "Audio exceeds maximum size."
        )
