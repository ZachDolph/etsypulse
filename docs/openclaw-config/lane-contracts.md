# EtsyPulse OpenClaw Lane Contracts

Each lane must return typed data compatible with the Pydantic schemas in `backend/app/schemas.py` and the agent contracts in `backend/app/agents/contracts.py`.

## Shared Requirements

- Include `run_id`, source/provenance, timestamp, confidence, and originating agent.
- Redact secrets in all debug summaries.
- Prefer deterministic demo fixtures unless live mode is explicitly enabled.
- Keep outputs small enough for the Judge Agent to inspect evidence quality.

## Lanes

- `etsypulse-bootstrap`: output `ShopProfile`.
- `etsypulse-keyword-serp`: output `KeywordSignal[]`.
- `etsypulse-competitor-watch`: output `CompetitorSignal[]`.
- `etsypulse-trend-scout`: output `TrendSignal[]`.
- `etsypulse-market-pulse`: output `MarketPulseSignal[]`.
- `etsypulse-judge`: output `JudgeScore[]`.
- `etsypulse-brief-delivery`: output `Brief[]`.
