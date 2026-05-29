from collections import deque
from dataclasses import dataclass, field
from time import monotonic


class RateLimitExceededError(ValueError):
    def __init__(self, scope: str, retry_after_seconds: int) -> None:
        self.scope = scope
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded for {scope}; retry after {retry_after_seconds}s")


@dataclass
class WindowCounter:
    limit: int
    window_seconds: int
    _events: dict[str, deque[float]] = field(default_factory=dict)

    def check(self, key: str, now: float | None = None) -> None:
        if self.limit <= 0:
            return
        current = monotonic() if now is None else now
        bucket = self._events.setdefault(key, deque())
        cutoff = current - self.window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            retry_after = max(1, int(bucket[0] + self.window_seconds - current))
            raise RateLimitExceededError(key, retry_after)
        bucket.append(current)

    def reset(self) -> None:
        self._events.clear()


class RateLimiter:
    def __init__(
        self,
        ip_limit_per_minute: int,
        shop_limit_per_hour: int,
        ip_window_seconds: int = 60,
        shop_window_seconds: int = 3600,
    ) -> None:
        self.ip_counter = WindowCounter(ip_limit_per_minute, ip_window_seconds)
        self.shop_counter = WindowCounter(shop_limit_per_hour, shop_window_seconds)

    def check_ip(self, ip_address: str, now: float | None = None) -> None:
        self.ip_counter.check(f"ip:{ip_address}", now)

    def check_shop(self, shop_key: str, now: float | None = None) -> None:
        self.shop_counter.check(f"shop:{shop_key}", now)

    def reset(self) -> None:
        self.ip_counter.reset()
        self.shop_counter.reset()
