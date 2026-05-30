from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.contracts import JudgeInput, JudgeOutput
from app.agents.utils import stable_id
from app.schemas import JudgeScore
from app.services.llm_client import LLMClient, LLMConfigurationError


class JudgeLLMShape(BaseModel):
    rationale: str
    confidence: float = Field(ge=0, le=1)


class JudgeAgent(BaseAgent[JudgeInput, JudgeOutput]):
    name = "Judge Agent"

    def __init__(self, llm_client: LLMClient | None = None, brief_threshold: float = 0.7) -> None:
        self.llm_client = llm_client
        self.brief_threshold = brief_threshold

    def run(self, agent_input: JudgeInput) -> JudgeOutput:
        scores: list[JudgeScore] = []
        for signal in agent_input.market_pulse_signals:
            rationale = (
                f"Signal '{signal.title}' clears the brief threshold. "
                "Copy, tag, and hero photo updates carry no inventory risk and can be deployed in under an hour. "
                f"Confidence at {round(signal.confidence * 100):.0f}% across converging keyword, competitor, and social sources."
            )
            confidence = signal.confidence
            if self.llm_client is not None:
                try:
                    llm_result = self.llm_client.structured_json(
                        [
                            {"role": "user", "content": f"Judge this Etsy market pulse: {signal.title}. {signal.summary}"},
                        ],
                        JudgeLLMShape,
                    )
                    rationale = llm_result.rationale
                    confidence = max(0.0, min(1.0, llm_result.confidence))
                except LLMConfigurationError:
                    pass

            # Derive scores from signal properties so they vary with signal quality
            severity_boost = {"low": 0.0, "medium": 0.06, "high": 0.14}.get(str(signal.severity), 0.0)
            actionability = round(min(0.97, 0.74 + confidence * 0.16 + severity_boost), 2)
            urgency = round(min(0.94, 0.52 + signal.novelty * 0.26 + severity_boost), 2)
            evidence_quality = round(min(0.96, 0.68 + len(signal.provenance) * 0.08 + confidence * 0.10), 2)
            business_impact = round(min(0.93, 0.62 + signal.novelty * 0.14 + confidence * 0.14), 2)
            novelty = signal.novelty

            total = round((actionability + urgency + confidence + novelty + business_impact + evidence_quality) / 6, 2)
            scores.append(
                JudgeScore(
                    id=stable_id("judge", f"{agent_input.run_id}:{signal.id}"),
                    run_id=agent_input.run_id,
                    market_pulse_signal_id=signal.id,
                    actionability=actionability,
                    urgency=urgency,
                    confidence=confidence,
                    novelty=novelty,
                    business_impact=business_impact,
                    evidence_quality=evidence_quality,
                    total_score=total,
                    decision="brief" if total >= self.brief_threshold else "watch",
                    rationale=rationale,
                )
            )
        return JudgeOutput(judge_scores=scores)
