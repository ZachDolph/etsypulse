# EtsyPulse

EtsyPulse is a hackathon demo for autonomous Etsy market intelligence. A seller will eventually enter an Etsy shop URL once, then the system will bootstrap market context, monitor competitors and trends, score opportunities with a Judge Agent, and show only actionable briefs.

EtsyPulse is currently implemented through Session 5: the local FastAPI demo pipeline runs without credentials, and OpenClaw-facing docs/config examples are prepared without making OpenClaw a runtime dependency.

## Stack Choice

- **Frontend:** React + Vite + TypeScript.
- **Backend:** FastAPI + Pydantic.
- **Deployment rationale:** Vite is the simplest fit for Vercel because it builds to static assets with minimal framework ceremony. FastAPI remains a separate backend service locally and can later be deployed to a Python-friendly host or adapted behind Vercel rewrites if needed.

## Repository Layout

```text
.
├── backend/          # FastAPI app and tests
├── frontend/         # React/Vite dashboard
├── .env.example      # Placeholder-only configuration
├── package.json      # Root convenience scripts
└── SESSION_TRACKER.md
```

## Local Setup

### 1. Environment

```bash
cp .env.example .env
```

Demo mode is enabled by default. The app runs without provider credentials. Live Bright Data and live LLM calls remain optional; tests use deterministic fixtures/fakes.

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","service":"etsypulse-api","demo_mode":true}
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The placeholder page calls `http://localhost:8000/health` by default.

To point the frontend at another backend URL, set:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Root Convenience Commands

```bash
npm run backend:dev
npm run backend:test
npm run frontend:dev
npm run frontend:build
```

## Demo Mode

- `DEMO_MODE=true` is the default.
- No credentials are required for this skeleton.
- Deterministic Bright Data-style fixture data and fake LLM mode let judges run without provider onboarding.
- Live mode is optional and enabled only when required environment variables are configured.

## Architecture Summary

The target architecture is a typed multi-agent pipeline:

1. Shop Bootstrap Agent builds the initial shop profile.
2. Keyword & SERP Agent tracks keyword opportunities.
3. Competitor Watch Agent detects listing and offer changes.
4. Trend Scout Agent monitors social and commerce trend signals.
5. Market Pulse Agent normalizes and deduplicates signals.
6. Judge Agent scores actionability and gates briefs.
7. Brief Delivery Agent formats seller-facing recommendations.

The deterministic local pipeline implements these agents as typed Python classes for demo mode. OpenClaw runtime integration remains optional and documented separately.


## Bright Data Demo Cache

Session 2 adds a no-network Bright Data abstraction at `backend/app/services/brightdata_client.py`. With `DEMO_MODE=true`, methods load cached JSON/Markdown from `backend/app/demo_data/brightdata_samples` and emit redacted debug events.

Validate all cached fixtures:

```bash
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/validate_brightdata_fixtures.py
```

Bright Data docs consulted for the abstraction include MCP tools `search_engine`, `scrape_as_markdown`, `session_stats`, `web_data_instagram_reels`, MCP Rapid/Pro modes, and Web Scraper APIs for TikTok, Reddit, Instagram, and Google Shopping.


## LLM Provider Layer

Session 3 adds `backend/app/services/llm_client.py` with provider order NVIDIA NIM first and OpenRouter fallback. It uses OpenAI-compatible `chat/completions` request and response shapes where possible.

Required for live calls:

- `NVIDIA_NIM_API_KEY`, `NVIDIA_NIM_BASE_URL`, `NVIDIA_NIM_MODEL` for primary provider. Default NIM base URL is `https://integrate.api.nvidia.com/v1`.
- `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL_FALLBACK` for fallback. Default OpenRouter base URL is `https://openrouter.ai/api/v1`.
- `LLM_TIMEOUT_SECONDS`, `LLM_RATE_LIMIT_PER_MINUTE`, and `LLM_JSON_RETRIES` control timeout, simple per-provider throttling, and structured JSON retry count.
- `LLM_TEST_MODE=true` forces the deterministic fake provider and makes no network calls.

