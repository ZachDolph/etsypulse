from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal, get_session, init_db
from app.schemas import (
    ActivityEvent,
    AdminDebugStatus,
    AgentRun,
    BootstrapRequest,
    Brief,
    DebugEvent,
    LiveSmokeResponse,
    ProviderStatus,
    SchedulerStatus,
    SchedulerTriggerRequest,
    SchedulerTriggerResponse,
    ShopProfile,
    StartDemoRunRequest,
)
from app.services.brightdata_client import BrightDataClient
from app.services.llm_client import LLMClient, LLMClientError
from app.services.rate_limiter import RateLimiter, RateLimitExceededError
from app.services.scheduler import SchedulerService
from app.agents.contracts import JudgeInput
from app.agents.judge import JudgeAgent
from app.agents.utils import stable_id
from app.schemas import EvidenceSource, MarketPulseSignal, utc_now
from app.store import EtsyPulseStore, NotFoundError


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    demo_mode: bool


settings = get_settings()
rate_limiter = RateLimiter(settings.rate_limit_public_per_minute, settings.rate_limit_shop_per_hour)
scheduler_service = SchedulerService(settings)


def initialize_app() -> None:
    init_db()
    with SessionLocal() as session:
        EtsyPulseStore(session).ensure_demo_seeded()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_app()
    yield


app = FastAPI(
    title="EtsyPulse API",
    summary="FastAPI backend for the EtsyPulse hackathon demo.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_public_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    try:
        rate_limiter.check_ip(client_ip)
    except RateLimitExceededError as exc:
        return JSONResponse(
            status_code=429,
            content={"detail": str(exc), "retry_after_seconds": exc.retry_after_seconds},
            headers={"Retry-After": str(exc.retry_after_seconds)},
        )
    return await call_next(request)


def enforce_shop_rate_limit(shop_key: str) -> None:
    try:
        rate_limiter.check_shop(shop_key)
    except RateLimitExceededError as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc


def get_store(session: Annotated[Session, Depends(get_session)]) -> EtsyPulseStore:
    return EtsyPulseStore(session)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="etsypulse-api", demo_mode=settings.demo_mode)


@app.post("/shops/bootstrap-request", response_model=ShopProfile)
def bootstrap_request(request: BootstrapRequest, store: Annotated[EtsyPulseStore, Depends(get_store)]) -> ShopProfile:
    shop_url = str(request.shop_url).rstrip("/")
    enforce_shop_rate_limit(shop_url)
    return store.bootstrap_shop(shop_url)


