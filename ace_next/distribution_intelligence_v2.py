from __future__ import annotations

import re
from typing import Any

from .distribution_timing_v1 import build_distribution_context_v1
from .serial_continuity_engine_v1 import build_serial_continuity_engine_v1


FORMAT_WINDOWS = {
    "image": ["12:00-18:00", "18:00-20:00"],
    "carousel": ["07:00-09:00", "20:00-22:00"],
    "story": ["11:00-13:00", "18:00-21:00"],
    "reel": ["12:00-14:00", "19:00-22:00"],
}

FORMAT_SIGNAL_PRIORITY = {
    "image": ["save_rate", "share_rate", "comment_depth_score"],
    "carousel": ["save_rate", "share_rate", "completion_rate"],
    "story": ["view_rate", "reply_rate", "completion_rate"],
    "reel": ["completion_rate", "watch_time_ms", "replay_rate", "share_rate"],
}

SEO_STOPWORDS = {
    "para", "com", "sem", "isso", "essa", "esse", "como", "mais", "menos", "sobre",
    "uma", "uns", "umas", "por", "que", "das", "dos", "nas", "nos", "the", "and",
    "de", "da", "do", "em", "ou", "se", "já", "aqui", "porque", "quando", "onde",
}


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize(value: Any) -> str:
    return _clean(value).lower()


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _normalize_format(value: Any) -> str:
    normalized = _normalize(value)
    if normalized in {"story", "stories"}:
        return "story"
    if normalized in {"carousel", "image", "reel"}:
        return normalized
    return "image"


def _keywords(*parts: Any) -> list[str]:
    joined = " ".join(_clean(part) for part in parts if _clean(part))
    words = re.findall(r"[a-zà-ÿ0-9]{3,}", _normalize(joined))
    unique: list[str] = []
    for word in words:
        if word in SEO_STOPWORDS:
            continue
        if word not in unique:
            unique.append(word)
    return unique[:12]


def _extract_recent_records(memory_context: dict[str, Any]) -> list[dict[str, Any]]:
    memory_context = _safe_dict(memory_context)
    recent: list[dict[str, Any]] = []

    for key in [
        "recent_content",
        "recent_posts",
        "ace_content_history",
        "ace_candidate_posts",
    ]:
        for item in _safe_list(memory_context.get(key)):
            if isinstance(item, dict):
                recent.append(item)

    episodic = _safe_dict(memory_context.get("episodic_performance_memory"))
    for key in ["records", "episodes", "items"]:
        for item in _safe_list(episodic.get(key)):
            if isinstance(item, dict):
                recent.append(item)

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in recent:
        identity = _clean(
            item.get("id")
            or item.get("record_id")
            or item.get("episode_id")
            or item.get("headline")
            or item.get("hook")
        )
        if identity and identity not in seen:
            seen.add(identity)
            deduped.append(item)
    return deduped[-24:]


def _metric_value(record: dict[str, Any], key: str) -> float | None:
    real_metrics = _safe_dict(record.get("real_metrics"))
    attention_metrics = _safe_dict(record.get("attention_metrics"))
    performance = _safe_dict(record.get("performance_context"))
    creative_plan = _safe_dict(record.get("creative_plan"))
    distribution = _safe_dict(creative_plan.get("distribution_context"))

    for source in [real_metrics, attention_metrics, performance, distribution]:
        value = _safe_float(source.get(key))
        if value is not None:
            return value
    return None


def _record_format(record: dict[str, Any]) -> str:
    creative_plan = _safe_dict(record.get("creative_plan"))
    return _normalize_format(
        creative_plan.get("publish_format_now")
        or creative_plan.get("format_recommendation")
        or record.get("publish_format_now")
        or record.get("format_recommendation")
    )


