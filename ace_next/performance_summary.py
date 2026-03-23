from __future__ import annotations

from typing import Any


def _derive_probe_block_reason(
    *,
    probe_requested: bool,
    probe_eligible: bool,
    probe_render_executed: bool,
    probe_publish_executed: bool,
    probe_receipt_created: bool,
) -> str | None:
    if not probe_requested:
        return None
    if not probe_eligible:
        return "probe_not_eligible_for_state"
    if probe_render_executed and not probe_publish_executed and not probe_receipt_created:
        return "probe_rendered_publish_not_completed"
    if not probe_render_executed and not probe_publish_executed and not probe_receipt_created:
        return "probe_not_executed"
    return None


def _derive_evidence_bridge_state(
    *,
    has_real_receipt: bool,
    has_media_id: bool,
    has_permalink: bool,
    latest_source_status: str | None,
    latest_probe_publish_executed: bool,
    probe_requested: bool,
) -> str:
    if latest_source_status in {"collected", "partial_collected"} and has_media_id:
        return "real_metrics_ready"
    if has_real_receipt and has_media_id and has_permalink:
        return "receipt_with_permalink"
    if has_real_receipt and has_media_id:
        return "receipt_with_media_id"
    if has_real_receipt:
        return "receipt_linked"
    if probe_requested:
        return "probe_requested_without_receipt"
    return "no_receipt"


