"""Domain-level exceptions shared by the service layer.

Routers catch these and translate them into the standard error envelope
(PRD §80) — the raw Mistral SDK exception is never allowed to reach the
router or the client.
"""

from __future__ import annotations


class MistralServiceError(Exception):
    """Raised when a Mistral API call fails after validation has already passed."""


class MistralTimeoutError(MistralServiceError):
    """Raised when a Mistral call exceeds the endpoint's timeout budget."""
