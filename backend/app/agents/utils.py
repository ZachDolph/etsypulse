from uuid import NAMESPACE_URL, uuid5

from app.schemas import ActivityEvent, EvidenceSource, utc_now


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{uuid5(NAMESPACE_URL, value).hex[:12]}"


def source(tool: str, url: str | None = None, title: str | None = None) -> EvidenceSource:
    return EvidenceSource(tool=tool, url=url, title=title or "Deterministic agent pipeline evidence", captured_at=utc_now())


def activity_event(run_id: str, agent: str, event_type: str, message: str) -> ActivityEvent:
    return ActivityEvent(
        id=stable_id("activity", f"{run_id}:{agent}:{event_type}:{message}"),
        run_id=run_id,
        agent=agent,
        event_type=event_type,
        message=message,
        timestamp=utc_now(),
    )
