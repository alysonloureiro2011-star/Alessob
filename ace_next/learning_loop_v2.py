from typing import Dict, Any


def extract_signals(record: Dict[str, Any]) -> Dict[str, Any]:
    perf = record.get("performance_ingest", {}) or {}
    attention = record.get("attention_metrics", {}) or {}

    return {
        "watch_time": perf.get("watch_time") or attention.get("watch_time"),
        "completion_rate": perf.get("completion_rate"),
        "shares": perf.get("shares"),
        "saves": perf.get("saves"),
    }


def evaluate_outcome(signals: Dict[str, Any]) -> Dict[str, Any]:
    score = 0

    if signals.get("watch_time", 0) > 5:
        score += 1
    if signals.get("completion_rate", 0) > 0.5:
        score += 1
    if signals.get("shares", 0) > 0:
        score += 1
    if signals.get("saves", 0) > 0:
        score += 1

    return {
        "score": score,
        "is_strong": score >= 3,
        "is_weak": score <= 1,
    }


def decide_next_strategy(record: Dict[str, Any]) -> Dict[str, Any]:
    signals = extract_signals(record)
    outcome = evaluate_outcome(signals)

    decision = {
        "next_hook_strategy": "neutral",
        "next_format_strategy": "neutral",
        "next_style_strategy": "neutral",
        "next_timing_strategy": "neutral",
    }

    if outcome["is_strong"]:
        decision.update({
            "next_hook_strategy": "replicate",
            "next_format_strategy": "replicate",
            "next_style_strategy": "replicate",
            "next_timing_strategy": "replicate",
        })

    elif outcome["is_weak"]:
        decision.update({
            "next_hook_strategy": "change",
            "next_format_strategy": "change",
            "next_style_strategy": "change",
            "next_timing_strategy": "shift",
        })

    return {
        "signals": signals,
        "outcome": outcome,
        "decision": decision,
    }


def run_learning_v2(record: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return decide_next_strategy(record)
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "fallback": True,
        }
