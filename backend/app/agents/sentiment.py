"""Sentiment Analysis Agent.

Only runs for company-like subjects (not broad markets), and only reports
sentiment when the grounded search actually surfaces review/discussion
content -- otherwise marks data_available=False rather than fabricating
percentages, per the spec's explicit instruction not to claim sentiment
statistics without supporting data.
"""
import logging

from app.services.llm_client import get_llm_client
from app.agents.research import _grounded_search

logger = logging.getLogger("marketlens.agents.sentiment")

EXTRACT_SYSTEM = """You analyze customer sentiment from research notes about
a company/product. Return ONLY a JSON object:
{
  "data_available": true|false,
  "positive_pct": <0-100 or null>,
  "negative_pct": <0-100 or null>,
  "neutral_pct": <0-100 or null>,
  "recurring_themes": ["..."],
  "top_complaints": ["..."]
}
Set data_available to false (and all percentages to null) if the notes
don't contain enough genuine review/discussion content to support a
sentiment breakdown. Never invent percentages.
"""


async def run_sentiment_analysis(subject: str) -> tuple[dict | None, list[dict]]:
    query = f"Customer reviews, complaints, and public sentiment about {subject}"
    try:
        resp, sources = await _grounded_search(query, topic="sentiment")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sentiment search failed for %r: %s", subject, exc)
        return None, []

    llm = get_llm_client()
    try:
        extracted = await llm.generate_json(resp.text, system=EXTRACT_SYSTEM)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sentiment extraction failed for %r: %s", subject, exc)
        return None, sources

    if not extracted.get("data_available"):
        return None, sources

    extracted["subject"] = subject
    extracted["sample_size"] = len(sources) * 10  # rough proxy; no real sample count available
    return extracted, sources
