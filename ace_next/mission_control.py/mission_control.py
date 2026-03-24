from __future__ import annotations

import re
import unicodedata
from typing import Any


WEAK_TRENDS = {
    "",
    "123",
    "hello",
    "oi",
    "test",
    "teste",
    "teste real",
}

TREND_FALLBACK = "clareza, disciplina e direção"
STYLE_FALLBACK = "official_next_visual_foundation_v1"
CONTENT_TYPE_FALLBACK = "image"
PLANNER_FALLBACK = "planner_unavailable_fallback"


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value or "")
        if not unicodedata.combining(char)
    )


def _normalize(value: Any) -> str:
    return _strip_accents(_clean_text(value)).lower()


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _queue_snapshot(queue_state: dict | None) -> dict[str, int]:
    queue_state = queue_state or {}
    return {
        "active_jobs": max(0, _coerce_int(queue_state.get("active_jobs"), 0)),
        "pending_jobs": max(0, _coerce_int(queue_state.get("pending_jobs"), 0)),
    }


def _trend_is_weak(trend_normalized: str) -> bool:
    return trend_normalized in WEAK_TRENDS


def _infer_signal_strength(recent_signal_score: float | None) -> str:
    if recent_signal_score is None:
        return "unknown"
    if recent_signal_score < 0.35:
        return "weak"
    if recent_signal_score >= 0.70:
        return "strong"
    return "medium"


def _build_goal(content_type: str) -> str:
    normalized = _normalize(content_type)
    if normalized == "reel":
        return "retention"
    if normalized == "carousel":
        return "saveability"
    if normalized == "story":
        return "engagement"
    return "authority"


def _build_hypothesis(content_type: str, style: str, goal: str, signal_strength: str) -> str:
    return (
        f"{_normalize(content_type) or 'image'}__"
        f"{_normalize(style) or 'official'}__"
        f"{_normalize(goal) or 'authority'}__"
        f"{_normalize(signal_strength) or 'unknown'}"
    )


def _build_priority(
    *,
    queue_full: bool,
    trend_weak: bool,
    signal_strength: str,
    planner_ok: bool,
) -> float:
    if queue_full:
        return 0.20
    if trend_weak:
        return 0.25
    if signal_strength == "strong":
        return 0.82 if planner_ok else 0.75
    if signal_strength == "medium":
        return 0.60 if planner_ok else 0.55
    if signal_strength == "weak":
        return 0.30
    return 0.55 if planner_ok else 0.50


def _build_confidence(
    *,
    queue_full: bool,
    trend_weak: bool,
    signal_strength: str,
    planner_ok: bool,
) -> float:
    if queue_full:
        return 0.22
    if trend_weak:
        return 0.28
    if signal_strength == "strong":
        return 0.86 if planner_ok else 0.78
    if signal_strength == "medium":
        return 0.67 if planner_ok else 0.58
    if signal_strength == "weak":
        return 0.31
    return 0.52 if planner_ok else 0.45


def _planner_bridge(trend: str, format_hint: str | None = None) -> dict[str, Any]:
    try:
        from ace_next.creative_planner import build_creative_plan

        plan = build_creative_plan(trend)
        plan_dict = plan.to_dict() if hasattr(plan, "to_dict") else dict(plan)

        raw_format = (
            plan_dict.get("format_recommendation")
            or plan_dict.get("publish_format_now")
            or plan_dict.get("strategic_target_format")
            or format_hint
            or CONTENT_TYPE_FALLBACK
        )

        content_type = _normalize(raw_format)
        if content_type in {"reel_premium", "reels", "video"}:
            content_type = "reel"
        elif content_type in {"carrossel", "carousel"}:
            content_type = "carousel"
        elif content_type in {"stories", "story"}:
            content_type = "story"
        elif content_type in {"image", "imagem", "post"}:
            content_type = "image"
        elif not content_type:
            content_type = CONTENT_TYPE_FALLBACK

        style = (
            _clean_text(plan_dict.get("publish_style"))
            or _clean_text(plan_dict.get("visual_style"))
            or STYLE_FALLBACK
        )

        planner_selected = (
            _clean_text(plan_dict.get("planner_selected"))
            or "creative_planner_bridge_ok"
        )

        return {
            "ok": True,
            "content_type": content_type,
            "style": style,
            "planner_selected": planner_selected,
        }
    except Exception:
        fallback_type = _normalize(format_hint) or CONTENT_TYPE_FALLBACK
        if fallback_type in {"carrossel"}:
            fallback_type = "carousel"
        if fallback_type in {"stories"}:
            fallback_type = "story"
        if fallback_type in {"reel_premium", "reels", "video"}:
            fallback_type = "reel"
        if fallback_type not in {"image", "carousel", "story", "reel"}:
            fallback_type = CONTENT_TYPE_FALLBACK

        return {
            "ok": False,
            "content_type": fallback_type,
            "style": STYLE_FALLBACK,
            "planner_selected": PLANNER_FALLBACK,
        }


