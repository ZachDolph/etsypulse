from app.agents.base import BaseAgent
from app.agents.contracts import MarketPulseInput, MarketPulseOutput
from app.agents.utils import source, stable_id
from app.schemas import MarketPulseSignal


class MarketPulseAgent(BaseAgent[MarketPulseInput, MarketPulseOutput]):
    name = "Market Pulse Agent"

    def run(self, agent_input: MarketPulseInput) -> MarketPulseOutput:
        source_ids = [signal.id for signal in agent_input.keyword_signals + agent_input.competitor_signals + agent_input.trend_signals]
        signals = [
            MarketPulseSignal(
                id=stable_id("pulse", f"{agent_input.run_id}:personalized-jewelry-gift-refresh"),
                run_id=agent_input.run_id,
                title="Personalized jewelry gift intent is a near-term opportunity",
                summary="Keyword, competitor, and trend signals align around positioning personalized jewelry listings as high-confidence gifts.",
                severity="medium",
                novelty=0.7,
                confidence=0.84,
                source_signal_ids=source_ids,
                provenance=[source("Market Pulse Agent")],
                originating_agent=self.name,
            )
        ]
        return MarketPulseOutput(market_pulse_signals=signals)
