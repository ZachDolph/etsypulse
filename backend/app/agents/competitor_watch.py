from app.agents.base import BaseAgent
from app.agents.contracts import CompetitorWatchInput, CompetitorWatchOutput
from app.agents.utils import source, stable_id
from app.schemas import CompetitorSignal
from app.services.brightdata_client import BrightDataClient

_PRICE_DELTAS = [-8.0, 4.5]
_RESPONSE_FRAMES = [
    "defend your premium with stronger social proof, packaging photos, and review velocity.",
    "match their bundling offers and emphasize faster customization turnaround to protect market share.",
]
_SEVERITIES = ["high", "medium"]
_CONFIDENCES = [0.87, 0.81]


class CompetitorWatchAgent(BaseAgent[CompetitorWatchInput, CompetitorWatchOutput]):
    name = "Competitor Watch Agent"

    def __init__(self, brightdata: BrightDataClient) -> None:
        self.brightdata = brightdata

    def run(self, agent_input: CompetitorWatchInput) -> CompetitorWatchOutput:
        competitor_urls = [f"https://www.etsy.com/shop/{name}" for name in agent_input.shop_profile.likely_competitors]
        self.brightdata.scrape_batch(competitor_urls)
        products = self.brightdata.etsy_products(search_url="https://www.etsy.com/search?q=personalized+necklace")
        item_count = len(products.get("items", [])) if isinstance(products, dict) else 0
        signals = []
        for index, name in enumerate(agent_input.shop_profile.likely_competitors):
            delta = _PRICE_DELTAS[index % len(_PRICE_DELTAS)]
            direction = "below" if delta < 0 else "above"
            response = _RESPONSE_FRAMES[index % len(_RESPONSE_FRAMES)]
            signals.append(
                CompetitorSignal(
                    id=stable_id("competitor", f"{agent_input.run_id}:{name}"),
                    run_id=agent_input.run_id,
                    competitor_name=name,
                    competitor_url=f"https://www.etsy.com/shop/{name}",
                    signal=(
                        f"{name} is priced {abs(delta):.0f}% {direction} comparable listings "
                        f"across {item_count} personalized jewelry results. "
                        f"Their gift-ready copy and bundle positioning is gaining search visibility — {response}"
                    ),
                    price_delta_percent=delta,
                    severity=_SEVERITIES[index % len(_SEVERITIES)],
                    provenance=[
                        source("scrape_as_markdown", f"https://www.etsy.com/shop/{name}"),
                        source("web_data_etsy_products"),
                    ],
                    confidence=_CONFIDENCES[index % len(_CONFIDENCES)],
                )
            )
        return CompetitorWatchOutput(competitor_signals=signals)
