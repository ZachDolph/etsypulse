# EtsyPulse Submission Package

## Project Title

**EtsyPulse: Autonomous Market Briefs for Etsy Sellers**

## Short Description

EtsyPulse turns live Etsy, search, competitor, and social signals into Judge-scored seller briefs, so Etsy shops see only the market moves worth acting on.

## Long Description

Etsy sellers operate in a market that changes faster than most small teams can research. Search intent shifts, competitors change positioning, social trends spike, and new buyer language appears across the web. Most sellers either ignore those signals or spend hours manually checking Etsy search, competitor shops, Reddit, TikTok, Instagram, and Google Shopping.

EtsyPulse is an autonomous market-intelligence dashboard for Etsy sellers. A seller enters an Etsy shop URL once. A typed multi-agent pipeline bootstraps the shop profile, monitors keywords and SERP patterns, watches competitor positioning, scouts social and shopping trends, normalizes those signals into market-pulse events, and then uses a Judge Agent to score actionability, urgency, novelty, confidence, evidence quality, and business impact. Only signals that pass the Judge threshold become seller-facing briefs.

The hackathon demo runs safely in deterministic demo mode with cached real Bright Data-style fixtures flowing through the implemented EtsyPulse orchestration path, while the backend also includes a live Bright Data Web Unlocker markdown path and live LLM JudgeAgent smoke path when credentials are configured. The React dashboard makes the product story clear: set the shop once, let agents monitor the market, and receive only actionable briefs with evidence and redacted provider debug traces.

## Recommended Tags

### Technology Tags

- Bright Data
- Web Unlocker
- Web Scraper API
- SERP API
- AI Agents
- Multi-Agent Systems
- FastAPI
- React
- Vite
- SQLite
- PostgreSQL
- Docker
- Vercel
- Render
- NVIDIA NIM
- OpenRouter
- OpenClaw

### Category Tags

- GTM Intelligence
- Market Intelligence
- E-commerce
- Seller Tools
- Competitive Intelligence
- Social Listening
- Small Business Automation
- Agentic Workflow
- Web Data
- B2B SaaS

## Hackathon Track Fit

Primary track: **GTM Intelligence**.

EtsyPulse directly matches the hackathon's GTM Intelligence examples: autonomous competitor monitoring, market research tools that synthesize live web signals into actionable briefs, social listening, and AI agents that use live web context to act on behalf of revenue teams. The product is scoped to Etsy sellers first, but the architecture generalizes to other marketplaces and merchant categories.

## TAM Analysis

EtsyPulse's initial wedge is Etsy seller intelligence. Etsy reported **5.6 million Etsy marketplace active sellers as of December 31, 2025** and **$876.3 million in 2025 services revenue**, showing that sellers already pay for optional growth and operating tools.

A conservative bottom-up TAM for Etsy-only seller intelligence:

- 5.6 million active Etsy sellers.
- Assumed average SaaS price: $19 per month for solo shops.
- Annualized TAM: 5.6M × $19 × 12 = **approximately $1.28B ARR**.

A more mature pricing model with power-seller and agency tiers could expand ARPA above $19/month. The broader marketplace-seller TAM becomes larger when EtsyPulse expands to Shopify, Amazon Handmade, eBay, Faire, Depop, and creator-commerce storefronts.

## SAM Analysis

The serviceable available market is smaller than all active sellers because not every shop is commercially active enough to pay for intelligence software. A practical first SAM is professional and growth-oriented Etsy sellers who already spend time or money on ads, SEO, competitive research, or listing optimization.

Conservative SAM model:

- 15% to 25% of Etsy marketplace active sellers are serious enough to pay for a recurring intelligence tool.
- 840,000 to 1.4 million reachable sellers.
- At $19/month, this implies **approximately $191M to $319M ARR** in Etsy-only SAM.

A second SAM proxy is Etsy's own seller-services revenue. Etsy's 2025 services revenue of **$876.3M** indicates meaningful seller willingness to pay for tools that improve visibility, fulfillment, ads, or operations. EtsyPulse positions itself as an external intelligence layer that helps sellers decide what to change before they spend more on ads or inventory.

## Revenue Opportunities

- **Solo seller subscription:** $19-$29/month for one shop, daily/weekly monitoring, and Judge-approved briefs.
- **Power seller tier:** $49-$99/month for multiple shops, more frequent monitoring, competitor tracking, and live provider mode.
- **Agency tier:** $199+/month for Etsy consultants, POD agencies, and marketplace growth teams managing many shops.
- **Action packs:** paid brief templates for listing refreshes, holiday campaigns, SEO tests, and competitor response plans.
- **Data/API access:** structured market-pulse feeds for larger seller tooling companies or ecommerce analytics platforms.
- **Affiliate/partner revenue:** integrations with listing optimization, print-on-demand, email, and ad-management tools.

## Competitive Landscape

### Etsy-Native SEO And Research Tools

- **eRank, Marmalead, Sale Samurai, Alura, EverBee:** strong keyword, listing, and competitor research tools for Etsy sellers.
- Weakness: mostly dashboard/research oriented; sellers still need to interpret signals and decide what to do.
- EtsyPulse difference: autonomous monitoring plus JudgeAgent filtering. The seller gets a brief, not another research tab.

### Marketplace And Ecommerce Intelligence Tools

- **Jungle Scout, Helium 10, SmartScout, DataHawk:** mature analytics for Amazon and larger marketplace operators.
- Weakness: less focused on Etsy's handmade/vintage/creative-commerce niche and cross-source social trend context.
- EtsyPulse difference: seller-friendly Etsy workflow with social, SERP, competitor, and Google Shopping signals normalized into one action object.

