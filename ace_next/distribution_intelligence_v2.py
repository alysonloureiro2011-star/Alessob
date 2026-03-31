from __future__ import annotations

from typing import Any, Dict


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _score_signal(metrics: dict[str, float]) -> float:
    return round(
        (metrics.get("share_rate", 0) * 0.3)
        + (metrics.get("save_rate", 0) * 0.25)
        + (metrics.get("completion_rate", 0) * 0.2)
        + (metrics.get("retention_rate", 0) * 0.15)
        + (metrics.get("replay_rate", 0) * 0.1),
        4,
    )


def _extract_metrics(record: dict[str, Any]) -> dict[str, float]:
    real = _safe_dict(record.get("real_metrics"))
    return {
        "share_rate": float(real.get("share_rate", 0)),
        "save_rate": float(real.get("save_rate", 0)),
        "completion_rate": float(real.get("completion_rate", 0)),
        "retention_rate": float(real.get("retention_rate", 0)),
        "replay_rate": float(real.get("replay_rate", 0)),
    }


def _best_timing(records: list[dict[str, Any]]) -> str:
    timing_scores: dict[str, list[float]] = {}

    for r in records:
        plan = _safe_dict(r.get("creative_plan"))
        timing = _text(plan.get("timing_hypothesis"))
        if not timing:
            continue

        score = _score_signal(_extract_metrics(r))
        timing_scores.setdefault(timing, []).append(score)

    best = ""
    best_score = 0

    for t, scores in timing_scores.items():
        avg = sum(scores) / len(scores)
        if avg > best_score:
            best = t
            best_score = avg

    return best


def _best_format(records: list[dict[str, Any]]) -> str:
    format_scores: dict[str, list[float]] = {}

    for r in records:
        plan = _safe_dict(r.get("creative_plan"))
        fmt = _text(plan.get("publish_format_now"))
        if not fmt:
            continue

        score = _score_signal(_extract_metrics(r))
        format_scores.setdefault(fmt, []).append(score)

    best = ""
    best_score = 0

    for f, scores in format_scores.items():
        avg = sum(scores) / len(scores)
        if avg > best_score:
            best = f
            best_score = avg

    return best


def build_distribution_intelligence_v2(
    *,
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    records = records or []

    best_timing = _best_timing(records)
    best_format = _best_format(records)

    confidence = "low"
    if len(records) >= 5:
        confidence = "high"
    elif len(records) >= 3:
        confidence = "medium"

    return {
        "ok": True,
        "module": "distribution_intelligence_v2",
        "records": len(records),
        "recommended_timing_hypothesis": best_timing,
        "recommended_format": best_format,
        "confidence": confidence,
        "distribution_mode": (
            "exploit"
            if confidence == "high"
            else "balanced"
            if confidence == "medium"
            else "explore"
        ),
        "notes": [
            f"records={len(records)}",
            f"best_timing={best_timing}",
            f"best_format={best_format}",
            f"confidence={confidence}",
        ],
        "study_alignment": {
            "timing_optimization": True,
            "format_bias_learning": True,
            "distribution_intelligence": True,
        },
    }
