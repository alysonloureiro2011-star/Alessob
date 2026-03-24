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


def _extract_format(record: dict[str, Any]) -> str:
    publish = dict(record.get("publish_result") or record.get("receipt") or {})
    creative_plan = dict(record.get("creative_plan") or {})

    for candidate in [
        publish.get("content_type"),
        creative_plan.get("publish_format_now"),
        creative_plan.get("format_recommendation"),
        creative_plan.get("strategic_target_format"),
    ]:
        if candidate:
            return str(candidate).lower()

    return "unknown"


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


def build_format_hour_matrix(
    *,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    records = list(records or [])
    buckets: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    ignored_records = 0

    for record in records:
        fmt = _extract_format(record)
        hour = _extract_hour(record)
        score = _extract_attention_score(record)

        if fmt == "unknown" or hour is None or score is None:
            ignored_records += 1
            continue

        buckets[fmt][hour].append(score)

    matrix: dict[str, list[dict[str, Any]]] = {}
    best_pairs: list[dict[str, Any]] = []

    for fmt, hour_map in buckets.items():
        rows: list[dict[str, Any]] = []
        for hour, scores in sorted(hour_map.items()):
            avg_score = round(sum(scores) / len(scores), 2)
            row = {
                "hour": hour,
                "records": len(scores),
                "avg_attention_score": avg_score,
            }
            rows.append(row)
            best_pairs.append(
                {
                    "format": fmt,
                    "hour": hour,
                    "records": len(scores),
                    "avg_attention_score": avg_score,
                }
            )
        matrix[fmt] = sorted(rows, key=lambda item: (item["avg_attention_score"], item["records"]), reverse=True)

    best_pairs = sorted(best_pairs, key=lambda item: (item["avg_attention_score"], item["records"]), reverse=True)

    return {
        "ok": True,
        "records_considered": len(records),
        "ignored_records": ignored_records,
        "formats_detected": sorted(matrix.keys()),
        "matrix": matrix,
        "best_pairs": best_pairs[:10],
    }
