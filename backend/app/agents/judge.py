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

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client

    def run(self, agent_input: JudgeInput) -> JudgeOutput:
        scores: list[JudgeScore] = []
        for signal in agent_input.market_pulse_signals:
            rationale = "The seller can test this with listing copy, tags, and bundling before changing inventory."
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
            actionability = 0.88
            urgency = 0.66
            novelty = signal.novelty
            business_impact = 0.74
            evidence_quality = 0.81
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
                    decision="brief" if total >= 0.7 else "watch",
                    rationale=rationale,
                )
            )
        return JudgeOutput(judge_scores=scores)
