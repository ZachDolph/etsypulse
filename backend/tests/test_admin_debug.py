import httpx
import pytest

from app.config import get_settings
from app.main import admin_debug_status, admin_live_smoke
from app.services.brightdata_client import BrightDataClient
from app.services.llm_client import LLMClient, LLMResult


@pytest.fixture(autouse=True)
def clear_settings(monkeypatch):
    for key in (
        "DEMO_MODE",
        "BRIGHTDATA_API_KEY",
        "BRIGHTDATA_UNLOCKER_ZONE",
        "NVIDIA_NIM_API_KEY",
        "NVIDIA_NIM_MODEL",
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL_FALLBACK",
    ):
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
    import app.main as main_module
    main_module.settings = get_settings()


def test_admin_debug_status_does_not_expose_secrets(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("BRIGHTDATA_API_KEY", "dummy-bd")
    monkeypatch.setenv("BRIGHTDATA_UNLOCKER_ZONE", "etsy-zone")
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "dummy-nim")
    monkeypatch.setenv("NVIDIA_NIM_MODEL", "nvidia/test")
    get_settings.cache_clear()

    import app.main as main_module
    main_module.settings = get_settings()
    status = admin_debug_status()

    assert status.demo_mode is False
    assert status.brightdata.configured is True
    assert status.nvidia_nim.configured is True
    dumped = status.model_dump_json()
    assert "dummy" not in dumped
    assert "api_key" not in dumped.lower()
    assert "token" not in dumped.lower()
    assert "credential" in dumped
    assert "configured" in dumped


def test_admin_live_smoke_uses_demo_without_credentials(monkeypatch) -> None:
    import app.main as main_module
    main_module.settings = get_settings()
    response = admin_live_smoke()

    assert response.status == "ok"
    assert response.debug_events
    assert {event.cache_mode for event in response.debug_events} == {"demo"}


def test_admin_live_smoke_can_use_mocked_live_providers(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("BRIGHTDATA_API_KEY", "bd-key")
    monkeypatch.setenv("BRIGHTDATA_UNLOCKER_ZONE", "zone")
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nim-key")
    monkeypatch.setenv("NVIDIA_NIM_MODEL", "nvidia/test")
    get_settings.cache_clear()

    import app.main as main_module
    main_module.settings = get_settings()

    monkeypatch.setattr(BrightDataClient, "_live_scrape_markdown", lambda self, url: "# live markdown")
    monkeypatch.setattr(
        LLMClient,
        "chat_completion",
        lambda self, messages, temperature=0.2, max_tokens=800, response_format=None: LLMResult(
            content='{"rationale":"live rationale","confidence":0.82}',
            provider="NVIDIA NIM",
            model="nvidia/test",
            token_counts={"total_tokens": 9},
        ),
    )

    response = admin_live_smoke()

    assert response.status == "ok"
    assert response.brightdata_summary == "Bright Data returned 15 markdown character(s)."
    assert "JudgeAgent produced 1 score" in (response.llm_summary or "")
