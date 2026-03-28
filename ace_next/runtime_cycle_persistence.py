from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .learning_loop_runtime_bridge import build_learning_loop_summary
from .performance_store import PerformanceStore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _record_id(runtime_result: dict[str, Any], publish_result: dict[str, Any]) -> str:
    existing = runtime_result.get("record_id") or publish_result.get("receipt_id")
    if existing:
        return str(existing)
    return f"cycle_{uuid4().hex}"


def _probe_context(runtime_result: dict[str, Any], publish_result: dict[str, Any]) -> dict[str, Any]:
    lab_probe_policy = _safe_dict(runtime_result.get("lab_probe_policy"))
    probe_payload = _safe_dict(publish_result.get("probe"))
    return {
        "requested": bool(lab_probe_policy.get("probe_requested") or runtime_result.get("probe_requested") or probe_payload.get("requested")),
        "requested_state": (
            lab_probe_policy.get("probe_state_requested")
            or probe_payload.get("requested_state")
            or runtime_result.get("authorization_state")
        ),
        "effective_state": (
            lab_probe_policy.get("probe_state_effective")
            or probe_payload.get("effective_state")
            or runtime_result.get("operational_state")
        ),
        "eligible": bool(lab_probe_policy.get("probe_eligible") or probe_payload.get("eligible")),
        "publish_executed": bool(
            lab_probe_policy.get("probe_publish_executed")
            or runtime_result.get("probe_publish_executed")
            or publish_result.get("real_probe_executed")
            or publish_result.get("publish_status") == "published_real_probe"
        ),
        "block_reason": (
            lab_probe_policy.get("probe_block_reason")
            or runtime_result.get("probe_block_reason")
            or probe_payload.get("probe_block_reason")
        ),
    }


def build_runtime_cycle_record(runtime_result: dict[str, Any]) -> dict[str, Any]:
    result = _safe_dict(runtime_result)
    publish_result = _safe_dict(result.get("publish_result"))
    performance_ingest = _safe_dict(result.get("performance_ingest"))
    real_metrics = _safe_dict(result.get("real_metrics_contract") or performance_ingest.get("real_metrics"))
    attention_metrics = _safe_dict(result.get("attention_metrics"))
    evidence_interpreter = _safe_dict(result.get("evidence_interpreter"))
    experiment_resolution = _safe_dict(result.get("experiment_resolution"))
    recommendation_engine = _safe_dict(result.get("recommendation_engine"))
    experiment_registry = _safe_dict(result.get("experiment_registry"))
    episodic_performance_memory = _safe_dict(result.get("episodic_performance_memory"))
    reflection_memory = _safe_dict(result.get("reflection_memory"))
    creative_plan = _safe_dict(result.get("creative_plan"))
    mission_decision = _safe_dict(result.get("mission_decision"))

    distribution_context = _safe_dict(creative_plan.get("distribution_context"))

    return {
        "record_id": _record_id(result, publish_result),
        "created_at": _now_iso(),
        "trend": result.get("trend"),
        "operational_state": result.get("operational_state"),
        "authorization_state": result.get("authorization_state"),
        "surface_mode": result.get("surface_mode"),
        "publish_status": publish_result.get("publish_status"),
        "publish_truth_state": result.get("publish_truth_state"),
        "publish_result": publish_result,
        "receipt": publish_result,
        "performance_ingest": performance_ingest,
        "real_metrics": real_metrics,
        "attention_metrics": attention_metrics,
        "evidence_interpreter": evidence_interpreter,
        "experiment_resolution": experiment_resolution,
        "recommendation_engine": recommendation_engine,
        "experiment_registry": experiment_registry,
        "episodic_performance_memory": episodic_performance_memory,
        "reflection_memory": reflection_memory,
        "probe_context": _probe_context(result, publish_result),
        "creative_plan": {
            "goal": creative_plan.get("goal"),
            "hypothesis": creative_plan.get("hypothesis") or mission_decision.get("hypothesis"),
            "hook": creative_plan.get("hook"),
            "headline": creative_plan.get("headline"),
            "publish_style": creative_plan.get("publish_style"),
            "publish_format_now": creative_plan.get("publish_format_now"),
            "timing_hypothesis": creative_plan.get("timing_hypothesis") or distribution_context.get("recommended_timing_hypothesis"),
            "serial_continuity": _safe_dict(creative_plan.get("serial_continuity")),
            "distribution_context": distribution_context,
        },
        "mission_context": {
            "goal": mission_decision.get("goal"),
            "hypothesis": mission_decision.get("hypothesis"),
            "content_type": mission_decision.get("content_type"),
            "style": mission_decision.get("style"),
            "confidence": mission_decision.get("confidence"),
        },
        "decision_memory_entries": list(result.get("decision_memory_entries") or []),
        "decision_memory_summary": _safe_dict(result.get("decision_memory_summary")),
        "next_cycle_hook_candidate": result.get("next_cycle_hook_candidate"),
    }


def persist_runtime_cycle(config: Any, runtime_result: dict[str, Any]) -> dict[str, Any]:
    result = _safe_dict(runtime_result)
    if not result:
        return {
            "ok": False,
            "persisted": False,
            "error": "runtime_result_empty",
        }

    try:
        store = PerformanceStore(config)
        record = build_runtime_cycle_record(result)
        performance_store_summary = store.upsert_record(record)
        all_records = store.list_records(limit=0)
        learning_loop_summary = build_learning_loop_summary(
            records=all_records,
            latest_record=record,
        )
        return {
            "ok": True,
            "persisted": True,
            "record_id": record.get("record_id"),
            "performance_store": performance_store_summary,
            "learning_loop": learning_loop_summary,
        }
    except Exception as exc:
        return {
            "ok": False,
            "persisted": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
