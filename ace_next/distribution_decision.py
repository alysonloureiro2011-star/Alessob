from __future__ import annotations

from collections import defaultdict
from typing import Any

from ace_next.format_hour_matrix import build_format_hour_matrix
from ace_next.timing_optimizer import build_timing_optimizer


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _extract_topic(record: dict[str, Any]) -> str | None:
    creative_plan = dict(record.get("creative_plan") or {})
    for candidate in [
        creative_plan.get("topic_seed"),
        record.get("trend"),
    ]:
        if candidate:
            return str(candidate).strip().lower()
    return None


def _extract_attention_score(record: dict[str, Any]) -> float | None:
    attention = dict(record.get("attention_metrics") or {})
    breakdown = dict(attention.get("breakdown") or {})
    score = _safe_float(breakdown.get("attention_score"))
    if score is not None:
        return score

    real_metrics = dict(record.get("real_metrics") or {})
    engagement_proxy = _safe_float(real_metrics.get("engagement_proxy"))
    if engagement_proxy is not None:
        return round(engagement_proxy * 100.0, 2)

    return None


def _topic_analysis(records: list[dict[str, Any]]) -> dict[str, Any]:
    topic_scores: dict[str, list[float]] = defaultdict(list)

    for record in records:
        topic = _extract_topic(record)
        score = _extract_attention_score(record)
        if topic and score is not None:
            topic_scores[topic].append(score)

    ranked_topics: list[dict[str, Any]] = []
    for topic, scores in topic_scores.items():
        avg_score = round(sum(scores) / len(scores), 2)
        ranked_topics.append(
            {
                "topic": topic,
                "records": len(scores),
                "avg_attention_score": avg_score,
            }
        )

    ranked_topics = sorted(
        ranked_topics,
        key=lambda item: (item["avg_attention_score"], item["records"]),
        reverse=True,
    )

    repeat_topic = ranked_topics[0]["topic"] if ranked_topics else None
    avoid_topic = ranked_topics[-1]["topic"] if len(ranked_topics) >= 2 else None

    return {
        "ok": True,
        "ranked_topics": ranked_topics,
        "repeat_topic": repeat_topic,
        "avoid_topic": avoid_topic,
    }


def build_distribution_decision(
    *,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    records = list(records or [])

    timing = build_timing_optimizer(records=records)
    matrix = build_format_hour_matrix(records=records)
    topics = _topic_analysis(records)

    best_pair = matrix["best_pairs"][0] if matrix.get("best_pairs") else None
    best_hour = timing.get("best_hour")
    suggested_format = best_pair["format"] if best_pair else None

    records_with_signal = 0
    for record in records:
        if _extract_attention_score(record) is not None:
            records_with_signal += 1

    should_post = records_with_signal >= 3 and best_hour is not None and suggested_format is not None

    if should_post:
        reason = "histórico indica melhor combinação de horário e formato"
        priority = "high" if (timing.get("confidence") or 0) >= 0.7 else "medium"
    else:
        reason = "histórico ainda insuficiente para decisão forte de distribuição"
        priority = "low"

    return {
        "ok": True,
        "should_post": should_post,
        "hour": best_hour,
        "format": suggested_format,
        "reason": reason,
        "priority": priority,
        "confidence": timing.get("confidence", 0.0),
        "repeat_topic": topics.get("repeat_topic"),
        "avoid_topic": topics.get("avoid_topic"),
        "timing_optimizer": timing,
        "format_hour_matrix": matrix,
        "topic_analysis": topics,
        "distribution_scope": "decision_only_no_publish_side_effect",
        "guardrails": {
            "changes_runtime": False,
            "changes_publish_engine": False,
            "uses_threads": False,
            "uses_new_dependencies": False,
        },
    }
