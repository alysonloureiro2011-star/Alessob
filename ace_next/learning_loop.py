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
    if source_status in {"collection_error", "missing_token", "ingest_error"}:
        return "collection_error"
    return "no_real_data_yet"


def _evidence_state(record: dict[str, Any]) -> str:
    evidence = dict(record.get("evidence_interpreter") or {})
    return str(evidence.get("evidence_state") or "unknown")


def _resolution_state(record: dict[str, Any]) -> str:
    resolution = dict(record.get("experiment_resolution") or {})
    return str(resolution.get("resolution_state") or "unknown")


def _recommended_action(record: dict[str, Any]) -> str:
    recommendation = dict(record.get("recommendation_engine") or {})
    return str(recommendation.get("recommended_action") or "unknown")


def _attention_breakdown(record: dict[str, Any]) -> dict[str, Any]:
    return dict((record.get("attention_metrics") or {}).get("breakdown") or {})


def _decision_core_summary(record: dict[str, Any]) -> dict[str, Any]:
    return dict(record.get("decision_core_summary") or {})


def _real_collection_state(records: list[dict[str, Any]], latest: dict[str, Any]) -> dict[str, Any]:
    source_status_values = [_source_status(record) for record in records]
    counts = dict(Counter(source_status_values))

    collected = counts.get("collected", 0) + counts.get("partial_collected", 0)
    errors = counts.get("ingest_error", 0) + counts.get("collection_error", 0) + counts.get("missing_token", 0)
    waiting = max(len(records) - collected - errors, 0)

    latest_real_metrics = dict(latest.get("real_metrics") or {})

    return {
        "ok": True,
        "records_with_real_collection": collected,
        "records_waiting_real_collection": waiting,
        "records_with_collection_error": errors,
        "latest_source_status": latest_real_metrics.get("source_status"),
        "latest_source_reason": latest_real_metrics.get("source_reason"),
        "latest_collected_at": latest_real_metrics.get("collected_at"),
        "source_status_counts": counts,
    }


def _real_analysis_state(records: list[dict[str, Any]], latest: dict[str, Any]) -> dict[str, Any]:
    latest_attention = _attention_breakdown(latest)
    latest_decision = _decision_core_summary(latest)

    attention_available = sum(
        1
        for record in records
        if _attention_breakdown(record).get("attention_score") is not None
    )

    return {
        "ok": True,
        "records_with_attention_analysis": attention_available,
        "latest_attention_score": latest_attention.get("attention_score"),
        "latest_view_rate": latest_attention.get("view_rate"),
        "latest_skip_rate": latest_attention.get("skip_rate"),
        "latest_avg_watch_time": latest_attention.get("avg_watch_time"),
        "latest_completion_proxy": latest_attention.get("completion_proxy"),
        "latest_share_rate": latest_attention.get("share_rate"),
        "latest_save_rate": latest_attention.get("save_rate"),
        "latest_comment_depth_score": latest_attention.get("comment_depth_score"),
        "latest_views_momentum": latest_attention.get("views_momentum"),
        "latest_series_continuation_rate": latest_attention.get("series_continuation_rate"),
        "latest_resonance_score": latest_decision.get("resonance_score"),
        "latest_reward_prediction_score": latest_decision.get("reward_prediction_score"),
    }


def _insight_generation_state(latest: dict[str, Any]) -> dict[str, Any]:
    latest_recommendation = dict(latest.get("recommendation_engine") or {})
    latest_reflection = dict(latest.get("reflection_memory") or {})

    return {
        "ok": True,
        "can_generate_insight": True,
        "latest_recommended_action": latest_recommendation.get("recommended_action"),
        "latest_next_best_step": latest_recommendation.get("next_best_step"),
        "latest_recommendation_reason": latest_recommendation.get("recommendation_reason"),
        "latest_reflection_notes": latest_reflection.get("notes"),
        "insight_mode": "conservative_suggestion_only",
    }


