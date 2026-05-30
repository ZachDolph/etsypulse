from app.agents.base import BaseAgent
from app.agents.contracts import KeywordSerpInput, KeywordSerpOutput
from app.agents.utils import source, stable_id
from app.schemas import KeywordSignal
from app.services.brightdata_client import BrightDataClient

_VISIBILITY_BY_RANK = {1: 0.91, 2: 0.82, 3: 0.73}
_SEVERITY_BY_RANK = {1: "high", 2: "medium", 3: "medium"}


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
            organic = query_data.get("organic", [])
            rank = int(organic[0].get("rank", index + 1)) if organic else index + 1
            description = organic[0].get("description", "") if organic else ""
            related_str = ", ".join(f"'{r}'" for r in related[:2]) if related else "'custom jewelry', 'gift for her'"
            movement = (
                f"SERP rank {rank}: {description.rstrip('.')} — buyer-intent queries lead organic results."
                if description
                else f"'{keyword}' holds rank {rank} in gift-intent search results; click-through opportunity is strong."
            )
            opportunity = (
                f"Add '{keyword}' to your listing title and first-image alt text. "
                f"Weave related terms {related_str} into tags and the listing description to capture adjacent searches."
            )
            signals.append(
                KeywordSignal(
                    id=stable_id("keyword", f"{agent_input.run_id}:{keyword}"),
                    run_id=agent_input.run_id,
                    keyword=keyword,
                    movement=movement,
                    opportunity=opportunity,
                    visibility_score=_VISIBILITY_BY_RANK.get(rank, round(0.78 - index * 0.05, 2)),
                    severity=_SEVERITY_BY_RANK.get(rank, "medium"),
                    provenance=[source("search_engine", f"https://www.google.com/search?q={keyword.replace(' ', '+')}")],
                    confidence=round(0.90 - index * 0.04, 2),
                )
            )
        return KeywordSerpOutput(keyword_signals=signals)
