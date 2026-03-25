from __future__ import annotations

from collections import Counter
from typing import Any

from .experiment_learning_contract import (
    build_learning_bridge_contract,
    derive_experiment_state_machine,
)


def _count_by(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    values = [str(record.get(key) or "unknown") for record in records]
    return dict(Counter(values))


def _source_status(record: dict[str, Any]) -> str:
    real_metrics = dict(record.get("real_metrics") or {})
    return str(real_metrics.get("source_status") or "unknown")


def _evidence_state(record: dict[str, Any]) -> str:
    evidence = dict(record.get("evidence_interpreter") or {})
    return str(evidence.get("evidence_state") or "unknown")


def _resolution_state(record: dict[str, Any]) -> str:
    resolution = dict(record.get("experiment_resolution") or {})
    return str(resolution.get("resolution_state") or "unknown")


def _recommended_action(record: dict[str, Any]) -> str:
    recommendation = dict(record.get("recommendation_engine") or {})
    return str(recommendation.get("recommended_action") or "unknown")


def _experiment_state(record: dict[str, Any]) -> str:
    experiment = dict(record.get("experiment_registry") or {})
    if experiment.get("experiment_state"):
        return str(experiment.get("experiment_state"))
    evidence = dict(record.get("evidence_interpreter") or {})
    resolution = dict(record.get("experiment_resolution") or {})
    publish_result = dict(record.get("publish_result") or {})
    real_metrics = dict(record.get("real_metrics") or {})
    machine = derive_experiment_state_machine(
        operational_state=str(record.get("operational_state") or "internal_lab"),
        evidence_state=str(evidence.get("evidence_state") or "no_receipt"),
        resolution_state=str(resolution.get("resolution_state") or "collecting"),
        publish_result=publish_result,
        evidence_interpreter=evidence,
        real_metrics=real_metrics,
    )
    return str(machine.get("experiment_state") or "unknown")


def build_learning_loop_summary(
    *,
    records: list[dict[str, Any]],
    latest_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    records = list(records or [])
    latest = dict(latest_record or (records[-1] if records else {}))

    operational_state_counts = _count_by(records, "operational_state")
    publish_status_counts = _count_by(records, "publish_status")
    evidence_state_counts = dict(Counter(_evidence_state(record) for record in records))
    resolution_state_counts = dict(Counter(_resolution_state(record) for record in records))
    recommendation_state_counts = dict(Counter(_recommended_action(record) for record in records))
    experiment_state_counts = dict(Counter(_experiment_state(record) for record in records))
    source_status_counts = dict(Counter(_source_status(record) for record in records))

    latest_evidence = dict(latest.get("evidence_interpreter") or {})
    latest_resolution = dict(latest.get("experiment_resolution") or {})
    latest_recommendation = dict(latest.get("recommendation_engine") or {})
    latest_publish_result = dict(latest.get("publish_result") or {})
    latest_real_metrics = dict(latest.get("real_metrics") or {})
    latest_episodic = dict(latest.get("episodic_performance_memory") or {})
    latest_serial_continuity = dict(
        dict(latest.get("creative_plan") or {}).get("serial_continuity")
        or latest.get("serial_continuity")
        or {}
    )
    latest_distribution_context = dict(
        dict(latest.get("creative_plan") or {}).get("distribution_context")
        or latest.get("distribution_context")
        or {}
    )

    latest_machine = derive_experiment_state_machine(
        operational_state=str(latest.get("operational_state") or "internal_lab"),
        evidence_state=str(latest_evidence.get("evidence_state") or "no_receipt"),
        resolution_state=str(latest_resolution.get("resolution_state") or "collecting"),
        publish_result=latest_publish_result,
        evidence_interpreter=latest_evidence,
        real_metrics=latest_real_metrics,
    )
    latest_learning_bridge = build_learning_bridge_contract(
        experiment_state_machine=latest_machine,
        recommendation_engine=latest_recommendation,
        episodic_memory=latest_episodic,
        serial_continuity=latest_serial_continuity,
        distribution_context=latest_distribution_context,
    )

    suggestions: list[str] = []
    if latest_machine.get("reason_for_repeat"):
        suggestions.append(latest_machine["reason_for_repeat"])
    if latest_machine.get("reason_not_resolved"):
        suggestions.append(latest_machine["reason_not_resolved"])
    if latest_serial_continuity.get("next_episode_seed"):
        suggestions.append(f"próximo episódio sugerido: {latest_serial_continuity.get('next_episode_seed')}")
    if not suggestions:
        suggestions.append("o learning loop permanece em modo conservador e auditável")

    return {
        "ok": True,
        "mode": "measurement_core_v2",
        "records_considered": len(records),
        "operational_state_counts": operational_state_counts,
        "publish_status_counts": publish_status_counts,
        "evidence_state_counts": evidence_state_counts,
        "resolution_state_counts": resolution_state_counts,
        "recommendation_state_counts": recommendation_state_counts,
        "experiment_state_counts": experiment_state_counts,
        "real_metrics_source_status_counts": source_status_counts,
        "latest_record_id": latest.get("record_id"),
        "latest_operational_state": latest.get("operational_state"),
        "latest_experiment_state": latest_machine.get("experiment_state"),
        "latest_evidence_state": latest_machine.get("evidence_state"),
        "latest_resolution_state": latest_machine.get("resolution_state"),
        "latest_recommended_action": latest_recommendation.get("recommended_action"),
        "latest_reason_for_repeat": latest_machine.get("reason_for_repeat"),
        "latest_reason_not_resolved": latest_machine.get("reason_not_resolved"),
        "latest_promotion_readiness": latest_machine.get("promotion_readiness"),
        "latest_learning_bridge": latest_learning_bridge,
        "episodic_memory_state": {
            "latest_episode_id": latest_episodic.get("episode_id"),
            "latest_series_name": latest_episodic.get("series_name"),
            "latest_continuity_state": latest_episodic.get("continuity_state"),
            "latest_next_episode_seed": latest_episodic.get("next_episode_seed"),
        },
        "serial_continuity_state": {
            "linked_series_candidate": latest_serial_continuity.get("linked_series_candidate"),
            "continuity_state": latest_serial_continuity.get("continuity_state"),
            "continuity_reason": latest_serial_continuity.get("continuity_reason"),
            "next_episode_seed": latest_serial_continuity.get("next_episode_seed"),
        },
        "distribution_state": {
            "recommended_next_format": latest_distribution_context.get("recommended_next_format"),
            "recommended_next_angle": latest_distribution_context.get("recommended_next_angle"),
            "recommended_next_series_action": latest_distribution_context.get("recommended_next_series_action"),
            "recommended_timing_hypothesis": latest_distribution_context.get("recommended_timing_hypothesis"),
        },
        "insight_control": {
            "can_record": True,
            "can_consolidate": True,
            "can_suggest": True,
            "can_change_brand_policy": False,
            "can_change_editorial_policy": False,
            "can_change_visual_policy": False,
            "can_autopublish_brand_live": False,
        },
        "suggestions": suggestions,
    }
