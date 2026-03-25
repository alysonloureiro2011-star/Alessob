from __future__ import annotations

from typing import Any

from .experiment_learning_contract import (
    build_learning_bridge_contract,
    derive_experiment_state_machine,
)


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _editorial_defaults(
    *,
    operational_state: str,
    experiment_state: str,
    serial_continuity: dict[str, Any],
    distribution_context: dict[str, Any],
) -> dict[str, Any]:
    serial_continuity = _safe_dict(serial_continuity)
    distribution_context = _safe_dict(distribution_context)

    recommended_next_format = distribution_context.get("recommended_next_format") or "image"
    recommended_next_angle = distribution_context.get("recommended_next_angle") or "reforçar clareza causal e payoff concreto"
    recommended_next_series_action = distribution_context.get("recommended_next_series_action") or "manter peça isolada até surgir fio narrativo real"
    recommended_timing_hypothesis = distribution_context.get("recommended_timing_hypothesis") or "usar janela conservadora e manter leitura disciplinada do sinal"
    source_mode = distribution_context.get("source_mode") or "conservative_fallback"

    if operational_state in {"internal_lab", "editorial_staging"} and not distribution_context:
        recommended_next_format = "carousel"
        recommended_next_series_action = "testar continuidade leve sem abrir nova frente"
        recommended_timing_hypothesis = "preferir janela de leitura mais intencional e medição de save/share"

    if experiment_state == "candidate_for_brand_live":
        recommended_next_series_action = "continuar o melhor fio narrativo sem tratar staging como vitória final"
        source_mode = "evidence_aware"

    if serial_continuity.get("linked_series_candidate"):
        recommended_next_series_action = "abrir próximo episódio coerente com base na linhagem já registrada"
        source_mode = "memory_informed"

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
    episodic_memory: dict[str, Any] | None = None,
    serial_continuity: dict[str, Any] | None = None,
    distribution_context: dict[str, Any] | None = None,
    publish_result: dict[str, Any] | None = None,
    real_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evidence_interpreter = _safe_dict(evidence_interpreter)
    experiment_resolution = _safe_dict(experiment_resolution)
    resonance_engine = _safe_dict(resonance_engine)
    reward_prediction = _safe_dict(reward_prediction)
    attention_metrics = _safe_dict(attention_metrics)
    episodic_memory = _safe_dict(episodic_memory)
    serial_continuity = _safe_dict(serial_continuity)
    distribution_context = _safe_dict(distribution_context)
    publish_result = _safe_dict(publish_result)
    real_metrics = _safe_dict(real_metrics)

    evidence_state = str(evidence_interpreter.get("evidence_state") or "no_receipt")
    resolution_state = str(experiment_resolution.get("resolution_state") or "collecting")
    attention_score = _safe_float(_safe_dict(attention_metrics.get("breakdown")).get("attention_score"))

    state_machine = derive_experiment_state_machine(
        operational_state=operational_state,
        evidence_state=evidence_state,
        resolution_state=resolution_state,
        publish_result=publish_result,
        evidence_interpreter=evidence_interpreter,
        real_metrics=real_metrics,
    )
    experiment_state = state_machine["experiment_state"]

    recommended_action = "collect_more"
    action_priority = "low"
    recommendation_reason = "manter leitura conservadora até existir evidência suficiente"
    next_best_step = "seguir registrando evidência real sem promover automaticamente"
    safe_to_repeat = True
    safe_to_promote_to_editorial_staging = False
    requires_human_review = False

    if experiment_state == "repeat_probe":
        recommended_action = "repeat_probe"
        action_priority = "medium"
        recommendation_reason = state_machine.get("reason_for_repeat") or "ainda não existe receipt real"
        next_best_step = "rodar probe explícito em internal_lab ou editorial_staging"
        safe_to_repeat = True
    elif experiment_state == "collecting":
        recommended_action = "hold_position"
        action_priority = "low"
        recommendation_reason = state_machine.get("reason_not_resolved") or "há receipt, mas ainda não existe media_id real"
        next_best_step = "aguardar media_id real antes de comparar variantes"
        safe_to_repeat = True
    elif experiment_state == "hold":
        recommended_action = "wait_metrics"
        action_priority = "low"
        recommendation_reason = state_machine.get("reason_not_resolved") or "há media_id real, mas ainda não há métricas suficientes"
        next_best_step = "aguardar nova leitura de ingestão antes de comparar variantes"
        safe_to_repeat = True
    elif experiment_state == "blocked_brand":
        recommended_action = "human_review_required"
        action_priority = "high"
        recommendation_reason = "o experimento está bloqueado por marca"
        next_best_step = "corrigir brand fit antes de qualquer repetição"
        safe_to_repeat = False
        requires_human_review = True
    elif experiment_state == "blocked_quality":
        recommended_action = "compare_variant"
        action_priority = "medium"
        recommendation_reason = "o experimento está bloqueado por qualidade"
        next_best_step = "comparar nova variante com mais clareza e payoff"
        safe_to_repeat = True
    elif experiment_state == "candidate_for_brand_live":
        recommended_action = "promote_to_editorial_staging_candidate"
        action_priority = "high"
        recommendation_reason = "a peça acumula sinal suficiente para candidatura conservadora, sem virar vitória final"
        next_best_step = "submeter a variante à revisão humana antes de qualquer promoção"
        safe_to_repeat = False
        safe_to_promote_to_editorial_staging = True
        requires_human_review = True
    elif resolution_state == "loser_candidate":
        recommended_action = "discard_variant"
        action_priority = "medium"
        recommendation_reason = "a variante mostrou baixa atratividade relativa"
        next_best_step = "não promover esta variante e priorizar outra hipótese"
        safe_to_repeat = False
    elif resolution_state in {"weak_signal", "observe"}:
        recommended_action = "compare_variant"
        action_priority = "medium"
        recommendation_reason = "há evidência real, mas o sinal ainda é fraco"
        next_best_step = "comparar outra variante mantendo a hipótese"
        safe_to_repeat = True

    editorial_defaults = _editorial_defaults(
        operational_state=operational_state,
        experiment_state=experiment_state,
        serial_continuity=serial_continuity,
        distribution_context=distribution_context,
    )

    if attention_score is not None and attention_score < 40:
        editorial_defaults["recommended_next_angle"] = "reduzir ruído, encurtar entrada e aumentar payoff concreto"
    if attention_score is not None and attention_score >= 60:
        editorial_defaults["recommended_next_series_action"] = "continuar a série com aprofundamento controlado"
        editorial_defaults["source_mode"] = "evidence_aware"

    learning_bridge = build_learning_bridge_contract(
        experiment_state_machine=state_machine,
        recommendation_engine={"recommended_action": recommended_action},
        episodic_memory=episodic_memory,
        serial_continuity=serial_continuity,
        distribution_context=distribution_context,
    )

    recommendation_reason_editorial = (
        "recomendação editorial gerada sem reabrir infra, usando evidência, estado experimental, memória e distribuição quando disponíveis"
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
            "experiment_state": experiment_state,
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
        "learning_reuse_reason": "reusar evidência real, memória episódica e continuidade sem transformar staging em vitória final",
        "evidence_aware_but_not_infra_reopened": True,
        "source_mode": editorial_defaults["source_mode"],
        "experiment_state": experiment_state,
        "promotion_readiness": state_machine.get("promotion_readiness"),
        "reason_for_repeat": state_machine.get("reason_for_repeat"),
        "reason_not_resolved": state_machine.get("reason_not_resolved"),
        "learning_bridge": learning_bridge,
    }
