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
) -> dict[str, Any]:
    real_metrics = dict(real_metrics_contract or {})
    attention_breakdown = dict(attention_metrics.get("breakdown") or {})
    return {
        "ok": True,
        "mode": "measurement_core_v1",
        "store_state": {
            "total_records": performance_store.get("total_records"),
            "latest_source_status": performance_store.get("latest_source_status"),
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
        "real_metrics_state": {
            "source_status": real_metrics.get("source_status"),
            "available_metrics": real_metrics.get("available_metrics"),
        },
        "guardrails": {
            "zero_fake_data": True,
            "zero_random": True,
            "brand_live_automation": False,
            "policy_autonomy": False,
        },
    }