Docs consulted for Session 3: NVIDIA NIM LLM API docs for OpenAI-compatible `POST /v1/chat/completions`, NVIDIA hosted endpoint docs for `https://integrate.api.nvidia.com`, OpenRouter chat completion docs for `POST /api/v1/chat/completions`, and OpenRouter structured outputs docs for `response_format` JSON schema.


## Deterministic Agent Pipeline

Session 4 adds backend-only deterministic agents and orchestration in `backend/app/agents/`. The pipeline uses cached Bright Data fixtures through `BrightDataClient` and the fake LLM path through `LLMClient(force_test_mode=True)` for demo runs. No OpenClaw runtime, scheduler, live Bright Data call, or live LLM call is required.

Agent roster implemented:

- `ShopBootstrapAgent`
- `KeywordSerpAgent`
- `CompetitorWatchAgent`
- `TrendScoutAgent`
- `MarketPulseAgent`
- `JudgeAgent`
- `BriefDeliveryAgent`

`POST /runs/start-demo` now executes the deterministic pipeline and persists the completed run, activity events, debug events, and approved briefs.

## OpenClaw Portable Workflow

Session 5 adds OpenClaw-facing documentation and config examples while keeping the core app runnable without OpenClaw. The recommended path is local workflow plus agent-to-agent coordination; Discord or other channel bindings are optional and intentionally excluded from the default example.

Files added:

- `docs/openclaw.md` explains how EtsyPulse maps local agents to OpenClaw agents.
- `docs/openclaw-config/openclaw.local-workflow.example.json` provides a portable `agents.list`, `tools.agentToAgent`, `tools.sessions`, and `agents.defaults.subagents` example.
- `docs/openclaw-config/AGENTS.etsypulse-coordinator.md`, `SOUL.etsypulse-coordinator.md`, and `lane-contracts.md` provide coordinator and lane instructions.
- `backend/app/services/openclaw_adapter.py` exposes a no-runtime-dependency mapping layer for future OpenClaw execution.

Smoke-test OpenClaw config examples and the backend demo pipeline:

```bash
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/smoke_openclaw_config.py
```

This smoke test does not require OpenClaw, Discord, Bright Data credentials, NVIDIA NIM credentials, or OpenRouter credentials.

## Hackathon Submission Checklist

- [ ] Demo mode runs from a fresh clone without credentials.
- [ ] Dashboard explains value within 30 seconds.
- [ ] Shop profile, signals, Judge scores, and briefs are visible.
- [ ] Bright Data usage is visible in code, debug events, and docs.
- [ ] NVIDIA NIM primary provider and OpenRouter fallback are documented and mocked in tests.
- [ ] Rate limiting protects public endpoints.
- [ ] Debug panel redacts all credentials.
- [ ] README and submission docs are complete.
- [ ] Secret scan passes before publishing.

## Current Status

Implemented through Session 5:

- FastAPI app with `/health`.
- React/Vite placeholder page that calls `/health`.
- Placeholder `.env.example`.
- Local setup documentation.
- Backend Pydantic schemas for shop profiles, listings, signals, Judge scores, briefs, runs, activity events, and debug events.
- SQLAlchemy persistence with a default local SQLite database and Postgres-compatible boundary.
- Deterministic demo records exposed through backend API routes.
- Bright Data client abstraction with demo fixtures, redacted debug events, and fixture validation command.
- LLM provider layer with NVIDIA NIM primary, OpenRouter fallback, fake test provider, structured JSON validation/retry, timeout/rate-limit settings, and redacted debug events.
- Deterministic backend agent classes and pipeline orchestration with activity/debug event persistence.
- OpenClaw portable workflow docs, config examples, no-runtime adapter, and smoke validation script.

Not implemented yet:

- OpenClaw runtime-backed agents beyond docs/config examples.
- Bright Data live calls.
- Production persistence migrations.
- Rate limiting.
