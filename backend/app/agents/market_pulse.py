from app.agents.base import BaseAgent
from app.agents.contracts import MarketPulseInput, MarketPulseOutput
from app.agents.utils import source, stable_id
from app.schemas import MarketPulseSignal


class MarketPulseAgent(BaseAgent[MarketPulseInput, MarketPulseOutput]):
    name = "Market Pulse Agent"

    def run(self, agent_input: MarketPulseInput) -> MarketPulseOutput:
        all_signals = agent_input.keyword_signals + agent_input.competitor_signals + agent_input.trend_signals
        source_ids = [s.id for s in all_signals]

        # Derive context from actual upstream signals
        top_keyword = agent_input.keyword_signals[0].keyword if agent_input.keyword_signals else "personalized jewelry"
        top_competitor = agent_input.competitor_signals[0].competitor_name if agent_input.competitor_signals else "a key competitor"
        top_trend = max(agent_input.trend_signals, key=lambda s: s.momentum_score) if agent_input.trend_signals else None
        platform = top_trend.platform if top_trend else "TikTok"

        # Aggregate confidence and derive severity
        all_confidences = [s.confidence for s in all_signals]
        avg_confidence = round(sum(all_confidences) / len(all_confidences), 2) if all_confidences else 0.82
        has_high = any(s.severity == "high" for s in all_signals)
        severity = "high" if has_high else "medium"

        slug = top_keyword.lower().replace(" ", "-")[:40]
        signals = [
            MarketPulseSignal(
                id=stable_id("pulse", f"{agent_input.run_id}:{slug}-gift-positioning"),
                run_id=agent_input.run_id,
                title=f"'{top_keyword}' gift-intent signals converging — act before the window closes",
                summary=(
                    f"Three independent data sources align on the same window: "
                    f"'{top_keyword}' ranks high in buyer-intent SERP results, {top_competitor} is actively repricing and repositioning gift-ready listings, "
                    f"and {platform} shows gift-first creative outperforming generic product content. "
                    f"Signal confidence averages {round(avg_confidence * 100):.0f}% across {len(all_signals)} inputs. "
                    "Copy, tag, and hero photo updates require no inventory changes and can be live within the hour."
                ),
                severity=severity,
                novelty=0.72,
                confidence=avg_confidence,
                source_signal_ids=source_ids,
                provenance=[source("Market Pulse Agent")],
                originating_agent=self.name,
            )
        ]
        return MarketPulseOutput(market_pulse_signals=signals)
