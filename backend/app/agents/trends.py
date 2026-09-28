"""Market Trend Agent.

Runs one grounded search for emerging/declining trends, then asks the LLM
to extract structured trend objects from the findings.
"""
import logging

from app.services.llm_client import get_llm_client
from app.agents.research import _grounded_search

logger = logging.getLogger("marketlens.agents.trends")

EXTRACT_SYSTEM = """You extract market trends from research notes. Return
ONLY a JSON object: {"trends": [ { "name": "...", "description": "...",
"direction": "emerging|growing|stable|declining", "business_impact": "...",
"confidence": <0-1 float, how well-supported this trend is by the notes> } ]}
Include 3-6 trends. Only include trends the notes actually support --
do not invent trends the research didn't surface.
"""


async def run_trend_analysis(subject: str) -> tuple[list[dict], list[dict]]:
    """Returns (trends, sources)."""
    query = f"Emerging trends, technology shifts, and declining patterns in {subject} right now"
    try:
        resp, sources = await _grounded_search(query, topic="trends")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Trend search failed for %r: %s", subject, exc)
        return [], []

    llm = get_llm_client()
    try:
        extracted = await llm.generate_json(resp.text, system=EXTRACT_SYSTEM)
        trends = extracted.get("trends", [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Trend extraction failed for %r: %s", subject, exc)
        trends = []

    for t in trends:
        t.setdefault("evidence", [])
        t.setdefault("affected_companies", [])
        t.setdefault("source_count", len(sources))

    return trends, sources
