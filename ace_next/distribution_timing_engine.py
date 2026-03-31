from __future__ import annotations

from collections import defaultdict
from typing import Any


PRIORITY_SIGNALS = (
    "share_rate",
    "save_rate",
    "completion_rate",
    "retention_rate",
    "replay_rate",
)


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _extract_metrics(record: dict[str, Any]) -> dict[str, float]:
    real_metrics = _safe_dict(record.get("real_metrics"))
    attention_metrics = _safe_dict(record.get("attention_metrics"))
    breakdown = _safe_dict(attention_metrics.get("breakdown"))

    return {
        "share_rate": _float(real_metrics.get("share_rate") or breakdown.get("share_rate")),
        "save_rate": _float(real_metrics.get("save_rate") or breakdown.get("save_rate")),
        "completion_rate": _float(real_metrics.get("completion_rate") or breakdown.get("completion_rate")),
        "retention_rate": _float(real_metrics.get("retention_rate") or breakdown.get("retention_rate")),
        "replay_rate": _float(real_metrics.get("replay_rate") or breakdown.get("replay_rate")),
    }


def _score_metrics(metrics: dict[str, float]) -> float:
    return round(
        (metrics["share_rate"] * 0.30)
        + (metrics["save_rate"] * 0.25)
        + (metrics["completion_rate"] * 0.18)
        + (metrics["retention_rate"] * 0.17)
        + (metrics["replay_rate"] * 0.10),
        4,
    )


def _timing_from_record(record: dict[str, Any]) -> str:
    creative_plan = _safe_dict(record.get("creative_plan"))
    distribution_context = _safe_dict(creative_plan.get("distribution_context"))
    return _text(
        distribution_context.get("recommended_timing_hypothesis")
        or creative_plan.get("timing_hypothesis")
        or record.get("timing_hypothesis")
    )


def _format_from_record(record: dict[str, Any]) -> str:
    creative_plan = _safe_dict(record.get("creative_plan"))
    return _text(
        creative_plan.get("publish_format_now")
        or creative_plan.get("format_recommendation")
        or record.get("content_type")
    )


def _style_from_record(record: dict[str, Any]) -> str:
    creative_plan = _safe_dict(record.get("creative_plan"))
    return _text(
        creative_plan.get("publish_style")
        or creative_plan.get("style")
    )


def _aggregate(records: list[dict[str, Any]], key_fn) -> dict[str, dict[str, float]]:
    bucket: dict[str, dict[str, float]] = defaultdict(
        lambda: {"count": 0.0, "total_score": 0.0}
    )

    for record in records:
        key = _text(key_fn(record))
        if not key:
            continue
        score = _score_metrics(_extract_metrics(record))
        bucket[key]["count"] += 1
        bucket[key]["total_score"] += score

    result: dict[str, dict[str, float]] = {}
    for key, payload in bucket.items():
        count = int(payload["count"])
        avg_score = round(payload["total_score"] / max(count, 1), 4)
        result[key] = {
            "count": count,
            "avg_score": avg_score,
        }
    return result


def _best_candidate(aggregated: dict[str, dict[str, float]]) -> dict[str, Any]:
    if not aggregated:
        return {"value": "", "count": 0, "avg_score": 0.0}

    ranked = sorted(
        aggregated.items(),
        key=lambda item: (item[1]["avg_score"], item[1]["count"]),
        reverse=True,
    )
    value, payload = ranked[0]
    return {
        "value": value,
        "count": payload["count"],
        "avg_score": payload["avg_score"],
    }


def build_distribution_timing_engine(
    *,
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    records = [_safe_dict(item) for item in _safe_list(records)]

    timing_map = _aggregate(records, _timing_from_record)
    format_map = _aggregate(records, _format_from_record)
    style_map = _aggregate(records, _style_from_record)

    best_timing = _best_candidate(timing_map)
    best_format = _best_candidate(format_map)
    best_style = _best_candidate(style_map)

    evidence_count = len(records)

    if evidence_count >= 7:
        confidence = "high"
    elif evidence_count >= 4:
        confidence = "medium"
    else:
        confidence = "low"

    mode = (
        "exploit"
        if confidence == "high"
        else "guided_exploration"
        if confidence == "medium"
        else "conservative_exploration"
    )

    return {
        "ok": True,
        "module": "distribution_timing_engine_v1",
        "records_considered": evidence_count,
        "confidence": confidence,
        "distribution_mode": mode,
        "recommended_timing_hypothesis": best_timing["value"],
        "recommended_next_format": best_format["value"],
        "recommended_style_bias": best_style["value"],
        "timing_candidate": best_timing,
        "format_candidate": best_format,
        "style_candidate": best_style,
        "priority_signals": list(PRIORITY_SIGNALS),
        "study_alignment": {
            "distribution_timing_engine": True,
            "attention_priority": True,
            "instagram_first": True,
            "multiplatform_ready": True,
        },
        "notes": [
            f"records={evidence_count}",
            f"confidence={confidence}",
            f"mode={mode}",
            f"best_timing={best_timing['value']}",
            f"best_format={best_format['value']}",
            f"best_style={best_style['value']}",
        ],
    }
