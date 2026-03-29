⁠from __future__ import annotations

from typing import Any

from .creative_planner import (
    PUBLISH_STYLE,
    SERIES_NAME,
    _build_creative_plan_legacy,
    _map_soberano_to_creative_plan,
)
from .creative_planner_soberano_v1 import build_creative_plan_soberano_v1
from .learning_decision_adapter_v1 import build_learning_decision_adapter_v1


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


def _safe_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _recent_memory_context(recent_memory: list[dict[str, Any]] | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    recent_memory = list(recent_memory or [])[-5:]
    normalized_recent: list[dict[str, Any]] = []

    for item in recent_memory:
        record = _safe_dict(item)
        creative_plan = _safe_dict(record.get("creative_plan"))
        distribution_context = _safe_dict(
            creative_plan.get("distribution_context")
            or record.get("distribution_context")
        )
        real_metrics = _safe_dict(record.get("real_metrics"))
        attention_metrics = _safe_dict(record.get("attention_metrics"))
        recommendation_engine = _safe_dict(record.get("recommendation_engine"))

        normalized_recent.append(
            {
                "trend": record.get("trend"),
                "operational_state": record.get("operational_state"),
                "publish_status": record.get("publish_status"),
                "publish_format_now": creative_plan.get("publish_format_now"),
                "publish_style": creative_plan.get("publish_style"),
                "goal": creative_plan.get("goal"),
                "hook": creative_plan.get("hook"),
                "hook_family": creative_plan.get("hook_family"),
                "headline": creative_plan.get("headline"),
                "timing_hypothesis": creative_plan.get("timing_hypothesis") or distribution_context.get("recommended_timing_hypothesis"),
                "recommended_next_format": distribution_context.get("recommended_next_format"),
                "recommended_next_angle": distribution_context.get("recommended_next_angle"),
                "recommended_next_series_action": distribution_context.get("recommended_next_series_action"),
                "real_metrics": real_metrics,
                "attention_metrics": attention_metrics,
                "recommended_action": recommendation_engine.get("recommended_action"),
            }
        )

    latest = normalized_recent[-1] if normalized_recent else {}
    performance_context = {
        "priority_signals": PRIORITY_SIGNALS,
        "recent_records": normalized_recent,
        "latest_operational_state": latest.get("operational_state"),
        "latest_publish_status": latest.get("publish_status"),
        "latest_recommended_next_format": latest.get("recommended_next_format"),
        "latest_recommended_timing_hypothesis": latest.get("timing_hypothesis"),
        "learning_state": "performance_informed" if normalized_recent else "cold_start",
    }
    return normalized_recent, performance_context


def _apply_learning_bias(
    overrides: dict[str, Any] | None,
    adapter_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    enriched = dict(overrides or {})
    adapter_payload = _safe_dict(adapter_payload)
    guidance = _safe_dict(adapter_payload.get("planner_learning_guidance"))

    if not adapter_payload.get("safe_to_apply"):
        return enriched

    if not enriched.get("publish_format_now") and guidance.get("recommended_format_bias"):
        enriched["publish_format_now"] = guidance.get("recommended_format_bias")

    if not enriched.get("timing_hypothesis") and guidance.get("recommended_timing_bias"):
        enriched["timing_hypothesis"] = guidance.get("recommended_timing_bias")

    if guidance.get("recommended_hook_family"):
        enriched["_learning_recommended_hook_family"] = guidance.get("recommended_hook_family")

    if guidance.get("recommended_hook_reference"):
        enriched["_learning_recommended_hook_reference"] = guidance.get("recommended_hook_reference")

    if guidance.get("recommended_series_action"):
        enriched["_learning_recommended_series_action"] = guidance.get("recommended_series_action")

    if guidance.get("forbidden_traits"):
        enriched["_learning_forbidden_traits"] = list(guidance.get("forbidden_traits") or [])

    enriched["_learning_confidence"] = guidance.get("confidence")
    enriched["_learning_exploration_budget"] = guidance.get("exploration_budget")

    return enriched


def _signal_context(
    mission_decision: dict[str, Any] | None,
    recent_memory: list[dict[str, Any]] | None,
    learning_adapter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mission_decision = _safe_dict(mission_decision)
    learning_adapter = _safe_dict(learning_adapter)
    recent_records, performance_context = _recent_memory_context(recent_memory)

    return {
        "source": "creative_planner_runtime_bridge_v2",
        "mission_context": {
            "goal": mission_decision.get("goal"),
            "hypothesis": mission_decision.get("hypothesis"),
            "content_type": mission_decision.get("content_type"),
            "priority": mission_decision.get("priority"),
            "confidence": mission_decision.get("confidence"),
        },
        "recent_content": recent_records,
        "performance_context": performance_context,
        "learning_adapter": learning_adapter,
        "study_tags": {
            "hook_opening": "0_3s",
            "pattern_interrupt": "3_5s",
            "priority_signals": PRIORITY_SIGNALS,
            "naturalism": "micro_expression_breathing_grain",
            "cinematic": "9x16_rule_of_thirds_bokeh_color_foley_ducking",
            "learning_to_planner": "active_adapter_v1",
        },
    }


def _brand_context(
    overrides: dict[str, Any] | None,
    mission_decision: dict[str, Any] | None,
) -> dict[str, Any]:
    overrides = dict(overrides or {})
    mission_decision = _safe_dict(mission_decision)
    return {
        "series_name": SERIES_NAME,
        "surface": "instagram_reels",
        "account": "@libertaverdades",
        "publish_style": overrides.get("publish_style") or PUBLISH_STYLE,
        "preferred_content_type": overrides.get("publish_format_now") or mission_decision.get("content_type"),
        "goal": overrides.get("goal") or mission_decision.get("goal"),
    }


def build_creative_plan(
    trend: str,
    overrides: dict[str, Any] | None = None,
    mission_decision: dict[str, Any] | None = None,
    recent_memory: list[dict[str, Any]] | None = None,
):
    overrides = dict(overrides or {})
    mission_decision = _safe_dict(mission_decision)
    recent_memory = list(recent_memory or [])

    learning_adapter = build_learning_decision_adapter_v1(
        records=recent_memory,
        latest_record=recent_memory[-1] if recent_memory else None,
    )
    enriched_overrides = _apply_learning_bias(overrides, learning_adapter)

    format_hint = (
        enriched_overrides.get("publish_format_now")
        or mission_decision.get("content_type")
        or None
    )

    signal_context = _signal_context(
        mission_decision,
        recent_memory,
        learning_adapter=learning_adapter,
    )
    brand_context = _brand_context(enriched_overrides, mission_decision)

    try:
        sovereign = build_creative_plan_soberano_v1(
            topic_seed=trend,
            signal_context=signal_context,
            brand_context=brand_context,
            format_hint=format_hint,
        )
        mapped = _map_soberano_to_creative_plan(
            trend,
            sovereign,
            overrides=enriched_overrides,
            mission_decision=mission_decision,
            recent_memory=recent_memory,
        )

        mapped.notes.append("runtime_signal_context_wired=true")
        mapped.notes.append(f"recent_memory_records={len(recent_memory)}")
        mapped.notes.append("planner_bridge=creative_planner_runtime_bridge_v2")
        mapped.notes.append(f"learning_adapter_safe_to_apply={str(bool(learning_adapter.get('safe_to_apply'))).lower()}")
        mapped.notes.append(f"learning_adapter_confidence={_text(learning_adapter.get('confidence'))}")

        guidance = _safe_dict(learning_adapter.get("planner_learning_guidance"))
        if guidance.get("recommended_format_bias"):
            mapped.notes.append(f"learning_recommended_format={guidance.get('recommended_format_bias')}")
        if guidance.get("recommended_timing_bias"):
            mapped.notes.append(f"learning_recommended_timing={guidance.get('recommended_timing_bias')}")
        if guidance.get("recommended_hook_family"):
            mapped.notes.append(f"learning_recommended_hook_family={guidance.get('recommended_hook_family')}")

        mapped.mission_context = {
            **dict(mapped.mission_context or {}),
            "signal_context_wired": True,
            "performance_informed": bool(recent_memory),
            "learning_adapter_wired": True,
            "learning_adapter_confidence": learning_adapter.get("confidence"),
        }
        return mapped

    except Exception as exc:
        legacy = _build_creative_plan_legacy(
            trend,
            overrides=enriched_overrides,
            mission_decision=mission_decision,
            recent_memory=recent_memory,
        )
        legacy.notes.append(f"planner_bridge_fail={type(exc).__name__}")
        legacy.notes.append("planner_bridge=creative_planner_runtime_bridge_v2")
        legacy.notes.append("learning_adapter_present=true")

        fallback_flags = list(legacy.fallback_flags or [])
        if "legacy_fallback" not in fallback_flags:
            fallback_flags.append("legacy_fallback")
        if "planner_bridge_fail" not in fallback_flags:
            fallback_flags.append("planner_bridge_fail")
        if "learning_adapter_present" not in fallback_flags:
            fallback_flags.append("learning_adapter_present")
        legacy.fallback_flags = fallback_flags
        return legacy
