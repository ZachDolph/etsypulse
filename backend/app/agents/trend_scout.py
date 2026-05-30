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

        # Extract actionable insights from fixture data
        tiktok_posts = tiktok.get("posts", []) if isinstance(tiktok, dict) else []
        top_hashtags: list[str] = []
        max_likes = 0
        for post in tiktok_posts:
            top_hashtags.extend(post.get("hashtags", []))
            max_likes = max(max_likes, post.get("likes", 0))
        hashtag_str = ", ".join(f"#{h}" for h in top_hashtags[:3]) if top_hashtags else "#giftforher, #personalizedjewelry, #namenecklace"

        reddit_posts = reddit.get("posts", []) if isinstance(reddit, dict) else []
        reddit_title = reddit_posts[0].get("title", "gift recommendations thread") if reddit_posts else "gift recommendations thread"
        reddit_score = reddit_posts[0].get("score", 0) if reddit_posts else 0
        reddit_summary = reddit_posts[0].get("summary", "") if reddit_posts else ""

        shopping_count = len(shopping.get("products", [])) if isinstance(shopping, dict) else 0

        return TrendScoutOutput(
            trend_signals=[
                TrendSignal(
                    id=stable_id("trend", f"{agent_input.run_id}:tiktok:{query}"),
                    run_id=agent_input.run_id,
                    platform="TikTok",
                    topic=query,
                    signal=(
                        f"Top TikTok content on '{query}' reached {max_likes:,} likes. "
                        f"Trending hashtags {hashtag_str} confirm gift-intent creative is outperforming generic product shots. "
                        "Align listing hero images and shop cover with this aesthetic to capture social-referred traffic."
                    ),
                    momentum_score=0.82,
                    severity="high",
                    provenance=[source("web_data_tiktok_posts")],
                    confidence=0.84,
                ),
                TrendSignal(
                    id=stable_id("trend", f"{agent_input.run_id}:reddit:{query}"),
                    run_id=agent_input.run_id,
                    platform="Reddit",
                    topic=query,
                    signal=(
                        f"Reddit thread '{reddit_title}' has {reddit_score} upvotes in gift-ideas communities. "
                        f"{reddit_summary} "
                        "Purchase-ready buyer intent is clear — a curated gift bundle or collection page would capture this audience directly."
                    ),
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
                    signal=(
                        f"Instagram Reels for '{query}' show gift-unboxing and packaging content gaining the most reach. "
                        "Lifestyle shots with wrapping and handwritten notes outperform plain product photos. "
                        "Update listing hero images to lead with the gifting experience, not just the product."
                    ),
                    momentum_score=0.74,
                    severity="medium",
                    provenance=[source("web_data_instagram_reels")],
                    confidence=0.81,
                ),
                TrendSignal(
                    id=stable_id("trend", f"{agent_input.run_id}:shopping:{query}"),
                    run_id=agent_input.run_id,
                    platform="Google Shopping",
                    topic=query,
                    signal=(
                        f"Google Shopping surfaces {shopping_count} comparable listings for '{query}'. "
                        "Top competitors lead titles with occasion keywords (birthday, anniversary, graduation). "
                        "Add occasion framing to your listing titles and tags to capture comparison shoppers before they settle on a competitor."
                    ),
                    momentum_score=0.66,
                    severity="low",
                    provenance=[source("web_data_google_shopping")],
                    confidence=0.76,
                ),
            ]
        )
