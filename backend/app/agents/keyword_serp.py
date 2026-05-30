from app.agents.base import BaseAgent
from app.agents.contracts import KeywordSerpInput, KeywordSerpOutput
from app.agents.utils import source, stable_id
from app.schemas import KeywordSignal
from app.services.brightdata_client import BrightDataClient


class KeywordSerpAgent(BaseAgent[KeywordSerpInput, KeywordSerpOutput]):
    name = "Keyword & SERP Agent"

    def __init__(self, brightdata: BrightDataClient) -> None:
        self.brightdata = brightdata

    def run(self, agent_input: KeywordSerpInput) -> KeywordSerpOutput:
        keywords = agent_input.shop_profile.seed_keywords[:3]
        serp = self.brightdata.serp_batch(keywords)
        queries = serp.get("queries", []) if isinstance(serp, dict) else []
        signals: list[KeywordSignal] = []
        for index, keyword in enumerate(keywords):
            query_data = queries[index % len(queries)] if queries else {}
            related = query_data.get("related_searches", [])
            signals.append(
                KeywordSignal(
                    id=stable_id("keyword", f"{agent_input.run_id}:{keyword}"),
                    run_id=agent_input.run_id,
                    keyword=keyword,
                    movement="Demo SERP fixture shows buyer intent around personalized jewelry gifts.",
                    opportunity=f"Refresh listing copy around '{keyword}' and related terms: {', '.join(related[:2])}.",
                    visibility_score=0.78,
                    severity="medium",
                    provenance=[source("search_engine", f"https://www.google.com/search?q={keyword.replace(' ', '+')}")],
                    confidence=0.84,
                )
            )
        return KeywordSerpOutput(keyword_signals=signals)
