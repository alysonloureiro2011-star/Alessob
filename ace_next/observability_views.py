from __future__ import annotations

from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return None


def _pick(d: Any, key: str, default: Any = None) -> Any:
    if isinstance(d, dict):
        return d.get(key, default)
    return default


def _compact_publish_result(payload: dict[str, Any]) -> dict[str, Any]:
    publish_result = _safe_dict(_pick(payload, "publish_result"))
    return {
        "publish_status": _pick(publish_result, "publish_status"),
        "content_type": _pick(publish_result, "content_type"),
        "style": _pick(publish_result, "style"),
        "created_at": _pick(publish_result, "created_at"),
        "surface_mode": _pick(publish_result, "surface_mode"),
        "main_surface_allowed": _pick(publish_result, "main_surface_allowed"),
        "probe_requested": _pick(publish_result, "probe_requested"),
        "probe_eligible": _pick(publish_result, "probe_eligible"),
        "probe_publish_executed": _pick(publish_result, "probe_publish_executed"),
        "probe_block_reason": _pick(publish_result, "probe_block_reason"),
    }


def _compact_runtime(payload: dict[str, Any]) -> dict[str, Any]:
    runtime = _safe_dict(_pick(payload, "runtime"))
    return {
        "timestamp": _pick(runtime, "timestamp"),
        "render_url": _pick(runtime, "render_url"),
        "enable_real_publish": _pick(runtime, "enable_real_publish"),
        "brand_surface_mode": _pick(runtime, "brand_surface_mode"),
        "brand_live_allowed": _pick(runtime, "brand_live_allowed"),
        "real_probe_route_supported": _pick(runtime, "real_probe_route_supported"),
        "real_probe_allowed_states": _pick(runtime, "real_probe_allowed_states"),
        "token_present": _pick(runtime, "token_present"),
        "ig_id_present": _pick(runtime, "ig_id_present"),
        "measurement_stack_import_error": _pick(runtime, "measurement_stack_import_error"),
        "authorization_stack_import_error": _pick(runtime, "authorization_stack_import_error"),
    }


def build_mission_debug_view(payload: dict[str, Any]) -> dict[str, Any]:
    payload = _safe_dict(payload)
    decision = _safe_dict(_pick(payload, "mission_decision"))
    mission_state = _safe_dict(_pick(payload, "mission_control_state"))

    return {
        "ok": True,
        "decision_present": bool(decision),
        "decision_state": _pick(decision, "decision_state"),
        "should_act": _safe_bool(_pick(decision, "should_act")),
        "reason": _pick(decision, "reason"),
        "goal": _pick(decision, "goal"),
        "content_type": _pick(decision, "content_type"),
        "priority": _safe_float(_pick(decision, "priority")),
        "confidence": _safe_float(_pick(decision, "confidence")),
        "api_budget_mode": _pick(decision, "api_budget_mode"),
        "planner_selected": _pick(decision, "planner_selected"),
        "guardrails": _safe_dict(_pick(decision, "guardrails")),
        "approval_required": _safe_bool(_pick(mission_state, "approval_required")),
        "blocked": _safe_bool(_pick(mission_state, "blocked")),
    }


def build_perf_view(payload: dict[str, Any]) -> dict[str, Any]:
    payload = _safe_dict(payload)
    publish_result = _safe_dict(_pick(payload, "publish_result"))
    evidence_interpreter = _safe_dict(_pick(payload, "evidence_interpreter"))
    experiment_resolution = _safe_dict(_pick(payload, "experiment_resolution"))
    recommendation_engine = _safe_dict(_pick(payload, "recommendation_engine"))
    attention_metrics = _safe_dict(_pick(payload, "attention_metrics"))
    resonance_engine = _safe_dict(_pick(payload, "resonance_engine"))
    reward_prediction = _safe_dict(_pick(payload, "reward_prediction"))
    thompson_sampler = _safe_dict(_pick(payload, "thompson_sampler"))

    attention_breakdown = _safe_dict(_pick(attention_metrics, "breakdown"))

    return {
        "ok": True,
        "performance_summary_present": bool(_safe_dict(_pick(payload, "performance_summary"))),
        "publish_status": _pick(publish_result, "publish_status"),
        "evidence_state": _pick(evidence_interpreter, "evidence_state"),
        "resolution_state": _pick(experiment_resolution, "resolution_state"),
        "recommended_action": _pick(recommendation_engine, "recommended_action"),
        "attention_score": _safe_float(_pick(attention_breakdown, "attention_score")),
        "resonance_score": _safe_float(_pick(resonance_engine, "resonance_score")),
        "reward_prediction_score": _safe_float(_pick(reward_prediction, "reward_prediction_score")),
        "selected_variant": _pick(thompson_sampler, "selected_variant"),
        "confidence_level": _pick(thompson_sampler, "confidence_level"),
        "winner_candidate": _safe_bool(_pick(thompson_sampler, "winner_candidate")),
    }


def build_analytics_view(payload: dict[str, Any]) -> dict[str, Any]:
    payload = _safe_dict(payload)
    evidence_interpreter = _safe_dict(_pick(payload, "evidence_interpreter"))
    experiment_resolution = _safe_dict(_pick(payload, "experiment_resolution"))
    recommendation_engine = _safe_dict(_pick(payload, "recommendation_engine"))

    return {
        "ok": True,
        "publish_result": _compact_publish_result(payload),
        "mission": build_mission_debug_view(payload),
        "performance": build_perf_view(payload),
        "evidence": {
            "evidence_state": _pick(evidence_interpreter, "evidence_state"),
            "evidence_strength": _pick(evidence_interpreter, "evidence_strength"),
            "evidence_ready_for_resolution": _safe_bool(_pick(evidence_interpreter, "evidence_ready_for_resolution")),
            "bridge_state": _pick(evidence_interpreter, "bridge_state"),
        },
        "recommendation": {
            "recommended_action": _pick(recommendation_engine, "recommended_action"),
            "action_priority": _pick(recommendation_engine, "action_priority"),
            "recommendation_reason": _pick(recommendation_engine, "recommendation_reason"),
            "next_best_step": _pick(recommendation_engine, "next_best_step"),
            "safe_to_repeat": _safe_bool(_pick(recommendation_engine, "safe_to_repeat")),
            "safe_to_promote_to_editorial_staging": _safe_bool(
                _pick(recommendation_engine, "safe_to_promote_to_editorial_staging")
            ),
            "requires_human_review": _safe_bool(_pick(recommendation_engine, "requires_human_review")),
        },
        "runtime": _compact_runtime(payload),
    }


def build_llm_debug_view(orchestrator_status: dict[str, Any]) -> dict[str, Any]:
    orchestrator_status = _safe_dict(orchestrator_status)
    return {
        "ok": True,
        "provider_mode": _pick(orchestrator_status, "default_provider_mode"),
        "openai_enabled": _safe_bool(_pick(orchestrator_status, "openai_enabled")),
        "gemini_enabled": _safe_bool(_pick(orchestrator_status, "gemini_enabled")),
        "openai_model": _pick(orchestrator_status, "openai_model"),
        "gemini_model": _pick(orchestrator_status, "gemini_model"),
    }


def build_observability_bundle(
    payload: dict[str, Any],
    orchestrator_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bundle = {
        "ok": True,
        "mission": build_mission_debug_view(payload),
        "perf": build_perf_view(payload),
        "analytics": build_analytics_view(payload),
    }
    if orchestrator_status is not None:
        bundle["llm"] = build_llm_debug_view(orchestrator_status)
    return bundle
