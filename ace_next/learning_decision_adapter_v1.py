from __future__ import annotations

from collections import defaultdict
from typing import Any

from .learning_loop import build_learning_loop_summary


PRIORITY_SIGNALS = (
    "share_rate",
    "save_rate",
    "completion_rate",
    "retention_rate",
    "watch_time_ms",
    "replay_rate",
)

BLOCKING_EXPERIMENT_STATES = {
    "repeat_probe",
    "collecting",
    "hold",
    "blocked_brand",
    "blocked_quality",
}

MIN_EVIDENCE_TO_APPLY = 3
MIN_EVIDENCE_HIGH_CONFIDENCE = 5


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

    return {
        "share_rate": _float(
            real_metrics.get("share_rate") or attention_metrics.get("share_rate")
        ),
        "save_rate": _float(
            real_metrics.get("save_rate") or attention_metrics.get("save_rate")
        ),
        "completion_rate": _float(
            real_metrics.get("completion_rate")
            or attention_metrics.get("completion_rate")
        ),
        "retention_rate": _float(
            real_metrics.get("retention_rate") or attention_metrics.get("retention_rate")
        ),
        "watch_time_ms": _float(
            real_metrics.get("watch_time_ms") or attention_metrics.get("watch_time_ms")
        ),
        "replay_rate": _float(
            real_metrics.get("replay_rate") or attention_metrics.get("replay_rate")
        ),
    }


def _normalize_watch_time(watch_time_ms: float) -> float:
    return min(max(watch_time_ms, 0.0) / 10000.0, 1.0)


def _score_metrics(metrics: dict[str, float]) -> float:
    return round(
        (metrics["share_rate"] * 0.28)
        + (metrics["save_rate"] * 0.22)
        + (metrics["completion_rate"] * 0.18)
        + (metrics["retention_rate"] * 0.14)
        + (metrics["replay_rate"] * 0.10)
        + (_normalize_watch_time(metrics["watch_time_ms"]) * 0.08),
        4,
    )


def _extract_plan_features(record: dict[str, Any]) -> dict[str, str]:
    plan = _safe_dict(record.get("creative_plan"))
    serial = _safe_dict(plan.get("serial_continuity"))
    distribution = _safe_dict(plan.get("distribution_context"))

    return {
        "hook": _text(plan.get("hook")),
        "hook_family": _text(plan.get("hook_family")),
        "format": _text(
            plan.get("publish_format_now") or plan.get("format_recommendation")
        ),
        "style": _text(plan.get("publish_style")),
        "angle": _text(plan.get("angle")),
        "cta": _text(plan.get("cta")),
        "timing_hypothesis": _text(
            plan.get("timing_hypothesis")
            or distribution.get("recommended_timing_hypothesis")
        ),
        "promotion_bias": _text(
            distribution.get("promotion_bias")
            or distribution.get("recommended_promotion_bias")
        ),
        "series_action": _text(
            distribution.get("recommended_next_series_action")
            or serial.get("next_episode_seed")
        ),
        "series_name": _text(plan.get("series_name")),
    }


def _aggregate_feature_scores(
    records: list[dict[str, Any]],
    feature_key: str,
) -> dict[str, dict[str, float]]:
    bucket: dict[str, dict[str, float]] = defaultdict(
        lambda: {"count": 0.0, "total_score": 0.0}
    )

    for record in records:
        features = _extract_plan_features(record)
        value = _text(features.get(feature_key))
        if not value:
            continue
        score = _score_metrics(_extract_metrics(record))
        bucket[value]["count"] += 1
        bucket[value]["total_score"] += score

    result: dict[str, dict[str, float]] = {}
    for key, payload in bucket.items():
        count = int(payload["count"])
        avg_score = round(payload["total_score"] / max(count, 1), 4)
        result[key] = {
            "count": count,
            "avg_score": avg_score,
        }
    return result


def _best_feature(
    records: list[dict[str, Any]],
    feature_key: str,
) -> dict[str, Any]:
    aggregated = _aggregate_feature_scores(records, feature_key)
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


def _worst_traits(records: list[dict[str, Any]]) -> list[str]:
    forbidden: list[str] = []

    for feature_key in (
        "hook_family",
        "format",
        "style",
        "angle",
        "cta",
        "timing_hypothesis",
    ):
        aggregated = _aggregate_feature_scores(records, feature_key)
        if not aggregated:
            continue

        ranked = sorted(
            aggregated.items(),
            key=lambda item: (item[1]["avg_score"], -item[1]["count"]),
        )

        worst_value, worst_payload = ranked[0]
        if worst_payload["count"] >= 2 and worst_payload["avg_score"] <= 0.18:
            forbidden.append(f"{feature_key}:{worst_value}")

    return forbidden


def _latest_plan_snapshot(latest_record: dict[str, Any]) -> dict[str, str]:
    return _extract_plan_features(latest_record)


def _exploration_budget(records_count: int, confidence: str) -> str:
    if records_count < 3:
        return "high"
    if confidence == "low":
        return "medium"
    return "low"


def _promotion_mode(
    *,
    confidence: str,
    latest_experiment_state: str,
    best_format: dict[str, Any],
) -> str:
    if latest_experiment_state in BLOCKING_EXPERIMENT_STATES:
        return "hold"
    if confidence == "high" and best_format["value"]:
        return "promote_winner"
    if confidence == "medium":
        return "guided_exploration"
    return "observe"


def _thompson_ready(
    *,
    records_count: int,
    confidence: str,
    latest_experiment_state: str,
) -> bool:
    return (
        records_count >= MIN_EVIDENCE_TO_APPLY
        and confidence in {"medium", "high"}
        and latest_experiment_state not in BLOCKING_EXPERIMENT_STATES
    )


