from app.agents.base import BaseAgent
from app.agents.contracts import BriefDeliveryInput, BriefDeliveryOutput
from app.agents.utils import source, stable_id
from app.schemas import Brief


class BriefDeliveryAgent(BaseAgent[BriefDeliveryInput, BriefDeliveryOutput]):
    name = "Brief Delivery Agent"

    def run(self, agent_input: BriefDeliveryInput) -> BriefDeliveryOutput:
        pulse_by_id = {signal.id: signal for signal in agent_input.market_pulse_signals}
        briefs: list[Brief] = []
        for score in agent_input.judge_scores:
            if score.decision != "brief":
                continue
            pulse = pulse_by_id[score.market_pulse_signal_id]
            briefs.append(
                Brief(
                    id=stable_id("brief", f"{agent_input.run_id}:{score.id}"),
                    run_id=agent_input.run_id,
                    shop_id=agent_input.shop_profile.id,
                    title="Test a gift-ready linen bundle this week",
                    summary=pulse.summary,
                    recommended_actions=[
                        "Create a two-pack or three-pack variation from existing towel inventory.",
                        "Add accurate gift-intent keywords to title, tags, and first paragraph.",
                        "Update the hero photo to show simple gift-ready presentation.",
                    ],
                    evidence=[pulse.title, score.rationale],
                    why_now="Signals align across search, competitor positioning, and social trend fixtures, and the action requires no new inventory.",
                    confidence=score.confidence,
                    judge_score=score,
                    provenance=[source(self.name)],
                )
            )
        return BriefDeliveryOutput(briefs=briefs)
