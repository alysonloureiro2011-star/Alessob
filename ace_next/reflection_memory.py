from __future__ import annotations

from typing import Any


def build_reflection_memory(*, record: dict[str, Any]) -> dict[str, Any]:
    real_metrics = dict(record.get("real_metrics") or {})
    publish_result = dict(record.get("publish_result") or {})
    probe_context = dict(record.get("probe_context") or {})
    evidence_interpreter = dict(record.get("evidence_interpreter") or {})
    experiment_resolution = dict(record.get("experiment_resolution") or {})
    recommendation_engine = dict(record.get("recommendation_engine") or {})

    status = str(evidence_interpreter.get("evidence_state") or real_metrics.get("source_status") or "not_available_yet")
    notes: list[str] = []

    if publish_result.get("media_id"):
        notes.append(f"media_id real presente: {publish_result.get('media_id')}")
    else:
        notes.append("a peça ainda não possui media_id real confirmado")

    if publish_result.get("permalink"):
        notes.append("permalink real disponível")
    else:
        notes.append("permalink real ainda não disponível")

    if probe_context.get("requested"):
        notes.append(f"probe real solicitado para estado: {probe_context.get('requested_state')}")
        if probe_context.get("publish_executed"):
            notes.append("o probe real foi executado")
        else:
            notes.append("o probe real não foi executado")

    evidence_state = str(evidence_interpreter.get("evidence_state") or "")
    resolution_state = str(experiment_resolution.get("resolution_state") or "")
    recommended_action = str(recommendation_engine.get("recommended_action") or "")
    requires_human_review = bool(recommendation_engine.get("requires_human_review"))

    if evidence_state in {"no_receipt", "receipt_only"}:
        notes.append("ainda sem evidência suficiente")
    elif evidence_state in {"linked_real_target", "metrics_pending"}:
        notes.append("há receipt mas ainda não há métrica suficiente")
    elif evidence_state == "weak_evidence":
        notes.append("há sinal real, mas ele ainda é fraco demais para decisão forte")
    elif evidence_state == "sufficient_evidence":
        notes.append("há evidência suficiente para interpretação conservadora")
    elif evidence_state == "ingest_error":
        notes.append("houve erro de ingestão de métricas reais")
        reason = real_metrics.get("source_reason")
        if reason:
            notes.append(str(reason))

    if resolution_state in {"collecting", "observe", "weak_signal"}:
        notes.append("experimento permanece em coleta")

    if bool(experiment_resolution.get("winner_candidate")):
        notes.append("variante candidata a vencedor conservador")

    if requires_human_review or recommended_action == "promote_to_editorial_staging_candidate":
        notes.append("revisão humana recomendada antes de qualquer promoção")

    return {
        "ok": True,
        "status": status,
        "notes": notes,
        "recommended_action": recommended_action or None,
        "guardrails": {
            "can_change_brand_policy": False,
            "can_change_editorial_policy": False,
            "can_change_visual_policy": False,
            "can_authorize_brand_live": False,
            "can_autopublish": False,
        },
    }