@app.get("/shops/{shop_id}", response_model=ShopProfile)
def get_shop(shop_id: str, store: Annotated[EtsyPulseStore, Depends(get_store)]) -> ShopProfile:
    try:
        return store.get_shop(shop_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/runs/start-demo", response_model=AgentRun)
def start_demo_run(
    store: Annotated[EtsyPulseStore, Depends(get_store)],
    request: Annotated[StartDemoRunRequest | None, Body()] = None,
) -> AgentRun:
    try:
        enforce_shop_rate_limit((request.shop_id if request and request.shop_id else "default-demo-shop"))
        return store.start_demo_run(request.shop_id if request else None)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/runs/{run_id}", response_model=AgentRun)
def get_run(run_id: str, store: Annotated[EtsyPulseStore, Depends(get_store)]) -> AgentRun:
    try:
        return store.get_run(run_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/activity", response_model=list[ActivityEvent])
def list_activity(store: Annotated[EtsyPulseStore, Depends(get_store)]) -> list[ActivityEvent]:
    return store.list_activity()


@app.get("/briefs", response_model=list[Brief])
def list_briefs(store: Annotated[EtsyPulseStore, Depends(get_store)]) -> list[Brief]:
    return store.list_briefs()


@app.get("/debug/events", response_model=list[DebugEvent])
def list_debug_events(store: Annotated[EtsyPulseStore, Depends(get_store)]) -> list[DebugEvent]:
    return store.list_debug_events()


@app.get("/scheduler/status", response_model=SchedulerStatus)
def scheduler_status() -> SchedulerStatus:
    return SchedulerStatus(
        demo_enabled=settings.scheduler_demo_enabled,
        intervals_minutes=scheduler_service.cadence.as_dict(),
        judge_brief_threshold=settings.judge_brief_threshold,
    )


@app.post("/scheduler/trigger", response_model=SchedulerTriggerResponse)
def trigger_scheduler_run(
    store: Annotated[EtsyPulseStore, Depends(get_store)],
    request: Annotated[SchedulerTriggerRequest | None, Body()] = None,
) -> SchedulerTriggerResponse:
    trigger_request = request or SchedulerTriggerRequest(mode="manual")
    enforce_shop_rate_limit(trigger_request.shop_id or "default-demo-shop")
    try:
        return scheduler_service.trigger(store, trigger_request)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def provider_status() -> AdminDebugStatus:
    brightdata_configured = bool(settings.brightdata_api_key and settings.brightdata_unlocker_zone)
    nvidia_configured = bool(settings.nvidia_nim_api_key and settings.nvidia_nim_model)
    openrouter_configured = bool(settings.openrouter_api_key and settings.openrouter_model_fallback)
    mode = "demo" if settings.demo_mode else "live"
    return AdminDebugStatus(
        demo_mode=settings.demo_mode,
        brightdata=ProviderStatus(
            name="Bright Data Web Unlocker",
            configured=brightdata_configured,
            mode=mode if brightdata_configured or settings.demo_mode else "hybrid",
            details={
                "credential": "configured" if settings.brightdata_api_key else "missing",
                "unlocker_zone": "configured" if settings.brightdata_unlocker_zone else "missing",
                "live_tool_path": "scrape_markdown via Web Unlocker API",
            },
        ),
        nvidia_nim=ProviderStatus(
            name="NVIDIA NIM",
            configured=nvidia_configured,
            mode=mode if nvidia_configured or settings.demo_mode else "hybrid",
            details={
                "credential": "configured" if settings.nvidia_nim_api_key else "missing",
                "base_url": settings.nvidia_nim_base_url,
                "model": settings.nvidia_nim_model or "missing",
            },
        ),
        openrouter=ProviderStatus(
            name="OpenRouter",
            configured=openrouter_configured,
            mode=mode if openrouter_configured or settings.demo_mode else "hybrid",
            details={
                "credential": "configured" if settings.openrouter_api_key else "missing",
                "base_url": settings.openrouter_base_url,
                "model": settings.openrouter_model_fallback or "missing",
            },
        ),
        live_ready=(not settings.demo_mode) and brightdata_configured and (nvidia_configured or openrouter_configured),
    )


@app.get("/admin/debug/status", response_model=AdminDebugStatus)
def admin_debug_status() -> AdminDebugStatus:
    return provider_status()


@app.post("/admin/live-smoke", response_model=LiveSmokeResponse)
def admin_live_smoke() -> LiveSmokeResponse:
    debug_events = []
    try:
        brightdata = BrightDataClient(demo_mode=settings.demo_mode)
        markdown = brightdata.scrape_markdown("https://example.com")
        debug_events.extend(brightdata.debug_events)

        llm = LLMClient(force_test_mode=settings.demo_mode)
        pulse = MarketPulseSignal(
            id=stable_id("pulse", "admin-live-smoke"),
            run_id="admin_live_smoke",
            title="Admin live smoke signal",
            summary="Score whether a seller should refresh Etsy listing copy based on one controlled live smoke check.",
            severity="low",
            novelty=0.5,
            confidence=0.7,
            provenance=[EvidenceSource(tool="admin_live_smoke", url="https://example.com", captured_at=utc_now())],
        )
        scores = JudgeAgent(llm).run(JudgeInput(run_id="admin_live_smoke", market_pulse_signals=[pulse])).judge_scores
        debug_events.extend(llm.debug_events)
        return LiveSmokeResponse(
            status="ok",
            brightdata_summary=f"Bright Data returned {len(markdown)} markdown character(s).",
            llm_summary=f"JudgeAgent produced {len(scores)} score(s) via {'demo fake provider' if settings.demo_mode else 'live provider order'}.",
            debug_events=debug_events,
        )
    except Exception as exc:
        return LiveSmokeResponse(
            status="error",
            debug_events=debug_events,
            error=f"{type(exc).__name__}: {exc}",
        )
