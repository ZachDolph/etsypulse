import socket
from collections.abc import Generator

import pytest
from sqlalchemy.orm import sessionmaker

from app.database import Base, build_engine
from app.services.brightdata_client import BrightDataClient, BrightDataClientError
from app.store import EtsyPulseStore


@pytest.fixture()
def store(tmp_path) -> Generator[EtsyPulseStore, None, None]:
    engine = build_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as session:
        yield EtsyPulseStore(session)


def test_validate_brightdata_demo_fixtures_loads_all_samples() -> None:
    results = BrightDataClient(demo_mode=True).validate_demo_fixtures()

    assert set(results) == set(BrightDataClient.FIXTURES)
    assert "Loaded object" in results["etsy_products"]
    assert "Loaded text" in results["scrape_markdown"]


def test_demo_mode_methods_make_no_network_calls(monkeypatch) -> None:
    def fail_network(*args, **kwargs):
        raise AssertionError("network access is forbidden in DEMO_MODE")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    client = BrightDataClient(demo_mode=True)

    assert client.etsy_products(shop_url="https://www.etsy.com/shop/demo-linen-studio")["items"]
    assert client.serp_batch(["linen tea towel"])["queries"]
    assert "Demo Linen Studio" in client.scrape_markdown("https://www.etsy.com/shop/demo-linen-studio")
    assert client.scrape_batch(["https://www.etsy.com/shop/demo-linen-studio"])["pages"]
    assert client.discover("linen kitchen gifts")["results"]
    assert client.tiktok_posts("linen hostess gift")["posts"]
    assert client.reddit_posts("housewarming kitchen gift")["posts"]
    assert client.instagram_reels("neutral kitchen linen")["reels"]
    assert client.google_shopping("linen tea towel set")["products"]

    assert len(client.debug_events) == 9
    assert {event.cache_mode for event in client.debug_events} == {"demo"}
    assert all(event.redacted for event in client.debug_events)
    assert all(event.latency_ms >= 0 for event in client.debug_events)
    assert all(event.request_shape.get("api_key") in (None, "[REDACTED]") for event in client.debug_events)


def test_debug_events_can_be_persisted(store: EtsyPulseStore) -> None:
    client = BrightDataClient(demo_mode=True, debug_sink=store.record_debug_event)
    client.google_shopping("linen tea towel set")

    events = store.list_debug_events()
    assert len(events) == 1
    assert events[0].provider == "Bright Data"
    assert events[0].tool_name == "web_data_google_shopping"
    assert events[0].cache_mode == "demo"
    assert events[0].response_summary.startswith("Loaded object")


def test_live_unsupported_operations_fall_back_to_cache() -> None:
    client = BrightDataClient(demo_mode=False)

    result = client.discover("linen kitchen gifts")

    assert result["results"]
    assert client.debug_events[0].cache_mode == "demo"
    assert client.debug_events[0].status == "stubbed"
    assert "cache fallback" in client.debug_events[0].response_summary

import httpx

from app.config import get_settings
from app.services.brightdata_client import BrightDataRateLimitError, BrightDataTimeoutError


def test_live_scrape_markdown_calls_brightdata_unlocker(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("BRIGHTDATA_API_KEY", "bd-key")
    monkeypatch.setenv("BRIGHTDATA_UNLOCKER_ZONE", "unlocker-zone")
    get_settings.cache_clear()
    request = httpx.Request("POST", "https://api.brightdata.com/request")

    def fake_post(url, **kwargs):
        assert url == "https://api.brightdata.com/request"
        assert kwargs["headers"]["Authorization"] == "Bearer bd-key"
        assert kwargs["json"] == {
            "zone": "unlocker-zone",
            "url": "https://example.com",
            "format": "raw",
            "data_format": "markdown",
        }
        return httpx.Response(200, request=request, text="# Example Domain")

    monkeypatch.setattr(httpx, "post", fake_post)
    client = BrightDataClient(demo_mode=False)

    assert client.scrape_markdown("https://example.com") == "# Example Domain"
    event = client.debug_events[0]
    assert event.cache_mode == "live"
    assert event.status == "success"
    assert event.request_shape["api_key"] == "[REDACTED]"
    assert event.request_shape["unlocker_zone"] == "unlocker-zone"
    get_settings.cache_clear()


def test_live_unsupported_brightdata_path_uses_explicit_cache_fallback(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("BRIGHTDATA_API_KEY", "bd-key")
    monkeypatch.setenv("BRIGHTDATA_UNLOCKER_ZONE", "unlocker-zone")
    get_settings.cache_clear()

    client = BrightDataClient(demo_mode=False)
    result = client.etsy_products(shop_url="https://www.etsy.com/shop/demo-linen-studio")

    assert result["items"]
    event = client.debug_events[0]
    assert event.status == "stubbed"
    assert event.cache_mode == "demo"
    assert "cache fallback" in event.response_summary
    get_settings.cache_clear()


def test_live_brightdata_errors_are_classified(monkeypatch) -> None:
    monkeypatch.setenv("BRIGHTDATA_API_KEY", "bd-key")
    monkeypatch.setenv("BRIGHTDATA_UNLOCKER_ZONE", "unlocker-zone")
    get_settings.cache_clear()

    def timeout_post(*args, **kwargs):
        raise httpx.TimeoutException("too slow")

    monkeypatch.setattr(httpx, "post", timeout_post)
    client = BrightDataClient(demo_mode=False)

    with pytest.raises(BrightDataTimeoutError):
        client.scrape_markdown("https://example.com")
    assert client.debug_events[0].error_class == "BrightDataTimeoutError"

    request = httpx.Request("POST", "https://api.brightdata.com/request")

    def rate_limited_post(*args, **kwargs):
        return httpx.Response(429, request=request, text="rate limited")

    monkeypatch.setattr(httpx, "post", rate_limited_post)
    client = BrightDataClient(demo_mode=False)
    with pytest.raises(BrightDataRateLimitError):
        client.scrape_markdown("https://example.com")
    assert client.debug_events[0].error_class == "BrightDataRateLimitError"
    get_settings.cache_clear()