### Social Listening And BI Platforms

- **Brandwatch, Sprout Social, Similarweb, Semrush:** strong data platforms for brands and agencies.
- Weakness: too broad, expensive, and analyst-heavy for solo Etsy sellers.
- EtsyPulse difference: small-business agent workflow that turns public web data into specific listing and offer actions.

### Etsy Built-In Seller Tools

- Etsy provides stats, ads, search tooling, and marketplace guidance.
- Weakness: sellers still lack independent competitor/social/search context and cross-web evidence.
- EtsyPulse difference: external market radar using Bright Data-powered web access and transparent debug traces.

## Unique Selling Proposition

**EtsyPulse is the always-on market analyst for Etsy sellers: it monitors live web signals across Etsy, search, competitors, and social commerce, then uses a Judge Agent to deliver only actionable briefs backed by evidence.**

The core differentiation is not just collecting data. It is the full loop: live web data → typed agent signals → normalized market pulse → Judge scoring → seller-ready brief → transparent debug evidence.

## Future Roadmap

### Near Term

- Deploy public Vercel frontend and Render backend with `DEMO_MODE=true` for judging.
- Add live Bright Data adapters for Etsy products, SERP, TikTok, Reddit, Instagram, and Google Shopping beyond the current Web Unlocker markdown path.
- Add persistent frontend tests and a repeatable Playwright demo recording script.
- Add a seller notification channel: email, Slack, Discord, or OpenClaw channel bridge.

### Product Expansion

- Seller-controlled monitoring cadence and competitor lists.
- Brief feedback loop: seller can mark actions useful/not useful to tune Judge thresholds.
- Holiday and seasonal opportunity packs for Etsy categories.
- Multi-shop dashboards for agencies and consultants.
- Historical trend and experiment tracking tied to listing changes.

### Platform Expansion

- Shopify, Amazon Handmade, eBay, Faire, Depop, and niche marketplace support.
- Durable scheduler and rate limiting with Redis or managed queues.
- OpenClaw runtime execution for portable local multi-agent coordination.
- CRM/ad-tool integrations for agencies and larger marketplace teams.

## Bright Data Requirement Proof

The project demonstrably uses Bright Data in both product design and code:

- Backend integration boundary: `backend/app/services/brightdata_client.py`.
- Bright Data tool abstractions: `web_data_etsy_products`, `search_engine`, `scrape_as_markdown`, `discover`, `web_data_tiktok_posts`, `web_data_reddit_posts`, `web_data_instagram_reels`, and `web_data_google_shopping`.
- Live Bright Data path: `BrightDataClient.scrape_markdown()` calls Bright Data Web Unlocker through `POST https://api.brightdata.com/request` with `format=raw` and `data_format=markdown` when `DEMO_MODE=false` and credentials are configured.
- Demo cache: `backend/app/demo_data/brightdata_samples/` contains deterministic Bright Data-style fixtures so judges can run the app without credentials.
- Fixture validator: `backend/scripts/validate_brightdata_fixtures.py`.
- Agent usage: `ShopBootstrapAgent`, `KeywordSerpAgent`, `CompetitorWatchAgent`, and `TrendScoutAgent` call the Bright Data client abstraction.
- Dashboard proof: the Debug panel shows Bright Data events, tool names, cache/live mode, latency, response summaries, and redacted request shapes.
- Admin proof: `GET /admin/debug/status` reports Bright Data configured/not configured status without secrets; `POST /admin/live-smoke` runs one controlled Bright Data live path when configured.
- Tests: `backend/tests/test_brightdata_client.py` verifies demo fixtures, no-network demo behavior, live Web Unlocker request shape, redaction, and error handling.

## Judge Criteria Mapping

### Application of Technology

EtsyPulse uses Bright Data as the web-data boundary, a typed FastAPI backend, deterministic demo fixtures, a live Web Unlocker path, a multi-agent pipeline, NVIDIA NIM/OpenRouter-compatible LLM provider layer, Docker deployment, and a React dashboard. The implementation is production-shaped while remaining judge-safe in demo mode.

### Presentation

The dashboard tells the story in under 30 seconds: enter a shop, run the demo, watch agents produce activity, inspect market signals, and read Judge-approved briefs. The submission package includes a cover image, video script, slide outline, architecture story, Bright Data proof, and business analysis.

### Business Value

EtsyPulse targets millions of marketplace sellers who need better market awareness but lack analyst time. The product reduces manual research, helps sellers react to competitor/search/social shifts, and creates a clear subscription SaaS path for solo sellers, power sellers, and agencies.

### Originality

Most seller tools provide dashboards, keyword tables, or listing audits. EtsyPulse reframes the product as autonomous market monitoring plus a Judge Agent that filters noise into action. The combination of live web data, multi-source evidence, and brief-only delivery is the unique product behavior.

## Source Notes

- Hackathon page: https://lablab.ai/ai-hackathons/brightdata-ai-agents-web-data-hackathon
- Submission guide: [LabLabAI Hackathon Submission Guidelines](https://lablab.ai/ai-hackathons/brightdata-ai-agents-web-data-hackathon)
- Etsy FY2025 results and seller/services metrics: https://investors.etsy.com/news-events/press-releases/detail/218/etsy-inc-reports-fourth-quarter-and-full-year-2025-results
- Etsy FY2025 Form 10-K reference: https://www.sec.gov/Archives/edgar/data/0001370637/000137063726000019/etsy-20251231.htm
