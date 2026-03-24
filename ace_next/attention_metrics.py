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


def _normalize_views_over_time(raw: Any) -> list[float]:
    if raw is None:
        return []
    points: list[float] = []

    if isinstance(raw, dict):
        iterable = list(raw.values())
    elif isinstance(raw, list):
        iterable = raw
    else:
        return []

    for item in iterable:
        if isinstance(item, dict):
            candidate = (
                item.get("value")
                or item.get("views")
                or item.get("count")
                or item.get("impressions")
            )
        else:
            candidate = item
        value = _to_float(candidate)
        if value is not None:
            points.append(value)

    return points


def _views_momentum(points: list[float]) -> float | None:
    if len(points) < 2:
        return None
    first = points[0]
    last = points[-1]
    if first <= 0:
        return None
    return max(-1.0, min((last - first) / first, 10.0))


def _views_velocity(points: list[float]) -> float | None:
    if len(points) < 2:
        return None
    deltas = []
    for index in range(1, len(points)):
        deltas.append(points[index] - points[index - 1])
    if not deltas:
        return None
    return sum(deltas) / len(deltas)


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
    series_continuation_rate = _to_float(inputs.get("series_continuation_rate"))
    resonance_score = _to_float(inputs.get("resonance_score"))
    reward_prediction_score = _to_float(inputs.get("reward_prediction_score"))

    views_over_time_points = _normalize_views_over_time(inputs.get("views_over_time"))
    views_momentum = _views_momentum(views_over_time_points)
    views_velocity = _views_velocity(views_over_time_points)

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
        "series_continuation_rate": _cap_normalize(series_continuation_rate, 1.0),
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
            "series_continuation_rate": round(series_continuation_rate, 4) if series_continuation_rate is not None else None,
            "views_over_time_points": views_over_time_points,
            "views_over_time_points_count": len(views_over_time_points),
            "views_momentum": round(views_momentum, 4) if views_momentum is not None else None,
            "views_velocity": round(views_velocity, 4) if views_velocity is not None else None,
            "resonance_score": round(resonance_score, 2) if resonance_score is not None else None,
            "reward_prediction_score": round(reward_prediction_score, 2) if reward_prediction_score is not None else None,
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
                "series_continuation_rate": series_continuation_rate,
                "views_over_time": views_over_time_points if views_over_time_points else None,
                "resonance_score": resonance_score,
                "reward_prediction_score": reward_prediction_score,
            }.items()
            if value is not None
        ],
        "notes": [
            "attention_score é derivado apenas de sinais reais disponíveis",
            "campos ausentes permanecem nulos; ausência de dado não vira sucesso falso",
            "resonance_score e reward_prediction_score entram como sinais contextuais, não como evidência fake",
            "views_over_time e series_continuation_rate ficam disponíveis quando houver coleta real correspondente",
        ],
    }
