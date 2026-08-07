"""In-memory per-key sliding-window rate limiter.

Every OCR/Speech call proxies to a paid Mistral API call — without this,
one script (or one confused browser tab retry-looping) can run up a real
bill. No Redis/DB (matches the app's no-persistence non-goals): limits
reset on restart and don't share state across multiple worker processes.
That's an accepted trade-off for a single-process deployment — move this to
Redis first if this app is ever run with multiple Uvicorn/Gunicorn workers.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from functools import lru_cache

from app.core.config import get_settings


class RateLimiter:
    def __init__(self, *, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        if len(hits) >= self.max_requests:
            return False
        hits.append(now)
        return True


@lru_cache
def get_rate_limiter() -> RateLimiter:
    settings = get_settings()
    return RateLimiter(
        max_requests=settings.rate_limit_requests_per_minute, window_seconds=60.0
    )
