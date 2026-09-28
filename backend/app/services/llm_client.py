"""
Provider-agnostic LLM client.

Wraps Gemini (via google-genai), using the built-in `GoogleSearch` grounding
tool as the research agents' web/news search mechanism.

Free-tier Gemini has TWO separate limits that matter here:
  - per-minute: 5 requests/minute for gemini-2.5-flash
  - per-day: 20 requests/day, total, for gemini-2.5-flash

This client throttles every call to respect the per-minute limit, and
retries with backoff on a per-minute 429. But a per-DAY 429 cannot be
fixed by waiting a few seconds -- retrying just burns more of the day's
already-exhausted budget for nothing. So this client detects which kind
of quota was hit (by the quotaId in the error) and fails immediately,
without retrying, when it's the daily limit.
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("marketlens.llm")


@dataclass
class GroundedSource:
    url: str
    title: str


@dataclass
class GroundedResponse:
    text: str
    sources: list[GroundedSource] = field(default_factory=list)


class DailyQuotaExhausted(Exception):
    """Raised when Gemini's free-tier PER-DAY request quota is hit. Retrying
    will not help until the quota resets (~24h) -- callers should treat this
    as a hard stop for the rest of this research run rather than retry."""


class LLMClient:
    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        raise NotImplementedError

    async def generate_json(self, prompt: str, system: Optional[str] = None) -> dict:
        raise NotImplementedError

    async def generate_grounded(self, prompt: str, system: Optional[str] = None) -> GroundedResponse:
        raise NotImplementedError


class GeminiClient(LLMClient):
    # Free tier allows 5 req/min for gemini-2.5-flash. Space calls at ~13s
    # apart (60/5 + margin) so we proactively stay under the limit instead
    # of hitting 429s constantly.
    MIN_INTERVAL_SECONDS = 13.0
    MAX_RETRIES = 2

    def __init__(self):
        from google import genai

        self._genai = genai
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = settings.GEMINI_MODEL
        self._lock = asyncio.Lock()
        self._last_call_at = 0.0
        self._daily_quota_hit = False  # once true, stop even trying for the rest of this process

    async def _throttle(self):
        async with self._lock:
            elapsed = time.monotonic() - self._last_call_at
            wait = self.MIN_INTERVAL_SECONDS - elapsed
            if wait > 0:
                logger.info("Throttling Gemini call: waiting %.1fs to stay under rate limit", wait)
                await asyncio.sleep(wait)
            self._last_call_at = time.monotonic()

    async def _call_with_retry(self, fn):
        if self._daily_quota_hit:
            raise DailyQuotaExhausted("Daily Gemini free-tier quota already exhausted this run")

        last_exc = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            await self._throttle()
            try:
                return await fn()
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                msg = str(exc)
                is_rate_limited = "429" in msg or "RESOURCE_EXHAUSTED" in msg
                is_daily = "PerDay" in msg  # e.g. "GenerateRequestsPerDayPerProjectPerModel-FreeTier"

                if is_rate_limited and is_daily:
                    self._daily_quota_hit = True
                    logger.warning(
                        "Gemini DAILY quota exhausted -- not retrying (won't reset for hours). "
                        "Remaining agent steps in this run will be skipped."
                    )
                    raise DailyQuotaExhausted(msg) from exc

                if is_rate_limited:
                    backoff = 20.0 * attempt
                    logger.warning(
                        "Gemini per-minute rate limit hit (attempt %d/%d) -- waiting %.0fs before retry",
                        attempt, self.MAX_RETRIES, backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise
        raise last_exc

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        from google.genai import types

        async def _do():
            config = types.GenerateContentConfig(system_instruction=system) if system else None
            resp = await self._client.aio.models.generate_content(
                model=self._model, contents=prompt, config=config
            )
            return resp.text or ""

        return await self._call_with_retry(_do)

    async def generate_json(self, prompt: str, system: Optional[str] = None) -> dict:
        from google.genai import types

        async def _do():
            full_system = (system or "") + "\nRespond with ONLY valid JSON. No markdown fences, no preamble."
            config = types.GenerateContentConfig(
                system_instruction=full_system, response_mime_type="application/json"
            )
            resp = await self._client.aio.models.generate_content(
                model=self._model, contents=prompt, config=config
            )
            text = (resp.text or "").strip()
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                cleaned = text.strip("`").removeprefix("json").strip()
                return json.loads(cleaned)

        return await self._call_with_retry(_do)

    async def generate_grounded(self, prompt: str, system: Optional[str] = None) -> GroundedResponse:
        from google.genai import types

        async def _do():
            config = types.GenerateContentConfig(
                system_instruction=system,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            )
            resp = await self._client.aio.models.generate_content(
                model=self._model, contents=prompt, config=config
            )
            text = resp.text or ""
            sources: list[GroundedSource] = []
            try:
                candidate = resp.candidates[0]
                grounding = candidate.grounding_metadata
                chunks = grounding.grounding_chunks or [] if grounding else []
                for chunk in chunks:
                    web = getattr(chunk, "web", None)
                    if web and web.uri:
                        sources.append(GroundedSource(url=web.uri, title=web.title or web.uri))
            except (AttributeError, IndexError, TypeError) as exc:
                logger.warning("Could not extract grounding metadata: %s", exc)
            return GroundedResponse(text=text, sources=sources)

        return await self._call_with_retry(_do)


_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is not None:
        return _client
    if settings.LLM_PROVIDER == "gemini":
        _client = GeminiClient()
    else:
        raise NotImplementedError(
            f"LLM_PROVIDER={settings.LLM_PROVIDER!r} has no client implementation yet. "
            "Only 'gemini' is wired up in this build."
        )
    return _client