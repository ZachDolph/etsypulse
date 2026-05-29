from sqlalchemy.orm import sessionmaker

from app.agents.contracts import PipelineRunInput
from app.agents.pipeline import PipelineRunner
from app.database import Base, build_engine
from app.services.brightdata_client import BrightDataClient
from app.services.llm_client import LLMClient
from app.services.openclaw_adapter import get_openclaw_agent_mappings, summarize_pipeline_for_openclaw
from app.store import EtsyPulseStore


def test_openclaw_agent_mappings_cover_pipeline_agents() -> None:
    mappings = get_openclaw_agent_mappings()

    assert len(mappings) == 7
    assert {mapping.openclaw_agent_id for mapping in mappings} == {
        "etsypulse-bootstrap",
        "etsypulse-keyword-serp",
        "etsypulse-competitor-watch",
        "etsypulse-trend-scout",
        "etsypulse-market-pulse",
        "etsypulse-judge",
        "etsypulse-brief-delivery",
    }
    assert all("agentToAgent" in mapping.required_tools for mapping in mappings)


def test_openclaw_summary_wraps_local_pipeline_output(tmp_path) -> None:
    engine = build_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with session_factory() as session:
        store = EtsyPulseStore(session)
        runner = PipelineRunner(
            store=store,
            brightdata=BrightDataClient(demo_mode=True, debug_sink=store.record_debug_event),
            llm_client=LLMClient(force_test_mode=True, debug_sink=store.record_debug_event),
        )
        output = runner.run_demo(PipelineRunInput(shop_url="https://www.etsy.com/shop/demo-linen-studio"))

    summary = summarize_pipeline_for_openclaw(output)

    assert summary.local_pipeline_status == "completed"
    assert summary.coordinator_agent_id == "etsypulse-coordinator"
    assert summary.brief_ids == [brief.id for brief in output.briefs]
    assert len(summary.handoffs) == 7
    assert summary.handoffs[0].payload_schema == "ShopProfile"
