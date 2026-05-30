# EtsyPulse Production Deployment Runbook

This runbook prepares EtsyPulse for a hackathon deployment with a Vercel frontend and Render backend. Demo mode remains the default public path.

## Architecture

```text
Vercel static frontend (etsypulse)
        | VITE_API_BASE_URL
        v
Render FastAPI backend (etsypulse-api)
        | DATABASE_URL
        v
Render Postgres
```

Optional live providers are configured on the backend only: Bright Data Web Unlocker, NVIDIA NIM, and OpenRouter. OpenClaw remains optional for the first hosted judge demo, but the intended production architecture supports a hosted or portable OpenClaw runtime instead of any developer-local gateway dependency.

For local personal runs, keep `RATE_LIMIT_ENABLED=false` unless you are explicitly testing public-demo throttling. Local demo mode should still show the debug panel, activity feed, scheduler, and cached Bright Data provenance without imposing hosted-demo limits.

## Frontend On Vercel

Use project name `etsypulse` if the name is available. The root `vercel.json` follows Vercel's current static configuration model with a Vite framework, frontend install/build commands, and `frontend/dist` output.

Required Vercel environment variable:

```env
VITE_API_BASE_URL=https://<render-backend>.onrender.com
```

After deployment, open the Vercel URL and confirm the demo banner, provider status panel, briefs, activity feed, and debug panel load.

## Backend On Render

The root `render.yaml` defines a Docker web service named `etsypulse-api` and a Postgres database named `etsypulse-db`. Render will use `backend/Dockerfile` and `/ready` as the health check path.

Set these Render environment variables before production use:

```env
APP_ENV=production
LOG_LEVEL=INFO
DEMO_MODE=true
RATE_LIMIT_ENABLED=true
CORS_ORIGINS=https://etsypulse.vercel.app
DATABASE_URL=<Render Postgres connection string>
BRIGHTDATA_API_KEY=<optional live key>
BRIGHTDATA_UNLOCKER_ZONE=<optional live zone>
NVIDIA_NIM_API_KEY=<optional live key>
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MODEL=<optional live model>
OPENROUTER_API_KEY=<optional fallback key>
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL_FALLBACK=<optional fallback model>
```

Keep `DEMO_MODE=true` for public judging. Use `POST /admin/live-smoke` only for a controlled private live check after credentials are configured.

## Hosted Demo Seed

The backend seeds demo records during startup. You can also run the seed command manually in a Render shell:

```bash
PYTHONPATH=/app python scripts/seed_demo_data.py
```

Locally:

```bash
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/seed_demo_data.py
```

## Health And Readiness

- `GET /health`: lightweight liveness check.
- `GET /ready`: database and deployment configuration readiness check.
- `GET /admin/debug/status`: provider configured/missing status without secrets.

Smoke commands:

```bash
curl https://<render-backend>.onrender.com/health
curl https://<render-backend>.onrender.com/ready
curl https://<render-backend>.onrender.com/admin/debug/status
```

## OpenClaw Strategy

OpenClaw is optional for the first deployment, but it should become a real hosted or portable runtime once the main frontend/backend/Postgres demo is stable. The frontend must not call a developer-local OpenClaw gateway. Valid runtime models are: a separate hosted OpenClaw service, a portable local OpenClaw installation used by whoever runs EtsyPulse, or a backend-managed OpenClaw runtime. OpenClaw docs/config examples remain in `docs/openclaw.md` and `docs/openclaw-config/`. Do not require Discord, Slack, or channel setup for judges.

Recommended sequence for launch readiness:

1. Deploy and verify Vercel, Render FastAPI, and Render Postgres.
2. Run the CaitlynMinimalist cached demo twice end-to-end from the public dashboard.
3. Verify `/health`, `/ready`, CORS, activity feed, briefs, and debug events from the deployed frontend.
4. Add a hosted OpenClaw runtime only after the main demo is stable, with backend-only credentials and hosted-demo rate/budget limits.

## Pre-Deploy Checks

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests -q
cd frontend && npm run build
docker build -t etsypulse-api:local backend
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/validate_deployment_env.py
```

For a private live validation, export provider env vars and run:

```bash
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/validate_deployment_env.py --live
curl -X POST https://<render-backend>.onrender.com/admin/live-smoke
```

## Rollback

- Vercel: promote the previous successful deployment.
- Render: roll back to the previous deploy from the service dashboard.
- If live providers fail during judging, set `DEMO_MODE=true` and redeploy/restart the backend.
