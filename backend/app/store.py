from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import ActivityRecord, BriefRecord, DebugRecord, RunRecord, ShopRecord
from app.demo_data import DEFAULT_SHOP_URL, build_demo_run, build_shop_profile
from app.schemas import ActivityEvent, AgentRun, Brief, DebugEvent, ShopProfile


def to_json(model):
    return model.model_dump(mode="json")


class NotFoundError(ValueError):
    pass


class EtsyPulseStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def bootstrap_shop(self, shop_url: str) -> ShopProfile:
        profile = build_shop_profile(shop_url)
        existing = self.session.get(ShopRecord, profile.id)
        if existing:
            return ShopProfile.model_validate(existing.profile)

        self.session.add(ShopRecord(id=profile.id, profile=to_json(profile), created_at=profile.timestamp))
        event = ActivityEvent(
            id=f"activity_bootstrap_{profile.id}",
            agent="Shop Bootstrap Agent",
            event_type="bootstrap_requested",
            message="Created deterministic demo shop profile from bootstrap request.",
            timestamp=profile.timestamp,
        )
        debug = DebugEvent(
            id=f"debug_bootstrap_{profile.id}",
            provider="Bright Data",
            operation="bootstrap_stub",
            status="stubbed",
            request_summary="Accepted Etsy shop URL; no Bright Data call made in Session 1.",
            response_summary="Created deterministic ShopProfile fixture.",
            timestamp=profile.timestamp,
        )
        self._upsert_activity(event)
        self._upsert_debug(debug)
        self.session.commit()
        return profile

    def get_shop(self, shop_id: str) -> ShopProfile:
        record = self.session.get(ShopRecord, shop_id)
        if not record:
            raise NotFoundError(f"Shop '{shop_id}' was not found")
        return ShopProfile.model_validate(record.profile)

    def start_demo_run(self, shop_id: str | None = None) -> AgentRun:
        if shop_id is None:
            shop = self.bootstrap_shop(DEFAULT_SHOP_URL)
        else:
            shop = self.get_shop(shop_id)

        run, activity, debug, briefs = build_demo_run(shop)
        self.session.merge(RunRecord(id=run.id, shop_id=shop.id, run=to_json(run), created_at=run.started_at))
        for event in activity:
            self._upsert_activity(event)
        for event in debug:
            self._upsert_debug(event)
        for brief in briefs:
            self._upsert_brief(brief)
        self.session.commit()
        return run

    def get_run(self, run_id: str) -> AgentRun:
        record = self.session.get(RunRecord, run_id)
        if not record:
            raise NotFoundError(f"Run '{run_id}' was not found")
        return AgentRun.model_validate(record.run)

    def list_activity(self) -> list[ActivityEvent]:
        records = self.session.scalars(select(ActivityRecord).order_by(ActivityRecord.timestamp.desc())).all()
        return [ActivityEvent.model_validate(record.event) for record in records]

    def list_debug_events(self) -> list[DebugEvent]:
        records = self.session.scalars(select(DebugRecord).order_by(DebugRecord.timestamp.desc())).all()
        return [DebugEvent.model_validate(record.event) for record in records]

    def record_debug_event(self, event: DebugEvent) -> None:
        self._upsert_debug(event)
        self.session.commit()

    def list_briefs(self) -> list[Brief]:
        records = self.session.scalars(select(BriefRecord).order_by(BriefRecord.timestamp.desc())).all()
        return [Brief.model_validate(record.brief) for record in records]

    def ensure_demo_seeded(self) -> None:
        shop = self.bootstrap_shop(DEFAULT_SHOP_URL)
        self.start_demo_run(shop.id)

    def _upsert_activity(self, event: ActivityEvent) -> None:
        self.session.merge(ActivityRecord(id=event.id, timestamp=event.timestamp, event=to_json(event)))

    def _upsert_debug(self, event: DebugEvent) -> None:
        self.session.merge(DebugRecord(id=event.id, timestamp=event.timestamp, event=to_json(event)))

    def _upsert_brief(self, brief: Brief) -> None:
        self.session.merge(
            BriefRecord(
                id=brief.id,
                run_id=brief.run_id,
                shop_id=brief.shop_id,
                timestamp=brief.timestamp,
                brief=to_json(brief),
            )
        )
