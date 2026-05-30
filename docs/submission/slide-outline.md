# EtsyPulse Slide Outline

Recommended length: 8-10 slides. Keep each slide to 2-3 concise sentences.

## Slide 1 — Title

**EtsyPulse: Autonomous Market Briefs for Etsy Sellers**

Subtitle: Set shop once. Agents monitor. Only actionable briefs appear.

Visual: cover image.

## Slide 2 — Problem

Etsy sellers compete in a market that changes across Etsy search, competitor listings, Google, Reddit, TikTok, Instagram, and shopping results. Most sellers do not have the time or tooling to monitor those signals continuously.

## Slide 3 — Solution

EtsyPulse is an always-on market analyst for Etsy sellers. A multi-agent pipeline transforms live web signals into Judge-scored briefs with recommended actions and evidence.

## Slide 4 — Product Demo Flow

A seller enters an Etsy shop URL once. The dashboard shows shop profile, agent activity, market signals, provider debug evidence, Judge scores, and actionable briefs.

## Slide 5 — Architecture

React/Vite dashboard -> FastAPI API -> scheduler/rate limiter -> typed agent pipeline -> Bright Data + LLM provider abstractions -> SQLite/Postgres persistence. Demo mode is credential-free; live mode is available when providers are configured.

## Slide 6 — Bright Data Integration

Bright Data powers the web-data boundary. EtsyPulse includes abstractions for Etsy products, SERP, markdown scraping, batch scraping, discovery, TikTok, Reddit, Instagram Reels, and Google Shopping, plus a live Web Unlocker markdown path.

## Slide 7 — Judge Agent

The Judge Agent scores actionability, urgency, confidence, novelty, business impact, and evidence quality. Only signals above threshold become seller-facing briefs, reducing noise and making the system useful for busy sellers.

## Slide 8 — Market And Business

Etsy reported 5.6 million Etsy marketplace active sellers as of December 31, 2025. At $19/month across active Etsy sellers, the Etsy-only bottom-up TAM is approximately $1.28B ARR; the first SAM is serious sellers and agencies already spending on growth tools.

## Slide 9 — Competitive Advantage

Existing Etsy tools focus on keyword tables, listing audits, or manual research. EtsyPulse combines multi-source live web data, autonomous monitoring, Judge scoring, and brief-only delivery.

## Slide 10 — Roadmap And Ask

Next steps: deploy the hosted demo, expand live Bright Data adapters, add notifications, add seller feedback loops, and support more marketplaces. EtsyPulse can become the market-intelligence layer for small ecommerce sellers.
