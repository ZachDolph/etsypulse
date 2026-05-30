# EtsyPulse Demo Video Script

Target length: 2-3 minutes.

## Goal

Show judges that EtsyPulse solves a real GTM intelligence problem with Bright Data-powered web data, autonomous agents, Judge scoring, and a clean dashboard that works in demo mode without credentials.

## Scene 1 — Opening Hook (0:00-0:20)

Narration:

"Etsy sellers are surrounded by market signals: competitor listings, search changes, social trends, Reddit conversations, and shopping results. The problem is that most sellers do not have time to monitor all of that every day. EtsyPulse turns those signals into actionable briefs. The seller enters their shop once, agents monitor the market, and only Judge-approved actions reach the dashboard."

Visuals:

- Show the cover image or dashboard hero.
- Highlight the line: "set shop once, agents monitor, only actionable briefs appear."

## Scene 2 — Shop Setup (0:20-0:45)

Narration:

"Here is the judge-safe demo flow. I can paste an Etsy shop URL, or click the demo shop button. Demo mode requires no credentials and uses cached Bright Data-style fixtures, so the app is reliable during judging."

Visuals:

- Open dashboard.
- Show demo mode banner.
- Click the demo shop button.
- Show shop profile and scheduler status loading into the page.

## Scene 3 — Agent Pipeline (0:45-1:20)

Narration:

"Behind the dashboard is a typed seven-agent pipeline. The Shop Bootstrap Agent extracts the seller profile, listings, seed keywords, and competitors. Keyword and SERP, Competitor Watch, and Trend Scout agents collect signals. Market Pulse normalizes those signals. Then the Judge Agent scores actionability, urgency, confidence, novelty, business impact, and evidence quality."

Visuals:

- Show activity feed.
- Scroll or focus on agent run states.
- Show market pulse panel with keyword, competitor, and trend sections.

## Scene 4 — Bright Data Proof (1:20-1:55)

Narration:

"Bright Data is the web data boundary. The backend has abstractions for Etsy products, SERP, markdown scraping, batch scraping, discovery, TikTok, Reddit, Instagram Reels, and Google Shopping. In demo mode these load deterministic fixtures. In live mode, the project includes a real Bright Data Web Unlocker path for markdown scraping. The debug panel makes that visible with tool names, cache or live mode, latency, response summaries, and redacted request shapes."

Visuals:

- Show Debug panel.
- Zoom on Bright Data provider events.
- Highlight cache/live mode, latency, redacted status, and tool names.
- Optionally show `/admin/debug/status` or provider status panel.

## Scene 5 — Judge-Approved Brief (1:55-2:30)

Narration:

"The key product decision is that EtsyPulse does not flood the seller with raw analytics. The Judge Agent is the gatekeeper. This brief recommends testing a personalized jewelry gift refresh this week, explains why now, shows supporting evidence, and breaks down the Judge score. The seller gets a concrete action, not another research dashboard."

Visuals:

- Show actionable brief card.
- Highlight recommended actions.
- Highlight Judge score breakdown.
- Show evidence and why-now text.

## Scene 6 — Business And Close (2:30-3:00)

Narration:

"EtsyPulse starts with Etsy sellers, a market with millions of active sellers and clear willingness to pay for growth tools. The same architecture can expand to other marketplaces, agencies, and ecommerce intelligence workflows. It is built for the hackathon as a portable demo, but the deployment path is production-shaped with FastAPI, React, Docker, Render, Vercel, and optional OpenClaw coordination. EtsyPulse gives small sellers an always-on market analyst powered by live web data."

Visuals:

- Show architecture summary or dashboard full view.
- End on cover image or brief card.

## Capture Checklist For Future Remotion/Playwright Session

- Start backend in demo mode.
- Start frontend and open dashboard.
- Capture 16:9 viewport, preferably 1920x1080.
- Use deterministic demo shop flow.
- Record these key UI states: hero, demo mode banner, shop setup, activity feed, market pulse panel, brief cards, debug panel, provider status.
- Do not expose `.env`, provider keys, terminal secrets, or admin credentials.
