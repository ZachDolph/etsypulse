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


def fixed_time(days_ago: int = 0) -> datetime:
    base = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    if days_ago:
        from datetime import timedelta
        return base - timedelta(days=days_ago)
    return base


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


def build_historical_brief_1(shop: ShopProfile) -> Brief:
    """'Occasion keywords' brief — 3 days ago."""
    run_id = stable_id("run", f"{shop.id}:session-hist-1")
    source = demo_source("demo_fixture", shop.shop_url)
    pulse = MarketPulseSignal(
        id=stable_id("pulse", f"{run_id}:occasion-keywords"),
        run_id=run_id,
        title="Add graduation and anniversary keywords before summer demand",
        summary="SERP data shows occasion-specific searches (graduation gift, anniversary jewelry) surging 3–4 weeks before holidays. Existing listings can capture this traffic with title and tag updates only.",
        severity="medium",
        novelty=0.64,
        confidence=0.81,
        source_signal_ids=[],
        provenance=[source],
        originating_agent="Market Pulse Agent",
        timestamp=fixed_time(days_ago=3),
    )
    score = JudgeScore(
        id=stable_id("judge", pulse.id),
        run_id=run_id,
        market_pulse_signal_id=pulse.id,
        actionability=0.84,
        urgency=0.79,
        confidence=0.81,
        novelty=0.64,
        business_impact=0.77,
        evidence_quality=0.80,
        total_score=0.78,
        decision="brief",
        rationale="Occasion keyword updates require no new inventory — add graduation, anniversary, and birthday phrases to top listing titles and tags before seasonal search volume peaks.",
        timestamp=fixed_time(days_ago=3),
    )
    return Brief(
        id=stable_id("brief", score.id),
        run_id=run_id,
        shop_id=shop.id,
        title="Add occasion keywords to top listings before summer gifting peaks",
        summary=pulse.summary,
        recommended_actions=[
            "Add 'graduation gift', 'anniversary jewelry', and 'birthday necklace' to your top 5 listing titles.",
            "Update listing tags to include occasion phrases — these have low competition but high buyer intent.",
            "Pin your gift-occasion listings to the top of your shop for the next 6 weeks.",
        ],
        evidence=[pulse.title, score.rationale],
        why_now="Occasion search volume ramps 3–4 weeks before peak gifting dates. Acting now captures early-funnel traffic before competitors optimize.",
        confidence=0.81,
        judge_score=score,
        provenance=[source],
        timestamp=fixed_time(days_ago=3),
    )


def build_historical_brief_2(shop: ShopProfile) -> Brief:
    """'Hero photo refresh' brief — 6 days ago."""
    run_id = stable_id("run", f"{shop.id}:session-hist-2")
    source = demo_source("demo_fixture", shop.shop_url)
    pulse = MarketPulseSignal(
        id=stable_id("pulse", f"{run_id}:hero-photo-refresh"),
        run_id=run_id,
        title="Gift-unboxing and packaging photos outperform plain product shots in current trend data",
        summary="Instagram Reels and TikTok data confirm that lifestyle and unboxing visuals for personalized jewelry are driving 2–3× more engagement than white-background product photos. Updating hero images across ring and necklace listings is a zero-inventory change.",
        severity="medium",
        novelty=0.71,
        confidence=0.79,
        source_signal_ids=[],
        provenance=[source],
        originating_agent="Market Pulse Agent",
        timestamp=fixed_time(days_ago=6),
    )
    score = JudgeScore(
        id=stable_id("judge", pulse.id),
        run_id=run_id,
        market_pulse_signal_id=pulse.id,
        actionability=0.82,
        urgency=0.68,
        confidence=0.79,
        novelty=0.71,
        business_impact=0.74,
        evidence_quality=0.83,
        total_score=0.76,
        decision="brief",
        rationale="Replacing hero photos with gift-ready and lifestyle images is a high-impact, zero-inventory change that directly aligns with current social trend signals.",
        timestamp=fixed_time(days_ago=6),
    )
    return Brief(
        id=stable_id("brief", score.id),
        run_id=run_id,
        shop_id=shop.id,
        title="Refresh hero photos to lead with gift-ready styling and unboxing",
        summary=pulse.summary,
        recommended_actions=[
            "Reshoot or source lifestyle photos showing your jewelry being unwrapped, gifted, or worn in a celebratory context.",
            "Make the first listing image show the product in gift-ready packaging — box, ribbon, and handwritten note.",
            "A/B test the new hero against the current product shot and track click-through rate changes over 2 weeks.",
        ],
        evidence=[pulse.title, score.rationale],
        why_now="Social trend data shows gift-framed visuals outperforming product shots right now. This is a photo swap, not an inventory change — implementable today.",
        confidence=0.79,
        judge_score=score,
        provenance=[source],
        timestamp=fixed_time(days_ago=6),
    )
