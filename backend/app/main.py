from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal, get_session, init_db
from app.schemas import (
    ActivityEvent,
    AgentRun,
    BootstrapRequest,
    Brief,
    DebugEvent,
    ShopProfile,
    StartDemoRunRequest,
)
from app.store import EtsyPulseStore, NotFoundError


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    demo_mode: bool


settings = get_settings()


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


def get_store(session: Annotated[Session, Depends(get_session)]) -> EtsyPulseStore:
    return EtsyPulseStore(session)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="etsypulse-api", demo_mode=settings.demo_mode)


@app.post("/shops/bootstrap-request", response_model=ShopProfile)
def bootstrap_request(request: BootstrapRequest, store: Annotated[EtsyPulseStore, Depends(get_store)]) -> ShopProfile:
    return store.bootstrap_shop(str(request.shop_url).rstrip("/"))


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
