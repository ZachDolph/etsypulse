from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from app.config import get_settings
from app.schemas import DebugEvent, utc_now

JsonValue = dict[str, Any] | list[Any]
DebugSink = Callable[[DebugEvent], None]

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "demo_data" / "brightdata_samples"


class BrightDataClientError(RuntimeError):
    pass


class BrightDataClient:
    """Bright Data integration boundary.

    Bright Data docs reviewed for Session 2:
    - MCP FAQ lists current tools `search_engine`, `scrape_as_markdown`,
      `scrape_as_html`, `session_stats`, `web_data_instagram_reels`, and
      browser tools such as `scraping_browser_navigate`.
    - Dataset docs cover structured Web Scraper APIs for TikTok, Reddit,
      Instagram, Google, and other platforms.

    App-level method names below stay stable for agents while mapping to the
    closest Bright Data MCP/Web Scraper tool names through TOOL_NAMES.
    """

    TOOL_NAMES = {
        "etsy_products": "web_data_etsy_products",
        "serp_batch": "search_engine",
        "scrape_markdown": "scrape_as_markdown",
        "scrape_batch": "scrape_as_markdown",
        "discover": "discover",
        "tiktok_posts": "web_data_tiktok_posts",
        "reddit_posts": "web_data_reddit_posts",
        "instagram_reels": "web_data_instagram_reels",
        "google_shopping": "web_data_google_shopping",
    }

    FIXTURES = {
        "etsy_products": "etsy_products.json",
        "serp_batch": "serp_batch.json",
        "scrape_markdown": "scrape_markdown.md",
        "scrape_batch": "scrape_batch.json",
        "discover": "discover.json",
        "tiktok_posts": "tiktok_posts.json",
        "reddit_posts": "reddit_posts.json",
        "instagram_reels": "instagram_reels.json",
        "google_shopping": "google_shopping.json",
    }

    def __init__(
        self,
        demo_mode: bool | None = None,
        samples_dir: Path = SAMPLES_DIR,
        debug_sink: DebugSink | None = None,
    ) -> None:
        settings = get_settings()
        self.demo_mode = settings.demo_mode if demo_mode is None else demo_mode
        self.samples_dir = samples_dir
        self.debug_sink = debug_sink
        self.debug_events: list[DebugEvent] = []
        self.brightdata_api_key = settings.brightdata_api_key
        self.brightdata_mcp_url = settings.brightdata_mcp_url

    def etsy_products(self, shop_url: str | None = None, search_url: str | None = None) -> JsonValue:
        if not shop_url and not search_url:
            raise ValueError("etsy_products requires shop_url or search_url")
        return self._execute("etsy_products", {"shop_url": shop_url, "search_url": search_url})

    def serp_batch(self, keywords: list[str]) -> JsonValue:
        if not keywords:
            raise ValueError("serp_batch requires at least one keyword")
        return self._execute("serp_batch", {"keywords": keywords})

    def scrape_markdown(self, url: str) -> str:
        return self._execute("scrape_markdown", {"url": url})

    def scrape_batch(self, urls: list[str]) -> JsonValue:
        if not urls:
            raise ValueError("scrape_batch requires at least one URL")
        return self._execute("scrape_batch", {"urls": urls})

    def discover(self, query: str) -> JsonValue:
        return self._execute("discover", {"query": query})

    def tiktok_posts(self, query: str) -> JsonValue:
        return self._execute("tiktok_posts", {"query": query})

    def reddit_posts(self, query: str) -> JsonValue:
        return self._execute("reddit_posts", {"query": query})

    def instagram_reels(self, query: str) -> JsonValue:
        return self._execute("instagram_reels", {"query": query})

    def google_shopping(self, query: str) -> JsonValue:
        return self._execute("google_shopping", {"query": query})

    def validate_demo_fixtures(self) -> dict[str, str]:
        results: dict[str, str] = {}
        for operation, fixture_name in self.FIXTURES.items():
            value = self._load_fixture(operation)
            results[operation] = self._summarize_response(value)
            if fixture_name.endswith(".json") and not isinstance(value, (dict, list)):
                raise BrightDataClientError(f"Fixture {fixture_name} did not parse as JSON object/list")
            if fixture_name.endswith(".md") and not isinstance(value, str):
                raise BrightDataClientError(f"Fixture {fixture_name} did not parse as Markdown text")
        return results

    def _execute(self, operation: str, request_shape: dict[str, Any]) -> Any:
        started = perf_counter()
        tool_name = self.TOOL_NAMES[operation]
        mode = "demo" if self.demo_mode else "live"
        safe_shape = self._redact(
            {
                "tool_name": tool_name,
                "request": request_shape,
                "mcp_url": self.brightdata_mcp_url,
                "api_key": self.brightdata_api_key,
            }
        )
        try:
            if self.demo_mode:
                response = self._load_fixture(operation)
                status = "stubbed"
                response_summary = self._summarize_response(response)
                return response

            raise BrightDataClientError(
                "Live Bright Data MCP execution is not enabled in Session 2; configure the MCP adapter in a later session."
            )
        except Exception as exc:
            status = "error"
            response_summary = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            latency_ms = round((perf_counter() - started) * 1000, 3)
            self._emit_debug_event(
                operation=operation,
                tool_name=tool_name,
                status=status,
                cache_mode=mode,
                latency_ms=latency_ms,
                request_shape=safe_shape,
                response_summary=response_summary,
            )

    def _load_fixture(self, operation: str) -> Any:
        fixture_path = self.samples_dir / self.FIXTURES[operation]
        if not fixture_path.exists():
            raise BrightDataClientError(f"Missing Bright Data demo fixture: {fixture_path}")

        if fixture_path.suffix == ".md":
            return fixture_path.read_text(encoding="utf-8")
        return json.loads(fixture_path.read_text(encoding="utf-8"))

    def _emit_debug_event(
        self,
        operation: str,
        tool_name: str,
        status: str,
        cache_mode: str,
        latency_ms: float,
        request_shape: dict[str, Any],
        response_summary: str,
    ) -> None:
        event = DebugEvent(
            id=f"debug_brightdata_{uuid5(NAMESPACE_URL, f'{operation}:{utc_now().isoformat()}').hex[:12]}",
            provider="Bright Data",
            tool_name=tool_name,
            operation=operation,
            status=status,
            cache_mode=cache_mode,
            latency_ms=latency_ms,
            request_shape=request_shape,
            request_summary=f"{cache_mode} call for Bright Data tool `{tool_name}` with redacted request shape.",
            response_summary=response_summary,
            redacted=True,
        )
        self.debug_events.append(event)
        if self.debug_sink:
            self.debug_sink(event)

    def _summarize_response(self, response: Any) -> str:
        if isinstance(response, list):
            return f"Loaded list with {len(response)} item(s)."
        if isinstance(response, dict):
            keys = ", ".join(sorted(response.keys())[:6])
            return f"Loaded object with keys: {keys}."
        if isinstance(response, str):
            return f"Loaded text with {len(response)} character(s)."
        return f"Loaded {type(response).__name__}."

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
