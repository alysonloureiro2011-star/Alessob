from __future__ import annotations

from typing import Any

EXPERIMENT_STATES = {
    "collecting",
    "repeat_probe",
    "hold",
    "internal_lab",
    "editorial_staging",
    "candidate_for_brand_live",
    "resolved_winner",
    "resolved_loser",
    "blocked_brand",
    "blocked_quality",
}


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def build_evidence_delta(
    *,
    publish_result: dict[str, Any] | None,
    evidence_interpreter: dict[str, Any] | None,
    real_metrics: dict[str, Any] | None,
) -> dict[str, Any]:
    publish = _safe_dict(publish_result)
    evidence = _safe_dict(evidence_interpreter)
    real_metrics = _safe_dict(real_metrics)

    has_receipt = bool(publish.get("receipt_id"))
    has_media_id = bool(publish.get("media_id"))
    evidence_state = _clean(evidence.get("evidence_state") or "no_receipt")
    source_status = _clean(real_metrics.get("source_status") or "not_available_yet")

    if not has_receipt:
        delta_state = "still_without_receipt"
    elif has_receipt and not has_media_id:
        delta_state = "receipt_without_media_id"
    elif has_media_id and source_status not in {"collected", "partial_collected"}:
        delta_state = "media_id_without_sufficient_metrics"
    else:
        delta_state = "metrics_ready_for_resolution"

    return {
        "delta_state": delta_state,
        "has_receipt": has_receipt,
        "has_media_id": has_media_id,
        "evidence_state": evidence_state,
        "source_status": source_status,
    }


def derive_experiment_state_machine(
    *,
    operational_state: str,
    evidence_state: str,
    resolution_state: str,
    publish_result: dict[str, Any] | None = None,
    evidence_interpreter: dict[str, Any] | None = None,
    real_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    delta = build_evidence_delta(
        publish_result=publish_result,
        evidence_interpreter=evidence_interpreter,
        real_metrics=real_metrics,
    )

    if operational_state == "blocked_brand":
        experiment_state = "blocked_brand"
    elif operational_state == "blocked_quality":
        experiment_state = "blocked_quality"
    elif delta["delta_state"] == "still_without_receipt":
        experiment_state = "repeat_probe"
    elif delta["delta_state"] == "receipt_without_media_id":
        experiment_state = "collecting"
    elif delta["delta_state"] == "media_id_without_sufficient_metrics":
        experiment_state = "hold"
    elif resolution_state in {"winner_candidate", "resolved_conservative"} and operational_state == "editorial_staging":
        experiment_state = "candidate_for_brand_live"
    elif resolution_state == "loser_candidate":
        experiment_state = "resolved_loser"
    elif resolution_state == "resolved_winner":
        experiment_state = "resolved_winner"
    elif operational_state == "editorial_staging":
        experiment_state = "editorial_staging"
    else:
        experiment_state = "internal_lab"

    reason_for_repeat = None
    if experiment_state == "repeat_probe":
        reason_for_repeat = "ainda não existe receipt real"
    elif experiment_state == "collecting":
        reason_for_repeat = "há receipt, mas ainda não existe media_id real"
    elif experiment_state == "hold":
        reason_for_repeat = "há media_id real, mas ainda não existem métricas suficientes"

    reason_not_resolved = None
    if experiment_state in {"collecting", "repeat_probe", "hold"}:
        reason_not_resolved = reason_for_repeat
    elif experiment_state == "candidate_for_brand_live":
        reason_not_resolved = "editorial_staging não é vitória final e ainda exige revisão humana"

    promotion_readiness = "not_ready"
    if experiment_state == "editorial_staging":
        promotion_readiness = "staging_only"
    elif experiment_state == "candidate_for_brand_live":
        promotion_readiness = "candidate_under_review"
    elif experiment_state == "resolved_winner":
        promotion_readiness = "winner_resolved_but_not_brand_live"

    return {
        "experiment_state": experiment_state,
        "operational_state": operational_state,
        "evidence_state": evidence_state,
        "resolution_state": resolution_state,
        "promotion_readiness": promotion_readiness,
        "reason_for_repeat": reason_for_repeat,
        "reason_not_resolved": reason_not_resolved,
        "evidence_delta": delta,
    }


def build_learning_bridge_contract(
    *,
    experiment_state_machine: dict[str, Any],
    recommendation_engine: dict[str, Any] | None = None,
    episodic_memory: dict[str, Any] | None = None,
    serial_continuity: dict[str, Any] | None = None,
    distribution_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    recommendation_engine = _safe_dict(recommendation_engine)
    episodic_memory = _safe_dict(episodic_memory)
    serial_continuity = _safe_dict(serial_continuity)
    distribution_context = _safe_dict(distribution_context)
    machine = _safe_dict(experiment_state_machine)

    return {
        "ok": True,
        "experiment_state": machine.get("experiment_state"),
        "operational_state": machine.get("operational_state"),
        "evidence_state": machine.get("evidence_state"),
        "resolution_state": machine.get("resolution_state"),
        "promotion_readiness": machine.get("promotion_readiness"),
        "reason_for_repeat": machine.get("reason_for_repeat"),
        "reason_not_resolved": machine.get("reason_not_resolved"),
        "safe_to_learn": machine.get("experiment_state") not in {"resolved_winner", "resolved_loser"},
        "fake_data_used": False,
        "serial_context_seen": bool(serial_continuity),
        "episodic_memory_seen": bool(episodic_memory),
        "distribution_context_seen": bool(distribution_context),
        "recommended_action": recommendation_engine.get("recommended_action"),
    }
