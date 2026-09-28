"""
Real multi-agent research pipeline, wired as a LangGraph StateGraph.

This is the live-mode counterpart to app/services/demo_data.py: it returns
the exact same dataset shape (sources / competitors / metrics / trends /
sentiment / insights / recommendations / risk_level / overall_confidence)
so app/services/orchestrator.py can call either interchangeably.

Nodes: planner -> web_research -> news_research -> competitor_intel ->
trend_analysis -> sentiment_analysis -> market_analyst -> strategy ->
evidence_check -> assemble.

Call counts are kept low (2 web questions, 2 competitors) because free-tier
Gemini caps gemini-2.5-flash at 20 requests/DAY (not just per-minute) --
a full run needs to comfortably fit under that ceiling.

Note on market sizing: unlike the demo generator, this pipeline does NOT
invent a market-size/CAGR number. Grounded web search frequently surfaces
a stated market size in prose, but reliably extracting a *verified* one
would need a dedicated numeric-extraction + cross-source verification step
beyond this build's scope -- so `metrics` is intentionally left empty here,
and the report legitimately shows "Insufficient reliable data found." for
that section rather than risk fabricating a figure, consistent with the
spec's "never fabricate market sizes" rule.
"""
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, END

from app.agents.planner import plan_research
from app.agents.research import run_web_research, run_news_research
from app.agents.competitor import discover_competitors, research_competitor
from app.agents.trends import run_trend_analysis
from app.agents.sentiment import run_sentiment_analysis
from app.agents.analyst import run_market_analysis, run_strategy
from app.agents.evidence import verify_and_score

logger = logging.getLogger("marketlens.agents.graph")


class PipelineState(TypedDict, total=False):
    query: str
    geography: str | None
    competitors_requested: list[str]
    plan: dict
    sources: list[dict]
    findings_text: str
    competitors: list[dict]
    trends: list[dict]
    sentiment: list[dict]
    market_overview: str
    insights: list[dict]
    recommendations: list[dict]
    overall_confidence: float
    risk_level: str


async def _node_plan(state: PipelineState) -> dict:
    plan = await plan_research(state["query"], state.get("geography"), state.get("competitors_requested", []))
    return {"plan": plan}


async def _node_web_and_news(state: PipelineState) -> dict:
    questions = state["plan"].get("research_questions", [state["query"]])
    web_sources, web_findings = await run_web_research(questions, state["query"])
    news_sources, news_findings = await run_news_research(state["query"])

    seen = {s["url"] for s in web_sources}
    all_sources = list(web_sources)
    for s in news_sources:
        if s["url"] not in seen:
            seen.add(s["url"])
            all_sources.append(s)

    findings_text = "\n\n".join(web_findings + news_findings)
    return {"sources": all_sources, "findings_text": findings_text}


async def _node_competitors(state: PipelineState) -> dict:
    requested = state.get("competitors_requested") or []
    names = requested if requested else await discover_competitors(state["query"], n=2)

    competitors: list[dict] = []
    new_sources: list[dict] = []
    seen = {s["url"] for s in state.get("sources", [])}

    for name in names[:2]:  # cap for daily quota budget (free tier: 20 req/day)
        extracted, sources = await research_competitor(name, state["query"])
        competitors.append(extracted)
        for s in sources:
            if s["url"] not in seen:
                seen.add(s["url"])
                new_sources.append(s)

    return {"competitors": competitors, "sources": state.get("sources", []) + new_sources}


async def _node_trends(state: PipelineState) -> dict:
    trends, new_sources = await run_trend_analysis(state["query"])
    seen = {s["url"] for s in state.get("sources", [])}
    merged_new = [s for s in new_sources if s["url"] not in seen]
    return {"trends": trends, "sources": state.get("sources", []) + merged_new}


async def _node_sentiment(state: PipelineState) -> dict:
    # Only worth attempting for company-like subjects (few named entities),
    # matching the spec's "where appropriate" scoping.
    is_company_like = len(state.get("competitors_requested") or []) <= 3
    if not is_company_like:
        return {"sentiment": []}

    result, new_sources = await run_sentiment_analysis(state["query"])
    seen = {s["url"] for s in state.get("sources", [])}
    merged_new = [s for s in new_sources if s["url"] not in seen]
    sentiment = [result] if result else []
    return {"sentiment": sentiment, "sources": state.get("sources", []) + merged_new}


async def _node_analysis(state: PipelineState) -> dict:
    analysis = await run_market_analysis(state["query"], state.get("findings_text", ""))
    return {
        "market_overview": analysis.get("market_overview", "Insufficient reliable data found."),
        "insights": analysis.get("insights", []),
    }


async def _node_strategy(state: PipelineState) -> dict:
    recs = await run_strategy(state["query"], state.get("market_overview", ""), state.get("findings_text", ""))
    return {"recommendations": recs}


async def _node_evidence(state: PipelineState) -> dict:
    filtered_trends, confidence, risk = verify_and_score(
        state.get("sources", []),
        state.get("competitors", []),
        state.get("trends", []),
        state.get("insights", []),
    )
    return {"trends": filtered_trends, "overall_confidence": confidence, "risk_level": risk}


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("plan", _node_plan)
    graph.add_node("web_and_news", _node_web_and_news)
    graph.add_node("competitors", _node_competitors)
    graph.add_node("trends", _node_trends)
    graph.add_node("sentiment", _node_sentiment)
    graph.add_node("analysis", _node_analysis)
    graph.add_node("strategy", _node_strategy)
    graph.add_node("evidence", _node_evidence)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "web_and_news")
    graph.add_edge("web_and_news", "competitors")
    graph.add_edge("competitors", "trends")
    graph.add_edge("trends", "sentiment")
    graph.add_edge("sentiment", "analysis")
    graph.add_edge("analysis", "strategy")
    graph.add_edge("strategy", "evidence")
    graph.add_edge("evidence", END)
    return graph.compile()


async def run_real_pipeline(query: str, competitors_requested: list[str], geography: str | None) -> dict:
    """Entry point matching demo_data.generate_demo_dataset's return shape."""
    app = build_graph()
    initial_state: PipelineState = {
        "query": query,
        "geography": geography,
        "competitors_requested": competitors_requested,
    }
    final_state = await app.ainvoke(initial_state)

    # Attach source_ids-equivalent linkage isn't tracked per-claim in this
    # build (would need each agent to return matched source indices) -- the
    # sources list itself is still fully real and stored, which is what the
    # UI's Sources tab and citation counts rely on.
    for ins in final_state.get("insights", []):
        ins.setdefault("source_ids", [])
    for rec in final_state.get("recommendations", []):
        rec.setdefault("supporting_evidence", [])

    return {
        "sources": final_state.get("sources", []),
        "competitors": final_state.get("competitors", []),
        "metrics": [],  # intentionally empty -- see module docstring
        "trends": final_state.get("trends", []),
        "sentiment": final_state.get("sentiment", []),
        "insights": final_state.get("insights", []),
        "recommendations": final_state.get("recommendations", []),
        "risk_level": final_state.get("risk_level", "medium"),
        "overall_confidence": final_state.get("overall_confidence", 0.5),
        "market_overview": final_state.get("market_overview", "Insufficient reliable data found."),
    }