from pydantic import BaseModel, Field

from app.agents.contracts import PipelineRunOutput


class OpenClawAgentMapping(BaseModel):
    etsy_pulse_agent: str
    openclaw_agent_id: str
    role: str
    required_tools: list[str] = Field(default_factory=list)


class OpenClawHandoff(BaseModel):
    from_agent_id: str
    to_agent_id: str
    payload_schema: str
    summary: str


class OpenClawRunRequest(BaseModel):
    shop_url: str
    coordinator_agent_id: str = "etsypulse-coordinator"
    mode: str = "local-workflow"


class OpenClawRunSummary(BaseModel):
    run_id: str
    coordinator_agent_id: str
    local_pipeline_status: str
    agent_ids: list[str]
    brief_ids: list[str]
    handoffs: list[OpenClawHandoff]


OPENCLAW_TOOL_NAMES = [
    "agentToAgent",
    "agents_list",
    "sessions_spawn",
    "sessions_send",
    "sessions_history",
    "session_status",
]


AGENT_MAPPINGS = [
    OpenClawAgentMapping(
        etsy_pulse_agent="Shop Bootstrap Agent",
        openclaw_agent_id="etsypulse-bootstrap",
        role="Extract shop profile, listings, seed keywords, and competitors.",
        required_tools=["agentToAgent", "sessions_spawn"],
    ),
    OpenClawAgentMapping(
        etsy_pulse_agent="Keyword & SERP Agent",
        openclaw_agent_id="etsypulse-keyword-serp",
        role="Monitor keyword and SERP changes.",
        required_tools=["agentToAgent", "sessions_spawn"],
    ),
    OpenClawAgentMapping(
        etsy_pulse_agent="Competitor Watch Agent",
        openclaw_agent_id="etsypulse-competitor-watch",
        role="Track competitor listing, pricing, and positioning signals.",
        required_tools=["agentToAgent", "sessions_spawn"],
    ),
    OpenClawAgentMapping(
        etsy_pulse_agent="Trend Scout Agent",
        openclaw_agent_id="etsypulse-trend-scout",
        role="Collect social, Reddit, search, and shopping trend signals.",
        required_tools=["agentToAgent", "sessions_spawn"],
    ),
    OpenClawAgentMapping(
        etsy_pulse_agent="Market Pulse Agent",
        openclaw_agent_id="etsypulse-market-pulse",
        role="Normalize signals into deduplicated market pulse events.",
        required_tools=["agentToAgent", "sessions_send"],
    ),
    OpenClawAgentMapping(
        etsy_pulse_agent="Judge Agent",
        openclaw_agent_id="etsypulse-judge",
        role="Score actionability, novelty, confidence, urgency, impact, and evidence quality.",
        required_tools=["agentToAgent", "sessions_send"],
    ),
    OpenClawAgentMapping(
        etsy_pulse_agent="Brief Delivery Agent",
        openclaw_agent_id="etsypulse-brief-delivery",
        role="Format approved signals into seller-facing briefs.",
        required_tools=["agentToAgent", "sessions_send"],
    ),
]


def get_openclaw_agent_mappings() -> list[OpenClawAgentMapping]:
    return list(AGENT_MAPPINGS)


def summarize_pipeline_for_openclaw(output: PipelineRunOutput, coordinator_agent_id: str = "etsypulse-coordinator") -> OpenClawRunSummary:
    agent_ids = [mapping.openclaw_agent_id for mapping in AGENT_MAPPINGS]
    handoffs = [
        OpenClawHandoff(
            from_agent_id=coordinator_agent_id,
            to_agent_id=mapping.openclaw_agent_id,
            payload_schema=_payload_schema_for(mapping.etsy_pulse_agent),
            summary=mapping.role,
        )
        for mapping in AGENT_MAPPINGS
    ]
    return OpenClawRunSummary(
        run_id=output.run.id,
        coordinator_agent_id=coordinator_agent_id,
        local_pipeline_status=output.run.status,
        agent_ids=agent_ids,
        brief_ids=[brief.id for brief in output.briefs],
        handoffs=handoffs,
    )


def _payload_schema_for(agent_name: str) -> str:
    schemas = {
        "Shop Bootstrap Agent": "ShopProfile",
        "Keyword & SERP Agent": "list[KeywordSignal]",
        "Competitor Watch Agent": "list[CompetitorSignal]",
        "Trend Scout Agent": "list[TrendSignal]",
        "Market Pulse Agent": "list[MarketPulseSignal]",
        "Judge Agent": "list[JudgeScore]",
        "Brief Delivery Agent": "list[Brief]",
    }
    return schemas[agent_name]
