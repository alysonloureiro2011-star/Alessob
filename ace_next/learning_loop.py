from __future__ import annotations

from collections import Counter
from typing import Any


def _count_by(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    values = [str(record.get(key) or "unknown") for record in records]
    return dict(Counter(values))


def _source_status(record: dict[str, Any]) -> str:
    real_metrics = dict(record.get("real_metrics") or {})
    return str(real_metrics.get("source_status") or "unknown")


def _ingestion_state(source_status: str) -> str:
    if source_status in {"collected", "partial_collected"}:
        return "real_data_collected"
    if source_status in {"collection_error", "missing_token"}:
        return "collection_error"
    return "no_real_data_yet"


def build_learning_loop_summary(
    *,
    records: list[dict[str, Any]],
    latest_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    records = list(records or [])
    latest = dict(latest_record or (records[-1] if records else {}))

    states = _count_by(records, "operational_state")
    publish_status = _count_by(records, "publish_status")
    evidence_status = _count_by(records, "evidence_status")

    source_status_values = [_source_status(record) for record in records]
    real_metrics_source_status_counts = dict(Counter(source_status_values))
    ingestion_state_counts = dict(Counter(_ingestion_state(status) for status in source_status_values))

    linked_with_receipt = sum(1 for record in records if record.get("receipt"))
    latest_real_metrics = dict(latest.get("real_metrics") or {})
    latest_reflection = dict(latest.get("reflection_memory") or {})
    latest_attention = dict(latest.get("attention_metrics") or {})
    latest_experiment = dict(latest.get("experiment_registry") or {})
    latest_episode = dict(latest.get("episodic_performance_memory") or {})

    attention_count = sum(
        1
        for record in records
        if ((record.get("attention_metrics") or {}).get("breakdown") or {}).get("attention_score") is not None
    )
    experiment_status_counts = dict(
        Counter(str((record.get("experiment_registry") or {}).get("status") or "unknown") for record in records)
    )
    resolved_experiments = experiment_status_counts.get("resolved", 0)
    experiments_resolved_percent = round((resolved_experiments / len(records)) * 100.0, 2) if records else 0.0

    suggestions: list[str] = []
    if not records:
        suggestions.append("Ainda não há registros suficientes para aprendizado útil.")
    else:
        suggestions.append("O learning loop está em modo de medição, registro e sugestão controlada.")
        if ingestion_state_counts.get("no_real_data_yet", 0) > 0:
            suggestions.append("Existem registros ainda sem métricas reais confirmadas.")
        if ingestion_state_counts.get("collection_error", 0) > 0:
            suggestions.append("Houve erro de coleta em parte dos registros; isso não deve ser tratado como sucesso.")
        if ingestion_state_counts.get("real_data_collected", 0) > 0:
            suggestions.append("Já existem registros com métricas reais coletadas e elegíveis para leitura básica.")
        if attention_count > 0:
            suggestions.append("Attention metrics já estão sendo calculadas só quando há base real suficiente.")
        if resolved_experiments > 0:
            suggestions.append("Há experimentos resolvidos; ainda assim nenhuma decisão de marca é automática.")

    return {
        "ok": True,
        "mode": "measurement_core_v1",
        "records_considered": len(records),
        "linked_with_receipt": linked_with_receipt,
        "operational_state_counts": states,
        "publish_status_counts": publish_status,
        "evidence_status_counts": evidence_status,
        "real_metrics_source_status_counts": real_metrics_source_status_counts,
        "ingestion_state_counts": ingestion_state_counts,
        "experiment_status_counts": experiment_status_counts,
        "experiments_resolved_percent": experiments_resolved_percent,
        "attention_metrics_available_records": attention_count,
        "latest_record_id": latest.get("record_id"),
        "latest_operational_state": latest.get("operational_state"),
        "latest_publish_status": latest.get("publish_status"),
        "latest_real_metrics_status": latest_real_metrics.get("source_status"),
        "latest_real_metrics_collected_at": latest_real_metrics.get("collected_at"),
        "latest_reflection_status": latest_reflection.get("status"),
        "latest_reflection_notes": latest_reflection.get("notes"),
        "latest_attention_score": (
            (latest_attention.get("breakdown") or {}).get("attention_score")
            if isinstance(latest_attention, dict)
            else None
        ),
        "latest_experiment_status": latest_experiment.get("status"),
        "latest_episode_id": latest_episode.get("episode_id"),
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
