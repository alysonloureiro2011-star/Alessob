from __future__ import annotations

from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _normalize_format(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"story", "stories"}:
        return "story"
    if normalized in {"carousel", "image", "reel"}:
        return normalized
    return "image"


FORMAT_DEFAULTS = {
    "image": {
        "format_hour_hint": "12:00-18:00",
        "timing_hypothesis": "imagem tende a performar melhor quando a leitura é rápida e o público ainda consegue salvar depois",
        "attention_metric_targets": ["save_rate", "share_rate", "comment_depth_score"],
        "distribution_reason": "imagem exige clareza rápida e valor percebido imediato",
    },
    "carousel": {
        "format_hour_hint": "07:00-09:00",
        "timing_hypothesis": "carrossel tende a performar melhor quando entra em janelas de leitura mais longa e intenção de salvamento",
        "attention_metric_targets": ["save_rate", "share_rate", "completion_proxy"],
        "distribution_reason": "carrossel depende mais de tempo de leitura e continuidade slide a slide",
    },
    "story": {
        "format_hour_hint": "11:00-13:00",
        "timing_hypothesis": "story tende a responder melhor em janelas curtas de atenção recorrente",
        "attention_metric_targets": ["view_rate", "reply_rate", "completion_proxy"],
        "distribution_reason": "story exige consumo rápido e densidade baixa",
    },
    "reel": {
        "format_hour_hint": "19:00-22:00",
        "timing_hypothesis": "reel tende a pedir janela de entretenimento e retenção competitiva",
        "attention_metric_targets": ["view_rate", "skip_rate", "completion_proxy"],
        "distribution_reason": "reel depende mais de retenção e rehook do que de leitura estática",
    },
}


def build_distribution_context_v1(
    *,
    format_recommendation: str,
    serial_continuity: dict[str, Any] | None = None,
    performance_context: dict[str, Any] | None = None,
    signal_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fmt = _normalize_format(format_recommendation)
    serial = _safe_dict(serial_continuity)
    performance = _safe_dict(performance_context)
    signal = _safe_dict(signal_context)

    defaults = dict(FORMAT_DEFAULTS[fmt])

    save_rate = _safe_float(performance.get("save_rate"))
    share_rate = _safe_float(performance.get("share_rate"))
    comment_depth_score = _safe_float(performance.get("comment_depth_score"))
    view_rate = _safe_float(performance.get("view_rate"))
    skip_rate = _safe_float(performance.get("skip_rate"))

    has_real_data = any(value is not None for value in [save_rate, share_rate, comment_depth_score, view_rate, skip_rate])

    source_mode = "real_data" if has_real_data else "conservative_fallback"
    data_confidence = "high" if has_real_data else "low"

    linked_series_candidate = bool(serial.get("sequel_candidate"))
    serial_distribution_hint = (
        "continuar a série em 24-48h para aproveitar continuidade editorial"
        if linked_series_candidate
        else "tratar como peça isolada até surgir continuidade real"
    )

    if fmt == "carousel" and save_rate is not None and save_rate >= 0.06:
        format_hour_hint = "07:00-09:00"
        distribution_reason = "histórico sugere que carrossel salva bem e merece janela de leitura mais intencional"
    elif fmt == "story" and view_rate is not None and view_rate >= 0.35:
        format_hour_hint = "11:00-13:00"
        distribution_reason = "histórico sugere boa abertura de stories em janelas curtas"
    elif fmt == "image" and share_rate is not None and share_rate >= 0.03:
        format_hour_hint = "12:00-18:00"
        distribution_reason = "imagem com share razoável pede janela social útil"
    else:
        format_hour_hint = defaults["format_hour_hint"]
        distribution_reason = defaults["distribution_reason"]

    timing_hypothesis = defaults["timing_hypothesis"]
    if linked_series_candidate:
        timing_hypothesis = f"{timing_hypothesis}; continuação serial tende a ganhar tração se a próxima peça sair sem quebrar o fio narrativo"

    return {
        "ok": True,
        "format_recommendation": fmt,
        "timing_hypothesis": timing_hypothesis,
        "format_hour_hint": format_hour_hint,
        "serial_distribution_hint": serial_distribution_hint,
        "linked_series_candidate": linked_series_candidate,
        "attention_metric_targets": defaults["attention_metric_targets"],
        "distribution_reason": distribution_reason,
        "data_confidence": data_confidence,
        "source_mode": source_mode,
        "signals_seen": {
            "save_rate": save_rate,
            "share_rate": share_rate,
            "comment_depth_score": comment_depth_score,
            "view_rate": view_rate,
            "skip_rate": skip_rate,
            "signal_source": signal.get("source"),
        },
    }


def distribution_timing_examples() -> dict[str, Any]:
    return {
        "ok": True,
        "carousel_real_data": build_distribution_context_v1(
            format_recommendation="carousel",
            serial_continuity={"sequel_candidate": True},
            performance_context={"save_rate": 0.08, "share_rate": 0.03},
            signal_context={"source": "performance_memory"},
        ),
        "story_fallback": build_distribution_context_v1(
            format_recommendation="story",
            serial_continuity={"sequel_candidate": False},
            performance_context={},
            signal_context={"source": "planner"},
        ),
    }
