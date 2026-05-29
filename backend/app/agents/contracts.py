from pydantic import BaseModel, Field

from app.schemas import (
    AgentRun,
    Brief,
    CompetitorSignal,
    JudgeScore,
    KeywordSignal,
    MarketPulseSignal,
    ShopProfile,
    TrendSignal,
)


class ShopBootstrapInput(BaseModel):
    shop_url: str


class ShopBootstrapOutput(BaseModel):
    shop_profile: ShopProfile


class KeywordSerpInput(BaseModel):
    run_id: str
    shop_profile: ShopProfile


class KeywordSerpOutput(BaseModel):
    keyword_signals: list[KeywordSignal]


class CompetitorWatchInput(BaseModel):
    run_id: str
    shop_profile: ShopProfile


class CompetitorWatchOutput(BaseModel):
    competitor_signals: list[CompetitorSignal]


class TrendScoutInput(BaseModel):
    run_id: str
    shop_profile: ShopProfile


class TrendScoutOutput(BaseModel):
    trend_signals: list[TrendSignal]


class MarketPulseInput(BaseModel):
    run_id: str
    keyword_signals: list[KeywordSignal] = Field(default_factory=list)
    competitor_signals: list[CompetitorSignal] = Field(default_factory=list)
    trend_signals: list[TrendSignal] = Field(default_factory=list)


class MarketPulseOutput(BaseModel):
    market_pulse_signals: list[MarketPulseSignal]


class JudgeInput(BaseModel):
    run_id: str
    market_pulse_signals: list[MarketPulseSignal]


class JudgeOutput(BaseModel):
    judge_scores: list[JudgeScore]


class BriefDeliveryInput(BaseModel):
    run_id: str
    shop_profile: ShopProfile
    market_pulse_signals: list[MarketPulseSignal]
    judge_scores: list[JudgeScore]


class BriefDeliveryOutput(BaseModel):
    briefs: list[Brief]


class PipelineRunInput(BaseModel):
    shop_url: str


class PipelineRunOutput(BaseModel):
    run: AgentRun
    shop_profile: ShopProfile
    briefs: list[Brief]