def _build_reasoning_trace(
    *,
    summary: dict[str, Any],
    best_hook_family: dict[str, Any],
    best_format: dict[str, Any],
    best_timing: dict[str, Any],
    best_series_action: dict[str, Any],
    best_promotion_bias: dict[str, Any],
) -> list[str]:
    trace = [
        f"latest_experiment_state={_text(summary.get('latest_experiment_state'))}",
        f"latest_recommended_action={_text(summary.get('latest_recommended_action'))}",
    ]

    if best_hook_family["value"]:
        trace.append(
            f"best_hook_family={best_hook_family['value']}|score={best_hook_family['avg_score']}|n={best_hook_family['count']}"
        )
    if best_format["value"]:
        trace.append(
            f"best_format={best_format['value']}|score={best_format['avg_score']}|n={best_format['count']}"
        )
    if best_timing["value"]:
        trace.append(
            f"best_timing={best_timing['value']}|score={best_timing['avg_score']}|n={best_timing['count']}"
        )
    if best_series_action["value"]:
        trace.append(
            f"best_series_action={best_series_action['value']}|score={best_series_action['avg_score']}|n={best_series_action['count']}"
        )
    if best_promotion_bias["value"]:
        trace.append(
            f"best_promotion_bias={best_promotion_bias['value']}|score={best_promotion_bias['avg_score']}|n={best_promotion_bias['count']}"
        )

    return trace


def build_learning_decision_adapter_v1(
    *,
    records: list[dict[str, Any]],
    latest_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    records = [_safe_dict(item) for item in _safe_list(records)]
    latest = _safe_dict(latest_record or (records[-1] if records else {}))
    summary = build_learning_loop_summary(records=records, latest_record=latest)

    latest_experiment_state = _text(summary.get("latest_experiment_state"))
    latest_learning_bridge = _safe_dict(summary.get("latest_learning_bridge"))

    best_hook_family = _best_feature(records, "hook_family")
    best_format = _best_feature(records, "format")
    best_timing = _best_feature(records, "timing_hypothesis")
    best_series_action = _best_feature(records, "series_action")
    best_promotion_bias = _best_feature(records, "promotion_bias")

    latest_snapshot = _latest_plan_snapshot(latest)
    forbidden_traits = _worst_traits(records)

    safe_to_apply = (
        latest_experiment_state not in BLOCKING_EXPERIMENT_STATES and bool(records)
    )

    if safe_to_apply and len(records) >= MIN_EVIDENCE_HIGH_CONFIDENCE:
        confidence = "high"
    elif safe_to_apply and len(records) >= MIN_EVIDENCE_TO_APPLY:
        confidence = "medium"
    else:
        confidence = "low"

    exploration_budget = _exploration_budget(len(records), confidence)
    promotion_mode = _promotion_mode(
        confidence=confidence,
        latest_experiment_state=latest_experiment_state,
        best_format=best_format,
    )
    thompson_ready = _thompson_ready(
        records_count=len(records),
        confidence=confidence,
        latest_experiment_state=latest_experiment_state,
    )

    planner_learning_guidance = {
        "recommended_hook_family": best_hook_family["value"]
        or latest_snapshot.get("hook_family")
        or "",
        "recommended_hook_reference": latest_snapshot.get("hook") or "",
        "recommended_format_bias": best_format["value"]
        or latest_snapshot.get("format")
        or "",
        "recommended_timing_bias": best_timing["value"]
        or latest_snapshot.get("timing_hypothesis")
        or "",
        "recommended_series_action": best_series_action["value"]
        or latest_snapshot.get("series_action")
        or "",
        "recommended_promotion_bias": best_promotion_bias["value"]
        or latest_snapshot.get("promotion_bias")
        or "",
        "forbidden_traits": forbidden_traits,
        "exploration_budget": exploration_budget,
        "promotion_mode": promotion_mode,
        "thompson_ready": thompson_ready,
        "confidence": confidence,
        "priority_signals": list(PRIORITY_SIGNALS),
    }

    reasons: list[str] = []
    if not records:
        reasons.append("não há histórico suficiente para orientar o planner")
    if latest_experiment_state in BLOCKING_EXPERIMENT_STATES:
        reasons.append(
            f"estado experimental ainda conservador: {latest_experiment_state}"
        )
    if safe_to_apply:
        reasons.append(
            "adapter pronto para orientar planner e promoção sem alterar política soberana"
        )
    if latest_learning_bridge.get("recommended_action"):
        reasons.append(
            f"recommended_action={latest_learning_bridge.get('recommended_action')}"
        )
    if thompson_ready:
        reasons.append("learning já pode preparar sinal para exploração guiada")

    return {
        "ok": True,
        "module": "learning_decision_adapter_v1",
        "records_considered": len(records),
        "safe_to_apply": safe_to_apply,
        "confidence": confidence,
        "planner_learning_guidance": planner_learning_guidance,
        "latest_plan_snapshot": latest_snapshot,
        "reasoning_trace": _build_reasoning_trace(
            summary=summary,
            best_hook_family=best_hook_family,
            best_format=best_format,
            best_timing=best_timing,
            best_series_action=best_series_action,
            best_promotion_bias=best_promotion_bias,
        ),
        "reasons": reasons,
        "summary": summary,
        "guardrails": {
            "can_record": True,
            "can_consolidate": True,
            "can_suggest": True,
            "can_change_brand_policy": False,
            "can_change_editorial_policy": False,
            "can_change_visual_policy": False,
            "can_autopublish_brand_live": False,
            "requires_existing_runtime": True,
            "requires_existing_planner": True,
        },
    }
