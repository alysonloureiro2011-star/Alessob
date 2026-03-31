from __future__ import annotations

from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _call_engine(symbol: Any, **kwargs: Any) -> dict[str, Any]:
    if symbol is None:
        return {}
    try:
        result = symbol(**kwargs)
        return result if isinstance(result, dict) else {}
    except Exception as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def build_distribution_intelligence_v2(
    *,
    records: list[dict[str, Any]] | None = None,
    distribution_timing_engine: Any | None = None,
    seo_social_engine: Any | None = None,
) -> dict[str, Any]:
    records = [_safe_dict(item) for item in _safe_list(records)]

    timing_block = _call_engine(
        distribution_timing_engine,
        records=records,
    )
    seo_block = _call_engine(
        seo_social_engine,
        records=records,
    )

    recommended_timing_hypothesis = _text(
        timing_block.get("recommended_timing_hypothesis")
    )
    recommended_format = _text(
        timing_block.get("recommended_next_format")
        or timing_block.get("recommended_format")
    )
    recommended_style_bias = _text(
        timing_block.get("recommended_style_bias")
    )
    recommended_hashtags = _safe_list(
        seo_block.get("recommended_hashtags")
    )
    recommended_caption_hooks = _safe_list(
        seo_block.get("recommended_caption_hooks")
    )

    confidence = _text(
        timing_block.get("confidence")
        or seo_block.get("confidence")
        or "low"
    ) or "low"

    distribution_mode = _text(
        timing_block.get("distribution_mode")
        or "conservative_exploration"
    ) or "conservative_exploration"

    notes: list[str] = [
        f"records={len(records)}",
        f"confidence={confidence}",
        f"distribution_mode={distribution_mode}",
        f"recommended_timing={recommended_timing_hypothesis}",
        f"recommended_format={recommended_format}",
        f"recommended_style_bias={recommended_style_bias}",
        f"hashtags={len(recommended_hashtags)}",
        f"caption_hooks={len(recommended_caption_hooks)}",
    ]

    if timing_block.get("error"):
        notes.append(f"timing_engine_error={timing_block.get('error')}")
    if seo_block.get("error"):
        notes.append(f"seo_engine_error={seo_block.get('error')}")

    return {
        "ok": True,
        "module": "distribution_intelligence_v2",
        "records": len(records),
        "confidence": confidence,
        "distribution_mode": distribution_mode,
        "recommended_timing_hypothesis": recommended_timing_hypothesis,
        "recommended_format": recommended_format,
        "recommended_next_format": recommended_format,
        "recommended_style_bias": recommended_style_bias,
        "recommended_hashtags": recommended_hashtags,
        "recommended_caption_hooks": recommended_caption_hooks,
        "recommended_description_policy": _text(
            seo_block.get("recommended_description_policy")
        ),
        "recommended_metadata_policy": _safe_dict(
            seo_block.get("recommended_metadata_policy")
        ),
        "recommended_next_angle": (
            "reforçar clareza causal, tensão narrativa e payoff concreto"
            if confidence in {"medium", "high"}
            else "manter hipótese conservadora e reduzir ruído na promessa"
        ),
        "recommended_next_series_action": (
            "aprofundar o fio que já mostrou sinal sem abrir nova frente"
            if confidence == "high"
            else "testar continuidade leve sem tratar o sinal como vitória final"
            if confidence == "medium"
            else "manter peça isolada até existir leitura mais confiável"
        ),
        "source_mode": (
            "timing_and_seo_engines"
            if timing_block or seo_block
            else "conservative_fallback"
        ),
        "timing_engine": timing_block,
        "seo_engine": seo_block,
        "study_alignment": {
            "timing_optimization": True,
            "format_bias_learning": True,
            "distribution_intelligence": True,
            "social_seo": True,
            "instagram_first": True,
            "multiplatform_ready": True,
        },
        "notes": notes,
    }
