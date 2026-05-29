from app.agents.base import BaseAgent
from app.agents.contracts import CompetitorWatchInput, CompetitorWatchOutput
from app.agents.utils import source, stable_id
from app.schemas import CompetitorSignal
from app.services.brightdata_client import BrightDataClient


class CompetitorWatchAgent(BaseAgent[CompetitorWatchInput, CompetitorWatchOutput]):
    name = "Competitor Watch Agent"

    def __init__(self, brightdata: BrightDataClient) -> None:
        self.brightdata = brightdata

    def run(self, agent_input: CompetitorWatchInput) -> CompetitorWatchOutput:
        competitor_urls = [f"https://www.etsy.com/shop/{name}" for name in agent_input.shop_profile.likely_competitors]
        self.brightdata.scrape_batch(competitor_urls)
        products = self.brightdata.etsy_products(search_url="https://www.etsy.com/search?q=linen+tea+towel")
        item_count = len(products.get("items", [])) if isinstance(products, dict) else 0
        signals = [
            CompetitorSignal(
                id=stable_id("competitor", f"{agent_input.run_id}:{name}"),
                run_id=agent_input.run_id,
                competitor_name=name,
                competitor_url=f"https://www.etsy.com/shop/{name}",
                signal=f"{name} is positioned near {item_count} comparable linen listings in demo cache; gift bundle positioning is visible.",
                price_delta_percent=-8.0 if index == 0 else 4.0,
                severity="medium",
                provenance=[source("scrape_as_markdown", f"https://www.etsy.com/shop/{name}"), source("web_data_etsy_products")],
                confidence=0.82,
            )
            for index, name in enumerate(agent_input.shop_profile.likely_competitors)
        ]
        return CompetitorWatchOutput(competitor_signals=signals)
