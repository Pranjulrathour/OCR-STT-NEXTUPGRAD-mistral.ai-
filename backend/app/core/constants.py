"""Fixed, non-configurable constants (PRD §78/§87/§88).

Anything a deployer might reasonably want to change belongs in
``core.config.Settings`` instead — these are structural facts about the API
contract itself, not environment-specific tuning knobs.
"""

from __future__ import annotations

API_V1_PREFIX = "/api/v1"
APP_VERSION = "1.0.0"

ALLOWED_OCR_CONTENT_TYPES = frozenset({"application/pdf", "image/png", "image/jpeg"})
ALLOWED_OCR_EXTENSIONS = frozenset({".pdf", ".png", ".jpg", ".jpeg"})

ALLOWED_AUDIO_CONTENT_TYPES = frozenset(
    {"audio/wav", "audio/wave", "audio/x-wav", "audio/webm", "audio/mp4", "audio/mpeg"}
)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE_SECONDS = 0.5
