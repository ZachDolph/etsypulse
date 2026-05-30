# EtsyPulse OpenClaw Integration Plan

EtsyPulse keeps the core demo runnable as a normal FastAPI service. OpenClaw is treated as an optional coordination layer for local multi-agent workflows, not as a hard dependency for judges.

## Current OpenClaw References Consulted

Session 5 used the bundled OpenClaw documentation in `/home/zdolph/.codex/skills/openclaw/references/documentation/` and verified these current config surfaces:

- OpenClaw reads JSON5 config from `~/.openclaw/openclaw.json`; `OPENCLAW_CONFIG_PATH` can point at another real file.
- Minimal agent config uses `agents.defaults.workspace`.
- Multi-agent routing uses `agents.list` for isolated agent definitions and optional `bindings` to route channels/accounts to agents.
- Agent-to-agent coordination is controlled by `tools.agentToAgent`.
- Session targeting tools are controlled by `tools.sessions`; sub-agent spawning is controlled by `agents.defaults.subagents` and `sessions_spawn` policy.
- Agent loop entry points include gateway `agent` / `agent.wait` style runs and CLI `openclaw agent` runs.

## Design Decision

The hackathon demo remains portable:

- `POST /runs/start-demo` runs the deterministic Python pipeline directly.
- OpenClaw config examples map EtsyPulse agents to OpenClaw agents and lane contracts.
- Discord, WhatsApp, Slack, or any other channel binding is optional and intentionally omitted from the default example.
- No evaluator needs a chat channel, Discord server, or global OpenClaw installation to run the core app.

## Agent Mapping

| EtsyPulse agent | OpenClaw agent id | Role |
| --- | --- | --- |
| Shop Bootstrap Agent | `etsypulse-bootstrap` | Convert Etsy shop URL into shop profile, listings, keywords, and competitor seeds. |
| Keyword & SERP Agent | `etsypulse-keyword-serp` | Monitor keyword and search result movement. |
| Competitor Watch Agent | `etsypulse-competitor-watch` | Track competitor listing, price, and positioning changes. |
| Trend Scout Agent | `etsypulse-trend-scout` | Pull social, Reddit, Instagram, TikTok, and shopping trend signals. |
| Market Pulse Agent | `etsypulse-market-pulse` | Normalize raw signals into deduplicated market pulse events. |
| Judge Agent | `etsypulse-judge` | Score actionability, urgency, confidence, novelty, impact, and evidence quality. |
| Brief Delivery Agent | `etsypulse-brief-delivery` | Format approved market pulse signals into seller-facing briefs. |
| Coordinator | `etsypulse-coordinator` | Orchestrate the lane order and write results back to the backend. |

## Recommended Local Workflow

1. Run EtsyPulse normally in demo mode.
2. Keep OpenClaw optional. If installed, copy `docs/openclaw-config/openclaw.local-workflow.example.json` to your OpenClaw config location or point `OPENCLAW_CONFIG_PATH` to a copy.
3. Use the coordinator workspace instructions from `docs/openclaw-config/AGENTS.etsypulse-coordinator.md`.
4. Keep channel bindings out of the default config. Add `bindings` only when intentionally connecting a chat channel.
5. Use agent-to-agent routing for specialist lanes. The OpenClaw-facing tool names to enable or review are `agentToAgent`, `sessions_spawn`, `sessions_send`, `sessions_list`, `sessions_history`, `agents_list`, and `session_status`.

## Optional Channel Mode

Channel mode is useful after the demo is already stable. It should be added as a separate operator choice with explicit sender allowlists. Do not make channel setup part of the judge path.

Example binding shape from OpenClaw docs:

```json
{
  "bindings": [
    { "agentId": "etsypulse-coordinator", "match": { "channel": "discord", "guildId": "REPLACE_WITH_GUILD_ID" } }
  ]
}
```

This is intentionally not present in the default example config.

## Integration Boundary

`backend/app/services/openclaw_adapter.py` exposes a small mapping layer for the backend. It does not import OpenClaw and does not start an OpenClaw gateway. Its job is to document and validate the contract between EtsyPulse pipeline steps and future OpenClaw agent routing.

Future live OpenClaw work should add a separate runtime client behind this adapter, then call the existing `PipelineRunner` only as a fallback or local demo mode.

## Hosted Runtime Evaluation

Do not wire the public dashboard to a local OpenClaw gateway. For the deployed hackathon demo, the credible live path is a backend-managed OpenClaw runtime:

- Deploy FastAPI, Postgres, and the Vercel dashboard first.
- Add an internal/private OpenClaw service on Render or another host only after the main demo is verified.
- Keep provider keys on backend/OpenClaw services only; never expose them to Vercel.
- Apply hosted-demo rate and budget controls around OpenClaw-triggered provider calls.
- Preserve the deterministic Python pipeline as the local/no-runtime fallback.
- Require no Discord or channel binding for judges; use local workflow and agent-to-agent routing instead.

Real OpenClaw integration will need a runtime adapter that can submit coordinator tasks, poll or subscribe for agent results, map OpenClaw events into `ActivityEvent` and `DebugEvent` records, and fall back cleanly when OpenClaw is unavailable.
