from functools import lru_cache
from os import getenv


def _parse_cors_origins(raw: str | None) -> list[str]:
    if not raw:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _parse_float(raw: str | None, default: float) -> float:
    if raw is None or raw == "":
        return default
    return float(raw)


def _parse_int(raw: str | None, default: int) -> int:
    if raw is None or raw == "":
        return default
    return int(raw)


class Settings:
    """Runtime settings sourced from environment variables only."""

    def __init__(self) -> None:
        self.demo_mode = getenv("DEMO_MODE", "true").lower() in {"1", "true", "yes", "on"}
        self.cors_origins = _parse_cors_origins(getenv("CORS_ORIGINS"))
        self.database_url = getenv("DATABASE_URL", "sqlite:///./data/etsypulse.db")
        self.brightdata_api_key = getenv("BRIGHTDATA_API_KEY")
        self.brightdata_mcp_url = getenv("BRIGHTDATA_MCP_URL")
        self.brightdata_unlocker_zone = getenv("BRIGHTDATA_UNLOCKER_ZONE") or getenv("BRIGHTDATA_ZONE")
        self.brightdata_timeout_seconds = _parse_float(getenv("BRIGHTDATA_TIMEOUT_SECONDS"), 30.0)
        self.nvidia_nim_api_key = getenv("NVIDIA_NIM_API_KEY")
        self.nvidia_nim_base_url = getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.nvidia_nim_model = getenv("NVIDIA_NIM_MODEL")
        self.openrouter_api_key = getenv("OPENROUTER_API_KEY")
        self.openrouter_base_url = getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.openrouter_model_fallback = getenv("OPENROUTER_MODEL_FALLBACK")
        self.llm_test_mode = getenv("LLM_TEST_MODE", "false").lower() in {"1", "true", "yes", "on"}
        self.llm_timeout_seconds = _parse_float(getenv("LLM_TIMEOUT_SECONDS"), 30.0)
        self.llm_rate_limit_per_minute = _parse_int(getenv("LLM_RATE_LIMIT_PER_MINUTE"), 30)
        self.llm_json_retries = _parse_int(getenv("LLM_JSON_RETRIES"), 2)

        self.scheduler_keyword_interval_minutes = _parse_int(getenv("SCHEDULER_KEYWORD_INTERVAL_MINUTES"), 360)
        self.scheduler_competitor_interval_minutes = _parse_int(getenv("SCHEDULER_COMPETITOR_INTERVAL_MINUTES"), 720)
        self.scheduler_trend_interval_minutes = _parse_int(getenv("SCHEDULER_TREND_INTERVAL_MINUTES"), 180)
        self.scheduler_demo_enabled = getenv("SCHEDULER_DEMO_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
        self.rate_limit_public_per_minute = _parse_int(getenv("RATE_LIMIT_PUBLIC_PER_MINUTE"), 120)
        self.rate_limit_shop_per_hour = _parse_int(getenv("RATE_LIMIT_SHOP_PER_HOUR"), 12)
        self.judge_brief_threshold = _parse_float(getenv("JUDGE_BRIEF_THRESHOLD"), 0.7)
        self.dedupe_window_minutes = _parse_int(getenv("DEDUPE_WINDOW_MINUTES"), 60)


@lru_cache
def get_settings() -> Settings:
    return Settings()
