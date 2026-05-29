from app.agents.brief_delivery import BriefDeliveryAgent
from app.agents.competitor_watch import CompetitorWatchAgent
from app.agents.contracts import (
    BriefDeliveryInput,
    CompetitorWatchInput,
    JudgeInput,
    KeywordSerpInput,
    MarketPulseInput,
    PipelineRunInput,
    PipelineRunOutput,
    ShopBootstrapInput,
    TrendScoutInput,
)
from app.agents.judge import JudgeAgent
from app.agents.keyword_serp import KeywordSerpAgent
from app.agents.market_pulse import MarketPulseAgent
from app.agents.shop_bootstrap import ShopBootstrapAgent
from app.agents.trend_scout import TrendScoutAgent
from app.agents.utils import activity_event, stable_id
from app.schemas import AgentRun, utc_now
from app.services.brightdata_client import BrightDataClient
from app.services.llm_client import LLMClient
from app.store import EtsyPulseStore


class PipelineRunner:
    def __init__(self, store: EtsyPulseStore, brightdata: BrightDataClient, llm_client: LLMClient | None = None) -> None:
        self.store = store
        self.brightdata = brightdata
        self.llm_client = llm_client
        self.shop_bootstrap = ShopBootstrapAgent(brightdata)
        self.keyword_serp = KeywordSerpAgent(brightdata)
        self.competitor_watch = CompetitorWatchAgent(brightdata)
        self.trend_scout = TrendScoutAgent(brightdata)
        self.market_pulse = MarketPulseAgent()
        self.judge = JudgeAgent(llm_client)
        self.brief_delivery = BriefDeliveryAgent()

    def run_demo(self, pipeline_input: PipelineRunInput) -> PipelineRunOutput:
        run_id = stable_id("run", f"{pipeline_input.shop_url}:session-4-agent-pipeline")
        shop_output = self.shop_bootstrap.run(ShopBootstrapInput(shop_url=pipeline_input.shop_url))
        shop = shop_output.shop_profile
        self.store.save_shop_profile(shop)
        self._record_step(run_id, self.shop_bootstrap.name, "completed", "Shop profile, listings, seed keywords, and competitors prepared.")

        keyword_output = self.keyword_serp.run(KeywordSerpInput(run_id=run_id, shop_profile=shop))
        self._record_step(run_id, self.keyword_serp.name, "completed", f"Generated {len(keyword_output.keyword_signals)} keyword signal(s).")

        competitor_output = self.competitor_watch.run(CompetitorWatchInput(run_id=run_id, shop_profile=shop))
        self._record_step(run_id, self.competitor_watch.name, "completed", f"Generated {len(competitor_output.competitor_signals)} competitor signal(s).")

        trend_output = self.trend_scout.run(TrendScoutInput(run_id=run_id, shop_profile=shop))
        self._record_step(run_id, self.trend_scout.name, "completed", f"Generated {len(trend_output.trend_signals)} trend signal(s).")

        pulse_output = self.market_pulse.run(
            MarketPulseInput(
                run_id=run_id,
                keyword_signals=keyword_output.keyword_signals,
                competitor_signals=competitor_output.competitor_signals,
                trend_signals=trend_output.trend_signals,
            )
        )
        self._record_step(run_id, self.market_pulse.name, "completed", f"Generated {len(pulse_output.market_pulse_signals)} market pulse signal(s).")

        judge_output = self.judge.run(JudgeInput(run_id=run_id, market_pulse_signals=pulse_output.market_pulse_signals))
        self._record_step(run_id, self.judge.name, "completed", f"Scored {len(judge_output.judge_scores)} market pulse signal(s).")

        brief_output = self.brief_delivery.run(
            BriefDeliveryInput(
                run_id=run_id,
                shop_profile=shop,
                market_pulse_signals=pulse_output.market_pulse_signals,
                judge_scores=judge_output.judge_scores,
            )
        )
        self._record_step(run_id, self.brief_delivery.name, "completed", f"Delivered {len(brief_output.briefs)} approved brief(s).")

        run = AgentRun(
            id=run_id,
            shop_id=shop.id,
            mode="demo",
            status="completed",
            started_at=utc_now(),
            completed_at=utc_now(),
            agents=[
                self.shop_bootstrap.name,
                self.keyword_serp.name,
                self.competitor_watch.name,
                self.trend_scout.name,
                self.market_pulse.name,
                self.judge.name,
                self.brief_delivery.name,
            ],
            keyword_signals=keyword_output.keyword_signals,
            competitor_signals=competitor_output.competitor_signals,
            trend_signals=trend_output.trend_signals,
            market_pulse_signals=pulse_output.market_pulse_signals,
            judge_scores=judge_output.judge_scores,
            brief_ids=[brief.id for brief in brief_output.briefs],
        )
        self.store.save_agent_run(run)
        for brief in brief_output.briefs:
            self.store.save_brief(brief)
        return PipelineRunOutput(run=run, shop_profile=shop, briefs=brief_output.briefs)

    def _record_step(self, run_id: str, agent: str, event_type: str, message: str) -> None:
        self.store.record_activity_event(activity_event(run_id, agent, event_type, message))
