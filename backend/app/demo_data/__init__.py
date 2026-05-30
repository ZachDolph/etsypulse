from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from app.schemas import (
    ActivityEvent,
    AgentRun,
    Brief,
    CompetitorSignal,
    DebugEvent,
    EvidenceSource,
    JudgeScore,
    KeywordSignal,
    Listing,
    MarketPulseSignal,
    ShopProfile,
    TrendSignal,
)

DEFAULT_SHOP_URL = "https://www.etsy.com/shop/CaitlynMinimalist"
AGENTS = [
    "Shop Bootstrap Agent",
    "Keyword & SERP Agent",
    "Competitor Watch Agent",
    "Trend Scout Agent",
    "Market Pulse Agent",
    "Judge Agent",
    "Brief Delivery Agent",
]


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{uuid5(NAMESPACE_URL, value).hex[:12]}"


def fixed_time() -> datetime:
    return datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)


def demo_source(tool: str, url: str | None = None) -> EvidenceSource:
    return EvidenceSource(tool=tool, url=url, title="Deterministic Session 1 demo fixture", captured_at=fixed_time())


def build_shop_profile(shop_url: str = DEFAULT_SHOP_URL) -> ShopProfile:
    shop_id = stable_id("shop", shop_url)
    source = demo_source("demo_fixture", shop_url)
    is_caitlyn = "caitlynminimalist" in shop_url.lower()
    if is_caitlyn:
        shop_name = "CaitlynMinimalist"
        category = "Jewelry / Personalized Gifts"
        summary = "Popular Etsy jewelry shop known for minimalist personalized necklaces, rings, bracelets, and gift-ready keepsakes."
        baseline = "High-volume personalized jewelry brand competing on minimalist style, gifting intent, and customization speed."
        seed_keywords = ["personalized necklace", "name necklace", "minimalist jewelry", "birth flower necklace"]
        competitors = ["GLDNxLayeredAndLong", "GracePersonalized"]
        listing_defs = [
            ("personalized-name-necklace", "Personalized Name Necklace", 32.0, ["personalized necklace", "name necklace", "minimalist jewelry"]),
            ("birth-flower-necklace", "Birth Flower Necklace", 38.0, ["birth flower necklace", "custom jewelry", "gift for her"]),
            ("dainty-initial-ring", "Dainty Initial Ring", 28.0, ["initial ring", "personalized jewelry", "minimalist ring"]),
        ]
    else:
        shop_name = "Demo Linen Studio"
        category = "Home & Living / Kitchen Textiles"
        summary = "Small-batch linen kitchen goods with giftable price points and neutral styling."
        baseline = "Premium handmade linen basics competing on natural materials and gift-ready presentation."
        seed_keywords = ["linen tea towel", "hostess gift", "neutral kitchen decor"]
        competitors = ["CottageLinenCo", "ModernHearthGoods"]
        listing_defs = [
            ("linen-tea-towel", "Washed Linen Tea Towel Set", 34.0, ["linen towel", "hostess gift", "kitchen decor"]),
            ("market-tote", "Natural Linen Market Tote", 46.0, ["linen tote", "farmers market", "eco gift"]),
        ]
    listings = [
        Listing(
            id=stable_id("listing", f"{shop_url}/{slug}"),
            shop_id=shop_id,
            title=title,
            url=f"{shop_url}/listing/{slug}",
            price=price,
            tags=tags,
            provenance=[source],
            confidence=0.92,
            timestamp=fixed_time(),
        )
        for slug, title, price, tags in listing_defs
    ]
    return ShopProfile(
        id=shop_id,
        shop_url=shop_url,
        shop_name=shop_name,
        category=category,
        summary=summary,
        listings=listings,
        seed_keywords=seed_keywords,
        likely_competitors=competitors,
        baseline_positioning=baseline,
        provenance=[source],
        confidence=0.91,
        timestamp=fixed_time(),
    )


