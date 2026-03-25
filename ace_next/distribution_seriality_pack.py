from __future__ import annotations

import re
from typing import Any

FORMAT_HOUR_MATRIX = {
    "image": {
        "primary_window": "12:00-18:00",
        "secondary_window": "19:00-21:00",
        "timing_hypothesis": "imagem tende a performar melhor quando a leitura é rápida e o usuário ainda consegue salvar depois",
    },
    "carousel": {
        "primary_window": "07:00-09:00",
        "secondary_window": "18:00-21:00",
        "timing_hypothesis": "carrossel tende a performar melhor em janelas de leitura mais longa e intenção de salvamento",
    },
    "story": {
        "primary_window": "11:00-13:00",
        "secondary_window": "18:00-20:00",
        "timing_hypothesis": "story tende a responder melhor em janelas curtas de atenção recorrente",
    },
    "reel": {
        "primary_window": "19:00-22:00",
        "secondary_window": "12:00-14:00",
        "timing_hypothesis": "reel tende a pedir janela de entretenimento e retenção competitiva",
    },
}


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


def _extract_signal_reading(performance_context: dict[str, Any], signal_context: dict[str, Any]) -> dict[str, Any]:
    performance_context = _safe_dict(performance_context)
    signal_context = _safe_dict(signal_context)

    reading = {
        "save_rate": _safe_float(performance_context.get("save_rate")),
        "share_rate": _safe_float(performance_context.get("share_rate")),
        "comment_depth_score": _safe_float(performance_context.get("comment_depth_score")),
        "view_rate": _safe_float(performance_context.get("view_rate")),
        "skip_rate": _safe_float(performance_context.get("skip_rate")),
        "views_over_time": performance_context.get("views_over_time"),
        "source_status": performance_context.get("source_status"),
        "signal_source": signal_context.get("source") or performance_context.get("source") or "planner",
    }
    has_real_signal = any(
        reading[key] is not None
        for key in ("save_rate", "share_rate", "comment_depth_score", "view_rate", "skip_rate")
    ) or bool(reading.get("views_over_time"))
    reading["source_mode"] = "real_signal" if has_real_signal else "conservative_fallback"
    reading["signal_confidence"] = "high" if has_real_signal else "low"
    return reading


def _hashtag_intelligence(topic_seed: str) -> list[str]:
    words = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", str(topic_seed or "").lower())
    stopwords = {
        "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos", "e", "em",
        "mais", "menos", "na", "nas", "no", "nos", "o", "os", "ou", "para", "por", "que",
        "se", "sem", "sobre", "um", "uma", "uns", "umas",
    }
    unique: list[str] = []
    for word in words:
        if len(word) < 3 or word in stopwords:
            continue
        slug = "#" + re.sub(r"[^a-z0-9]+", "", word)
        if slug and slug not in unique:
            unique.append(slug)
    seed_tags = unique[:4]
    seed_tags.extend(["#libertaaverdade", "#valorreal", "#clareza"])
    deduped: list[str] = []
    for item in seed_tags:
        if item not in deduped:
            deduped.append(item)
    return deduped[:8]


def _recommended_next_angle(signal_reading: dict[str, Any]) -> str:
    if signal_reading.get("skip_rate") is not None and float(signal_reading["skip_rate"]) >= 0.45:
        return "encurtar abertura, reduzir ruído e antecipar payoff concreto"
    if signal_reading.get("save_rate") is not None and float(signal_reading["save_rate"]) >= 0.06:
        return "aprofundar utilidade prática e reforçar estrutura de salvamento"
    if signal_reading.get("share_rate") is not None and float(signal_reading["share_rate"]) >= 0.03:
        return "explorar ângulo mais compartilhável sem inflar promessa"
    return "reforçar clareza causal e payoff concreto"


def _recommended_next_format(current_format: str, signal_reading: dict[str, Any], linked_series_candidate: bool) -> str:
    if linked_series_candidate and current_format in {"image", "story"}:
        return "carousel"
    if signal_reading.get("view_rate") is not None and float(signal_reading["view_rate"]) >= 0.4:
        return "reel"
    return current_format


def build_distribution_seriality_pack(
    *,
    topic_seed: str,
    format_recommendation: str,
    serial_continuity: dict[str, Any] | None = None,
    performance_context: dict[str, Any] | None = None,
    signal_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fmt = _normalize_format(format_recommendation)
    serial = _safe_dict(serial_continuity)
    signal_reading = _extract_signal_reading(_safe_dict(performance_context), _safe_dict(signal_context))
    linked_series_candidate = bool(
        serial.get("linked_series_candidate")
        or serial.get("sequel_candidate")
    )

    matrix = dict(FORMAT_HOUR_MATRIX[fmt])
    recommended_next_format = _recommended_next_format(fmt, signal_reading, linked_series_candidate)
    recommended_next_angle = _recommended_next_angle(signal_reading)
    recommended_next_series_action = (
        "publicar continuação em 24-48h"
        if linked_series_candidate
        else "manter peça isolada até surgir continuidade real"
    )
    recommended_timing_hypothesis = matrix["timing_hypothesis"]
    if linked_series_candidate:
        recommended_timing_hypothesis = (
            f"{recommended_timing_hypothesis}; continuidade tende a ganhar tração se a próxima peça sair sem quebrar o fio narrativo"
        )

    sequel_recommendation = {
        "linked_series_candidate": linked_series_candidate,
        "next_episode_seed": serial.get("next_episode_seed"),
        "episode_index_hint": serial.get("episode_index_hint"),
        "sequel_recommendation": (
            "continuar a série com aprofundamento controlado"
            if linked_series_candidate
            else "não forçar serialidade ainda"
        ),
    }

    winner_expansion_policy = (
        "expandir apenas em editorial_staging ou internal_lab; nunca autorizar brand_live automaticamente"
    )

    seo_editorial = {
        "hashtags": _hashtag_intelligence(topic_seed),
        "caption_guidance": "legenda concreta, menos abstrata, sem coach barato e sem promessa inflada",
        "avoid_abstract_excess": True,
    }

    return {
        "ok": True,
        "source_mode": signal_reading["source_mode"],
        "signal_reading": signal_reading,
        "format_hour_matrix": FORMAT_HOUR_MATRIX,
        "recommended_next_format": recommended_next_format,
        "recommended_next_angle": recommended_next_angle,
        "recommended_next_series_action": recommended_next_series_action,
        "recommended_timing_hypothesis": recommended_timing_hypothesis,
        "linked_series_candidate": linked_series_candidate,
        "sequel_recommendation": sequel_recommendation,
        "winner_expansion_policy": winner_expansion_policy,
        "serial_publishing_logic": {
            "linked_series_candidate": linked_series_candidate,
            "sequel_recommendation": sequel_recommendation["sequel_recommendation"],
            "winner_expansion_policy": winner_expansion_policy,
        },
        "seo_editorial": seo_editorial,
        "brand_live_allowed": False,
        "authorization_scope": "recommend_only",
        "primary_window": matrix["primary_window"],
        "secondary_window": matrix["secondary_window"],
    }
