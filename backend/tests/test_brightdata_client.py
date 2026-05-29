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


def test_live_mode_is_guarded_without_mcp_adapter() -> None:
    client = BrightDataClient(demo_mode=False)

    with pytest.raises(BrightDataClientError):
        client.discover("linen kitchen gifts")

    assert client.debug_events[0].cache_mode == "live"
    assert client.debug_events[0].status == "error"
