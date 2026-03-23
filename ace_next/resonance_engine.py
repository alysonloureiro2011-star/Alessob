from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _normalize(value: float | None, cap: float) -> float | None:
    if value is None or cap <= 0:
        return None
    clipped = max(0.0, min(value, cap))
    return clipped / cap


def build_resonance_engine(*, record: dict[str, Any]) -> dict[str, Any]:
    real_metrics = dict(record.get("real_metrics") or {})
    attention_metrics = dict(record.get("attention_metrics") or {})
    attention_breakdown = dict(attention_metrics.get("breakdown") or {})

    source_status = str(real_metrics.get("source_status") or "not_available_yet")

    share_rate = _to_float(attention_breakdown.get("share_rate"))
    save_rate = _to_float(attention_breakdown.get("save_rate"))
    comment_depth_score = _to_float(attention_breakdown.get("comment_depth_score"))
    completion_proxy = _to_float(attention_breakdown.get("completion_proxy"))
    engagement_proxy = _to_float(real_metrics.get("engagement_proxy"))

    normalized = {
        "share_rate": _normalize(share_rate, 0.08),
        "save_rate": _normalize(save_rate, 0.10),
        "comment_depth_score": _normalize(comment_depth_score, 0.04),
        "completion_proxy": _normalize(completion_proxy, 1.0),
        "engagement_proxy": _normalize(engagement_proxy, 0.20),
    }
    usable = [value for value in normalized.values() if value is not None]

    resonance_score = None
    if source_status in {"collected", "partial_collected"} and len(usable) >= 2:
        resonance_score = round(sum(usable) / len(usable) * 100.0, 2)

    reasons: list[str] = []
    if resonance_score is None:
        reasons.append("dados reais ainda insuficientes para calcular resonance_score")
    else:
        reasons.append("resonance_score derivado apenas de sinais reais disponíveis")

    return {
        "ok": True,
        "mode": "conservative_resonance_engine_v1",
        "source_status": source_status,
        "resonance_score": resonance_score,
        "breakdown": {
            "share_rate": share_rate,
            "save_rate": save_rate,
            "comment_depth_score": comment_depth_score,
            "completion_proxy": completion_proxy,
            "engagement_proxy": engagement_proxy,
        },
        "normalized_components": normalized,
        "reasons": reasons,
        "audit": {
            "random_used": False,
            "fake_score_used": False,
            "brand_autonomy": False,
        },
    }
