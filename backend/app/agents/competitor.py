"""Competitor Intelligence Agent.

For each competitor (either user-supplied or discovered via a grounded
"who are the major players" search), runs a grounded search for that
company specifically, then asks the LLM to extract structured comparison
data (business model, pricing, positioning, strengths/weaknesses) from the
grounded findings -- never inventing figures the search didn't surface.
"""
import logging

from app.services.llm_client import get_llm_client

logger = logging.getLogger("marketlens.agents.competitor")

DISCOVER_PROMPT = "Who are the {n} most significant companies/competitors in {subject}? Reply with just a comma-separated list of company names, nothing else."

EXTRACT_SYSTEM = """You extract structured competitor intelligence from
research notes. Given notes about a company, return ONLY a JSON object:
{
  "business_model": "...",
  "products": ["..."],
  "pricing": "...",
  "target_market": "...",
  "geography": ["..."],
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "positioning": "...",
  "recent_developments": ["..."],
  "market_position_score": <number 0-100, your best estimate of relative market strength>
}
If the notes don't support a field, use a short honest placeholder like
"Not clearly established from available sources" rather than inventing
specifics. Never invent numeric figures (revenue, users, funding amounts)
that aren't in the notes.
"""


async def discover_competitors(subject: str, n: int = 4) -> list[str]:
    llm = get_llm_client()
    try:
        text = await llm.generate(DISCOVER_PROMPT.format(n=n, subject=subject))
        names = [n.strip() for n in text.split(",") if n.strip()]
        return names[:n]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Competitor discovery failed for %r: %s", subject, exc)
        return []


async def research_competitor(name: str, subject_context: str) -> tuple[dict, list[dict]]:
    """Returns (structured_competitor_dict, sources)."""
    from app.agents.research import _grounded_search

    query = f"{name} company overview: business model, pricing, products, target market, recent news, strengths and weaknesses, in the context of {subject_context}"
    resp, sources = await _grounded_search(query, topic="competitor")
    for s in sources:
        s["company"] = name

    llm = get_llm_client()
    try:
        extracted = await llm.generate_json(
            f"Company: {name}\n\nResearch notes:\n{resp.text}", system=EXTRACT_SYSTEM
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Competitor extraction failed for %r: %s", name, exc)
        extracted = {
            "business_model": "Not clearly established from available sources",
            "products": [],
            "pricing": "Not clearly established from available sources",
            "target_market": "Not clearly established from available sources",
            "geography": [],
            "strengths": [],
            "weaknesses": [],
            "positioning": "Not clearly established from available sources",
            "recent_developments": [],
            "market_position_score": None,
        }

    extracted["name"] = name
    return extracted, sources