def _controlled_validation_state(latest: dict[str, Any]) -> dict[str, Any]:
    latest_evidence = dict(latest.get("evidence_interpreter") or {})
    latest_resolution = dict(latest.get("experiment_resolution") or {})
    latest_recommendation = dict(latest.get("recommendation_engine") or {})

    return {
        "ok": True,
        "evidence_state": latest_evidence.get("evidence_state"),
        "evidence_strength": latest_evidence.get("evidence_strength"),
        "evidence_ready_for_resolution": latest_evidence.get("evidence_ready_for_resolution"),
        "resolution_state": latest_resolution.get("resolution_state"),
        "can_resolve": latest_resolution.get("can_resolve"),
        "promotion_readiness": latest_resolution.get("promotion_readiness"),
        "requires_human_review": latest_recommendation.get("requires_human_review"),
        "brand_live_allowed": False,
    }


def _controlled_adjustment_state(latest: dict[str, Any]) -> dict[str, Any]:
    latest_resolution = dict(latest.get("experiment_resolution") or {})
    latest_recommendation = dict(latest.get("recommendation_engine") or {})
    recommended_action = str(latest_recommendation.get("recommended_action") or "")

    safe_actions = {
        "collect_more",
        "repeat_probe",
        "compare_variant",
        "hold_position",
        "promote_to_editorial_staging_candidate",
        "discard_variant",
        "human_review_required",
    }

    return {
        "ok": True,
        "controlled_adjustment_only": True,
        "policy_autonomy": False,
        "brand_live_automation": False,
        "latest_recommended_action": recommended_action or None,
        "adjustment_action_is_safe": recommended_action in safe_actions if recommended_action else False,
        "can_adjust_parameters_only": bool(latest_resolution.get("can_resolve")),
        "requires_human_review": latest_recommendation.get("requires_human_review"),
    }


