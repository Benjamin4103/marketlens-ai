"""Market Analyst Agent + Strategy Agent.

These don't search the web themselves -- they synthesize everything the
upstream agents (web, news, competitor, trend, sentiment) already gathered
into insights (tagged fact/inference) and prioritized recommendations. This
is the RAG-style "context construction -> LLM -> evidence-backed analysis"
step from the spec, using the gathered findings as the retrieved context.
"""
import logging

from app.services.llm_client import get_llm_client

logger = logging.getLogger("marketlens.agents.analyst")

ANALYST_SYSTEM = """You are a senior market analyst. Given research
findings about a market/company, produce a JSON object:
{
  "market_overview": "2-4 sentence factual summary",
  "insights": [
    {"section": "market_overview|opportunities|challenges", "claim_type": "fact|inference", "text": "...", "confidence": <0-1>}
  ]
}
"fact" claims must be directly supported by the findings. "inference" claims
are your reasoned interpretation -- label them as such. Include 4-8
insights. Do not invent statistics not present in the findings.
"""

STRATEGY_SYSTEM = """You are a strategy consultant. Given market analysis
findings, produce a JSON object:
{
  "recommendations": [
    {
      "recommendation": "...", "rationale": "...",
      "expected_impact": "...", "risk": "...",
      "confidence": <0-1>, "priority": <1-3, 1=highest>
    }
  ]
}
Include 3-5 recommendations, each genuinely actionable and grounded in the
findings provided -- not generic business advice.
"""


async def run_market_analysis(subject: str, findings_text: str) -> dict:
    llm = get_llm_client()
    prompt = f"Subject: {subject}\n\nResearch findings:\n{findings_text[:12000]}"
    try:
        return await llm.generate_json(prompt, system=ANALYST_SYSTEM)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Market analysis failed for %r: %s", subject, exc)
        return {"market_overview": "Insufficient reliable data found.", "insights": []}


async def run_strategy(subject: str, market_overview: str, findings_text: str) -> list[dict]:
    llm = get_llm_client()
    prompt = (
        f"Subject: {subject}\n\nMarket overview:\n{market_overview}\n\n"
        f"Research findings:\n{findings_text[:8000]}"
    )
    try:
        result = await llm.generate_json(prompt, system=STRATEGY_SYSTEM)
        return result.get("recommendations", [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Strategy generation failed for %r: %s", subject, exc)
        return []
