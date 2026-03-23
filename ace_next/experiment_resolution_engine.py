from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def build_experiment_resolution(
    *,
    experiment_context: dict[str, Any],
    thompson_sampler: dict[str, Any],
    reward_prediction: dict[str, Any],
    attention_metrics: dict[str, Any],
    evidence_interpreter: dict[str, Any],
) -> dict[str, Any]:
    evidence_state = str(evidence_interpreter.get("evidence_state") or "no_receipt")
    evidence_strength = str(evidence_interpreter.get("evidence_strength") or "none")
    evidence_ready = bool(evidence_interpreter.get("evidence_ready_for_resolution"))

    attention_breakdown = dict(attention_metrics.get("breakdown") or {})
    attention_score = _to_float(attention_breakdown.get("attention_score"))
    reward_prediction_score = _to_float(reward_prediction.get("reward_prediction_score"))
    posterior_mean = _to_float(thompson_sampler.get("posterior_mean"))

    previous_status = str(experiment_context.get("status") or "unknown")

    resolution_state = "collecting"
    can_resolve = False
    winner_candidate = False
    loser_candidate = False
    keep_collecting = True
    confidence_level = "low"
    promotion_readiness = "not_ready"
    resolution_reason = "ainda sem evidência suficiente para resolução conservadora"

    if evidence_state == "ingest_error":
        resolution_state = "observe"
        can_resolve = False
        keep_collecting = False
        confidence_level = "low"
        resolution_reason = "houve erro de ingestão; a prioridade é revisar a evidência antes de decidir"
    elif not evidence_ready:
        if evidence_state == "weak_evidence":
            resolution_state = "weak_signal"
            can_resolve = False
            keep_collecting = True
            confidence_level = "low"
            resolution_reason = "há sinal real, mas ele ainda é fraco demais para resolver o experimento"
        else:
            resolution_state = "collecting"
            can_resolve = False
            keep_collecting = True
            confidence_level = "low"
            resolution_reason = "o experimento permanece em coleta por falta de base suficiente"
    else:
        if (
            posterior_mean is not None
            and posterior_mean >= 0.82
            and (reward_prediction_score or 0) >= 70
            and (attention_score is None or attention_score >= 60)
        ):
            winner_candidate = True
            can_resolve = True
            keep_collecting = False
            confidence_level = "high" if evidence_strength == "strong" else "medium"
            resolution_state = "resolved_conservative" if evidence_strength == "strong" else "winner_candidate"
            promotion_readiness = "editorial_staging_candidate"
            resolution_reason = "a variante acumulou evidência conservadora suficiente para candidatura controlada"
        elif (
            posterior_mean is not None
            and posterior_mean <= 0.35
            and reward_prediction_score is not None
            and reward_prediction_score < 45
            and attention_score is not None
            and attention_score < 50
        ):
            loser_candidate = True
            can_resolve = True
            keep_collecting = False
            confidence_level = "medium" if evidence_strength in {"moderate", "strong"} else "low"
            resolution_state = "resolved_conservative" if evidence_strength == "strong" else "loser_candidate"
            promotion_readiness = "discard_candidate"
            resolution_reason = "a variante mostrou sinal fraco consistente e entra em descarte conservador"
        else:
            resolution_state = "observe"
            can_resolve = False
            keep_collecting = True
            confidence_level = "medium" if evidence_strength in {"moderate", "strong"} else "low"
            resolution_reason = "há evidência real, mas ela ainda não é suficientemente conclusiva"

    return {
        "ok": True,
        "previous_status": previous_status,
        "resolution_state": resolution_state,
        "can_resolve": can_resolve,
        "winner_candidate": winner_candidate,
        "loser_candidate": loser_candidate,
        "keep_collecting": keep_collecting,
        "confidence_level": confidence_level,
        "resolution_reason": resolution_reason,
        "promotion_readiness": promotion_readiness,
        "audit": {
            "brand_live_allowed": False,
            "random_used": False,
            "fake_resolution_used": False,
        },
    }
