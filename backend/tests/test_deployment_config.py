from app.config import deployment_warnings, get_settings
from app.database import normalize_database_url


def test_demo_deployment_env_has_no_required_live_warnings(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("APP_ENV", "development")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.demo_mode is True
    assert deployment_warnings(settings) == []


def test_live_deployment_env_requires_provider_configuration(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.delenv("BRIGHTDATA_API_KEY", raising=False)
    monkeypatch.delenv("BRIGHTDATA_UNLOCKER_ZONE", raising=False)
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_NIM_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL_FALLBACK", raising=False)
    get_settings.cache_clear()

    warnings = deployment_warnings(get_settings())

    assert any("BRIGHTDATA" in warning for warning in warnings)
    assert any("NVIDIA_NIM" in warning or "OPENROUTER" in warning for warning in warnings)


def test_render_postgres_urls_use_psycopg_driver() -> None:
    assert normalize_database_url("postgres://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db" # pragma: allowlist secret
    assert normalize_database_url("postgresql://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db" # pragma: allowlist secret
    assert normalize_database_url("sqlite:///./data/etsypulse.db") == "sqlite:///./data/etsypulse.db" # pragma: allowlist secret


def test_rate_limiting_defaults_to_local_off_and_production_on(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)
    get_settings.cache_clear()
    assert get_settings().rate_limit_enabled is False

    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()
    assert get_settings().rate_limit_enabled is True

    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()
    assert get_settings().rate_limit_enabled is False
