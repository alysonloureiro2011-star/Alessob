from __future__ import annotations

from typing import Any

from .learning_loop_v2 import run_learning_v2


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def build_learning_strategy_bridge(latest_record: dict[str, Any] | None) -> dict[str, Any]:
    record = _safe_dict(latest_record)
    if not record:
        return {
            "ok": True,
            "strategy_state": "no_record",
            "decision": {
                "next_hook_strategy": "neutral",
                "next_format_strategy": "neutral",
                "next_style_strategy": "neutral",
                "next_timing_strategy": "neutral",
            },
            "signals": {},
            "outcome": {},
        }

    result = _safe_dict(run_learning_v2(record))
    decision = _safe_dict(result.get("decision"))
    signals = _safe_dict(result.get("signals"))
    outcome = _safe_dict(result.get("outcome"))

    return {
        "ok": result.get("ok", True),
        "strategy_state": "decision_ready" if decision else "decision_empty",
        "decision": {
            "next_hook_strategy": decision.get("next_hook_strategy", "neutral"),
            "next_format_strategy": decision.get("next_format_strategy", "neutral"),
            "next_style_strategy": decision.get("next_style_strategy", "neutral"),
            "next_timing_strategy": decision.get("next_timing_strategy", "neutral"),
        },
        "signals": signals,
        "outcome": outcome,
        "record_id": record.get("record_id"),
        "publish_status": record.get("publish_status"),
        "operational_state": record.get("operational_state"),
    }
