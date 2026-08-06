"""Filename sanitization and content-type sniffing (PRD §92).

Never trust a client-supplied filename or ``Content-Type`` header on its own
— they are attacker-controlled input, sanitized here before being used in a
response or logged.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_filename(raw_name: str | None) -> str:
    if not raw_name:
        return "upload"
    name = PurePosixPath(raw_name).name  # strip any path components
    name = _UNSAFE_CHARS.sub("_", name)
    return name[:255] or "upload"


def file_extension(filename: str) -> str:
    return PurePosixPath(filename.lower()).suffix
