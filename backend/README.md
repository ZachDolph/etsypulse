# EtsyPulse Backend

FastAPI service for EtsyPulse. It exposes the shop bootstrap flow, deterministic agent pipeline, scheduler trigger, activity feed, debug feed, and seller briefs.

## Local Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The default database is `sqlite:///./data/etsypulse.db`. Set `DATABASE_URL` to another SQLite path or a Postgres URL when deploying.

## API Routes

- `GET /health`
- `POST /shops/bootstrap-request`
- `GET /shops/{shop_id}`
- `POST /runs/start-demo`
- `GET /runs/{run_id}`
- `POST /scheduler/trigger`
- `GET /scheduler/status`
- `GET /activity`
- `GET /briefs`
- `GET /debug/events`
- `GET /admin/debug/status`
- `POST /admin/live-smoke`

## Persistence

SQLAlchemy stores typed Pydantic payloads in top-level tables for shops, runs, briefs, activity events, and debug events. SQLite works locally; the database URL boundary is Postgres-compatible for later deployment work.

## Agent Pipeline

`app.agents` contains the typed local pipeline:

- `ShopBootstrapAgent`
- `KeywordSerpAgent`
- `CompetitorWatchAgent`
- `TrendScoutAgent`
- `MarketPulseAgent`
- `JudgeAgent`
- `BriefDeliveryAgent`

`POST /runs/start-demo` runs the complete deterministic pipeline, persists the run, and emits activity/debug events.

## Scheduler and Rate Limiting

`app.services.scheduler.SchedulerService` provides manual and demo scheduled runs. The current scheduler wraps the local deterministic pipeline and records `scheduled_run_started`, `scheduled_run_completed`, and `duplicate_suppressed` activity events.

Configurable settings:

- `SCHEDULER_KEYWORD_INTERVAL_MINUTES`
- `SCHEDULER_COMPETITOR_INTERVAL_MINUTES`
- `SCHEDULER_TREND_INTERVAL_MINUTES`
- `SCHEDULER_DEMO_ENABLED`
- `RATE_LIMIT_PUBLIC_PER_MINUTE`
- `RATE_LIMIT_SHOP_PER_HOUR`
- `JUDGE_BRIEF_THRESHOLD`
- `DEDUPE_WINDOW_MINUTES`

`app.services.rate_limiter.RateLimiter` enforces in-process per-IP and per-shop windows. This is sufficient for the portable demo; distributed deployment should replace it with Redis or managed edge limits.

## Live Integration

`DEMO_MODE=true` remains the default. With `DEMO_MODE=false`, `BrightDataClient.scrape_markdown()` uses Bright Data Web Unlocker API (`POST https://api.brightdata.com/request`) with `format=raw` and `data_format=markdown`. Live LLM judging uses `LLMClient` provider order: NVIDIA NIM first, OpenRouter fallback.

Admin/debug endpoints:

- `GET /admin/debug/status` reports configured/not configured state without secrets.
- `POST /admin/live-smoke` runs one controlled Bright Data markdown fetch and one JudgeAgent scoring pass.

## Bright Data Client

`app.services.brightdata_client.BrightDataClient` is the Bright Data boundary. In `DEMO_MODE=true`, methods load deterministic fixtures from `backend/app/demo_data/brightdata_samples` and emit redacted debug events with tool name, request shape, cache/live mode, latency, and response summary.

Validate fixtures:

```bash
cd ..
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/validate_brightdata_fixtures.py
```

## LLM Client

`app.services.llm_client.LLMClient` uses NVIDIA NIM first and OpenRouter fallback with OpenAI-compatible chat-completion shapes. Tests and demo pipeline runs use deterministic fake responses and do not call live LLM APIs.

## OpenClaw Adapter

`app.services.openclaw_adapter` maps the local seven-agent pipeline to OpenClaw agent IDs and handoff summaries without importing or requiring OpenClaw. See `docs/openclaw.md` and `docs/openclaw-config/`.

Smoke-test OpenClaw config examples and local pipeline health:

```bash
cd ..
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/smoke_openclaw_config.py
```

## Tests

```bash
cd ..
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests -q
```
