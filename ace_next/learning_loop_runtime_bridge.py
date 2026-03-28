from __future__ import annotations

from typing import Any

from .learning_loop import build_learning_loop_summary as base_build_learning_loop_summary


PRIORITY_SIGNALS = [
    "save_rate",
    "share_rate",
    "completion_rate",
    "retention_rate",
    "watch_time_ms",
    "replay_rate",
]


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _first_non_null(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _priority_metric_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    record = _safe_dict(record)
    real_metrics = _safe_dict(record.get("real_metrics"))
    performance_ingest = _safe_dict(record.get("performance_ingest"))
    ingest_real_metrics = _safe_dict(performance_ingest.get("real_metrics"))
    attention_metrics = _safe_dict(record.get("attention_metrics"))
    attention_breakdown = _safe_dict(attention_metrics.get("breakdown"))

    source_status = str(
        _first_non_null(
            real_metrics.get("source_status"),
            ingest_real_metrics.get("source_status"),
            attention_metrics.get("source_status"),
            "unknown",
        )
    )

    return {
        "source_status": source_status,
        "save_rate": _first_non_null(real_metrics.get("save_rate"), ingest_real_metrics.get("save_rate"), attention_breakdown.get("save_rate")),
        "share_rate": _first_non_null(real_metrics.get("share_rate"), ingest_real_metrics.get("share_rate"), attention_breakdown.get("share_rate")),
        "completion_rate": _first_non_null(real_metrics.get("completion_rate"), ingest_real_metrics.get("completion_rate"), attention_breakdown.get("completion_rate")),
        "retention_rate": _first_non_null(real_metrics.get("retention_rate"), ingest_real_metrics.get("retention_rate"), attention_breakdown.get("retention_rate")),
        "watch_time_ms": _first_non_null(real_metrics.get("watch_time_ms"), ingest_real_metrics.get("watch_time_ms"), attention_breakdown.get("watch_time_ms")),
        "replay_rate": _first_non_null(real_metrics.get("replay_rate"), ingest_real_metrics.get("replay_rate"), attention_breakdown.get("replay_rate")),
        "attention_score": attention_breakdown.get("attention_score"),
    }


def _decision_inputs_ready(snapshot: dict[str, Any]) -> bool:
    source_status = str(snapshot.get("source_status") or "unknown")
    if source_status in {"collected", "partial_collected"}:
        return True
    return any(snapshot.get(signal) is not None for signal in PRIORITY_SIGNALS)


def _decision_levers(record: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    record = _safe_dict(record)
    creative_plan = _safe_dict(record.get("creative_plan"))
    distribution_context = _safe_dict(
        creative_plan.get("distribution_context")
        or record.get("distribution_context")
    )
    decision_memory_summary = _safe_dict(record.get("decision_memory_summary"))
    recommendation_engine = _safe_dict(record.get("recommendation_engine"))
    ready = _decision_inputs_ready(snapshot)

    base_state = "data_ready" if ready else "collecting"

    return {
        "hook": {
            "state": base_state,
            "candidate": record.get("next_cycle_hook_candidate") or decision_memory_summary.get("next_cycle_hook_candidate") or creative_plan.get("hook"),
            "reason": recommendation_engine.get("recommended_action") or "collecting_priority_signals",
        },
        "format": {
            "state": base_state,
            "candidate": distribution_context.get("recommended_next_format") or creative_plan.get("publish_format_now"),
            "reason": distribution_context.get("recommended_next_series_action") or recommendation_engine.get("recommended_action") or "collecting_priority_signals",
        },
        "style": {
            "state": base_state,
            "candidate": creative_plan.get("publish_style"),
            "reason": creative_plan.get("hypothesis") or recommendation_engine.get("recommendation_reason") or "collecting_priority_signals",
        },
        "timing": {
            "state": base_state,
            "candidate": distribution_context.get("recommended_timing_hypothesis") or creative_plan.get("timing_hypothesis"),
            "reason": distribution_context.get("recommended_next_series_action") or "collecting_priority_signals",
        },
    }


def build_learning_loop_summary(
    *,
    records: list[dict[str, Any]],
    latest_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = base_build_learning_loop_summary(records=records, latest_record=latest_record)
    latest = dict(latest_record or (records[-1] if records else {}))
    snapshot = _priority_metric_snapshot(latest)
    summary["priority_metric_snapshot"] = snapshot
    summary["decision_inputs_ready"] = _decision_inputs_ready(snapshot)
    summary["signals_priority"] = PRIORITY_SIGNALS
    summary["decision_levers"] = _decision_levers(latest, snapshot)
    summary["learning_mode"] = "performance_driven_when_metrics_exist"
    return summary