def _accumulated_learning_state(records: list[dict[str, Any]], latest: dict[str, Any]) -> dict[str, Any]:
    evidence_ready_count = sum(
        1
        for record in records
        if bool((record.get("evidence_interpreter") or {}).get("evidence_ready_for_resolution"))
    )
    resolved_count = sum(
        1
        for record in records
        if str((record.get("experiment_resolution") or {}).get("resolution_state") or "") == "resolved_conservative"
    )

    latest_episode = dict(latest.get("episodic_performance_memory") or {})

    return {
        "ok": True,
        "records_considered": len(records),
        "evidence_ready_records": evidence_ready_count,
        "resolved_conservative_records": resolved_count,
        "latest_episode_id": latest_episode.get("episode_id"),
        "latest_real_metrics_status": latest_episode.get("real_metrics_status"),
        "latest_evidence_state": latest_episode.get("evidence_state"),
        "latest_resolution_state": latest_episode.get("resolution_state"),
        "latest_recommendation_state": latest_episode.get("recommendation_state"),
    }


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

    evidence_state_counts = dict(Counter(_evidence_state(record) for record in records))
    resolution_state_counts = dict(Counter(_resolution_state(record) for record in records))
    recommendation_state_counts = dict(Counter(_recommended_action(record) for record in records))

    linked_with_receipt = sum(1 for record in records if record.get("receipt"))
    evidence_ready_count = sum(
        1
        for record in records
        if bool((record.get("evidence_interpreter") or {}).get("evidence_ready_for_resolution"))
    )

    latest_real_metrics = dict(latest.get("real_metrics") or {})
    latest_reflection = dict(latest.get("reflection_memory") or {})
    latest_attention = dict(latest.get("attention_metrics") or {})
    latest_experiment = dict(latest.get("experiment_registry") or {})
    latest_episode = dict(latest.get("episodic_performance_memory") or {})
    latest_evidence = dict(latest.get("evidence_interpreter") or {})
    latest_resolution = dict(latest.get("experiment_resolution") or {})
    latest_recommendation = dict(latest.get("recommendation_engine") or {})

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
        suggestions.append("O learning loop permanece em modo de registro, leitura conservadora e sugestão controlada.")
        if ingestion_state_counts.get("no_real_data_yet", 0) > 0:
            suggestions.append("Existem registros ainda sem métricas reais confirmadas.")
        if evidence_state_counts.get("metrics_pending", 0) > 0:
            suggestions.append("Há peças com target real ligado, mas ainda sem maturidade de evidência.")
        if evidence_state_counts.get("weak_evidence", 0) > 0:
            suggestions.append("Há sinais fracos reais que ainda não devem ser promovidos.")
        if evidence_state_counts.get("sufficient_evidence", 0) > 0:
            suggestions.append("Já existem casos com evidência suficiente para interpretação conservadora.")
        if resolution_state_counts.get("resolved_conservative", 0) > 0:
            suggestions.append("Há resolução conservadora registrada; ainda assim nenhuma promoção de marca é automática.")
        if recommendation_state_counts.get("promote_to_editorial_staging_candidate", 0) > 0:
            suggestions.append("Algumas variantes já podem virar candidatas a staging editorial, sempre com revisão humana.")

    return {
        "ok": True,
        "mode": "measurement_core_v1",
        "records_considered": len(records),
        "linked_with_receipt": linked_with_receipt,
        "evidence_ready_records": evidence_ready_count,
        "operational_state_counts": states,
        "publish_status_counts": publish_status,
        "evidence_status_counts": evidence_status,
        "real_metrics_source_status_counts": real_metrics_source_status_counts,
        "ingestion_state_counts": ingestion_state_counts,
        "evidence_state_counts": evidence_state_counts,
        "resolution_state_counts": resolution_state_counts,
        "recommendation_state_counts": recommendation_state_counts,
        "experiment_status_counts": experiment_status_counts,
        "experiments_resolved_percent": experiments_resolved_percent,
        "attention_metrics_available_records": attention_count,
        "latest_record_id": latest.get("record_id"),
        "latest_operational_state": latest.get("operational_state"),
        "latest_publish_status": latest.get("publish_status"),
        "latest_real_metrics_status": latest_real_metrics.get("source_status"),
        "latest_real_metrics_collected_at": latest_real_metrics.get("collected_at"),
        "latest_evidence_state": latest_evidence.get("evidence_state"),
        "latest_evidence_strength": latest_evidence.get("evidence_strength"),
        "latest_resolution_state": latest_resolution.get("resolution_state"),
        "latest_can_resolve": latest_resolution.get("can_resolve"),
        "latest_recommended_action": latest_recommendation.get("recommended_action"),
        "latest_next_best_step": latest_recommendation.get("next_best_step"),
        "latest_requires_human_review": latest_recommendation.get("requires_human_review"),
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
        "real_collection_state": _real_collection_state(records, latest),
        "real_analysis_state": _real_analysis_state(records, latest),
        "insight_generation_state": _insight_generation_state(latest),
        "controlled_validation_state": _controlled_validation_state(latest),
        "controlled_adjustment_state": _controlled_adjustment_state(latest),
        "accumulated_learning_state": _accumulated_learning_state(records, latest),
        "episodic_memory_state": {
            "latest_episode_id": latest_episode.get("episode_id"),
            "latest_real_metrics_status": latest_episode.get("real_metrics_status"),
            "latest_evidence_state": latest_episode.get("evidence_state"),
            "latest_resolution_state": latest_episode.get("resolution_state"),
            "latest_recommendation_state": latest_episode.get("recommendation_state"),
            "has_media_id": latest_episode.get("has_media_id"),
            "has_permalink": latest_episode.get("has_permalink"),
            "has_real_receipt": latest_episode.get("has_real_receipt"),
        },
        "performance_memory_state": {
            "records_considered": len(records),
            "latest_record_id": latest.get("record_id"),
            "latest_publish_status": latest.get("publish_status"),
            "latest_real_metrics_status": latest_real_metrics.get("source_status"),
            "latest_attention_score": ((latest_attention.get("breakdown") or {}).get("attention_score")),
            "latest_evidence_state": latest_evidence.get("evidence_state"),
            "latest_resolution_state": latest_resolution.get("resolution_state"),
        },
        "suggestions": suggestions,
    }
