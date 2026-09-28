"""Research Planner Agent.

Input: raw query + optional geography/time period/competitors.
Output: a structured research plan (list of research questions) that the
downstream agents use to focus their searches.
"""
from app.services.llm_client import get_llm_client

PLANNER_SYSTEM = """You are a market research planning analyst. Given a
research subject, produce a focused research plan: a JSON object with a
"research_questions" array of 6-10 short, specific questions covering
market size, growth, major players, segments, consumer behavior,
regulation, recent developments, technology trends, competitive
landscape, opportunities, and risks -- whichever are actually relevant to
the subject (skip irrelevant ones, e.g. a single-company subject doesn't
need 'market segments').

Also include "subject_type": one of "market", "company", "comparison" and
"primary_entities": a short list of the main company/market names involved.
"""


async def plan_research(query: str, geography: str | None, competitors: list[str]) -> dict:
    llm = get_llm_client()
    prompt = f"Research subject: {query}"
    if geography:
        prompt += f"\nGeography: {geography}"
    if competitors:
        prompt += f"\nKnown competitors to include: {', '.join(competitors)}"

    try:
        plan = await llm.generate_json(prompt, system=PLANNER_SYSTEM)
        if "research_questions" not in plan:
            raise ValueError("planner response missing research_questions")
        return plan
    except Exception:
        # Defensive fallback -- never let a malformed planner response abort
        # the whole pipeline; downstream agents can still work off the raw
        # query alone.
        return {
            "research_questions": [
                f"What is the current state of {query}?",
                f"Who are the major players in {query}?",
                f"What are the recent developments in {query}?",
                f"What trends are shaping {query}?",
            ],
            "subject_type": "market",
            "primary_entities": competitors or [query],
        }
