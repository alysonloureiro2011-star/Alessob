from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def build_reward_prediction(
    *,
    record: dict[str, Any],
    resonance_engine: dict[str, Any],
) -> dict[str, Any]:
    attention_metrics = dict(record.get("attention_metrics") or {})
    attention_breakdown = dict(attention_metrics.get("breakdown") or {})
    real_metrics = dict(record.get("real_metrics") or {})

    source_status = str(real_metrics.get("source_status") or "not_available_yet")
    resonance_score = _to_float(resonance_engine.get("resonance_score"))
    attention_score = _to_float(attention_breakdown.get("attention_score"))

    usable = [value for value in [resonance_score, attention_score] if value is not None]

    reward_prediction_score = None
    reward_band = "unknown"
    if source_status in {"collected", "partial_collected"} and usable:
        reward_prediction_score = round(sum(usable) / len(usable), 2)
        if reward_prediction_score >= 80:
            reward_band = "high"
        elif reward_prediction_score >= 60:
            reward_band = "moderate"
        else:
            reward_band = "low"

    reasons: list[str] = []
    if reward_prediction_score is None:
        reasons.append("reward prediction ainda sem base real suficiente")
    else:
        reasons.append("reward prediction deriva de resonance_score + attention_score auditáveis")

    return {
        "ok": True,
        "mode": "conservative_reward_prediction_v1",
        "source_status": source_status,
        "reward_prediction_score": reward_prediction_score,
        "reward_band": reward_band,
        "breakdown": {
            "resonance_score": resonance_score,
            "attention_score": attention_score,
        },
        "reasons": reasons,
        "audit": {
            "random_used": False,
            "fake_score_used": False,
            "policy_autonomy": False,
        },
    }
