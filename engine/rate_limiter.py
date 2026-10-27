"""
In-memory sliding-window rate limiter & Anti-Spam protection for Luxe Wave Hospitality API.
Protects AI endpoints, RFQ forms, and webhooks against DDOS, quota drain, and crawler floods.
"""
import threading
import time
from collections import defaultdict, deque

class RateLimiter:
    """Sliding-window in-memory rate limiter."""
    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _cleanup(self, key: str, now: float) -> int:
        hits = self._hits.get(key)
        if not hits:
            return 0
        while hits and (now - hits[0]) >= self.window_seconds:
            hits.popleft()
        if not hits:
            del self._hits[key]
            return 0
        return len(hits)

    def is_limited(self, key: str) -> bool:
        with self._lock:
            now = time.monotonic()
            return self._cleanup(key, now) >= self.max_attempts

    def hit(self, key: str) -> bool:
        """Records hit. Returns True if accepted, False if rate limited."""
        with self._lock:
            now = time.monotonic()
            count = self._cleanup(key, now)
            if count >= self.max_attempts:
                return False
            self._hits[key].append(now)
            return True

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

# Production limiter instances for Luxe Wave
contact_form_limiter = RateLimiter(max_attempts=5, window_seconds=10 * 60)      # 5 inquiries per 10 mins per IP
chat_stream_limiter = RateLimiter(max_attempts=30, window_seconds=5 * 60)       # 30 messages per 5 mins per session
webhook_limiter = RateLimiter(max_attempts=60, window_seconds=60)               # 60 events/minute