def _format_score(record: dict[str, Any], fmt: str) -> float:
    if _record_format(record) != fmt:
        return -1.0

    signals = {
        "save_rate": _metric_value(record, "save_rate") or 0.0,
        "share_rate": _metric_value(record, "share_rate") or 0.0,
        "completion_rate": _metric_value(record, "completion_rate") or 0.0,
        "retention_rate": _metric_value(record, "retention_rate") or 0.0,
        "watch_time_ms": _metric_value(record, "watch_time_ms") or 0.0,
        "replay_rate": _metric_value(record, "replay_rate") or 0.0,
        "view_rate": _metric_value(record, "view_rate") or 0.0,
        "reply_rate": _metric_value(record, "reply_rate") or 0.0,
    }

    return round(
        (signals["share_rate"] * 0.24)
        + (signals["save_rate"] * 0.22)
        + (signals["completion_rate"] * 0.18)
        + (signals["retention_rate"] * 0.12)
        + (signals["replay_rate"] * 0.10)
        + (signals["view_rate"] * 0.07)
        + (signals["reply_rate"] * 0.03)
        + (min(signals["watch_time_ms"] / 10000.0, 1.0) * 0.04),
        4,
    )


def _best_format_from_history(records: list[dict[str, Any]]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for fmt in ["image", "carousel", "story", "reel"]:
        scores = [score for score in (_format_score(record, fmt) for record in records) if score >= 0.0]
        if not scores:
            continue
        candidates.append(
            {
                "format": fmt,
                "count": len(scores),
                "avg_score": round(sum(scores) / max(len(scores), 1), 4),
            }
        )

    if not candidates:
        return {"format": "", "count": 0, "avg_score": 0.0}

    candidates.sort(key=lambda item: (item["avg_score"], item["count"]), reverse=True)
    return candidates[0]


def _build_timing_matrix(current_format: str, best_history_format: dict[str, Any]) -> dict[str, Any]:
    matrix: dict[str, Any] = {}
    best_format = _clean(best_history_format.get("format"))

    for fmt, windows in FORMAT_WINDOWS.items():
        preferred_window = windows[0]
        confidence = "low"
        reason = "fallback conservador por formato"

        if best_format == fmt and best_history_format.get("count", 0) >= 2:
            preferred_window = windows[0]
            confidence = "high"
            reason = "histórico recente sugere maior aderência deste formato"
        elif fmt == current_format:
            preferred_window = windows[0]
            confidence = "medium"
            reason = "janela preferida do formato atual"
        else:
            preferred_window = windows[-1]
            confidence = "low"
            reason = "janela secundária para diversificação"

        matrix[fmt] = {
            "preferred_window": preferred_window,
            "all_windows": windows,
            "confidence": confidence,
            "reason": reason,
            "priority_signals": FORMAT_SIGNAL_PRIORITY[fmt],
        }

    return matrix


def _build_seo_social_context(topic_seed: str, hook: str, angle: str, current_plan: dict[str, Any]) -> dict[str, Any]:
    current_plan = _safe_dict(current_plan)
    body = _clean(current_plan.get("body"))
    headline = _clean(current_plan.get("headline"))
    cta = _clean(current_plan.get("cta"))

    keyword_candidates = _keywords(topic_seed, hook, angle, headline, body)
    on_screen_keywords = keyword_candidates[:4]
    caption_keywords = keyword_candidates[:8]

    hashtag_candidates = [f"#{word.replace(' ', '')}" for word in keyword_candidates[:5]]

    return {
        "keyword_candidates": keyword_candidates,
        "on_screen_keywords": on_screen_keywords,
        "caption_keywords": caption_keywords,
        "hashtag_candidates": hashtag_candidates,
        "seo_reason": "prioriza discoverability por linguagem natural, texto em tela e legenda estratégica",
        "cta_distribution_hint": _clean(cta) or "fechar com CTA de save ou share conforme objetivo editorial",
    }


def build_distribution_intelligence_v2(
    *,
    topic_seed: str,
    hook: str,
    angle: str,
    format_recommendation: str,
    sequel_potential: str = "medium",
    memory_context: dict[str, Any] | None = None,
    performance_context: dict[str, Any] | None = None,
    signal_context: dict[str, Any] | None = None,
    current_plan: dict[str, Any] | None = None,
    series_name: str | None = None,
) -> dict[str, Any]:
    memory_context = _safe_dict(memory_context)
    performance_context = _safe_dict(performance_context)
    signal_context = _safe_dict(signal_context)
    current_plan = _safe_dict(current_plan)

    fmt = _normalize_format(format_recommendation)
    recent_records = _extract_recent_records(memory_context)
    best_history_format = _best_format_from_history(recent_records)

    serial_continuity = build_serial_continuity_engine_v1(
        topic_seed=topic_seed,
        hook=hook,
        angle=angle,
        sequel_potential=sequel_potential,
        memory_context=memory_context,
        series_name=series_name,
    )

    distribution_context = build_distribution_context_v1(
        format_recommendation=fmt,
        serial_continuity=serial_continuity,
        performance_context=performance_context,
        signal_context=signal_context,
    )

    timing_matrix = _build_timing_matrix(fmt, best_history_format)
    seo_social = _build_seo_social_context(topic_seed, hook, angle, current_plan)

    recommended_next_format = fmt
    recommended_next_format_reason = "manter formato recomendado atual"
    if best_history_format.get("format") and best_history_format.get("avg_score", 0.0) >= 0.12:
        recommended_next_format = _clean(best_history_format.get("format"))
        recommended_next_format_reason = "histórico recente sugere viés tático para formato com melhor score"

    recommended_timing_hypothesis = _clean(distribution_context.get("timing_hypothesis"))
    preferred_window = _safe_dict(timing_matrix.get(recommended_next_format)).get("preferred_window") or distribution_context.get("format_hour_hint")

    confidence = "low"
    if recent_records and best_history_format.get("count", 0) >= 3:
        confidence = "high"
    elif recent_records:
        confidence = "medium"

    return {
        "ok": True,
        "module": "distribution_intelligence_v2",
        "format_recommendation": fmt,
        "recommended_next_format": recommended_next_format,
        "recommended_next_format_reason": recommended_next_format_reason,
        "recommended_timing_hypothesis": recommended_timing_hypothesis,
        "recommended_publish_window": preferred_window,
        "confidence": confidence,
        "distribution_context": distribution_context,
        "serial_continuity": serial_continuity,
        "timing_matrix": timing_matrix,
        "seo_social": seo_social,
        "best_history_format": best_history_format,
        "records_considered": len(recent_records),
        "study_tags": {
            "timing_optimized": True,
            "dynamic_format_hour_matrix": True,
            "serial_continuity": True,
            "seo_social": True,
        },
        "reasoning_trace": [
            f"current_format={fmt}",
            f"best_history_format={_clean(best_history_format.get('format'))}",
            f"records_considered={len(recent_records)}",
            f"preferred_window={preferred_window}",
            f"continuity_mode={_clean(serial_continuity.get('continuity_source_mode'))}",
            f"distribution_mode={_clean(distribution_context.get('source_mode'))}",
        ],
    }


def distribution_intelligence_examples() -> dict[str, Any]:
    return {
        "ok": True,
        "example_reel": build_distribution_intelligence_v2(
            topic_seed="clareza e disciplina no caos digital",
            hook="O problema quase nunca é falta de esforço.",
            angle="disciplina sem eixo vira desperdício",
            format_recommendation="reel",
            sequel_potential="high",
            memory_context={
                "recent_content": [
                    {
                        "record_id": "r1",
                        "creative_plan": {"publish_format_now": "reel"},
                        "real_metrics": {"share_rate": 0.06, "completion_rate": 0.62, "watch_time_ms": 9100},
                    },
                    {
                        "record_id": "r2",
                        "creative_plan": {"publish_format_now": "carousel"},
                        "real_metrics": {"save_rate": 0.09, "share_rate": 0.03},
                    },
                ]
            },
            performance_context={"share_rate": 0.04, "completion_rate": 0.57, "watch_time_ms": 8200},
            signal_context={"source": "performance_memory"},
            current_plan={"headline": "Sem eixo, intensidade vira ruído.", "cta": "salve para revisar antes do próximo impulso"},
        )
    }
