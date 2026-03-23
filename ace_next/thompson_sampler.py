from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def build_thompson_sampler(
    *,
    record: dict[str, Any],
    reward_prediction: dict[str, Any],
    conservative_mode: bool = True,
) -> dict[str, Any]:
    creative_plan = dict(record.get("creative_plan") or {})
    visual_template = dict(record.get("visual_template") or {})
    real_metrics = dict(record.get("real_metrics") or {})

    selected_variant = (
        visual_template.get("template_id")
        or creative_plan.get("visual_style")
        or creative_plan.get("headline")
        or "default_variant"
    )

    source_status = str(real_metrics.get("source_status") or "not_available_yet")
    reward_prediction_score = _to_float(reward_prediction.get("reward_prediction_score"))

    posterior_mean = None
    confidence_level = "low"
    winner_candidate = False
    decision_state = "collecting"

    if reward_prediction_score is not None:
        posterior_mean = round(reward_prediction_score / 100.0, 4)

    if source_status in {"collected", "partial_collected"} and posterior_mean is not None:
        if posterior_mean >= 0.75:
            confidence_level = "medium"
            winner_candidate = True
            decision_state = "winner_candidate"
        else:
            confidence_level = "low"
            decision_state = "observe"
    elif source_status == "ingest_error":
        decision_state = "ingest_error"
    else:
        decision_state = "collecting"

    return {
        "ok": True,
        "mode": "deterministic_thompson_proxy_v1",
        "conservative_mode": bool(conservative_mode),
        "selected_variant": selected_variant,
        "posterior_mean": posterior_mean,
        "confidence_level": confidence_level,
        "winner_candidate": winner_candidate,
        "decision_state": decision_state,
        "reasons": [
            "nenhum sorteio aleatório foi usado",
            "posterior_mean é derivado de reward_prediction_score auditável",
        ],
        "audit": {
            "random_used": False,
            "fake_score_used": False,
            "brand_autonomy": False,
        },
    }
