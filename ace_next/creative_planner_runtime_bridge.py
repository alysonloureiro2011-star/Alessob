from __future__ import annotations

from typing import Any, Dict

from .creative_planner import build_creative_plan as base_build_creative_plan
from .learning_decision_adapter_v1 import build_learning_decision_adapter_v1
from .distribution_intelligence_v2 import build_distribution_intelligence_v2
from .reel_retention_policy import evaluate_reel_retention_policy


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


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
            text = _clean_text(item)
            if text and text not in merged:
                merged.append(text)
    return merged


def _normalize_format(value: Any) -> str:
    normalized = _clean_text(value).lower()
    if normalized in {"story", "stories"}:
        return "story"
    if normalized in {"carousel", "image"}:
        return normalized
    return "image"


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


def _retention_payload_from_plan(plan: dict[str, Any]) -> dict[str, Any]:
    notes = _merge_unique(
        [str(item) for item in _safe_list(plan.get("notes"))],
        [
            "planner_bridge=runtime_compatible",
            "bridge_recomputed_retention=true",
        ],
    )

    return {
        "hook": plan.get("hook"),
        "headline": plan.get("headline"),
        "angle": plan.get("angle"),
        "body": plan.get("body"),
        "cta": plan.get("cta"),
        "support_points": [str(item) for item in _safe_list(plan.get("support_points")) if _clean_text(item)],
        "notes": notes,
        "visual_style": "cinematic_natural_editorial",
        "publish_style": plan.get("publish_style"),
        "color_profile": "cinematic_vertical_premium",
        "publish_format_now": _normalize_format(plan.get("publish_format_now")),
        "strategic_target_format": _normalize_format(
            plan.get("strategic_target_format") or plan.get("publish_format_now")
        ),
        "timing_hypothesis": plan.get("timing_hypothesis"),
    }


def _official_path_quality_state(
    *,
    critic: dict[str, Any],
    retention_policy: dict[str, Any],
) -> str:
    critic = _safe_dict(critic)
    caption_gate = _safe_dict(critic.get("caption_gate"))
    veto_reasons = _safe_list(retention_policy.get("veto_reasons"))
    retention_signal_ready = bool(retention_policy.get("publish_ready"))

    if veto_reasons:
        return "blocked_retention_gate"
    if retention_signal_ready and critic.get("approved") and caption_gate.get("approved"):
        return "approved"
    if critic.get("failed_floors"):
        return "needs_rewrite"
    return "needs_rewrite"


def _recompute_runtime_quality(plan: dict[str, Any]) -> dict[str, Any]:
    updated = dict(plan)

    retention_policy = evaluate_reel_retention_policy(
        _retention_payload_from_plan(updated)
    )
    official_quality_state = _official_path_quality_state(
        critic=_safe_dict(updated.get("critic")),
        retention_policy=retention_policy,
    )
    official_publish_ready = official_quality_state == "approved"
    retention_signal_ready = bool(retention_policy.get("publish_ready"))

    updated["retention_policy"] = retention_policy
    updated["retention_score"] = float(retention_policy.get("premium_eligibility_score") or 0.0)
    updated["premium_eligibility_score"] = float(retention_policy.get("premium_eligibility_score") or 0.0)
    updated["publish_ready"] = official_publish_ready
    updated["official_path_quality_state"] = official_quality_state
    updated["veto_reasons"] = [str(item) for item in _safe_list(retention_policy.get("veto_reasons"))]
    updated["lift_targets"] = [str(item) for item in _safe_list(retention_policy.get("lift_targets"))]
    updated["study_axes_applied"] = [str(item) for item in _safe_list(retention_policy.get("study_axes_applied"))]

    updated["notes"] = _merge_unique(
        [str(item) for item in _safe_list(updated.get("notes"))],
        [
            f"retention_signal_ready={retention_signal_ready}",
            f"official_publish_ready={official_publish_ready}",
            f"official_path_quality_state={official_quality_state}",
            "runtime_bridge_quality_recomputed=true",
        ],
    )

    existing_flags = [str(item) for item in _safe_list(updated.get("fallback_flags"))]
    normalized_flags = [flag for flag in existing_flags if flag not in {"retention_signal_not_ready", "official_quality_not_ready"}]

    if not retention_signal_ready:
        normalized_flags.append("retention_signal_not_ready")
    if not official_publish_ready:
        normalized_flags.append("official_quality_not_ready")

    updated["fallback_flags"] = _merge_unique(normalized_flags)

    return updated


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
        plan["publish_format_now"] = _normalize_format(learning_guidance["recommended_format_bias"])

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
        plan["publish_format_now"] = _normalize_format(distribution["recommended_format"])

    if not _clean_text(plan.get("strategic_target_format")):
        plan["strategic_target_format"] = _normalize_format(plan.get("publish_format_now"))

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
        "runtime_bridge_recomputed_quality": True,
    }

    plan["notes"] = _merge_unique(
        [str(item) for item in _safe_list(plan.get("notes"))],
        [
            "planner_bridge=runtime_compatible",
            f"learning_confidence={learning.get('confidence')}",
            f"distribution_confidence={distribution.get('confidence')}",
        ],
    )

    return _recompute_runtime_quality(plan)


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

    final_plan["planner_bridge_meta"] = {
        "module": "creative_planner_runtime_bridge_v5",
        "learning_confidence": learning.get("confidence"),
        "distribution_confidence": distribution.get("confidence"),
        "runtime_signature_compatible": True,
        "retention_recomputed_after_bridge": True,
    }

    return final_plan
