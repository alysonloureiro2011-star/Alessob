from __future__ import annotations

from typing import Any


def build_recommendation_engine(
    *,
    evidence_interpreter: dict[str, Any],
    experiment_resolution: dict[str, Any],
    resonance_engine: dict[str, Any],
    reward_prediction: dict[str, Any],
    attention_metrics: dict[str, Any],
    operational_state: str,
) -> dict[str, Any]:
    evidence_state = str(evidence_interpreter.get("evidence_state") or "no_receipt")
    resolution_state = str(experiment_resolution.get("resolution_state") or "collecting")
    winner_candidate = bool(experiment_resolution.get("winner_candidate"))
    loser_candidate = bool(experiment_resolution.get("loser_candidate"))

    recommended_action = "collect_more"
    action_priority = "low"
    recommendation_reason = "manter leitura conservadora até existir evidência suficiente"
    next_best_step = "seguir registrando evidência real sem promover automaticamente"
    safe_to_repeat = True
    safe_to_promote_to_editorial_staging = False
    requires_human_review = False

    if evidence_state == "no_receipt":
        recommended_action = "repeat_probe"
        action_priority = "medium"
        recommendation_reason = "ainda não existe receipt real"
        next_best_step = "rodar probe explícito em internal_lab ou editorial_staging"
        safe_to_repeat = True
    elif evidence_state in {"receipt_only", "linked_real_target", "metrics_pending"}:
        recommended_action = "wait_metrics"
        action_priority = "low"
        recommendation_reason = "há bridge real mínima, mas ainda não há métricas suficientes"
        next_best_step = "aguardar nova leitura de ingestão antes de comparar variantes"
        safe_to_repeat = True
    elif evidence_state == "ingest_error":
        recommended_action = "human_review_required"
        action_priority = "high"
        recommendation_reason = "houve erro de ingestão e a evidência precisa ser revisada"
        next_best_step = "inspecionar token, receipt, media_id e leitura de insights"
        safe_to_repeat = False
        requires_human_review = True
    elif resolution_state == "weak_signal":
        recommended_action = "compare_variant"
        action_priority = "medium"
        recommendation_reason = "há evidência real, mas o sinal ainda é fraco"
        next_best_step = "comparar outra variante mantendo a hipótese"
        safe_to_repeat = True
    elif winner_candidate and resolution_state in {"winner_candidate", "resolved_conservative"}:
        recommended_action = "promote_to_editorial_staging_candidate"
        action_priority = "high"
        recommendation_reason = "a variante acumulou sinal suficiente para candidatura conservadora"
        next_best_step = "submeter a variante à revisão humana antes de qualquer promoção"
        safe_to_repeat = False
        safe_to_promote_to_editorial_staging = True
        requires_human_review = True
    elif loser_candidate and resolution_state in {"loser_candidate", "resolved_conservative"}:
        recommended_action = "discard_variant"
        action_priority = "medium"
        recommendation_reason = "a variante mostrou baixa atratividade relativa"
        next_best_step = "não promover esta variante e priorizar outra hipótese"
        safe_to_repeat = False
    elif resolution_state == "observe":
        recommended_action = "hold_position"
        action_priority = "low"
        recommendation_reason = "há evidência real, mas ainda não conclusiva"
        next_best_step = "continuar coleta antes de qualquer decisão"
        safe_to_repeat = True

    return {
        "ok": True,
        "recommended_action": recommended_action,
        "action_priority": action_priority,
        "recommendation_reason": recommendation_reason,
        "next_best_step": next_best_step,
        "safe_to_repeat": safe_to_repeat,
        "safe_to_promote_to_editorial_staging": safe_to_promote_to_editorial_staging,
        "requires_human_review": requires_human_review,
        "guardrails": {
            "brand_live_allowed": False,
            "autopublish_allowed": False,
            "policy_autonomy": False,
        },
        "decision_inputs": {
            "evidence_state": evidence_state,
            "resolution_state": resolution_state,
            "resonance_score": resonance_engine.get("resonance_score"),
            "reward_prediction_score": reward_prediction.get("reward_prediction_score"),
            "attention_score": (attention_metrics.get("breakdown") or {}).get("attention_score"),
            "operational_state": operational_state,
        },
    }
