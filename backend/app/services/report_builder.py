"""
Assembles the structured report `sections` dict from a research dataset.
Mirrors the 19-section spec: sections with no reliable underlying data are
explicitly marked rather than fabricated.
"""

INSUFFICIENT = "Insufficient reliable data found."


def build_report_sections(query, dataset: dict, demo_mode: bool = True) -> dict:
    metrics = dataset["metrics"]
    competitors = dataset["competitors"]
    trends = dataset["trends"]
    sentiment = dataset["sentiment"]
    recs = dataset["recommendations"]
    insights = dataset["insights"]

    size_metric = next((m for m in metrics if "Size" in m["metric_name"]), None)
    growth_metric = next((m for m in metrics if "CAGR" in m["metric_name"]), None)

    sections = {}

    sections["executive_summary"] = (
        f"This report covers {query.raw_query}"
        + (f" ({query.geography})" if query.geography else "")
        + f". Based on {len(dataset['sources'])} sources, the market shows "
        f"{'growth' if trends and any(t['direction'] in ('growing', 'emerging') for t in trends) else 'mixed'} "
        f"signals, with {len(competitors)} notable competitors identified. "
        f"Overall research confidence: {round(dataset['overall_confidence'] * 100)}%."
    )

    sections["research_scope"] = {
        "query": query.raw_query,
        "geography": query.geography or "Not specified",
        "time_period": query.time_period or "Not specified",
        "depth": query.depth.value if hasattr(query.depth, "value") else query.depth,
        "sources_reviewed": len(dataset["sources"]),
    }

    sections["market_overview"] = dataset.get("market_overview") or next(
        (i["text"] for i in insights if i["section"] == "market_overview" and i["claim_type"] == "fact"),
        INSUFFICIENT,
    )

    if size_metric and growth_metric:
        sections["market_size_growth"] = {
            "market_size": f"${size_metric['value']}B ({size_metric['year']})",
            "cagr": f"{growth_metric['value']}%",
            "confidence": size_metric["confidence"],
        }
    else:
        sections["market_size_growth"] = INSUFFICIENT

    sections["key_market_drivers"] = [
        t["name"] for t in trends if t["direction"] in ("growing", "emerging")
    ] or INSUFFICIENT

    sections["market_challenges"] = [
        t["name"] for t in trends if t["direction"] == "declining"
    ] or [
        "No significant declining trends identified in the reviewed sources."
    ]

    sections["customer_segments"] = sorted(
        {c["target_market"] for c in competitors}
    ) if competitors else INSUFFICIENT

    sections["competitive_landscape"] = (
        f"{len(competitors)} competitors identified: " + ", ".join(c["name"] for c in competitors)
        if competitors else INSUFFICIENT
    )

    sections["competitor_comparison"] = [
        {
            "name": c["name"],
            "business_model": c["business_model"],
            "pricing": c["pricing"],
            "target_market": c["target_market"],
            "positioning": c["positioning"],
            "strengths": c["strengths"],
            "weaknesses": c["weaknesses"],
        }
        for c in competitors
    ] or INSUFFICIENT

    sections["market_trends"] = [
        {"name": t["name"], "direction": t["direction"], "confidence": t["confidence"]}
        for t in trends
    ] or INSUFFICIENT

    sections["recent_developments"] = [
        dev for c in competitors for dev in c["recent_developments"]
    ] or INSUFFICIENT

    sections["customer_sentiment"] = (
        [
            {"subject": s["subject"], "positive_pct": s["positive_pct"],
             "negative_pct": s["negative_pct"], "recurring_themes": s["recurring_themes"]}
            for s in sentiment
        ] if sentiment else INSUFFICIENT
    )

    sections["swot_analysis"] = {
        "strengths": list({s for c in competitors for s in c["strengths"]})[:5] or INSUFFICIENT,
        "weaknesses": list({w for c in competitors for w in c["weaknesses"]})[:5] or INSUFFICIENT,
        "opportunities": [i["text"] for i in insights if i["section"] == "opportunities"] or INSUFFICIENT,
        "threats": [t["name"] for t in trends if t["direction"] == "declining"] or INSUFFICIENT,
    }

    sections["opportunities"] = [
        i["text"] for i in insights if i["section"] == "opportunities"
    ] or INSUFFICIENT

    sections["threats"] = [
        t["name"] for t in trends if t["direction"] == "declining"
    ] or ["No major threats surfaced in the reviewed sources."]

    sections["strategic_recommendations"] = [
        {
            "recommendation": r["recommendation"],
            "rationale": r["rationale"],
            "expected_impact": r["expected_impact"],
            "risk": r["risk"],
            "confidence": r["confidence"],
        }
        for r in recs
    ] or INSUFFICIENT

    sections["key_takeaways"] = [
        sections["executive_summary"],
        f"Risk level assessed as {dataset['risk_level']}.",
        f"{len(trends)} market trends tracked; {sum(1 for t in trends if t['direction'] in ('growing','emerging'))} trending positive.",
    ]

    sections["sources_count"] = len(dataset["sources"])

    sections["confidence_assessment"] = {
        "overall_confidence": dataset["overall_confidence"],
        "risk_level": dataset["risk_level"],
        "note": (
            "This report was generated in DEMO MODE using deterministic simulated "
            "data for demonstration purposes. No real market research was performed. "
            "Configure OPENAI_API_KEY / SEARCH_API_KEY / NEWS_API_KEY and set "
            "DEMO_MODE=false to enable live research."
        ) if demo_mode else None,
    }

    return sections
