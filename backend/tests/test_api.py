from collections.abc import Generator

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import sessionmaker

from app.database import Base, build_engine
from app.main import (
    app,
    bootstrap_request,
    get_run,
    get_shop,
    list_activity,
    list_briefs,
    list_debug_events,
    start_demo_run,
)
from app.schemas import BootstrapRequest, StartDemoRunRequest
from app.store import EtsyPulseStore


@pytest.fixture()
def store(tmp_path) -> Generator[EtsyPulseStore, None, None]:
    engine = build_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as session:
        yield EtsyPulseStore(session)


def test_required_routes_are_registered() -> None:
    routes = {(route.path, tuple(sorted(route.methods or []))) for route in app.routes}

    assert ("/ready", ("GET",)) in routes
    assert ("/shops/bootstrap-request", ("POST",)) in routes
    assert ("/shops/{shop_id}", ("GET",)) in routes
    assert ("/runs/start-demo", ("POST",)) in routes
    assert ("/runs/{run_id}", ("GET",)) in routes
    assert ("/activity", ("GET",)) in routes
    assert ("/briefs", ("GET",)) in routes
    assert ("/debug/events", ("GET",)) in routes


def test_bootstrap_shop_and_get_shop(store: EtsyPulseStore) -> None:
    profile = bootstrap_request(BootstrapRequest(shop_url="https://www.etsy.com/shop/session-one"), store)

    assert profile.shop_name in {"CaitlynMinimalist", "Demo Linen Studio"}
    assert profile.listings

    fetched = get_shop(profile.id, store)
    assert fetched.id == profile.id


def test_start_demo_run_and_fetch_related_records(store: EtsyPulseStore) -> None:
    run = start_demo_run(store, StartDemoRunRequest())

    assert run.status == "completed"
    assert run.keyword_signals
    assert run.market_pulse_signals
    assert run.judge_scores[0].decision == "brief"

    fetched_run = get_run(run.id, store)
    assert fetched_run.id == run.id

    assert list_activity(store)
    assert list_briefs(store)[0].recommended_actions
    assert all(event.redacted for event in list_debug_events(store))


def test_missing_records_raise_404(store: EtsyPulseStore) -> None:
    with pytest.raises(HTTPException) as shop_error:
        get_shop("missing_shop", store)
    assert shop_error.value.status_code == 404

    with pytest.raises(HTTPException) as run_error:
        get_run("missing_run", store)
    assert run_error.value.status_code == 404