def decide_mission(
    trend: str,
    *,
    format_hint: str | None = None,
    signal_context: dict | None = None,
    brand_context: dict | None = None,
    queue_state: dict | None = None,
    recent_signal_score: float | None = None,
) -> dict:
    trend_clean = _clean_text(trend)
    trend_normalized = _normalize(trend_clean)
    trend_weak = _trend_is_weak(trend_normalized)

    if trend_weak:
        trend_clean = TREND_FALLBACK
        trend_normalized = _normalize(trend_clean)

    queue = _queue_snapshot(queue_state)
    queue_full = queue["active_jobs"] >= 2 or queue["pending_jobs"] >= 3

    recent_signal_score = _coerce_float(recent_signal_score)
    signal_strength = _infer_signal_strength(recent_signal_score)
    planner = _planner_bridge(trend_clean, format_hint=format_hint)

    content_type = planner["content_type"]
    style = planner["style"]
    planner_selected = planner["planner_selected"]
    planner_ok = bool(planner["ok"])

    goal = _build_goal(content_type)
    hypothesis = _build_hypothesis(content_type, style, goal, signal_strength)
    priority = _build_priority(
        queue_full=queue_full,
        trend_weak=trend_weak,
        signal_strength=signal_strength,
        planner_ok=planner_ok,
    )
    confidence = _build_confidence(
        queue_full=queue_full,
        trend_weak=trend_weak,
        signal_strength=signal_strength,
        planner_ok=planner_ok,
    )

    if queue_full:
        should_act = False
        reason = "queue_full"
        decision_state = "blocked_queue"
    elif trend_weak:
        should_act = False
        reason = "weak_trend"
        decision_state = "blocked_trend"
    elif signal_strength == "weak":
        should_act = False
        reason = "weak_signal"
        decision_state = "blocked_signal"
    else:
        should_act = True
        reason = "approved_conservative"
        decision_state = "ready"

    if signal_strength == "strong":
        api_budget_mode = "premium"
    elif signal_strength == "medium":
        api_budget_mode = "normal"
    else:
        api_budget_mode = "lean"

    return {
        "ok": True,
        "should_act": should_act,
        "reason": reason,
        "decision_state": decision_state,
        "trend": trend_clean,
        "trend_normalized": trend_normalized,
        "style": style,
        "content_type": content_type,
        "goal": goal,
        "hypothesis": hypothesis,
        "priority": round(priority, 2),
        "api_budget_mode": api_budget_mode,
        "confidence": round(confidence, 2),
        "planner_selected": planner_selected,
        "queue_full": queue_full,
        "signal_strength": signal_strength,
        "guardrails": {
            "brand_live_allowed": False,
            "safe_for_brand_live": False,
            "requires_human_review": True,
        },
        "inputs": {
            "format_hint": format_hint,
            "recent_signal_score": recent_signal_score,
            "queue_state": queue,
            "signal_context": signal_context or {},
            "brand_context": brand_context or {},
        },
    }


def mission_control_examples() -> dict:
    return {
        "ok": True,
        "examples": {
            "strong_signal": decide_mission(
                "disciplina",
                recent_signal_score=0.82,
                queue_state={"active_jobs": 0, "pending_jobs": 0},
            ),
            "queue_full": decide_mission(
                "disciplina",
                recent_signal_score=0.82,
                queue_state={"active_jobs": 2, "pending_jobs": 3},
            ),
        },
    }
