from datetime import datetime, timezone
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field, HttpUrl


T = TypeVar("T")


Decision = Literal["ignore", "watch", "brief"]
Severity = Literal["low", "medium", "high"]
RunStatus = Literal["queued", "running", "completed", "failed"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceSource(BaseModel):
    tool: str
    url: str | None = None
    title: str | None = None
    captured_at: datetime = Field(default_factory=utc_now)


class Listing(BaseModel):
    id: str
    shop_id: str
    title: str
    url: str
    price: float = Field(ge=0)
    currency: str = "USD"
    tags: list[str] = Field(default_factory=list)
    provenance: list[EvidenceSource] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime = Field(default_factory=utc_now)


class ShopProfile(BaseModel):
    id: str
    shop_url: str
    shop_name: str
    category: str
    summary: str
    listings: list[Listing] = Field(default_factory=list)
    seed_keywords: list[str] = Field(default_factory=list)
    likely_competitors: list[str] = Field(default_factory=list)
    baseline_positioning: str
    provenance: list[EvidenceSource] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime = Field(default_factory=utc_now)


class KeywordSignal(BaseModel):
    id: str
    run_id: str
    keyword: str
    movement: str
    opportunity: str
    visibility_score: float = Field(ge=0, le=1)
    severity: Severity
    provenance: list[EvidenceSource] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime = Field(default_factory=utc_now)


class CompetitorSignal(BaseModel):
    id: str
    run_id: str
    competitor_name: str
    competitor_url: str
    signal: str
    price_delta_percent: float | None = None
    severity: Severity
    provenance: list[EvidenceSource] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime = Field(default_factory=utc_now)


class TrendSignal(BaseModel):
    id: str
    run_id: str
    platform: str
    topic: str
    signal: str
    momentum_score: float = Field(ge=0, le=1)
    severity: Severity
    provenance: list[EvidenceSource] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime = Field(default_factory=utc_now)


class MarketPulseSignal(BaseModel):
    id: str
    run_id: str
    title: str
    summary: str
    severity: Severity
    novelty: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    source_signal_ids: list[str] = Field(default_factory=list)
    provenance: list[EvidenceSource] = Field(default_factory=list)
    originating_agent: str = "Market Pulse Agent"
    timestamp: datetime = Field(default_factory=utc_now)


class JudgeScore(BaseModel):
    id: str
    run_id: str
    market_pulse_signal_id: str
    actionability: float = Field(ge=0, le=1)
    urgency: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    business_impact: float = Field(ge=0, le=1)
    evidence_quality: float = Field(ge=0, le=1)
    total_score: float = Field(ge=0, le=1)
    decision: Decision
    rationale: str
    timestamp: datetime = Field(default_factory=utc_now)


class Brief(BaseModel):
    id: str
    run_id: str
    shop_id: str
    title: str
    summary: str
    recommended_actions: list[str]
    evidence: list[str]
    why_now: str
    confidence: float = Field(ge=0, le=1)
    judge_score: JudgeScore
    provenance: list[EvidenceSource] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=utc_now)


class AgentRun(BaseModel):
    id: str
    shop_id: str
    mode: Literal["demo", "live"] = "demo"
    status: RunStatus
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    agents: list[str] = Field(default_factory=list)
    keyword_signals: list[KeywordSignal] = Field(default_factory=list)
    competitor_signals: list[CompetitorSignal] = Field(default_factory=list)
    trend_signals: list[TrendSignal] = Field(default_factory=list)
    market_pulse_signals: list[MarketPulseSignal] = Field(default_factory=list)
    judge_scores: list[JudgeScore] = Field(default_factory=list)
    brief_ids: list[str] = Field(default_factory=list)


class ActivityEvent(BaseModel):
    id: str
    run_id: str | None = None
    agent: str
    event_type: str
    message: str
    severity: Literal["info", "warning", "error"] = "info"
    timestamp: datetime = Field(default_factory=utc_now)


class DebugEvent(BaseModel):
    id: str
    run_id: str | None = None
    provider: str
    tool_name: str | None = None
    model: str | None = None
    operation: str
    status: Literal["stubbed", "success", "error"]
    cache_mode: Literal["demo", "live"] = "demo"
    latency_ms: float = Field(default=0, ge=0)
    request_shape: dict[str, Any] = Field(default_factory=dict)
    token_counts: dict[str, int] = Field(default_factory=dict)
    error_class: str | None = None
    fallback_used: bool = False
    request_summary: str
    response_summary: str
    redacted: bool = True
    timestamp: datetime = Field(default_factory=utc_now)


class BootstrapRequest(BaseModel):
    shop_url: HttpUrl


class StartDemoRunRequest(BaseModel):
    shop_id: str | None = None


class ListResponse(BaseModel, Generic[T]):
    items: list[T]
