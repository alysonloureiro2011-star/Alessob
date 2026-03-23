from __future__ import annotations

from typing import Any


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
) -> dict[str, Any]:
    real_metrics = dict(real_metrics_contract or {})
    attention_breakdown = dict(attention_metrics.get("breakdown") or {})
    publish = dict(publish_result or {})
    probe = dict(probe_context or {})

    source_status = str(real_metrics.get("source_status") or "unknown")
    collection_attempted = bool(performance_ingest.get("attempted"))
    collection_success = bool(performance_ingest.get("collection_success"))

    return {
        "ok": True,
        "mode": "measurement_core_v1",
        "probe_state": {
            "requested": bool(probe.get("requested")),
            "requested_state": probe.get("requested_state"),
            "effective_state": probe.get("effective_state"),
            "eligible": bool(probe.get("eligible")),
            "publish_executed": bool(probe.get("publish_executed")),
        },
        "publish_state": {
            "publish_status": publish.get("publish_status"),
            "has_media_id": bool(publish.get("media_id")),
            "has_permalink": bool(publish.get("permalink")),
            "media_id": publish.get("media_id"),
            "permalink": publish.get("permalink"),
            "receipt_id": publish.get("receipt_id"),
            "operational_state": publish.get("operational_state"),
        },
        "ingestion_state": {
            "attempted": collection_attempted,
            "success": collection_success,
            "source_status": source_status,
            "source_reason": real_metrics.get("source_reason"),
        },
        "store_state": {
            "total_records": performance_store.get("total_records"),
            "latest_source_status": performance_store.get("latest_source_status"),
            "latest_probe_publish_executed": performance_store.get("latest_probe_publish_executed"),
        },
        "learning_state": {
            "records_considered": learning_loop.get("records_considered"),
            "latest_real_metrics_status": learning_loop.get("latest_real_metrics_status"),
        },
        "experiment_state": {
            "total_experiments": experiment_registry.get("total_experiments"),
            "experiments_resolved_percent": experiment_registry.get("experiments_resolved_percent"),
            "winner_confidence": experiment_registry.get("winner_confidence"),
        },
        "episodic_memory_state": {
            "memory_reuse_rate": episodic_performance_memory.get("memory_reuse_rate"),
            "learning_validity_score": episodic_performance_memory.get("learning_validity_score"),
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
        "guardrails": {
            "zero_fake_data": True,
            "zero_random": True,
            "brand_live_automation": False,
            "policy_autonomy": False,
        },
    }
