from collections.abc import Generator

import pytest
from sqlalchemy.orm import sessionmaker

from app.agents.brief_delivery import BriefDeliveryAgent
from app.agents.competitor_watch import CompetitorWatchAgent
from app.agents.contracts import (
    BriefDeliveryInput,
    CompetitorWatchInput,
    JudgeInput,
    KeywordSerpInput,
    MarketPulseInput,
    PipelineRunInput,
    ShopBootstrapInput,
    TrendScoutInput,
)
from app.agents.judge import JudgeAgent
from app.agents.keyword_serp import KeywordSerpAgent
from app.agents.market_pulse import MarketPulseAgent
from app.agents.pipeline import PipelineRunner
from app.agents.shop_bootstrap import ShopBootstrapAgent
from app.agents.trend_scout import TrendScoutAgent
from app.database import Base, build_engine
from app.services.brightdata_client import BrightDataClient
from app.services.llm_client import LLMClient
from app.store import EtsyPulseStore


@pytest.fixture()
def store(tmp_path) -> Generator[EtsyPulseStore, None, None]:
    engine = build_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as session:
        yield EtsyPulseStore(session)


@pytest.fixture()
def brightdata() -> BrightDataClient:
    return BrightDataClient(demo_mode=True)


def test_shop_bootstrap_agent_extracts_profile(brightdata: BrightDataClient) -> None:
    output = ShopBootstrapAgent(brightdata).run(ShopBootstrapInput(shop_url="https://www.etsy.com/shop/demo-linen-studio"))

    assert output.shop_profile.shop_name == "Demo Linen Studio"
    assert output.shop_profile.listings
    assert output.shop_profile.seed_keywords
    assert output.shop_profile.likely_competitors


def test_keyword_serp_agent_outputs_keyword_signals(brightdata: BrightDataClient) -> None:
    shop = ShopBootstrapAgent(brightdata).run(ShopBootstrapInput(shop_url="https://www.etsy.com/shop/demo-linen-studio")).shop_profile
    output = KeywordSerpAgent(brightdata).run(KeywordSerpInput(run_id="run_test", shop_profile=shop))

    assert output.keyword_signals
    assert output.keyword_signals[0].run_id == "run_test"
    assert output.keyword_signals[0].provenance[0].tool == "search_engine"


def test_competitor_watch_agent_outputs_competitor_signals(brightdata: BrightDataClient) -> None:
    shop = ShopBootstrapAgent(brightdata).run(ShopBootstrapInput(shop_url="https://www.etsy.com/shop/demo-linen-studio")).shop_profile
    output = CompetitorWatchAgent(brightdata).run(CompetitorWatchInput(run_id="run_test", shop_profile=shop))

    assert len(output.competitor_signals) == len(shop.likely_competitors)
    assert output.competitor_signals[0].competitor_url.startswith("https://www.etsy.com/shop/")


def test_trend_scout_agent_outputs_social_and_search_signals(brightdata: BrightDataClient) -> None:
    shop = ShopBootstrapAgent(brightdata).run(ShopBootstrapInput(shop_url="https://www.etsy.com/shop/demo-linen-studio")).shop_profile
    output = TrendScoutAgent(brightdata).run(TrendScoutInput(run_id="run_test", shop_profile=shop))

    assert {signal.platform for signal in output.trend_signals} == {"TikTok", "Reddit", "Instagram", "Google Shopping"}


def test_market_pulse_agent_normalizes_signals(brightdata: BrightDataClient) -> None:
    shop = ShopBootstrapAgent(brightdata).run(ShopBootstrapInput(shop_url="https://www.etsy.com/shop/demo-linen-studio")).shop_profile
    keyword = KeywordSerpAgent(brightdata).run(KeywordSerpInput(run_id="run_test", shop_profile=shop))
    competitor = CompetitorWatchAgent(brightdata).run(CompetitorWatchInput(run_id="run_test", shop_profile=shop))
    trend = TrendScoutAgent(brightdata).run(TrendScoutInput(run_id="run_test", shop_profile=shop))

    output = MarketPulseAgent().run(
        MarketPulseInput(
            run_id="run_test",
            keyword_signals=keyword.keyword_signals,
            competitor_signals=competitor.competitor_signals,
            trend_signals=trend.trend_signals,
        )
    )

    assert output.market_pulse_signals
    assert output.market_pulse_signals[0].source_signal_ids
    assert output.market_pulse_signals[0].originating_agent == "Market Pulse Agent"


def test_judge_agent_scores_market_pulse_with_fake_llm(brightdata: BrightDataClient) -> None:
    shop = ShopBootstrapAgent(brightdata).run(ShopBootstrapInput(shop_url="https://www.etsy.com/shop/demo-linen-studio")).shop_profile
    keyword = KeywordSerpAgent(brightdata).run(KeywordSerpInput(run_id="run_test", shop_profile=shop))
    pulse = MarketPulseAgent().run(MarketPulseInput(run_id="run_test", keyword_signals=keyword.keyword_signals))
    llm = LLMClient(force_test_mode=True)

    output = JudgeAgent(llm).run(JudgeInput(run_id="run_test", market_pulse_signals=pulse.market_pulse_signals))

    assert output.judge_scores
    assert output.judge_scores[0].decision == "brief"
    assert output.judge_scores[0].rationale == "fake_rationale"
    assert llm.debug_events


def test_brief_delivery_agent_formats_approved_briefs(brightdata: BrightDataClient) -> None:
    shop = ShopBootstrapAgent(brightdata).run(ShopBootstrapInput(shop_url="https://www.etsy.com/shop/demo-linen-studio")).shop_profile
    keyword = KeywordSerpAgent(brightdata).run(KeywordSerpInput(run_id="run_test", shop_profile=shop))
    pulse = MarketPulseAgent().run(MarketPulseInput(run_id="run_test", keyword_signals=keyword.keyword_signals))
    judge = JudgeAgent(LLMClient(force_test_mode=True)).run(JudgeInput(run_id="run_test", market_pulse_signals=pulse.market_pulse_signals))

    output = BriefDeliveryAgent().run(
        BriefDeliveryInput(
            run_id="run_test",
            shop_profile=shop,
            market_pulse_signals=pulse.market_pulse_signals,
            judge_scores=judge.judge_scores,
        )
    )

    assert output.briefs
    assert output.briefs[0].recommended_actions
    assert output.briefs[0].judge_score.decision == "brief"


def test_pipeline_runner_persists_run_activity_briefs_and_debug(store: EtsyPulseStore) -> None:
    brightdata = BrightDataClient(demo_mode=True, debug_sink=store.record_debug_event)
    llm = LLMClient(debug_sink=store.record_debug_event, force_test_mode=True)
    runner = PipelineRunner(store=store, brightdata=brightdata, llm_client=llm)

    output = runner.run_demo(PipelineRunInput(shop_url="https://www.etsy.com/shop/demo-linen-studio"))

    assert output.run.status == "completed"
    assert output.run.keyword_signals
    assert output.run.competitor_signals
    assert output.run.trend_signals
    assert output.run.market_pulse_signals
    assert output.run.judge_scores
    assert output.briefs
    assert store.get_run(output.run.id).id == output.run.id
    assert len(store.list_activity()) >= 7
    assert store.list_briefs()
    assert any(event.provider == "Fake LLM" for event in store.list_debug_events())
