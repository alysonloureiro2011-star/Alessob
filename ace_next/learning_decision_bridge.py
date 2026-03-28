from __future__ import annotations

from typing import Any

from .learning_loop import build_learning_loop_summary

PRIORITY_SIGNALS = [
    "share_rate",
    "save_rate",
    "completion_rate",
    "retention_rate",
    "watch_time_ms",
    "replay_rate",
]


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _extract_real_metrics(record: dict[str, Any]) -> dict[str, float]:
    real_metrics = _safe_dict(record.get("real_metrics"))
    attention_metrics = _safe_dict(record.get("attention_metrics"))
    return {
        "share_rate": _safe_float(real_metrics.get("share_rate") or attention_metrics.get("share_rate")),
        "save_rate": _safe_float(real_metrics.get("save_rate") or attention_metrics.get("save_rate")),
        "completion_rate": _safe_float(real_metrics.get("completion_rate") or attention_metrics.get("completion_rate")),
        "retention_rate": _safe_float(real_metrics.get("retention_rate") or attention_metrics.get("retention_rate")),
        "watch_time_ms": _safe_float(real_metrics.get("watch_time_ms") or attention_metrics.get("watch_time_ms")),
        "replay_rate": _safe_float(real_metrics.get("replay_rate") or attention_metrics.get("replay_rate")),
    }


def _latest_plan(record: dict[str, Any]) -> dict[str, Any]:
    return _safe_dict(record.get("creative_plan"))


def _score_record(record: dict[str, Any]) -> float:
    metrics = _extract_real_metrics(record)
    return round(
        metrics["share_rate"] * 0.24
        + metrics["save_rate"] * 0.22
        + metrics["completion_rate"] * 0.22
        + metrics["retention_rate"] * 0.16
        + metrics["replay_rate"] * 0.10
        + min(metrics["watch_time_ms"] / 10000.0, 1.0) * 0.06,
        4,
    )


def _best_record(records: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = []
    for record in records:
        current = _safe_dict(record)
        ranked.append((current, _score_record(current)))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[0][0] if ranked else {}


def _decision_from_best_record(best_record: dict[str, Any], latest_record: dict[str, Any]) -> dict[str, Any]:
    best_plan = _latest_plan(best_record)
    latest_plan = _latest_plan(latest_record)
    best_distribution = _safe_dict(best_plan.get("distribution_context"))

    next_format = (
        best_distribution.get("recommended_next_format")
        or best_plan.get("publish_format_now")
        or latest_plan.get("publish_format_now")
        or "reel"
    )
    next_timing = (
        best_distribution.get("recommended_timing_hypothesis")
        or best_plan.get("timing_hypothesis")
        or latest_plan.get("timing_hypothesis")
        or "timing_not_defined"
    )
    next_angle = (
        best_distribution.get("recommended_next_angle")
        or best_plan.get("angle")
        or latest_plan.get("angle")
        or "clarity_tension_payoff"
    )
    next_hook = best_plan.get("hook") or latest_plan.get("hook") or "hook_not_defined"
    next_series_action = (
        best_distribution.get("recommended_next_series_action")
        or _safe_dict(best_plan.get("serial_continuity")).get("next_episode_seed")
        or "maintain_series_continuity"
    )

    return {
        "next_format": next_format,
        "next_timing_hypothesis": next_timing,
        "next_angle": next_angle,
        "next_hook_reference": next_hook,
        "next_series_action": next_series_action,
    }


def build_learning_decision_bridge(
    *,
    records: list[dict[str, Any]],
    latest_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    records = [_safe_dict(record) for record in _safe_list(records)]
    latest_record = _safe_dict(latest_record or (records[-1] if records else {}))
    summary = build_learning_loop_summary(records=records, latest_record=latest_record)

    best_record = _best_record(records)
    best_metrics = _extract_real_metrics(best_record)
    decision = _decision_from_best_record(best_record, latest_record)

    learning_ready = bool(best_record) and summary.get("latest_experiment_state") not in {"repeat_probe", "collecting"}
    confidence = "high" if learning_ready and _score_record(best_record) >= 0.35 else "low"

    reasons: list[str] = []
    if not best_record:
        reasons.append("sem histórico suficiente para direcionar próxima decisão")
    if summary.get("latest_experiment_state") in {"repeat_probe", "collecting"}:
        reasons.append("ciclo mais recente ainda não tem evidência estável")
    if learning_ready:
        reasons.append("bridge prioriza share/save/completion/retention sobre métricas de vaidade")

    return {
        "ok": True,
        "bridge": "learning_decision_bridge_v1",
        "priority_signals": list(PRIORITY_SIGNALS),
        "learning_ready": learning_ready,
        "confidence": confidence,
        "decision": decision,
        "best_record_id": best_record.get("record_id"),
        "best_metrics": best_metrics,
        "best_score": _score_record(best_record) if best_record else 0.0,
        "latest_experiment_state": summary.get("latest_experiment_state"),
        "latest_recommended_action": summary.get("latest_recommended_action"),
        "reasons": reasons,
        "summary": summary,
    }
