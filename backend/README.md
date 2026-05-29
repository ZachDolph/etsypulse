# EtsyPulse Backend

FastAPI service for EtsyPulse. Session 5 includes typed API contracts, deterministic demo records, SQLAlchemy persistence, a Bright Data demo-cache abstraction, an LLM provider layer, deterministic backend agents, and OpenClaw-facing config docs. Bright Data live calls, OpenClaw runtime execution, and live scraping are intentionally not integrated yet.

## Local

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The default database is `sqlite:///./data/etsypulse.db`. Override with `DATABASE_URL` for another SQLite path or a Postgres URL in later deployment work.

## API Routes

- `GET /health`
- `POST /shops/bootstrap-request`
- `GET /shops/{shop_id}`
- `POST /runs/start-demo`
- `GET /runs/{run_id}`
- `GET /activity`
- `GET /briefs`
- `GET /debug/events`

## Persistence Choice

SQLAlchemy is used instead of SQLModel because neither package was present after Session 0, and SQLAlchemy is the smaller direct dependency for a SQLite/Postgres-compatible persistence boundary. Session 1 stores typed Pydantic payloads as JSON in normalized top-level tables for shops, runs, briefs, activity events, and debug events.

## Bright Data Client

`app.services.brightdata_client.BrightDataClient` is the Session 2 integration boundary. In `DEMO_MODE=true`, every method loads deterministic fixtures from `backend/app/demo_data/brightdata_samples` and emits a redacted `DebugEvent` with tool name, request shape, cache/live mode, latency, and response summary.

Methods:

- `etsy_products(shop_url | search_url)` maps to target MCP tool `web_data_etsy_products`.
- `serp_batch(keywords)` maps to current MCP docs tool `search_engine`.
- `scrape_markdown(url)` maps to current MCP docs tool `scrape_as_markdown`.
- `scrape_batch(urls)` batches cached results for the current MCP docs tool `scrape_as_markdown`.
- `discover(query)` is kept as an app-level discovery abstraction for future live adapter work.
- `tiktok_posts(query)` maps to target MCP/Web Scraper capability `web_data_tiktok_posts`; Bright Data docs also list TikTok Posts discover/collect API endpoints.
- `reddit_posts(query)` maps to target capability `web_data_reddit_posts`; Bright Data docs list the Reddit Scraper API for URL or keyword input.
- `instagram_reels(query)` maps to current MCP docs tool `web_data_instagram_reels` and Instagram Reels API endpoints.
- `google_shopping(query)` maps to target capability `web_data_google_shopping`; Bright Data docs list Google Scraper API support for Shopping.

Docs consulted in Session 2:

- Bright Data MCP FAQ: current MCP tools include `search_engine`, `scrape_as_markdown`, `scrape_as_html`, `session_stats`, `web_data_instagram_reels`, and browser tools.
- Bright Data MCP modes: Rapid mode supports search and markdown scraping; Pro/tool groups unlock structured data and browser automation.
- Bright Data Web Scraper API docs: TikTok, Reddit, Instagram, and Google Scraper APIs provide structured JSON endpoints.

Validate demo fixtures:

```bash
cd ..
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/validate_brightdata_fixtures.py
```


## LLM Client

`app.services.llm_client.LLMClient` is the Session 3 provider boundary. Provider order is NVIDIA NIM primary, then OpenRouter fallback. Tests and local demos can use `LLM_TEST_MODE=true` for a deterministic fake provider with no network calls.

Current live API mapping, based on docs reviewed in Session 3:

- NVIDIA NIM LLM: OpenAI-compatible `POST /v1/chat/completions`. Hosted default base URL is `https://integrate.api.nvidia.com/v1`; self-hosted NIMs should use their own `/v1` base URL.
- OpenRouter: OpenAI-like `POST https://openrouter.ai/api/v1/chat/completions`.
- Structured JSON: OpenRouter documents `response_format` with `type: json_schema`; the client sends that shape when validating Pydantic schemas and also retries invalid JSON locally.

Environment variables:

- `NVIDIA_NIM_API_KEY`
- `NVIDIA_NIM_BASE_URL`
- `NVIDIA_NIM_MODEL`
- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL`
- `OPENROUTER_MODEL_FALLBACK`
- `LLM_TEST_MODE`
- `LLM_TIMEOUT_SECONDS`
- `LLM_RATE_LIMIT_PER_MINUTE`
- `LLM_JSON_RETRIES`

Each call emits a redacted `DebugEvent` with provider, model, latency, token counts when available, error class, and whether fallback was used.


## Deterministic Agents

Session 4 adds `app.agents` with a typed `BaseAgent`, per-agent input/output contracts, and a `PipelineRunner`. `POST /runs/start-demo` uses this runner in demo mode. The runner records an `ActivityEvent` after each step and persists the final `AgentRun` and `Brief` records.

Implemented agents:

- `ShopBootstrapAgent`: loads cached Etsy product and markdown data to build `ShopProfile`.
- `KeywordSerpAgent`: loads cached SERP data to produce `KeywordSignal` records.
- `CompetitorWatchAgent`: loads cached competitor/product data to produce `CompetitorSignal` records.
- `TrendScoutAgent`: loads cached TikTok, Reddit, Instagram, and Google Shopping data to produce `TrendSignal` records.
- `MarketPulseAgent`: normalizes source signals into `MarketPulseSignal` records.
- `JudgeAgent`: scores market pulse signals and uses fake LLM structured JSON in demo pipeline runs.
- `BriefDeliveryAgent`: formats approved Judge scores into seller-facing `Brief` records.

No scheduler or OpenClaw runtime dependency exists yet.

## OpenClaw Adapter

Session 5 adds `app.services.openclaw_adapter` plus portable docs/config examples under `docs/openclaw-config/`. The adapter maps the local seven-agent pipeline to OpenClaw agent IDs and handoff summaries without importing or requiring OpenClaw. The documented OpenClaw tool/config surfaces are `agentToAgent`, `sessions_spawn`, `sessions_send`, `sessions_history`, `agents_list`, `session_status`, `agents.list`, and `agents.defaults.subagents`.

Smoke-test the OpenClaw config examples and local backend pipeline:

```bash
cd ..
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/smoke_openclaw_config.py
```

## Test

```bash
cd ..
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests -q
```
