from app.agents.base import BaseAgent
from app.agents.contracts import BriefDeliveryInput, BriefDeliveryOutput
from app.agents.utils import source, stable_id
from app.schemas import Brief


class BriefDeliveryAgent(BaseAgent[BriefDeliveryInput, BriefDeliveryOutput]):
    name = "Brief Delivery Agent"

    def run(self, agent_input: BriefDeliveryInput) -> BriefDeliveryOutput:
        pulse_by_id = {signal.id: signal for signal in agent_input.market_pulse_signals}
        top_keywords = agent_input.shop_profile.seed_keywords[:2]
        kw_phrase = " and ".join(f"'{k}'" for k in top_keywords) if top_keywords else "'personalized jewelry'"
        shop_name = agent_input.shop_profile.shop_name
        briefs: list[Brief] = []
        for score in agent_input.judge_scores:
            if score.decision != "brief":
                continue
            pulse = pulse_by_id[score.market_pulse_signal_id]
            # Derive a concise brief title from the pulse title
            pulse_topic = pulse.title.split("'")[1] if "'" in pulse.title else top_keywords[0] if top_keywords else "gift positioning"
            briefs.append(
                Brief(
                    id=stable_id("brief", f"{agent_input.run_id}:{score.id}"),
                    run_id=agent_input.run_id,
                    shop_id=agent_input.shop_profile.id,
                    title=f"Refresh {shop_name} gift positioning on {kw_phrase} — act this week",
                    summary=pulse.summary,
                    recommended_actions=[
                        f"Update your top 3 listing titles to lead with gift-occasion language ({kw_phrase}) and seasonal intent phrases (birthday, anniversary, graduation).",
                        f"Refresh hero listing photos with gift-ready styling: unboxing, packaging, and handwritten-note visuals outperform plain product shots in current trend data.",
                        f"Create a curated gift guide collection or bundle from your best-selling personalized listings to capture gift-comparison shoppers.",
                    ],
                    evidence=[pulse.title, score.rationale],
                    why_now=(
                        f"Judge confidence at {round(score.confidence * 100):.0f}%: "
                        f"'{pulse_topic}' keyword momentum, competitor repositioning, and social-trend data all converge this week. "
                        "These are copy, tag, and photo changes only — no inventory risk, and they can go live in under an hour."
                    ),
                    confidence=score.confidence,
                    judge_score=score,
                    provenance=[source(self.name)],
                )
            )
        return BriefDeliveryOutput(briefs=briefs)
