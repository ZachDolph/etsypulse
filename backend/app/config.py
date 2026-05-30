from functools import lru_cache
from os import getenv

from dotenv import load_dotenv


load_dotenv()


def _getenv(name: str, default: str | None = None) -> str | None:
    value = getenv(name, default)
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    lowered = stripped.lower()
    if lowered.startswith("your_") or lowered in {"placeholder", "replace_me", "changeme", "todo"}:
        return None
    return stripped


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


def _parse_bool(raw: str | None, default: bool) -> bool:
    if raw is None or raw == "":
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


class Settings:
    """Runtime settings sourced from environment variables or a local .env file."""

    def __init__(self) -> None:
        self.app_env = _getenv("APP_ENV", "development") or "development"
        self.log_level = _getenv("LOG_LEVEL", "INFO") or "INFO"
        self.demo_mode = _parse_bool(_getenv("DEMO_MODE"), True)
        self.cors_origins = _parse_cors_origins(_getenv("CORS_ORIGINS"))
        self.database_url = _getenv("DATABASE_URL") or "sqlite:///./data/etsypulse.db"
        self.brightdata_api_key = _getenv("BRIGHTDATA_API_KEY")
        self.brightdata_mcp_url = _getenv("BRIGHTDATA_MCP_URL")
        self.brightdata_unlocker_zone = _getenv("BRIGHTDATA_UNLOCKER_ZONE") or _getenv("BRIGHTDATA_ZONE")
        self.brightdata_timeout_seconds = _parse_float(_getenv("BRIGHTDATA_TIMEOUT_SECONDS"), 30.0)
        self.nvidia_nim_api_key = _getenv("NVIDIA_NIM_API_KEY")
        self.nvidia_nim_base_url = _getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1") or "https://integrate.api.nvidia.com/v1"
        self.nvidia_nim_model = _getenv("NVIDIA_NIM_MODEL")
        self.openrouter_api_key = _getenv("OPENROUTER_API_KEY")
        self.openrouter_base_url = _getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1") or "https://openrouter.ai/api/v1"
        self.openrouter_model_fallback = _getenv("OPENROUTER_MODEL_FALLBACK")
        self.llm_test_mode = _parse_bool(_getenv("LLM_TEST_MODE"), False)
        self.llm_timeout_seconds = _parse_float(_getenv("LLM_TIMEOUT_SECONDS"), 30.0)
        self.llm_rate_limit_per_minute = _parse_int(_getenv("LLM_RATE_LIMIT_PER_MINUTE"), 30)
        self.llm_json_retries = _parse_int(_getenv("LLM_JSON_RETRIES"), 2)

        self.scheduler_keyword_interval_minutes = _parse_int(_getenv("SCHEDULER_KEYWORD_INTERVAL_MINUTES"), 360)
        self.scheduler_competitor_interval_minutes = _parse_int(_getenv("SCHEDULER_COMPETITOR_INTERVAL_MINUTES"), 720)
        self.scheduler_trend_interval_minutes = _parse_int(_getenv("SCHEDULER_TREND_INTERVAL_MINUTES"), 180)
        self.scheduler_demo_enabled = _parse_bool(_getenv("SCHEDULER_DEMO_ENABLED"), True)
        self.rate_limit_enabled = _parse_bool(_getenv("RATE_LIMIT_ENABLED"), self.app_env == "production")
        self.rate_limit_public_per_minute = _parse_int(_getenv("RATE_LIMIT_PUBLIC_PER_MINUTE"), 120)
        self.rate_limit_shop_per_hour = _parse_int(_getenv("RATE_LIMIT_SHOP_PER_HOUR"), 12)
        self.judge_brief_threshold = _parse_float(_getenv("JUDGE_BRIEF_THRESHOLD"), 0.7)
        self.dedupe_window_minutes = _parse_int(_getenv("DEDUPE_WINDOW_MINUTES"), 60)

    @property
    def brightdata_live_ready(self) -> bool:
        return bool(self.brightdata_api_key and self.brightdata_unlocker_zone)

    @property
    def llm_live_ready(self) -> bool:
        nvidia_ready = bool(self.nvidia_nim_api_key and self.nvidia_nim_model)
        openrouter_ready = bool(self.openrouter_api_key and self.openrouter_model_fallback)
        return nvidia_ready or openrouter_ready

    @property
    def live_ready(self) -> bool:
        return self.brightdata_live_ready and self.llm_live_ready


def deployment_warnings(settings: Settings) -> list[str]:
    warnings: list[str] = []
    if settings.app_env == "production" and settings.database_url.startswith("sqlite"):
        warnings.append("Production deployments should use a hosted Postgres DATABASE_URL instead of SQLite.")
    if settings.app_env == "production" and not settings.cors_origins:
        warnings.append("CORS_ORIGINS should include the deployed Vercel frontend URL.")
    if not settings.demo_mode and not settings.brightdata_live_ready:
        warnings.append("Live mode requires BRIGHTDATA_API_KEY and BRIGHTDATA_UNLOCKER_ZONE.")
    if not settings.demo_mode and not settings.llm_live_ready:
        warnings.append("Live mode requires NVIDIA_NIM_* or OPENROUTER_* provider configuration.")
    return warnings


@lru_cache
def get_settings() -> Settings:
    return Settings()
