from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _parse_hour(value: Any) -> int | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        return int(dt.hour)
    except Exception:
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


def _extract_hour(record: dict[str, Any]) -> int | None:
    publish = dict(record.get("publish_result") or record.get("receipt") or {})
    for candidate in [
        publish.get("created_at"),
        record.get("created_at"),
    ]:
        hour = _parse_hour(candidate)
        if hour is not None:
            return hour
    return None


def build_timing_optimizer(
    *,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    records = list(records or [])

    hour_buckets: dict[int, list[float]] = defaultdict(list)
    ignored_records = 0

    for record in records:
        hour = _extract_hour(record)
        score = _extract_attention_score(record)

        if hour is None or score is None:
            ignored_records += 1
            continue

        hour_buckets[hour].append(score)

    hour_scores: list[dict[str, Any]] = []
    for hour, scores in sorted(hour_buckets.items()):
        avg_score = round(sum(scores) / len(scores), 2)
        hour_scores.append(
            {
                "hour": hour,
                "records": len(scores),
                "avg_attention_score": avg_score,
            }
        )

    if not hour_scores:
        return {
            "ok": True,
            "best_hour": None,
            "confidence": 0.0,
            "records_considered": len(records),
            "records_used": 0,
            "ignored_records": ignored_records,
            "hour_rank": [],
            "reason": "histórico insuficiente para otimização de horário",
        }

    ranked = sorted(
        hour_scores,
        key=lambda item: (item["avg_attention_score"], item["records"]),
        reverse=True,
    )

    best = ranked[0]
    runner_up = ranked[1] if len(ranked) > 1 else None

    confidence = 0.55
    if runner_up:
        delta = max(best["avg_attention_score"] - runner_up["avg_attention_score"], 0.0)
        confidence = min(0.95, round(0.55 + (delta / 100.0) + min(best["records"], 10) * 0.02, 2))
    else:
        confidence = min(0.85, round(0.55 + min(best["records"], 10) * 0.02, 2))

    return {
        "ok": True,
        "best_hour": best["hour"],
        "confidence": confidence,
        "records_considered": len(records),
        "records_used": sum(item["records"] for item in hour_scores),
        "ignored_records": ignored_records,
        "hour_rank": ranked,
        "reason": "melhor horário calculado com base no histórico de atenção disponível",
    }
