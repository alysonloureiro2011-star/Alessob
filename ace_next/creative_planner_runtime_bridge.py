from __future__ import annotations

from typing import Any, Dict

from .creative_planner import build_creative_plan as base_build_creative_plan
from .learning_decision_adapter_v1 import build_learning_decision_adapter_v1
from .distribution_intelligence_v2 import build_distribution_intelligence_v2


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _unwrap_plan(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        if isinstance(value.get("creative_plan"), dict):
            return dict(value["creative_plan"])
        return dict(value)
    if hasattr(value, "to_dict"):
        try:
            parsed = value.to_dict()
            if isinstance(parsed, dict):
                return dict(parsed)
        except Exception:
            return {}
    return {}


def _merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in group:
            text = " ".join(str(item or "").strip().split())
            if text and text not in merged:
                merged.append(text)
    return merged


def _performance_context_from_legacy(
    *,
    trend: str,
    mission_decision: dict[str, Any],
    recent_memory: list[dict[str, Any]],
) -> Dict[str, Any]:
    latest_record = _safe_dict(recent_memory[-1]) if recent_memory else {}
    return {
        "trend": trend,
        "records": recent_memory,
        "latest_record": latest_record,
        "mission_decision": mission_decision,
    }


def _apply_learning_and_distribution(
    *,
    base_plan: dict[str, Any],
    learning: dict[str, Any],
    distribution: dict[str, Any],
) -> dict[str, Any]:
    plan = dict(base_plan)
    learning_guidance = _safe_dict(learning.get("planner_learning_guidance"))

    if learning_guidance.get("recommended_hook_family"):
        plan["hook_family"] = learning_guidance["recommended_hook_family"]

    if learning_guidance.get("recommended_format_bias"):
        plan["publish_format_now"] = learning_guidance["recommended_format_bias"]

    if learning_guidance.get("recommended_timing_bias"):
        plan["timing_hypothesis"] = learning_guidance["recommended_timing_bias"]

    if learning_guidance.get("recommended_series_action"):
        serial = _safe_dict(plan.get("serial_continuity"))
        serial["next_episode_seed"] = learning_guidance["recommended_series_action"]
        plan["serial_continuity"] = serial
        plan["series_next"] = learning_guidance["recommended_series_action"]

    if learning_guidance.get("recommended_promotion_bias"):
        plan["promotion_bias"] = learning_guidance["recommended_promotion_bias"]

    if distribution.get("recommended_timing_hypothesis"):
        plan["timing_hypothesis"] = distribution["recommended_timing_hypothesis"]

    if distribution.get("recommended_format"):
        plan["publish_format_now"] = distribution["recommended_format"]

    existing_distribution = _safe_dict(plan.get("distribution_context"))
    merged_distribution = {
        **existing_distribution,
        **distribution,
    }
    plan["distribution_context"] = merged_distribution

    plan["learning_layer"] = {
        "confidence": learning.get("confidence"),
        "mode": learning_guidance.get("promotion_mode"),
        "exploration_budget": learning_guidance.get("exploration_budget"),
        "thompson_ready": learning_guidance.get("thompson_ready"),
    }

    existing_trace = _safe_dict(plan.get("decision_trace"))
    plan["decision_trace"] = {
        **existing_trace,
        "learning_applied": bool(learning_guidance),
        "distribution_applied": bool(distribution),
    }

    plan["notes"] = _merge_unique(
        _safe_list(plan.get("notes")),
        [
            "planner_bridge=runtime_compatible",
            f"learning_confidence={learning.get('confidence')}",
            f"distribution_confidence={distribution.get('confidence')}",
        ],
    )

    return plan


def build_creative_plan(
    trend: str,
    overrides: dict[str, Any] | None = None,
    mission_decision: dict[str, Any] | None = None,
    recent_memory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    overrides = _safe_dict(overrides)
    mission_decision = _safe_dict(mission_decision)
    recent_memory = _safe_list(recent_memory)

    base_plan = _unwrap_plan(
        base_build_creative_plan(
            trend,
            overrides=overrides,
            mission_decision=mission_decision,
            recent_memory=recent_memory,
        )
    )

    performance_context = _performance_context_from_legacy(
        trend=trend,
        mission_decision=mission_decision,
        recent_memory=recent_memory,
    )

    learning = _safe_dict(
        build_learning_decision_adapter_v1(
            records=_safe_list(performance_context.get("records")),
            latest_record=performance_context.get("latest_record"),
        )
    )

    distribution = _safe_dict(
        build_distribution_intelligence_v2(
            records=_safe_list(performance_context.get("records")),
        )
    )

    final_plan = _apply_learning_and_distribution(
        base_plan=base_plan,
        learning=learning,
        distribution=distribution,
    )

    return {
        "ok": True,
        "module": "creative_planner_runtime_bridge_v3",
        "creative_plan": final_plan,
        "learning": learning,
        "distribution": distribution,
        "compatibility": {
            "runtime_signature_compatible": True,
            "accepts_trend_overrides_mission_recent_memory": True,
        },
    }
