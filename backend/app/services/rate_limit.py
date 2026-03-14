import time
from collections import deque
from dataclasses import dataclass


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after: int | None = None


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = {}

    def hit(self, key: str) -> RateLimitResult:
        now = time.time()
        window_start = now - self.window_seconds
        bucket = self._requests.setdefault(key, deque())
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            retry_after = int(bucket[0] + self.window_seconds - now)
            return RateLimitResult(allowed=False, retry_after=max(retry_after, 1))
        bucket.append(now)
        return RateLimitResult(allowed=True)
