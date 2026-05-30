import json
import socket

import httpx
import pytest
from pydantic import BaseModel

from app.config import get_settings
from app.services.llm_client import LLMClient, LLMConfigurationError, LLMResult


class DemoDecision(BaseModel):
    decision: str
    confidence: float


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch):
    for key in (
        "LLM_TEST_MODE",
        "NVIDIA_NIM_API_KEY",
        "NVIDIA_NIM_BASE_URL",
        "NVIDIA_NIM_MODEL",
        "OPENROUTER_API_KEY",
        "OPENROUTER_BASE_URL",
        "OPENROUTER_MODEL_FALLBACK",
        "LLM_TIMEOUT_SECONDS",
        "LLM_RATE_LIMIT_PER_MINUTE",
        "LLM_JSON_RETRIES",
    ):
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_fake_provider_makes_no_network_calls(monkeypatch) -> None:
    monkeypatch.setenv("LLM_TEST_MODE", "true")
    get_settings.cache_clear()

    def fail_network(*args, **kwargs):
        raise AssertionError("network access is forbidden in LLM_TEST_MODE")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    monkeypatch.setattr(httpx, "post", fail_network)

    client = LLMClient()
    result = client.chat_completion([{"role": "user", "content": "Say hi"}])

    assert result.provider == "Fake LLM"
    assert result.content.startswith("Fake LLM response")
    assert client.debug_events[0].status == "stubbed"
    assert client.debug_events[0].token_counts["total_tokens"] == 20
    assert client.debug_events[0].request_shape["api_key"] is None


def test_structured_json_validates_schema_with_fake_provider(monkeypatch) -> None:
    monkeypatch.setenv("LLM_TEST_MODE", "true")
    get_settings.cache_clear()

    client = LLMClient()
    parsed = client.structured_json(
        [{"role": "user", "content": "Return a decision and confidence"}],
        DemoDecision,
    )

    assert parsed.decision == "fake_decision"
    assert parsed.confidence == pytest.approx(0.75)


def test_structured_json_retries_after_invalid_json(monkeypatch) -> None:
    monkeypatch.setenv("LLM_TEST_MODE", "true")
    monkeypatch.setenv("LLM_JSON_RETRIES", "1")
    get_settings.cache_clear()

    client = LLMClient()
    calls = {"count": 0}

    def fake_chat_completion(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return LLMResult(content="not json", provider="Fake LLM", model="fake-json-model")
        return LLMResult(
            content=json.dumps({"decision": "brief", "confidence": 0.9}),
            provider="Fake LLM",
            model="fake-json-model",
        )

    monkeypatch.setattr(client, "chat_completion", fake_chat_completion)
    parsed = client.structured_json([{"role": "user", "content": "score"}], DemoDecision)

    assert parsed.decision == "brief"
    assert calls["count"] == 2
    assert any(event.operation == "structured_json_validation" for event in client.debug_events)


def test_provider_order_uses_openrouter_fallback(monkeypatch) -> None:
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nim-key")
    monkeypatch.setenv("NVIDIA_NIM_MODEL", "nvidia/test-model")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("OPENROUTER_MODEL_FALLBACK", "meta-llama/llama-3.1-8b-instruct:free")
    monkeypatch.setenv("LLM_RATE_LIMIT_PER_MINUTE", "100000")
    get_settings.cache_clear()

    request = httpx.Request("POST", "https://example.test")
    calls = {"count": 0}

    def fake_post(url, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            response = httpx.Response(503, request=request, json={"error": "nim unavailable"})
            raise httpx.HTTPStatusError("service unavailable", request=request, response=response)
        assert url == "https://openrouter.ai/api/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer or-key"
        return httpx.Response(
            200,
            request=request,
            json={
                "choices": [{"message": {"role": "assistant", "content": "fallback ok"}, "finish_reason": "stop"}],
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    client = LLMClient()
    result = client.chat_completion([{"role": "user", "content": "hello"}])

    assert result.provider == "OpenRouter"
    assert result.fallback_used is True
    assert result.content == "fallback ok"
    assert calls["count"] == 2
    assert client.debug_events[0].provider == "NVIDIA NIM"
    assert client.debug_events[0].status == "error"
    assert client.debug_events[0].error_class == "LLMProviderError"
    assert client.debug_events[1].provider == "OpenRouter"
    assert client.debug_events[1].fallback_used is True
    assert client.debug_events[1].token_counts["total_tokens"] == 5
    assert client.debug_events[1].request_shape["api_key"] == "[REDACTED]"


def test_missing_provider_config_fails_fast() -> None:
    with pytest.raises(LLMConfigurationError):
        LLMClient()

from app.services.llm_client import LLMProviderError, LLMRateLimitError, LLMTimeoutError, LLMMalformedResponseError


def test_llm_live_errors_are_classified(monkeypatch) -> None:
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nim-key")
    monkeypatch.setenv("NVIDIA_NIM_MODEL", "nvidia/test-model")
    monkeypatch.setenv("LLM_RATE_LIMIT_PER_MINUTE", "100000")
    get_settings.cache_clear()

    def timeout_post(*args, **kwargs):
        raise httpx.TimeoutException("too slow")

    monkeypatch.setattr(httpx, "post", timeout_post)
    client = LLMClient()
    with pytest.raises(LLMProviderError) as timeout_error:
        client.chat_completion([{"role": "user", "content": "hello"}])
    assert isinstance(timeout_error.value.__cause__, LLMTimeoutError)
    assert client.debug_events[0].error_class == "LLMTimeoutError"

    request = httpx.Request("POST", "https://example.test")

    def rate_limit_post(*args, **kwargs):
        return httpx.Response(429, request=request, json={"error": "rate limited"})

    monkeypatch.setattr(httpx, "post", rate_limit_post)
    client = LLMClient()
    with pytest.raises(LLMProviderError) as rate_error:
        client.chat_completion([{"role": "user", "content": "hello"}])
    assert isinstance(rate_error.value.__cause__, LLMRateLimitError)
    assert client.debug_events[0].error_class == "LLMRateLimitError"

    def malformed_post(*args, **kwargs):
        return httpx.Response(200, request=request, json={"unexpected": []})

    monkeypatch.setattr(httpx, "post", malformed_post)
    client = LLMClient()
    with pytest.raises(LLMProviderError) as malformed_error:
        client.chat_completion([{"role": "user", "content": "hello"}])
    assert isinstance(malformed_error.value.__cause__, LLMMalformedResponseError)
    assert client.debug_events[0].error_class == "LLMMalformedResponseError"
