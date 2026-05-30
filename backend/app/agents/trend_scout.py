from app.agents.base import BaseAgent
from app.agents.contracts import TrendScoutInput, TrendScoutOutput
from app.agents.utils import source, stable_id
from app.schemas import TrendSignal
from app.services.brightdata_client import BrightDataClient


class TrendScoutAgent(BaseAgent[TrendScoutInput, TrendScoutOutput]):
    name = "Trend Scout Agent"

    def __init__(self, brightdata: BrightDataClient) -> None:
        self.brightdata = brightdata

    def run(self, agent_input: TrendScoutInput) -> TrendScoutOutput:
        query = agent_input.shop_profile.seed_keywords[0] if agent_input.shop_profile.seed_keywords else "personalized jewelry gift"
        tiktok = self.brightdata.tiktok_posts(query)
        reddit = self.brightdata.reddit_posts(query)
        instagram = self.brightdata.instagram_reels(query)
        shopping = self.brightdata.google_shopping(query)
        return TrendScoutOutput(
            trend_signals=[
                TrendSignal(
                    id=stable_id("trend", f"{agent_input.run_id}:tiktok:{query}"),
                    run_id=agent_input.run_id,
                    platform="TikTok",
                    topic=query,
                    signal=f"TikTok demo cache has {len(tiktok.get('posts', []))} post(s) around personalized jewelry gift intent.",
                    momentum_score=0.74,
                    severity="medium",
                    provenance=[source("web_data_tiktok_posts")],
                    confidence=0.8,
                ),
                TrendSignal(
                    id=stable_id("trend", f"{agent_input.run_id}:reddit:{query}"),
                    run_id=agent_input.run_id,
                    platform="Reddit",
                    topic=query,
                    signal=f"Reddit demo cache has {len(reddit.get('posts', []))} practical gift discussion(s).",
                    momentum_score=0.69,
                    severity="medium",
                    provenance=[source("web_data_reddit_posts")],
                    confidence=0.78,
                ),
                TrendSignal(
                    id=stable_id("trend", f"{agent_input.run_id}:instagram:{query}"),
                    run_id=agent_input.run_id,
                    platform="Instagram",
                    topic=query,
                    signal=f"Instagram reels demo cache has {len(instagram.get('reels', []))} personalized jewelry styling signal(s).",
                    momentum_score=0.71,
                    severity="medium",
                    provenance=[source("web_data_instagram_reels")],
                    confidence=0.79,
                ),
                TrendSignal(
                    id=stable_id("trend", f"{agent_input.run_id}:shopping:{query}"),
                    run_id=agent_input.run_id,
                    platform="Google Shopping",
                    topic=query,
                    signal=f"Google Shopping demo cache has {len(shopping.get('products', []))} comparable product(s) for price anchoring.",
                    momentum_score=0.66,
                    severity="low",
                    provenance=[source("web_data_google_shopping")],
                    confidence=0.76,
                ),
            ]
        )