def build_demo_run(shop: ShopProfile) -> tuple[AgentRun, list[ActivityEvent], list[DebugEvent], list[Brief]]:
    run_id = stable_id("run", f"{shop.id}:session-1-demo")
    source = demo_source("demo_fixture", shop.shop_url)

    keyword_signal = KeywordSignal(
        id=stable_id("keyword", f"{run_id}:hostess gift"),
        run_id=run_id,
        keyword="hostess gift",
        movement="Demo SERP visibility increased for giftable kitchen textiles.",
        opportunity="Bundle tea towels into a ready-to-gift set before seasonal entertaining demand rises.",
        visibility_score=0.78,
        severity="medium",
        provenance=[source],
        confidence=0.86,
        timestamp=fixed_time(),
    )
    competitor_signal = CompetitorSignal(
        id=stable_id("competitor", f"{run_id}:CottageLinenCo"),
        run_id=run_id,
        competitor_name="CottageLinenCo",
        competitor_url="https://www.etsy.com/shop/CottageLinenCo",
        signal="Competitor is positioning similar towels as bundled housewarming gifts.",
        price_delta_percent=-8.0,
        severity="medium",
        provenance=[source],
        confidence=0.82,
        timestamp=fixed_time(),
    )
    trend_signal = TrendSignal(
        id=stable_id("trend", f"{run_id}:quiet hosting"),
        run_id=run_id,
        platform="Reddit/TikTok demo aggregate",
        topic="quiet hosting",
        signal="Neutral, reusable kitchen textiles are appearing in hosting and housewarming conversations.",
        momentum_score=0.74,
        severity="medium",
        provenance=[source],
        confidence=0.8,
        timestamp=fixed_time(),
    )
    pulse_signal = MarketPulseSignal(
        id=stable_id("pulse", f"{run_id}:gift-bundle"),
        run_id=run_id,
        title="Gift-ready linen bundles are a near-term positioning opportunity",
        summary="Keyword, competitor, and trend stubs all point toward packaging existing linen towels as hostess or housewarming gifts.",
        severity="medium",
        novelty=0.68,
        confidence=0.84,
        source_signal_ids=[keyword_signal.id, competitor_signal.id, trend_signal.id],
        provenance=[source],
        timestamp=fixed_time(),
    )
    judge_score = JudgeScore(
        id=stable_id("judge", pulse_signal.id),
        run_id=run_id,
        market_pulse_signal_id=pulse_signal.id,
        actionability=0.88,
        urgency=0.66,
        confidence=0.84,
        novelty=0.68,
        business_impact=0.73,
        evidence_quality=0.8,
        total_score=0.77,
        decision="brief",
        rationale="The seller can test a bundle and listing copy change without new inventory.",
        timestamp=fixed_time(),
    )
    brief = Brief(
        id=stable_id("brief", judge_score.id),
        run_id=run_id,
        shop_id=shop.id,
        title="Test a personalized jewelry gift-positioning refresh",
        summary="Refresh personalized necklace and birth-flower listings around gift intent, customization confidence, and ready-to-gift presentation.",
        recommended_actions=[
            "Create a gift-ready listing variation using existing personalized jewelry inventory.",
            "Add accurate gift-intent terms such as personalized gift, name necklace, and gift for her.",
            "Use the first listing image to show personalization options and gift-ready packaging.",
        ],
        evidence=[keyword_signal.opportunity, competitor_signal.signal, trend_signal.signal],
        why_now="The cached signals align around personalized jewelry, gifting intent, and high-conversion customization language.",
        confidence=0.84,
        judge_score=judge_score,
        provenance=[source],
        timestamp=fixed_time(),
    )
    run = AgentRun(
        id=run_id,
        shop_id=shop.id,
        status="completed",
        started_at=fixed_time(),
        completed_at=fixed_time(),
        agents=AGENTS,
        keyword_signals=[keyword_signal],
        competitor_signals=[competitor_signal],
        trend_signals=[trend_signal],
        market_pulse_signals=[pulse_signal],
        judge_scores=[judge_score],
        brief_ids=[brief.id],
    )
    activity = [
        ActivityEvent(
            id=stable_id("activity", f"{run_id}:bootstrap"),
            run_id=run_id,
            agent="Shop Bootstrap Agent",
            event_type="shop_profile_ready",
            message="Loaded deterministic demo shop profile.",
            timestamp=fixed_time(),
        ),
        ActivityEvent(
            id=stable_id("activity", f"{run_id}:judge"),
            run_id=run_id,
            agent="Judge Agent",
            event_type="brief_approved",
            message="Approved one market pulse signal for seller-facing brief.",
            timestamp=fixed_time(),
        ),
    ]
    debug = [
        DebugEvent(
            id=stable_id("debug", f"{run_id}:brightdata"),
            run_id=run_id,
            provider="Bright Data",
            operation="demo_fixture_load",
            status="stubbed",
            request_summary="Loaded cached Bright Data-style records; no network call made.",
            response_summary="Returned one shop profile, three signals, and one brief.",
            timestamp=fixed_time(),
        ),
        DebugEvent(
            id=stable_id("debug", f"{run_id}:llm"),
            run_id=run_id,
            provider="NVIDIA NIM / OpenRouter",
            operation="judge_scoring_stub",
            status="stubbed",
            request_summary="No LLM request made in Session 1.",
            response_summary="Deterministic JudgeScore fixture returned.",
            timestamp=fixed_time(),
        ),
    ]
    return run, activity, debug, [brief]
