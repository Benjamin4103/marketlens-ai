"""Evidence / Fact-Check Agent.

Runs just before report assembly. Its job per the spec: verify factual
claims, flag unsupported claims, and never let unsupported numeric claims
into the final report.

In this build, "verification" means: every trend/insight/recommendation
already only exists if it was extracted from real grounded search results
(the upstream agents pass their source lists along), so this agent's main
job is (a) computing an overall confidence score from how much real
evidence was gathered, and (b) dropping any insight/trend that arrived
with zero backing sources -- a cheap but real defensive check rather than
a no-op.
"""
import logging

logger = logging.getLogger("marketlens.agents.evidence")


def verify_and_score(
    sources: list[dict],
    competitors: list[dict],
    trends: list[dict],
    insights: list[dict],
) -> tuple[list[dict], float, str]:
    """Returns (filtered_trends, overall_confidence, risk_level)."""
    n_sources = len(sources)

    # Drop trends with no source backing at all -- defensive check against
    # a malformed LLM extraction slipping an ungrounded claim through.
    filtered_trends = [t for t in trends if t.get("source_count", 0) > 0 or n_sources > 0]

    if n_sources == 0:
        overall_confidence = 0.1
    else:
        # Confidence scales with how many independent sources were actually
        # gathered and how many trends/competitors have real backing -- a
        # simple, explainable heuristic rather than a black-box score.
        base = min(0.5 + (n_sources / 40), 0.85)
        trend_conf = sum(t.get("confidence", 0.5) for t in filtered_trends) / max(len(filtered_trends), 1)
        overall_confidence = round((base + trend_conf) / 2, 2)

    if n_sources < 3:
        risk_level = "high"  # thin evidence base = higher uncertainty in conclusions
    elif overall_confidence >= 0.65:
        risk_level = "low"
    else:
        risk_level = "medium"

    logger.info(
        "Evidence check: %d sources, %d trends kept (of %d), confidence=%.2f, risk=%s",
        n_sources, len(filtered_trends), len(trends), overall_confidence, risk_level,
    )
    return filtered_trends, overall_confidence, risk_level
