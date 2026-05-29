import pytest

from app.services.rate_limiter import RateLimiter, RateLimitExceededError


def test_rate_limiter_limits_per_ip_window() -> None:
    limiter = RateLimiter(ip_limit_per_minute=2, shop_limit_per_hour=10, ip_window_seconds=60)

    limiter.check_ip("203.0.113.10", now=0)
    limiter.check_ip("203.0.113.10", now=1)

    with pytest.raises(RateLimitExceededError) as exc:
        limiter.check_ip("203.0.113.10", now=2)

    assert exc.value.retry_after_seconds > 0
    limiter.check_ip("203.0.113.10", now=61)


def test_rate_limiter_limits_per_shop_window() -> None:
    limiter = RateLimiter(ip_limit_per_minute=10, shop_limit_per_hour=1, shop_window_seconds=3600)

    limiter.check_shop("shop_123", now=0)

    with pytest.raises(RateLimitExceededError):
        limiter.check_shop("shop_123", now=10)

    limiter.check_shop("shop_123", now=3601)
