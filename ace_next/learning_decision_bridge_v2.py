# ACE Ω — LEARNING DECISION BRIDGE V2
# NÃO SUBSTITUI NADA. MÓDULO ADITIVO.

from __future__ import annotations
from typing import Any

from .learning_loop import build_learning_loop_summary

PRIORITY_SIGNALS = [
    "share_rate",
    "save_rate",
    "completion_rate",
    "retention_rate",
    "watch_time_ms",
    "replay_rate",
]


def _safe_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _safe_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _f(v: Any) -> float:
    try:
        return float(v)
    except:
        return 0.0


def _metrics(record: dict) -> dict:
    r = _safe_dict(record.get("real_metrics"))
    a = _safe_dict(record.get("attention_metrics"))
    return {
        "share": _f(r.get("share_rate") or a.get("share_rate")),
        "save": _f(r.get("save_rate") or a.get("save_rate")),
        "completion": _f(r.get("completion_rate") or a.get("completion_rate")),
        "retention": _f(r.get("retention_rate") or a.get("retention_rate")),
        "watch": _f(r.get("watch_time_ms") or a.get("watch_time_ms")),
        "replay": _f(r.get("replay_rate") or a.get("replay_rate")),
    }


def _score(m: dict) -> float:
    return (
        m["share"] * 0.25
        + m["save"] * 0.22
        + m["completion"] * 0.22
        + m["retention"] * 0.16
        + m["replay"] * 0.10
        + min(m["watch"] / 10000.0, 1.0) * 0.05
    )


def _best(records: list[dict]) -> dict:
    ranked = [(r, _score(_metrics(r))) for r in records]
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked[0][0] if ranked else {}


def build_learning_decision_bridge_v2(*, records: list[dict], latest_record: dict | None = None) -> dict:
    records = [_safe_dict(r) for r in _safe_list(records)]
    latest = _safe_dict(latest_record or (records[-1] if records else {}))

    summary = build_learning_loop_summary(records=records, latest_record=latest)

    best = _best(records)
    m = _metrics(best)

    plan = _safe_dict(best.get("creative_plan"))
    dist = _safe_dict(plan.get("distribution_context"))

    decision = {
        "next_format": dist.get("recommended_next_format") or plan.get("publish_format_now") or "reel",
        "next_timing": dist.get("recommended_timing_hypothesis") or "test_peak_window",
        "next_angle": dist.get("recommended_next_angle") or "high_tension_clarity",
        "next_hook": plan.get("hook") or "optimize_0_3s",
        "next_series": dist.get("recommended_next_series_action") or "continue_series",
    }

    ready = summary.get("latest_experiment_state") not in ["repeat_probe", "collecting"]

    return {
        "ok": True,
        "module": "learning_decision_bridge_v2",
        "ready": ready,
        "confidence": "high" if ready and _score(m) > 0.35 else "low",
        "decision": decision,
        "metrics": m,
        "summary": summary,
    }
