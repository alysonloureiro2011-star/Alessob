from __future__ import annotations

from typing import Any

PRIORITY_SIGNALS = [
    "save_rate",
    "share_rate",
    "completion_rate",
    "retention_rate",
    "watch_time_ms",
    "replay_rate",
]


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _extract_metric(real_metrics: dict[str, Any], attention_metrics: dict[str, Any], *keys: str) -> float:
    for key in keys:
        if key in real_metrics:
            return _safe_number(real_metrics.get(key))
        if key in attention_metrics:
            return _safe_number(attention_metrics.get(key))
    return 0.0


def _extract_signals(record: dict[str, Any]) -> dict[str, float]:
    real_metrics = _safe_dict(record.get("real_metrics"))
    attention_metrics = _safe_dict(record.get("attention_metrics"))

    return {
        "save_rate": _extract_metric(real_metrics, attention_metrics, "save_rate", "saves_rate", "save_ratio"),
        "share_rate": _extract_metric(real_metrics, attention_metrics, "share_rate", "shares_rate", "share_ratio"),
        "completion_rate": _extract_metric(real_metrics, attention_metrics, "completion_rate", "completion_ratio"),
        "retention_rate": _extract_metric(real_metrics, attention_metrics, "retention_rate", "watch_time_ratio"),
        "watch_time_ms": _extract_metric(real_metrics, attention_metrics, "watch_time_ms", "watch_time"),
        "replay_rate": _extract_metric(real_metrics, attention_metrics, "replay_rate", "replay_ratio"),
    }


def _score_signal_pack(signals: dict[str, float]) -> dict[str, Any]:
    weighted_score = (
        signals.get("save_rate", 0.0) * 0.24
        + signals.get("share_rate", 0.0) * 0.24
        + signals.get("completion_rate", 0.0) * 0.18
        + signals.get("retention_rate", 0.0) * 0.18
        + signals.get("replay_rate", 0.0) * 0.10
        + min(signals.get("watch_time_ms", 0.0) / 10000.0, 1.0) * 0.06
    )

    if weighted_score >= 0.72:
        quality_band = "strong"
    elif weighted_score >= 0.46:
        quality_band = "mixed"
    else:
        quality_band = "weak"

    return {
        "weighted_score": round(weighted_score, 4),
        "quality_band": quality_band,
    }


def build_learning_decision_policy(record: dict[str, Any] | None) -> dict[str, Any]:
    latest = _safe_dict(record)
    if not latest:
        return {
            "ok": True,
            "policy_state": "no_record",
            "priority_signals": list(PRIORITY_SIGNALS),
            "signals": {},
            "score": {"weighted_score": 0.0, "quality_band": "unknown"},
            "next_cycle_strategy": {
                "hook_strategy": "neutral",
                "format_strategy": "neutral",
                "style_strategy": "neutral",
                "timing_strategy": "neutral",
            },
            "reasons": ["sem record para orientar próximo ciclo"],
        }

    signals = _extract_signals(latest)
    score = _score_signal_pack(signals)
    quality_band = score.get("quality_band")

    if quality_band == "strong":
        strategy = {
            "hook_strategy": "exploit_best_hook",
            "format_strategy": "reinforce_winning_format",
            "style_strategy": "preserve_high_signal_style",
            "timing_strategy": "repeat_high_signal_window",
        }
        reasons = [
            "save/share/completion em banda forte",
            "repetir padrão vencedor com ajuste fino conservador",
        ]
    elif quality_band == "mixed":
        strategy = {
            "hook_strategy": "tighten_hook_opening",
            "format_strategy": "keep_format_test_new_angle",
            "style_strategy": "preserve_style_reduce_noise",
            "timing_strategy": "test_adjacent_window",
        }
        reasons = [
            "resultado misto: preservar parte vencedora e testar ângulo/timing",
        ]
    else:
        strategy = {
            "hook_strategy": "replace_hook_family",
            "format_strategy": "test_new_format",
            "style_strategy": "reduce_genericity_raise_naturalism",
            "timing_strategy": "shift_distribution_window",
        }
        reasons = [
            "sinais fracos: trocar hook/formato e elevar naturalismo",
        ]

    return {
        "ok": True,
        "policy_state": "decision_ready",
        "priority_signals": list(PRIORITY_SIGNALS),
        "signals": signals,
        "score": score,
        "next_cycle_strategy": strategy,
        "reasons": reasons,
        "record_id": latest.get("record_id"),
        "operational_state": latest.get("operational_state"),
        "publish_status": latest.get("publish_status"),
    }
