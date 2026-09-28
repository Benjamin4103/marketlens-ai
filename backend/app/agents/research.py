"""Web Research Agent + News Research Agent.

Both use Gemini's Google Search grounding tool to retrieve real, live web
results with citations -- this is the actual "search the web, retrieve
sources, extract useful information" step from the spec, backed by real
data rather than simulated data.
"""
import logging

from app.services.llm_client import get_llm_client, GroundedResponse

logger = logging.getLogger("marketlens.agents.research")


async def _grounded_search(query: str, topic: str) -> tuple[GroundedResponse, list[dict]]:
    llm = get_llm_client()
    resp = await llm.generate_grounded(
        query,
        system=(
            "You are a market research analyst. Answer concisely and factually, "
            "citing what you find. Do not speculate beyond what search results support."
        ),
    )
    sources = [
        {
            "url": s.url,
            "title": s.title,
            "publisher": None,
            "published_at": None,
            "source_type": "web",
            "topic": topic,
            "company": None,
            "relevance_score": 0.75,
            "is_demo": False,
        }
        for s in resp.sources
    ]
    return resp, sources


async def run_web_research(research_questions: list[str], subject: str) -> tuple[list[dict], list[str]]:
    """Runs grounded search for the market/overview-oriented questions.
    Returns (sources, findings_text_list)."""
    all_sources: list[dict] = []
    findings: list[str] = []
    seen_urls: set[str] = set()

    for q in research_questions[:2]:  # cap to keep pipeline within daily quota budget
        try:
            resp, sources = await _grounded_search(f"{subject}: {q}", topic="market")
            findings.append(f"Q: {q}\nA: {resp.text}")
            for s in sources:
                if s["url"] not in seen_urls:
                    seen_urls.add(s["url"])
                    all_sources.append(s)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Web research failed for question %r: %s", q, exc)

    return all_sources, findings


async def run_news_research(subject: str) -> tuple[list[dict], list[str]]:
    """Runs grounded search specifically for recent developments/news."""
    query = f"Latest news, funding, product launches, and major announcements about {subject} in the last 12 months"
    try:
        resp, sources = await _grounded_search(query, topic="recent news")
        for s in sources:
            s["source_type"] = "news"
        return sources, [resp.text]
    except Exception as exc:  # noqa: BLE001
        logger.warning("News research failed for %r: %s", subject, exc)
        return [], []