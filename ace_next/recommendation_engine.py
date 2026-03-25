from __future__ import annotations

from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _editorial_defaults(operational_state: str, evidence_state: str, resolution_state: str) -> dict[str, Any]:
    recommended_next_format = "image"
    recommended_next_angle = "reforçar clareza causal e payoff concreto"
    recommended_next_series_action = "manter peça isolada até surgir fio narrativo real"
    recommended_timing_hypothesis = "usar janela conservadora e manter leitura disciplinada do sinal"
    source_mode = "conservative_fallback"

    if operational_state in {"internal_lab", "editorial_staging"}:
        recommended_next_format = "carousel"
        recommended_next_series_action = "testar continuidade leve sem abrir nova frente"
        recommended_timing_hypothesis = "preferir janela de leitura mais intencional e medição de save/share"
    if evidence_state == "no_receipt":
        recommended_next_angle = "repetir hipótese com copy mais nítida antes de interpretar mérito final"
    elif resolution_state in {"weak_signal", "observe"}:
        recommended_next_angle = "comparar nova variante com ângulo mais preciso e menos ruído"
        source_mode = "evidence_aware"
    elif resolution_state in {"winner_candidate", "resolved_conservative"}:
        recommended_next_angle = "continuar o melhor ângulo atual sem inflar promessa"
        recommended_next_series_action = "abrir próximo episódio coerente com a peça vencedora"
        source_mode = "evidence_aware"

    return {
        "recommended_next_format": recommended_next_format,
        "recommended_next_angle": recommended_next_angle,
        "recommended_next_series_action": recommended_next_series_action,
        "recommended_timing_hypothesis": recommended_timing_hypothesis,
        "source_mode": source_mode,
    }


def build_recommendation_engine(
    *,
    evidence_interpreter: dict[str, Any],
    experiment_resolution: dict[str, Any],
    resonance_engine: dict[str, Any],
    reward_prediction: dict[str, Any],
    attention_metrics: dict[str, Any],
    operational_state: str,
) -> dict[str, Any]:
    evidence_interpreter = _safe_dict(evidence_interpreter)
    experiment_resolution = _safe_dict(experiment_resolution)
    resonance_engine = _safe_dict(resonance_engine)
    reward_prediction = _safe_dict(reward_prediction)
    attention_metrics = _safe_dict(attention_metrics)

    evidence_state = str(evidence_interpreter.get("evidence_state") or "no_receipt")
    resolution_state = str(experiment_resolution.get("resolution_state") or "collecting")
    winner_candidate = bool(experiment_resolution.get("winner_candidate"))
    loser_candidate = bool(experiment_resolution.get("loser_candidate"))
    attention_score = _safe_float(_safe_dict(attention_metrics.get("breakdown")).get("attention_score"))

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

    editorial_defaults = _editorial_defaults(
        operational_state=operational_state,
        evidence_state=evidence_state,
        resolution_state=resolution_state,
    )

    if attention_score is not None and attention_score < 40:
        editorial_defaults["recommended_next_angle"] = "reduzir ruído, encurtar entrada e aumentar payoff concreto"
    if attention_score is not None and attention_score >= 60:
        editorial_defaults["recommended_next_series_action"] = "continuar a série com aprofundamento controlado"
        editorial_defaults["source_mode"] = "evidence_aware"

    recommendation_reason_editorial = (
        "recomendação editorial gerada sem reabrir infra, usando estado de evidência + resolução + atenção disponível"
    )
    learning_reuse_reason = (
        "reusar o que já foi medido para escolher próximo formato, próximo ângulo e próxima continuidade"
    )

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
            "attention_score": attention_score,
            "operational_state": operational_state,
        },
        "recommended_next_format": editorial_defaults["recommended_next_format"],
        "recommended_next_angle": editorial_defaults["recommended_next_angle"],
        "recommended_next_series_action": editorial_defaults["recommended_next_series_action"],
        "recommended_timing_hypothesis": editorial_defaults["recommended_timing_hypothesis"],
        "recommendation_reason_editorial": recommendation_reason_editorial,
        "learning_reuse_reason": learning_reuse_reason,
        "evidence_aware_but_not_infra_reopened": True,
        "source_mode": editorial_defaults["source_mode"],
    }
