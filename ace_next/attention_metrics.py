from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _cap_normalize(value: float | None, cap: float) -> float | None:
    if value is None or cap <= 0:
        return None
    return max(0.0, min(value / cap, 1.0))


def build_attention_metrics(
    *,
    real_metrics: dict[str, Any],
    attention_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inputs = dict(attention_inputs or {})
    source_status = str(real_metrics.get("source_status") or "unknown")

    impressions = _to_float(real_metrics.get("impressions"))
    reach = _to_float(real_metrics.get("reach"))
    likes = _to_float(real_metrics.get("likes"))
    comments = _to_float(real_metrics.get("comments"))
    saves = _to_float(real_metrics.get("saves"))
    shares = _to_float(real_metrics.get("shares"))
    engagement_proxy = _to_float(real_metrics.get("engagement_proxy"))

    views = _to_float(inputs.get("views"))
    plays = _to_float(inputs.get("plays"))
    avg_watch_time = _to_float(inputs.get("avg_watch_time"))
    explicit_completion_proxy = _to_float(inputs.get("completion_proxy"))
    explicit_skip_rate = _to_float(inputs.get("skip_rate"))
    duration_seconds = _to_float(inputs.get("duration_seconds"))

    view_base = views if views is not None else plays if plays is not None else impressions
    view_rate = _safe_div(view_base, reach) if reach is not None else None

    completion_proxy = explicit_completion_proxy
    if completion_proxy is None and avg_watch_time is not None and duration_seconds is not None and duration_seconds > 0:
        completion_proxy = max(0.0, min(avg_watch_time / duration_seconds, 1.0))

    skip_rate = explicit_skip_rate
    if skip_rate is None and completion_proxy is not None:
        skip_rate = max(0.0, min(1.0 - completion_proxy, 1.0))

    base_for_engagement = reach if reach is not None and reach > 0 else impressions
    share_rate = _safe_div(shares, base_for_engagement)
    save_rate = _safe_div(saves, base_for_engagement)
    comment_depth_score = _safe_div(comments, base_for_engagement)

    normalized_components = {
        "view_rate": _cap_normalize(view_rate, 2.0),
        "completion_proxy": _cap_normalize(completion_proxy, 1.0),
        "share_rate": _cap_normalize(share_rate, 0.08),
        "save_rate": _cap_normalize(save_rate, 0.10),
        "comment_depth_score": _cap_normalize(comment_depth_score, 0.04),
        "engagement_proxy": _cap_normalize(engagement_proxy, 0.20),
    }
    available_components = [value for value in normalized_components.values() if value is not None]
    attention_score = None
    if source_status in {"collected", "partial_collected"} and len(available_components) >= 2:
        attention_score = round(sum(available_components) / len(available_components) * 100, 2)

    return {
        "ok": True,
        "source_status": source_status,
        "breakdown": {
            "views": views,
            "plays": plays,
            "impressions": impressions,
            "reach": reach,
            "likes": likes,
            "comments": comments,
            "saves": saves,
            "shares": shares,
            "engagement_proxy": engagement_proxy,
            "view_rate": round(view_rate, 4) if view_rate is not None else None,
            "skip_rate": round(skip_rate, 4) if skip_rate is not None else None,
            "avg_watch_time": round(avg_watch_time, 3) if avg_watch_time is not None else None,
            "completion_proxy": round(completion_proxy, 4) if completion_proxy is not None else None,
            "share_rate": round(share_rate, 4) if share_rate is not None else None,
            "save_rate": round(save_rate, 4) if save_rate is not None else None,
            "comment_depth_score": round(comment_depth_score, 4) if comment_depth_score is not None else None,
            "attention_score": attention_score,
        },
        "available_inputs": [
            key
            for key, value in {
                "views": views,
                "plays": plays,
                "impressions": impressions,
                "reach": reach,
                "likes": likes,
                "comments": comments,
                "saves": saves,
                "shares": shares,
                "engagement_proxy": engagement_proxy,
                "avg_watch_time": avg_watch_time,
                "completion_proxy": completion_proxy,
                "skip_rate": skip_rate,
            }.items()
            if value is not None
        ],
        "notes": [
            "attention_score é derivado apenas de sinais reais disponíveis",
            "campos ausentes permanecem nulos; ausência de dado não vira sucesso falso",
        ],
    }
