from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock

from app.agents.contracts import PipelineRunInput
from app.agents.pipeline import PipelineRunner
from app.agents.utils import activity_event, stable_id
from app.config import Settings
from app.demo_data import DEFAULT_SHOP_URL
from app.schemas import AgentRun, SchedulerCheckType, SchedulerTriggerRequest, SchedulerTriggerResponse, utc_now
from app.services.brightdata_client import BrightDataClient
from app.services.llm_client import LLMClient
from app.store import EtsyPulseStore


@dataclass(frozen=True)
class SchedulerCadence:
    keyword_interval_minutes: int
    competitor_interval_minutes: int
    trend_interval_minutes: int

    def as_dict(self) -> dict[str, int]:
        return {
            "keyword": self.keyword_interval_minutes,
            "competitor": self.competitor_interval_minutes,
            "trend": self.trend_interval_minutes,
        }


@dataclass
class SchedulerService:
    settings: Settings
    _running_shop_ids: set[str] = field(default_factory=set)
    _lock: Lock = field(default_factory=Lock)

    @property
    def cadence(self) -> SchedulerCadence:
        return SchedulerCadence(
            keyword_interval_minutes=self.settings.scheduler_keyword_interval_minutes,
            competitor_interval_minutes=self.settings.scheduler_competitor_interval_minutes,
            trend_interval_minutes=self.settings.scheduler_trend_interval_minutes,
        )

    def due_checks(self, last_run_at: datetime | None, now: datetime | None = None) -> list[SchedulerCheckType]:
        if last_run_at is None:
            return ["keyword", "competitor", "trend"]
        current = now or utc_now()
        due: list[SchedulerCheckType] = []
        intervals = self.cadence.as_dict()
        for check_type in ("keyword", "competitor", "trend"):
            if current - last_run_at >= timedelta(minutes=intervals[check_type]):
                due.append(check_type)  # type: ignore[arg-type]
        return due

    def run_due_demo_cycle(self, store: EtsyPulseStore, shop_id: str | None = None) -> SchedulerTriggerResponse | None:
        shop = store.bootstrap_shop(DEFAULT_SHOP_URL) if shop_id is None else store.get_shop(shop_id)
        latest = store.latest_run_for_shop(shop.id)
        due = self.due_checks(latest.completed_at if latest else None)
        if not due:
            return None
        check_type: SchedulerCheckType = "all" if len(due) == 3 else due[0]
        return self.trigger(store, SchedulerTriggerRequest(shop_id=shop.id, check_type=check_type, mode="demo_scheduled"))

    def trigger(self, store: EtsyPulseStore, request: SchedulerTriggerRequest) -> SchedulerTriggerResponse:
        shop = store.bootstrap_shop(DEFAULT_SHOP_URL) if request.shop_id is None else store.get_shop(request.shop_id)
        check_types = self._resolve_check_types(request.check_type)
        run_key = f"{shop.id}:{','.join(check_types)}"
        if not self._try_lock(run_key):
            latest = store.latest_run_for_shop(shop.id)
            event = activity_event(
                latest.id if latest else stable_id("run", f"{shop.id}:duplicate-suppressed"),
                "Scheduler Service",
                "duplicate_suppressed",
                f"Suppressed overlapping scheduled run for {shop.shop_name}.",
            )
            store.record_activity_event(event)
            return SchedulerTriggerResponse(
                status="duplicate_suppressed",
                run=latest,
                check_types=check_types,
                message="An overlapping run is already active for this shop and check set.",
                duplicate_suppressed=True,
            )

        try:
            store.record_activity_event(
                activity_event(
                    stable_id("run", f"{shop.id}:scheduled:{','.join(check_types)}"),
                    "Scheduler Service",
                    "scheduled_run_started",
                    f"Started {request.mode} scheduled run for checks: {', '.join(check_types)}.",
                )
            )
            run = self._run_pipeline(store, shop.shop_url)
            store.record_activity_event(
                activity_event(
                    run.id,
                    "Scheduler Service",
                    "scheduled_run_completed",
                    f"Completed scheduled run for checks: {', '.join(check_types)}.",
                )
            )
            return SchedulerTriggerResponse(
                status="completed",
                run=run,
                check_types=check_types,
                message="Scheduled demo run completed.",
                duplicate_suppressed=False,
            )
        finally:
            self._unlock(run_key)

    def _run_pipeline(self, store: EtsyPulseStore, shop_url: str) -> AgentRun:
        brightdata = BrightDataClient(demo_mode=self.settings.demo_mode, debug_sink=store.record_debug_event)
        llm_client = LLMClient(debug_sink=store.record_debug_event, force_test_mode=self.settings.demo_mode)
        pipeline = PipelineRunner(
            store=store,
            brightdata=brightdata,
            llm_client=llm_client,
            judge_threshold=self.settings.judge_brief_threshold,
        )
        return pipeline.run_demo(PipelineRunInput(shop_url=shop_url)).run

    def _resolve_check_types(self, check_type: SchedulerCheckType | str) -> list[SchedulerCheckType]:
        if check_type == "all":
            return ["keyword", "competitor", "trend"]
        return [check_type]  # type: ignore[list-item]

    def _try_lock(self, run_key: str) -> bool:
        with self._lock:
            if run_key in self._running_shop_ids:
                return False
            self._running_shop_ids.add(run_key)
            return True

    def _unlock(self, run_key: str) -> None:
        with self._lock:
            self._running_shop_ids.discard(run_key)

    def force_lock_for_test(self, shop_id: str, check_type: SchedulerCheckType | str = "all") -> str:
        check_types = self._resolve_check_types(check_type)
        run_key = f"{shop_id}:{','.join(check_types)}"
        with self._lock:
            self._running_shop_ids.add(run_key)
        return run_key
