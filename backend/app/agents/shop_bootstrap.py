from app.agents.base import BaseAgent
from app.agents.contracts import ShopBootstrapInput, ShopBootstrapOutput
from app.schemas import Listing, ShopProfile
from app.services.brightdata_client import BrightDataClient
from app.agents.utils import source, stable_id


class ShopBootstrapAgent(BaseAgent[ShopBootstrapInput, ShopBootstrapOutput]):
    name = "Shop Bootstrap Agent"

    def __init__(self, brightdata: BrightDataClient) -> None:
        self.brightdata = brightdata

    def run(self, agent_input: ShopBootstrapInput) -> ShopBootstrapOutput:
        products = self.brightdata.etsy_products(shop_url=agent_input.shop_url)
        markdown = self.brightdata.scrape_markdown(agent_input.shop_url)
        items = products.get("items", []) if isinstance(products, dict) else []
        shop_id = stable_id("shop", agent_input.shop_url)
        evidence = [source("web_data_etsy_products", agent_input.shop_url), source("scrape_as_markdown", agent_input.shop_url)]
        listings = [
            Listing(
                id=stable_id("listing", item.get("url", f"{agent_input.shop_url}:{index}")),
                shop_id=shop_id,
                title=item.get("title", "Untitled listing"),
                url=item.get("url", agent_input.shop_url),
                price=float(item.get("price", 0)),
                currency=item.get("currency", "USD"),
                tags=list(item.get("tags", [])),
                provenance=evidence,
                confidence=0.9,
            )
            for index, item in enumerate(items)
        ]
        seed_keywords = sorted({tag for listing in listings for tag in listing.tags})[:5]
        profile = ShopProfile(
            id=shop_id,
            shop_url=agent_input.shop_url,
            shop_name="Demo Linen Studio",
            category="Home & Living / Kitchen Textiles",
            summary=markdown.splitlines()[2] if len(markdown.splitlines()) > 2 else "Demo Etsy shop profile.",
            listings=listings,
            seed_keywords=seed_keywords or ["linen tea towel", "hostess gift"],
            likely_competitors=["CottageLinenCo", "ModernHearthGoods"],
            baseline_positioning="Giftable handmade linen basics with neutral home styling.",
            provenance=evidence,
            confidence=0.91,
        )
        return ShopBootstrapOutput(shop_profile=profile)
