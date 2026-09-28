"""
Deterministic, clearly-labeled sample data used when DEMO_MODE is on (or no
LLM key is configured). This lets the full pipeline — sources, competitors,
trends, sentiment, insights, recommendations, report — run end-to-end without
any paid API keys, while being unmistakably marked as simulated.

Real-mode agents (LangGraph + OpenAI + search/news APIs) live in
app/agents/ and app/services/orchestrator.py switches between the two based
on `settings.effective_demo_mode`.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import random


def _seed_for(query: str) -> random.Random:
    """Deterministic per-query RNG so the same query always yields the same
    demo report (useful for the 'What Changed?' diff feature to be stable
    between identical re-runs, while still varying by query)."""
    h = hashlib.sha256(query.strip().lower().encode()).hexdigest()
    return random.Random(int(h[:16], 16))


GENERIC_PUBLISHERS = [
    ("MarketWatch Insights", "web"),
    ("TechCrunch", "news"),
    ("Reuters Business", "news"),
    ("Statista Research", "report"),
    ("Economic Times", "news"),
    ("Crunchbase News", "news"),
    ("Company Newsroom", "company_site"),
    ("Industry Analyst Report", "report"),
]

TREND_TEMPLATES = [
    ("Increasing consolidation among top players", "growing"),
    ("Rising customer demand for AI-native features", "emerging"),
    ("Shift toward subscription-based pricing models", "growing"),
    ("Regulatory scrutiny increasing in core markets", "emerging"),
    ("Margin pressure from new low-cost entrants", "growing"),
    ("Declining interest in legacy on-premise offerings", "declining"),
    ("Growing investor interest and funding activity", "emerging"),
    ("Stabilizing growth rate after early hype cycle", "stable"),
]

STRENGTH_POOL = [
    "Strong brand recognition", "Large existing user base", "Deep pockets for R&D",
    "Efficient go-to-market motion", "Strong partner ecosystem", "Early-mover advantage",
    "Superior unit economics", "Loyal enterprise customer base",
]
WEAKNESS_POOL = [
    "High customer acquisition cost", "Limited international presence",
    "Slower release cadence than peers", "Dependence on a single revenue stream",
    "Recent leadership turnover", "Narrower product breadth than category leaders",
]

RISK_LEVELS = ["low", "medium", "high"]


def generate_demo_dataset(query: str, competitors_requested: list[str], geography: str | None) -> dict:
    """Returns a fully-formed, internally-consistent demo dataset for one
    research query. Every numeric claim here is synthetic and every source
    is fabricated for demonstration only — is_demo=True is set throughout so
    the UI can render a clear 'Simulated Data' badge."""
    rng = _seed_for(query)
    now = datetime.now(timezone.utc)

    # ---- Sources ----
    n_sources = rng.randint(8, 14)
    sources = []
    for i in range(n_sources):
        publisher, stype = rng.choice(GENERIC_PUBLISHERS)
        days_ago = rng.randint(1, 400)
        sources.append({
            "url": f"https://example-demo-source.local/{query.lower().replace(' ', '-')}/{i+1}",
            "title": f"{query} — {publisher} analysis #{i+1}",
            "publisher": publisher,
            "published_at": now - timedelta(days=days_ago),
            "source_type": stype,
            "topic": rng.choice(["market size", "competition", "regulation", "funding", "consumer trends"]),
            "company": None,
            "relevance_score": round(rng.uniform(0.55, 0.98), 2),
            "is_demo": True,
        })

    # ---- Competitors ----
    default_names = ["Alpha Corp", "Beta Systems", "Gamma Technologies", "Delta Innovations"]
    names = competitors_requested if competitors_requested else default_names[:rng.randint(3, 4)]
    competitors = []
    for name in names:
        strengths = rng.sample(STRENGTH_POOL, k=2)
        weaknesses = rng.sample(WEAKNESS_POOL, k=2)
        competitors.append({
            "name": name,
            "business_model": rng.choice(["B2B SaaS subscription", "Marketplace / commission-based",
                                           "Freemium with paid tiers", "Direct enterprise licensing"]),
            "products": [f"{name} Core Platform", f"{name} Analytics Add-on"],
            "pricing": rng.choice(["$29-$299/mo tiered", "Custom enterprise pricing",
                                    "Free tier + usage-based pricing"]),
            "target_market": rng.choice(["SMB", "Mid-market", "Enterprise", "Consumer + SMB"]),
            "geography": [geography] if geography else ["Global"],
            "strengths": strengths,
            "weaknesses": weaknesses,
            "positioning": f"Positions itself as the {rng.choice(['most affordable', 'most enterprise-ready', 'most innovative', 'fastest-growing'])} option in the category.",
            "recent_developments": [
                f"Announced {rng.choice(['a new funding round', 'a strategic partnership', 'a major product launch', 'international expansion'])} in the last {rng.randint(2, 11)} months.",
            ],
            "market_position_score": round(rng.uniform(35, 92), 1),
        })

    # ---- Market metrics ----
    base_size = round(rng.uniform(1.5, 120), 1)
    growth = round(rng.uniform(4, 34), 1)
    metrics = [
        {"metric_name": f"Estimated Market Size {now.year}", "value": base_size, "unit": "USD_BN",
         "year": now.year, "confidence": round(rng.uniform(0.5, 0.8), 2)},
        {"metric_name": "Projected CAGR (5yr)", "value": growth, "unit": "PERCENT",
         "year": now.year, "confidence": round(rng.uniform(0.5, 0.75), 2)},
    ]

    # ---- Trends ----
    chosen_trends = rng.sample(TREND_TEMPLATES, k=rng.randint(4, 6))
    trends = []
    for name, direction in chosen_trends:
        trends.append({
            "name": name,
            "description": f"{name}, based on patterns observed across {rng.randint(3, 7)} sampled sources.",
            "direction": direction,
            "evidence": [{"claim": f"Multiple sources reference {name.lower()}.", "source_idx": rng.randint(0, n_sources - 1)}],
            "affected_companies": [c["name"] for c in rng.sample(competitors, k=min(2, len(competitors)))],
            "business_impact": rng.choice([
                "May compress margins for slower-moving incumbents.",
                "Opens a window for differentiated new entrants.",
                "Likely to raise customer expectations across the category.",
                "Could accelerate consolidation via M&A.",
            ]),
            "source_count": rng.randint(2, 6),
            "confidence": round(rng.uniform(0.45, 0.85), 2),
        })

    # ---- Sentiment (only for company/comparison subjects — mark unavailable for broad markets) ----
    has_sentiment = len(names) <= 6
    sentiment = []
    if has_sentiment:
        for name in names[:3]:
            pos = round(rng.uniform(30, 65), 1)
            neg = round(rng.uniform(10, 35), 1)
            neu = round(100 - pos - neg, 1)
            sentiment.append({
                "subject": name,
                "positive_pct": pos, "negative_pct": neg, "neutral_pct": max(neu, 0),
                "sample_size": rng.randint(40, 400),
                "recurring_themes": rng.sample(
                    ["pricing concerns", "ease of use", "customer support quality",
                     "feature depth", "reliability", "onboarding experience"], k=3),
                "top_complaints": rng.sample(
                    ["Support response times", "Pricing transparency", "Learning curve",
                     "Missing integrations"], k=2),
                "data_available": True,
            })

    # ---- Insights (fact / inference / recommendation) ----
    insights = [
        {"section": "market_overview", "claim_type": "fact",
         "text": f"{n_sources} sources were reviewed covering {query}, spanning market sizing, competitor activity, and recent news.",
         "confidence": 0.9},
        {"section": "market_overview", "claim_type": "inference",
         "text": f"The presence of {len(competitors)} active competitors with distinct positioning suggests a moderately fragmented market rather than a clear monopoly.",
         "confidence": 0.6},
        {"section": "opportunities", "claim_type": "inference",
         "text": "Segments with fewer specialized players may represent lower-competition entry points.",
         "confidence": 0.55},
    ]

    # ---- Recommendations ----
    recommendations = [
        {
            "recommendation": "Differentiate on a specific underserved segment rather than competing broadly.",
            "rationale": "Established players already cover the mainstream segment; a focused wedge is more defensible for a new entrant.",
            "expected_impact": "Faster initial traction, lower CAC in the near term.",
            "risk": "Smaller addressable market if the segment is too narrow.",
            "confidence": 0.6, "priority": 1,
        },
        {
            "recommendation": "Monitor pricing model shifts among leading competitors closely over the next 2 quarters.",
            "rationale": "Multiple sources point to pricing experimentation across the category.",
            "expected_impact": "Avoid being undercut or overpriced relative to the market.",
            "risk": "Reactive pricing changes can erode margin if done too aggressively.",
            "confidence": 0.55, "priority": 2,
        },
        {
            "recommendation": "Track regulatory developments given rising scrutiny signals in the source set.",
            "rationale": "Emerging regulatory trend detected across news sources.",
            "expected_impact": "Reduced compliance risk and better-timed market entry.",
            "risk": "Regulation may be slower-moving or region-specific; low near-term urgency.",
            "confidence": 0.5, "priority": 3,
        },
    ]

    risk_level = rng.choice(RISK_LEVELS)
    overall_confidence = round(rng.uniform(0.55, 0.8), 2)

    return {
        "sources": sources,
        "competitors": competitors,
        "metrics": metrics,
        "trends": trends,
        "sentiment": sentiment,
        "insights": insights,
        "recommendations": recommendations,
        "risk_level": risk_level,
        "overall_confidence": overall_confidence,
    }
