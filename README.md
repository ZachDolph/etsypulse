# EtsyPulse

EtsyPulse is an autonomous Etsy market-intelligence dashboard for sellers. A seller enters an Etsy shop URL once, then the system bootstraps a shop profile, monitors keyword/SERP movement, watches competitors, scans social-commerce trends, scores signals with a Judge Agent, and emits only actionable briefs.

The project is built for a hackathon demo: it runs locally in deterministic demo mode without Bright Data, NVIDIA NIM, OpenRouter, OpenClaw, Discord, or other provider onboarding.

## Features

- FastAPI backend with typed Pydantic API and agent contracts.
- React + Vite judge-facing dashboard with shop setup, briefs, signals, activity, and debug traces.
- Deterministic seven-agent pipeline for demo mode.
- Cached Bright Data-style fixtures plus a live Bright Data Web Unlocker markdown path with redacted debug events.
- NVIDIA NIM primary LLM provider and OpenRouter fallback behind a no-live-call test mode.
- Scheduler service for manual and demo scheduled runs.
- Per-IP and per-shop rate limiting for public backend actions.
- Duplicate suppression for overlapping scheduled jobs.
- OpenClaw-oriented docs/config examples without requiring OpenClaw at runtime.

## Architecture

```text
React/Vite dashboard
        |
        v
FastAPI API + SQLite/Postgres-compatible persistence
        |
        v
Scheduler + rate limiting + duplicate suppression
        |
        v
Typed agent pipeline
  Shop Bootstrap -> Keyword/SERP -> Competitor Watch -> Trend Scout
  -> Market Pulse -> Judge -> Brief Delivery
        |
        v
Bright Data client abstraction + LLM provider abstraction
```

The backend stores shop profiles, runs, activity events, debug events, and briefs. Demo mode uses local fixtures and fake LLM responses so every run is repeatable.

## Repository Layout

```text
backend/                FastAPI app, services, agents, scripts, tests
frontend/               React/Vite judge-facing dashboard
docs/openclaw.md        Optional OpenClaw integration plan
docs/openclaw-config/   Portable OpenClaw config examples
.env.example            Placeholder-only environment config
```

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
```

Demo mode is enabled by default and requires no credentials.

### 2. Run Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Check health:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","service":"etsypulse-api","demo_mode":true}
```

### 3. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dashboard loads backend health, scheduler status, shop profile, briefs, activity, market signals, and debug traces. Set `VITE_API_BASE_URL=http://localhost:8000` if the backend URL changes.

## Usage Examples

Bootstrap a shop profile:

```bash
curl -X POST http://localhost:8000/shops/bootstrap-request \
  -H 'Content-Type: application/json' \
  -d '{"shop_url":"https://www.etsy.com/shop/demo-linen-studio"}'
```

Run the deterministic demo pipeline:

```bash
curl -X POST http://localhost:8000/runs/start-demo \
  -H 'Content-Type: application/json' \
  -d '{}'
```

Trigger a scheduled demo check manually:

```bash
curl -X POST http://localhost:8000/scheduler/trigger \
  -H 'Content-Type: application/json' \
  -d '{"check_type":"all","mode":"demo_scheduled"}'
```

Read dashboard data:

```bash
curl http://localhost:8000/activity
curl http://localhost:8000/briefs
curl http://localhost:8000/debug/events
curl http://localhost:8000/scheduler/status
```

## API Surface

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

## Configuration

All runtime configuration comes from `.env` or process environment variables. Do not commit real secrets.

Core settings:

- `DEMO_MODE`: defaults to `true`.
- `DATABASE_URL`: defaults to local SQLite.
- `CORS_ORIGINS`: comma-separated frontend origins.
- `RATE_LIMIT_PUBLIC_PER_MINUTE`: per-IP public request limit.
- `RATE_LIMIT_SHOP_PER_HOUR`: per-shop action limit.
- `SCHEDULER_KEYWORD_INTERVAL_MINUTES`, `SCHEDULER_COMPETITOR_INTERVAL_MINUTES`, `SCHEDULER_TREND_INTERVAL_MINUTES`: autonomous check cadences.
- `JUDGE_BRIEF_THRESHOLD`: minimum Judge total score for brief delivery.
- `DEDUPE_WINDOW_MINUTES`: planned duplicate-signal window for future persisted dedupe.
- `BRIGHTDATA_UNLOCKER_ZONE`, `BRIGHTDATA_TIMEOUT_SECONDS`: live Bright Data Web Unlocker settings.

Provider settings:

- `BRIGHTDATA_API_KEY`, `BRIGHTDATA_MCP_URL`
- `NVIDIA_NIM_API_KEY`, `NVIDIA_NIM_BASE_URL`, `NVIDIA_NIM_MODEL`
- `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL_FALLBACK`
- `LLM_TEST_MODE`, `LLM_TIMEOUT_SECONDS`, `LLM_RATE_LIMIT_PER_MINUTE`, `LLM_JSON_RETRIES`

## Live Mode

Demo mode remains the default. Set `DEMO_MODE=false` only when provider credentials are configured. Session 8 wires one controlled Bright Data live path through Web Unlocker markdown scraping and one live LLM JudgeAgent scoring path through NVIDIA NIM with OpenRouter fallback. Unsupported Bright Data product abstractions use explicit cached fallback events until their dedicated live adapters are implemented.

Check provider readiness without exposing secrets:

```bash
curl http://localhost:8000/admin/debug/status
```

Run a controlled live smoke check:

```bash
curl -X POST http://localhost:8000/admin/live-smoke
```

## Demo Mode

Demo mode is the safest way to run the project for judging and development:

- Bright Data calls load cached fixtures from `backend/app/demo_data/brightdata_samples`.
- LLM judging uses deterministic fake responses in automated tests and demo pipeline runs.
- Scheduled demo runs execute the same local pipeline and record activity/debug events.
- No network calls or provider credentials are required for tests.

Validate Bright Data fixtures:

```bash
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/validate_brightdata_fixtures.py
```

Validate optional OpenClaw config examples and local pipeline health:

```bash
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/smoke_openclaw_config.py
```

## OpenClaw

OpenClaw is optional for the portable demo. EtsyPulse includes OpenClaw-facing docs and config examples so the agent roster can later be coordinated through local workflow and `agentToAgent` routing.

Start here: `docs/openclaw.md`.

The default app path does not require Discord, Slack, WhatsApp, or any chat channel.

## Development

Run backend tests:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests -q
```

Run backend compile checks:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m py_compile backend/app/*.py backend/app/agents/*.py backend/app/services/*.py backend/app/demo_data/*.py backend/scripts/*.py
```

Build frontend:

```bash
cd frontend
npm run build
```

Root convenience commands are also available:

```bash
npm run backend:dev
npm run backend:test
npm run frontend:dev
npm run frontend:build
```

## Contributing

- Keep demo mode deterministic and credential-free.
- Add tests for every important service or route change.
- Keep API and agent boundaries typed with Pydantic models.
- Never commit `.env` or provider secrets.

## License & Support