def build_performance_summary(
    *,
    performance_store: dict[str, Any],
    learning_loop: dict[str, Any],
    experiment_registry: dict[str, Any],
    episodic_performance_memory: dict[str, Any],
    attention_metrics: dict[str, Any],
    real_metrics_contract: dict[str, Any] | None,
    performance_ingest: dict[str, Any],
    publish_result: dict[str, Any] | None,
    reflection_memory: dict[str, Any],
    probe_context: dict[str, Any] | None,
    resonance_engine: dict[str, Any],
    reward_prediction: dict[str, Any],
    thompson_sampler: dict[str, Any],
    decision_core_summary: dict[str, Any],
    evidence_interpreter: dict[str, Any],
    experiment_resolution: dict[str, Any],
    recommendation_engine: dict[str, Any],
    wave10_summary: dict[str, Any],
    wave11_summary: dict[str, Any],
) -> dict[str, Any]:
    real_metrics = dict(real_metrics_contract or {})
    attention_breakdown = dict(attention_metrics.get("breakdown") or {})
    publish = dict(publish_result or {})
    probe = dict(probe_context or {})

    source_status = str(real_metrics.get("source_status") or "unknown")
    collection_attempted = bool(performance_ingest.get("attempted"))
    collection_success = bool(performance_ingest.get("collection_success"))

    has_real_receipt = bool(publish.get("receipt_id"))
    has_media_id = bool(publish.get("media_id"))
    has_permalink = bool(publish.get("permalink"))

    probe_requested = bool(probe.get("requested"))
    probe_state_requested = probe.get("requested_state")
    probe_state_effective = probe.get("effective_state")
    probe_eligible = bool(probe.get("eligible"))
    probe_render_executed = bool(probe.get("render_executed"))
    probe_publish_executed = bool(probe.get("publish_executed"))
    probe_receipt_created = has_real_receipt
    probe_block_reason = _derive_probe_block_reason(
        probe_requested=probe_requested,
        probe_eligible=probe_eligible,
        probe_render_executed=probe_render_executed,
        probe_publish_executed=probe_publish_executed,
        probe_receipt_created=probe_receipt_created,
    )

    store_latest_source_status = performance_store.get("latest_source_status")
    store_latest_probe_publish_executed = performance_store.get("latest_probe_publish_executed")
    latest_source_status = store_latest_source_status if store_latest_source_status is not None else source_status
    latest_probe_publish_executed = (
        store_latest_probe_publish_executed
        if store_latest_probe_publish_executed is not None
        else probe_publish_executed
    )
    latest_real_metrics_status = (
        performance_store.get("latest_real_metrics_status")
        or latest_source_status
    )

    evidence_bridge_state = {
        "has_real_receipt": has_real_receipt,
        "has_media_id": has_media_id,
        "has_permalink": has_permalink,
        "latest_probe_publish_executed": latest_probe_publish_executed,
        "latest_real_metrics_status": latest_real_metrics_status,
        "latest_source_status": latest_source_status,
        "evidence_bridge_state": _derive_evidence_bridge_state(
            has_real_receipt=has_real_receipt,
            has_media_id=has_media_id,
            has_permalink=has_permalink,
            latest_source_status=latest_source_status,
            latest_probe_publish_executed=bool(latest_probe_publish_executed),
            probe_requested=probe_requested,
        ),
    }

    return {
        "ok": True,
        "mode": "measurement_core_v1",
        "probe_summary": {
            "probe_requested": probe_requested,
            "probe_state_requested": probe_state_requested,
            "probe_state_effective": probe_state_effective,
            "probe_eligible": probe_eligible,
            "probe_render_executed": probe_render_executed,
            "probe_publish_executed": probe_publish_executed,
            "probe_receipt_created": probe_receipt_created,
            "probe_block_reason": probe_block_reason,
        },
        "publish_state": {
            "publish_status": publish.get("publish_status"),
            "has_real_receipt": has_real_receipt,
            "has_media_id": has_media_id,
            "has_permalink": has_permalink,
            "receipt_id": publish.get("receipt_id"),
            "media_id": publish.get("media_id"),
            "permalink": publish.get("permalink"),
            "content_type": publish.get("content_type"),
            "style": publish.get("style"),
            "operational_state": publish.get("operational_state"),
            "created_at": publish.get("created_at"),
        },
        "publish_receipt_bridge": {
            "publish_status": publish.get("publish_status"),
            "receipt_id": publish.get("receipt_id"),
            "media_id": publish.get("media_id"),
            "permalink": publish.get("permalink"),
            "content_type": publish.get("content_type"),
            "style": publish.get("style"),
            "created_at": publish.get("created_at"),
        },
        "ingestion_state": {
            "attempted": collection_attempted,
            "success": collection_success,
            "source_status": source_status,
            "source_reason": real_metrics.get("source_reason"),
        },
        "evidence_bridge_state": evidence_bridge_state,
        "decision_core_state": {
            "resonance_score": resonance_engine.get("resonance_score"),
            "reward_prediction_score": reward_prediction.get("reward_prediction_score"),
            "selected_variant": thompson_sampler.get("selected_variant"),
            "confidence_level": thompson_sampler.get("confidence_level"),
            "experiment_decision_state": thompson_sampler.get("decision_state"),
            "posterior_mean": thompson_sampler.get("posterior_mean"),
            "winner_candidate": thompson_sampler.get("winner_candidate"),
            "summary": decision_core_summary,
        },
        "evidence_interpreter": evidence_interpreter,
        "experiment_resolution": experiment_resolution,
        "recommendation_engine": recommendation_engine,
        "evidence_interpretation_state": {
            "evidence_state": evidence_interpreter.get("evidence_state"),
            "evidence_strength": evidence_interpreter.get("evidence_strength"),
            "evidence_ready_for_resolution": evidence_interpreter.get("evidence_ready_for_resolution"),
        },
        "experiment_resolution_state": {
            "resolution_state": experiment_resolution.get("resolution_state"),
            "can_resolve": experiment_resolution.get("can_resolve"),
            "promotion_readiness": experiment_resolution.get("promotion_readiness"),
            "keep_collecting": experiment_resolution.get("keep_collecting"),
        },
        "recommendation_state": {
            "recommended_action": recommendation_engine.get("recommended_action"),
            "next_best_step": recommendation_engine.get("next_best_step"),
            "requires_human_review": recommendation_engine.get("requires_human_review"),
        },
        "store_state": {
            "total_records": performance_store.get("total_records"),
            "latest_source_status": performance_store.get("latest_source_status"),
            "latest_real_metrics_status": performance_store.get("latest_real_metrics_status"),
            "latest_probe_publish_executed": performance_store.get("latest_probe_publish_executed"),
            "latest_media_id": performance_store.get("latest_media_id"),
            "latest_permalink": performance_store.get("latest_permalink"),
        },
        "learning_state": {
            "records_considered": learning_loop.get("records_considered"),
            "latest_real_metrics_status": learning_loop.get("latest_real_metrics_status"),
            "latest_evidence_state": learning_loop.get("latest_evidence_state"),
            "latest_resolution_state": learning_loop.get("latest_resolution_state"),
            "latest_recommended_action": learning_loop.get("latest_recommended_action"),
        },
        "experiment_state": {
            "total_experiments": experiment_registry.get("total_experiments"),
            "experiments_resolved_percent": experiment_registry.get("experiments_resolved_percent"),
            "winner_confidence": experiment_registry.get("winner_confidence"),
        },
        "episodic_memory_state": {
            "memory_reuse_rate": episodic_performance_memory.get("memory_reuse_rate"),
            "learning_validity_score": episodic_performance_memory.get("learning_validity_score"),
            "episodes_with_receipt": episodic_performance_memory.get("episodes_with_receipt"),
            "episodes_with_media_id": episodic_performance_memory.get("episodes_with_media_id"),
            "episodes_with_permalink": episodic_performance_memory.get("episodes_with_permalink"),
            "latest_evidence_state": episodic_performance_memory.get("latest_evidence_state"),
            "latest_resolution_state": episodic_performance_memory.get("latest_resolution_state"),
            "latest_recommendation_state": episodic_performance_memory.get("latest_recommendation_state"),
        },
        "attention_state": {
            "source_status": attention_metrics.get("source_status"),
            "attention_score": attention_breakdown.get("attention_score"),
            "view_rate": attention_breakdown.get("view_rate"),
            "completion_proxy": attention_breakdown.get("completion_proxy"),
        },
        "reflection_state": {
            "status": reflection_memory.get("status"),
            "notes": reflection_memory.get("notes"),
        },
        "wave10_summary": wave10_summary,
        "wave11_summary": wave11_summary,
        "guardrails": {
            "zero_fake_data": True,
            "zero_random": True,
            "brand_live_automation": False,
            "policy_autonomy": False,
        },
    }
