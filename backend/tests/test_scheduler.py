from collections.abc import Generator
from datetime import timedelta

import pytest
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.database import Base, build_engine
from app.demo_data import DEFAULT_SHOP_URL
from app.main import scheduler_status, trigger_scheduler_run
from app.schemas import SchedulerTriggerRequest, utc_now
from app.services.scheduler import SchedulerService
from app.store import EtsyPulseStore


@pytest.fixture()
def store(tmp_path) -> Generator[EtsyPulseStore, None, None]:
    engine = build_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as session:
        yield EtsyPulseStore(session)


def test_scheduler_due_checks_use_configured_intervals() -> None:
    settings = Settings()
    settings.scheduler_keyword_interval_minutes = 10
    settings.scheduler_competitor_interval_minutes = 20
    settings.scheduler_trend_interval_minutes = 30
    service = SchedulerService(settings)
    now = utc_now()

    assert service.due_checks(None, now=now) == ["keyword", "competitor", "trend"]
    assert service.due_checks(now - timedelta(minutes=21), now=now) == ["keyword", "competitor"]


def test_scheduler_due_cycle_runs_when_shop_has_no_previous_run(store: EtsyPulseStore) -> None:
    settings = Settings()
    service = SchedulerService(settings)

    response = service.run_due_demo_cycle(store)

    assert response is not None
    assert response.status == "completed"
    assert response.check_types == ["keyword", "competitor", "trend"]


def test_scheduler_trigger_runs_demo_pipeline_and_records_activity(store: EtsyPulseStore) -> None:
    settings = Settings()
    service = SchedulerService(settings)

    response = service.trigger(store, SchedulerTriggerRequest(check_type="all", mode="demo_scheduled"))

    assert response.status == "completed"
    assert response.run is not None
    assert response.run.status == "completed"
    assert response.check_types == ["keyword", "competitor", "trend"]
    assert any(event.event_type == "scheduled_run_completed" for event in store.list_activity())


def test_scheduler_suppresses_overlapping_duplicate_runs(store: EtsyPulseStore) -> None:
    settings = Settings()
    service = SchedulerService(settings)
    shop = store.bootstrap_shop(DEFAULT_SHOP_URL)
    existing = store.start_demo_run(shop.id)
    service.force_lock_for_test(shop.id, "all")

    response = service.trigger(store, SchedulerTriggerRequest(shop_id=shop.id, check_type="all"))

    assert response.status == "duplicate_suppressed"
    assert response.duplicate_suppressed is True
    assert response.run is not None
    assert response.run.id == existing.id
    assert any(event.event_type == "duplicate_suppressed" for event in store.list_activity())


def test_scheduler_routes_are_registered_and_status_shape() -> None:
    status = scheduler_status()

    assert status.demo_enabled is True
    assert set(status.intervals_minutes) == {"keyword", "competitor", "trend"}
    assert status.judge_brief_threshold >= 0


def test_manual_trigger_endpoint_handler(store: EtsyPulseStore) -> None:
    response = trigger_scheduler_run(store, SchedulerTriggerRequest(check_type="keyword", mode="manual"))

    assert response.status == "completed"
    assert response.check_types == ["keyword"]
    assert response.run is not None
