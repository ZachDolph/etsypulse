import json
import sys
import tempfile
from pathlib import Path

from sqlalchemy.orm import sessionmaker

from app.agents.contracts import PipelineRunInput
from app.agents.pipeline import PipelineRunner
from app.database import Base, build_engine
from app.services.brightdata_client import BrightDataClient
from app.services.llm_client import LLMClient
from app.services.openclaw_adapter import get_openclaw_agent_mappings, summarize_pipeline_for_openclaw
from app.store import EtsyPulseStore

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "docs" / "openclaw-config" / "openclaw.local-workflow.example.json"
REQUIRED_DOCS = [
    ROOT / "docs" / "openclaw.md",
    ROOT / "docs" / "openclaw-config" / "AGENTS.etsypulse-coordinator.md",
    ROOT / "docs" / "openclaw-config" / "SOUL.etsypulse-coordinator.md",
    ROOT / "docs" / "openclaw-config" / "lane-contracts.md",
]


def validate_files() -> dict:
    missing = [str(path.relative_to(ROOT)) for path in [CONFIG_PATH, *REQUIRED_DOCS] if not path.exists()]
    if missing:
        raise AssertionError(f"Missing OpenClaw config/doc files: {', '.join(missing)}")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    agent_ids = {agent["id"] for agent in config["agents"]["list"]}
    expected_ids = {"etsypulse-coordinator", *{mapping.openclaw_agent_id for mapping in get_openclaw_agent_mappings()}}
    missing_agents = expected_ids - agent_ids
    if missing_agents:
        raise AssertionError(f"OpenClaw config is missing agents: {sorted(missing_agents)}")

    if config["bindings"] != []:
        raise AssertionError("Portable OpenClaw config must not require channel bindings")
    if not config["tools"]["agentToAgent"]["enabled"]:
        raise AssertionError("agentToAgent must be enabled in the local workflow example")
    if config["tools"]["sessions"]["visibility"] != "tree":
        raise AssertionError("sessions.visibility should stay tree for portable subagent runs")
    return config


def run_backend_pipeline_smoke() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        engine = build_engine(f"sqlite:///{Path(temp_dir) / 'smoke.db'}")
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        with session_factory() as session:
            store = EtsyPulseStore(session)
            brightdata = BrightDataClient(demo_mode=True, debug_sink=store.record_debug_event)
            llm_client = LLMClient(force_test_mode=True, debug_sink=store.record_debug_event)
            runner = PipelineRunner(store=store, brightdata=brightdata, llm_client=llm_client)
            output = runner.run_demo(PipelineRunInput(shop_url="https://www.etsy.com/shop/demo-linen-studio"))
            summary = summarize_pipeline_for_openclaw(output)

            if output.run.status != "completed":
                raise AssertionError(f"Expected completed run, got {output.run.status}")
            if len(output.briefs) < 1:
                raise AssertionError("Expected at least one demo brief")
            if len(summary.agent_ids) != 7:
                raise AssertionError("Expected seven OpenClaw specialist agent ids")
            if len(store.list_activity()) < 7:
                raise AssertionError("Expected activity events from every pipeline step")
            if not store.list_debug_events():
                raise AssertionError("Expected Bright Data and LLM debug events")
            return output.run.id


def main() -> int:
    validate_files()
    run_id = run_backend_pipeline_smoke()
    print("OpenClaw config smoke passed")
    print(f"Backend demo pipeline smoke passed: {run_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"OpenClaw smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
