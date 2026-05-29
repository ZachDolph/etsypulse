from pydantic import ValidationError
import pytest

from app.demo_data import build_demo_run, build_shop_profile
from app.schemas import JudgeScore, ShopProfile


def test_demo_shop_profile_schema_round_trip() -> None:
    profile = build_shop_profile("https://www.etsy.com/shop/example")
    encoded = profile.model_dump(mode="json")
    decoded = ShopProfile.model_validate(encoded)

    assert decoded.id == profile.id
    assert decoded.listings[0].confidence == pytest.approx(0.92)
    assert decoded.provenance[0].tool == "demo_fixture"


def test_judge_score_bounds_are_validated() -> None:
    with pytest.raises(ValidationError):
        JudgeScore(
            id="judge_bad",
            run_id="run_bad",
            market_pulse_signal_id="pulse_bad",
            actionability=1.2,
            urgency=0.5,
            confidence=0.5,
            novelty=0.5,
            business_impact=0.5,
            evidence_quality=0.5,
            total_score=0.5,
            decision="brief",
            rationale="Invalid actionability should fail.",
        )


def test_demo_run_contains_required_agent_outputs() -> None:
    profile = build_shop_profile()
    run, activity, debug, briefs = build_demo_run(profile)

    assert run.status == "completed"
    assert run.keyword_signals
    assert run.competitor_signals
    assert run.trend_signals
    assert run.market_pulse_signals
    assert run.judge_scores[0].decision == "brief"
    assert briefs[0].judge_score.id == run.judge_scores[0].id
    assert activity
    assert all(event.redacted for event in debug)
