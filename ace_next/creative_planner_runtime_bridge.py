from __future__ import annotations

from typing import Any, Dict

from .creative_planner import build_creative_plan as base_build_creative_plan
from .learning_decision_adapter_v1 import build_learning_decision_adapter_v1
from .distribution_intelligence_v2 import build_distribution_intelligence_v2


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def build_creative_plan(
    *,
    mission_context: dict[str, Any] | None = None,
    performance_context: dict[str, Any] | None = None,
) -> dict[str, Any]:

    mission = _safe_dict(mission_context)
    performance = _safe_dict(performance_context)

    base_plan = _safe_dict(
        base_build_creative_plan(
            mission_context=mission,
            performance_context=performance,
        )
    )

    records = performance.get("records") or []

    learning = _safe_dict(
        build_learning_decision_adapter_v1(
            records=records,
            latest_record=performance.get("latest_record"),
        )
    )

    distribution = _safe_dict(
        build_distribution_intelligence_v2(
            records=records,
        )
    )

    learning_guidance = _safe_dict(
        learning.get("planner_learning_guidance")
    )

    # === APPLY LEARNING ===
    if learning_guidance.get("recommended_hook_family"):
        base_plan["hook_family"] = learning_guidance["recommended_hook_family"]

    if learning_guidance.get("recommended_format_bias"):
        base_plan["publish_format_now"] = learning_guidance[
            "recommended_format_bias"
        ]

    if learning_guidance.get("recommended_timing_bias"):
        base_plan["timing_hypothesis"] = learning_guidance[
            "recommended_timing_bias"
        ]

    if learning_guidance.get("recommended_series_action"):
        base_plan["series_next"] = learning_guidance[
            "recommended_series_action"
        ]

    if learning_guidance.get("recommended_promotion_bias"):
        base_plan["promotion_bias"] = learning_guidance[
            "recommended_promotion_bias"
        ]

    # === APPLY DISTRIBUTION ===
    if distribution.get("recommended_timing_hypothesis"):
        base_plan["timing_hypothesis"] = distribution[
            "recommended_timing_hypothesis"
        ]

    if distribution.get("recommended_format"):
        base_plan["publish_format_now"] = distribution[
            "recommended_format"
        ]

    # === ATTACH CONTEXT ===
    base_plan["learning_layer"] = {
        "confidence": learning.get("confidence"),
        "mode": learning_guidance.get("promotion_mode"),
        "exploration_budget": learning_guidance.get("exploration_budget"),
        "thompson_ready": learning_guidance.get("thompson_ready"),
    }

    base_plan["distribution_context"] = distribution

    base_plan["decision_trace"] = {
        "learning_applied": bool(learning_guidance),
        "distribution_applied": True,
    }

    return {
        "ok": True,
        "module": "creative_planner_runtime_bridge_v2",
        "creative_plan": base_plan,
        "learning": learning,
        "distribution": distribution,
    }
