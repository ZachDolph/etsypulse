from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from time import monotonic, perf_counter, sleep
from typing import Any, Literal, TypeVar
from uuid import NAMESPACE_URL, uuid5

import httpx
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.schemas import DebugEvent, utc_now

T = TypeVar("T", bound=BaseModel)
DebugSink = Callable[[DebugEvent], None]
ChatMessage = dict[str, str]


class LLMClientError(RuntimeError):
    pass


class LLMConfigurationError(LLMClientError):
    pass


class LLMProviderError(LLMClientError):
    pass


class LLMRateLimitError(LLMProviderError):
    pass


class LLMTimeoutError(LLMProviderError):
    pass


class LLMMalformedResponseError(LLMProviderError):
    pass


class LLMInvalidJSONError(LLMClientError):
    pass


@dataclass(frozen=True)
class LLMProviderConfig:
    name: Literal["nvidia_nim", "openrouter", "fake"]
    display_name: str
    base_url: str
    api_key: str | None
    model: str


@dataclass
class LLMResult:
    content: str
    provider: str
    model: str
    token_counts: dict[str, int] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    fallback_used: bool = False


@dataclass
class _ProviderAttempt:
    config: LLMProviderConfig
    fallback_used: bool


class LLMClient:
    """Provider-ordered LLM client for EtsyPulse.

    Docs verified for Session 3:
    - NVIDIA NIM LLM exposes OpenAI-compatible `POST /v1/chat/completions`.
    - NVIDIA hosted API examples use `https://integrate.api.nvidia.com` with
      endpoint `/v1/chat/completions`.
    - OpenRouter exposes `POST https://openrouter.ai/api/v1/chat/completions`
      and supports OpenAI-like `messages`, `model`, `max_tokens`, and
      `response_format` for JSON/structured outputs.
    """

    def __init__(self, debug_sink: DebugSink | None = None, force_test_mode: bool = False) -> None:
        settings = get_settings()
        self.debug_sink = debug_sink
        self.debug_events: list[DebugEvent] = []
        self.timeout_seconds = settings.llm_timeout_seconds
        self.rate_limit_per_minute = max(settings.llm_rate_limit_per_minute, 1)
        self.json_retries = max(settings.llm_json_retries, 0)
        self._last_request_at: dict[str, float] = {}
        self.test_mode = force_test_mode or settings.llm_test_mode
        self.providers = self._build_provider_order(settings, force_test_mode=force_test_mode)

    def chat_completion(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 800,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResult:
        last_error: Exception | None = None
        for index, attempt in enumerate(self.providers):
            try:
                return self._chat_with_provider(
                    attempt=attempt,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
            except Exception as exc:
                last_error = exc
                if index == len(self.providers) - 1:
                    break
        raise LLMProviderError(f"All LLM providers failed: {last_error}") from last_error

    def structured_json(
        self,
        messages: list[ChatMessage],
        response_model: type[T],
        temperature: float = 0.1,
        max_tokens: int = 800,
    ) -> T:
        schema = response_model.model_json_schema()
        structured_format = {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "strict": True,
                "schema": schema,
            },
        }
        json_instruction = {
            "role": "system",
            "content": "Return only valid JSON matching the requested schema. Do not include markdown fences.",
        }
        last_error: Exception | None = None
        for attempt_number in range(self.json_retries + 1):
            attempt_messages = [json_instruction, *messages]
            if attempt_number:
                attempt_messages.append(
                    {
                        "role": "user",
                        "content": "The previous response was invalid JSON or failed schema validation. Return corrected JSON only.",
                    }
                )
            result = self.chat_completion(
                attempt_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=structured_format,
            )
            try:
                return response_model.model_validate_json(self._extract_json_text(result.content))
            except (ValidationError, ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                self._emit_debug_event(
                    provider=result.provider,
                    model=result.model,
                    operation="structured_json_validation",
                    status="error",
                    latency_ms=0,
                    request_shape={"schema": response_model.__name__, "attempt": attempt_number + 1},
                    response_summary="Structured JSON validation failed; retrying if attempts remain.",
                    token_counts=result.token_counts,
                    error_class=type(exc).__name__,
                    fallback_used=result.fallback_used,
                )
        raise LLMInvalidJSONError(f"Unable to produce valid {response_model.__name__}: {last_error}") from last_error

    def _build_provider_order(self, settings, force_test_mode: bool = False) -> list[_ProviderAttempt]:
        if force_test_mode or settings.llm_test_mode:
            return [
                _ProviderAttempt(
                    LLMProviderConfig(
                        name="fake",
                        display_name="Fake LLM",
                        base_url="fake://local-test-provider",
                        api_key=None,
                        model="fake-json-model",
                    ),
                    fallback_used=False,
                )
            ]

        providers: list[_ProviderAttempt] = []
        if settings.nvidia_nim_api_key and settings.nvidia_nim_model:
            providers.append(
                _ProviderAttempt(
                    LLMProviderConfig(
                        name="nvidia_nim",
                        display_name="NVIDIA NIM",
                        base_url=settings.nvidia_nim_base_url.rstrip("/"),
                        api_key=settings.nvidia_nim_api_key,
                        model=settings.nvidia_nim_model,
                    ),
                    fallback_used=False,
                )
            )
        if settings.openrouter_api_key and settings.openrouter_model_fallback:
            providers.append(
                _ProviderAttempt(
                    LLMProviderConfig(
                        name="openrouter",
                        display_name="OpenRouter",
                        base_url=settings.openrouter_base_url.rstrip("/"),
                        api_key=settings.openrouter_api_key,
                        model=settings.openrouter_model_fallback,
                    ),
                    fallback_used=bool(providers),
                )
            )
        if not providers:
            raise LLMConfigurationError(
                "No LLM provider configured. Set LLM_TEST_MODE=true for tests/demo, or configure NVIDIA_NIM_* and/or OPENROUTER_* env vars."
            )
        return providers

    def _chat_with_provider(
        self,
        attempt: _ProviderAttempt,
        messages: list[ChatMessage],
        temperature: float,
        max_tokens: int,
        response_format: dict[str, Any] | None,
    ) -> LLMResult:
        config = attempt.config
        started = perf_counter()
        request_shape = self._redact(
            {
                "provider": config.display_name,
                "base_url": config.base_url,
                "model": config.model,
                "api_key": config.api_key,
                "message_count": len(messages),
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format_type": response_format.get("type") if response_format else None,
                "timeout_seconds": self.timeout_seconds,
                "rate_limit_per_minute": self.rate_limit_per_minute,
            }
        )
        try:
            self._enforce_rate_limit(config.name)
            if config.name == "fake":
                result = self._fake_chat(config, response_format=response_format, fallback_used=attempt.fallback_used)
            else:
                result = self._openai_compatible_chat(
                    config,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    fallback_used=attempt.fallback_used,
                )
            latency_ms = round((perf_counter() - started) * 1000, 3)
            self._emit_debug_event(
                provider=config.display_name,
                model=config.model,
                operation="chat_completion",
                status="stubbed" if config.name == "fake" else "success",
                latency_ms=latency_ms,
                request_shape=request_shape,
                response_summary="Returned chat completion content.",
                token_counts=result.token_counts,
                fallback_used=attempt.fallback_used,
            )
            return result
        except Exception as exc:
            latency_ms = round((perf_counter() - started) * 1000, 3)
            self._emit_debug_event(
                provider=config.display_name,
                model=config.model,
                operation="chat_completion",
                status="error",
                latency_ms=latency_ms,
                request_shape=request_shape,
                response_summary=f"{type(exc).__name__}: {exc}",
                error_class=type(exc).__name__,
                fallback_used=attempt.fallback_used,
            )
            raise

    def _openai_compatible_chat(
        self,
        config: LLMProviderConfig,
        messages: list[ChatMessage],
        temperature: float,
        max_tokens: int,
        response_format: dict[str, Any] | None,
        fallback_used: bool,
    ) -> LLMResult:
        payload: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if response_format:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        if config.name == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/etsypulse/etsypulse"
            headers["X-Title"] = "EtsyPulse"

        try:
            response = httpx.post(
                self._chat_completions_url(config),
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            if response.status_code == 429:
                raise LLMRateLimitError(f"{config.display_name} rate limited the request")
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"{config.display_name} request timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(f"{config.display_name} HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(str(exc)) from exc
        except ValueError as exc:
            raise LLMMalformedResponseError(f"{config.display_name} returned non-JSON response") from exc

        try:
            content = data["choices"][0]["message"].get("content") or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMMalformedResponseError("Provider response did not match OpenAI chat-completions shape") from exc
        return LLMResult(
            content=content,
            provider=config.display_name,
            model=str(data.get("model") or config.model),
            token_counts=self._extract_usage(data.get("usage", {})),
            raw=data,
            fallback_used=fallback_used,
        )

    def _chat_completions_url(self, config: LLMProviderConfig) -> str:
        base_url = config.base_url.rstrip("/")
        if base_url.endswith("/v1") or base_url.endswith("/api/v1"):
            return f"{base_url}/chat/completions"
        if config.name == "openrouter":
            return f"{base_url}/api/v1/chat/completions"
        return f"{base_url}/v1/chat/completions"

    def _fake_chat(self, config: LLMProviderConfig, response_format: dict[str, Any] | None, fallback_used: bool) -> LLMResult:
        if response_format and response_format.get("type") == "json_schema":
            schema = response_format.get("json_schema", {}).get("schema", {})
            content = json.dumps(self._fake_json_for_schema(schema))
        else:
            content = "Fake LLM response for deterministic EtsyPulse tests."
        return LLMResult(
            content=content,
            provider=config.display_name,
            model=config.model,
            token_counts={"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
            raw={"fake": True},
            fallback_used=fallback_used,
        )

    def _fake_json_for_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, prop in schema.get("properties", {}).items():
            prop_type = prop.get("type")
            if prop_type == "string":
                result[key] = f"fake_{key}"
            elif prop_type in {"number", "integer"}:
                result[key] = 1 if prop_type == "integer" else 0.75
            elif prop_type == "boolean":
                result[key] = True
            elif prop_type == "array":
                result[key] = []
            elif prop_type == "object":
                result[key] = {}
            else:
                result[key] = None
        return result

    def _enforce_rate_limit(self, provider_name: str) -> None:
        min_interval = 60.0 / self.rate_limit_per_minute
        now = monotonic()
        last = self._last_request_at.get(provider_name)
        if last is not None:
            delay = min_interval - (now - last)
            if delay > 0:
                sleep(delay)
        self._last_request_at[provider_name] = monotonic()

    def _extract_json_text(self, content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`").strip()
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()
        return stripped

    def _extract_usage(self, usage: Any) -> dict[str, int]:
        if not isinstance(usage, dict):
            return {}
        counts: dict[str, int] = {}
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            value = usage.get(key)
            if isinstance(value, int):
                counts[key] = value
        return counts

    def _emit_debug_event(
        self,
        provider: str,
        model: str,
        operation: str,
        status: str,
        latency_ms: float,
        request_shape: dict[str, Any],
        response_summary: str,
        token_counts: dict[str, int] | None = None,
        error_class: str | None = None,
        fallback_used: bool = False,
    ) -> None:
        event = DebugEvent(
            id=f"debug_llm_{uuid5(NAMESPACE_URL, f'{provider}:{operation}:{utc_now().isoformat()}').hex[:12]}",
            provider=provider,
            tool_name="chat_completions",
            model=model,
            operation=operation,
            status=status,
            cache_mode="demo" if provider == "Fake LLM" else "live",
            latency_ms=latency_ms,
            request_shape=request_shape,
            token_counts=token_counts or {},
            error_class=error_class,
            fallback_used=fallback_used,
            request_summary="OpenAI-compatible chat-completions request with redacted credentials.",
            response_summary=response_summary,
            redacted=True,
        )
        self.debug_events.append(event)
        if self.debug_sink:
            self.debug_sink(event)

    def _redact(self, value: Any) -> Any:
        if isinstance(value, dict):
            redacted: dict[str, Any] = {}
            for key, item in value.items():
                lowered = key.lower()
                if any(token in lowered for token in ("api_key", "token", "secret", "password", "auth", "key")):
                    redacted[key] = "[REDACTED]" if item else None
                else:
                    redacted[key] = self._redact(item)
            return redacted
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        return value
