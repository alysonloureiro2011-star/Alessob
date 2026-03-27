from __future__ import annotations

from typing import Any

from .runtime_contracts import safe_dict


VALID_EDITORIAL_TASK_TYPES = {
    "planner",
    "hook",
    "headline",
    "caption",
    "continuity",
    "distribution",
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_content_type(value: Any) -> str:
    clean = _clean_text(value).lower()
    return clean if clean in {"image", "carousel", "story", "reel"} else "image"


def _infer_task_type(mission_decision: dict[str, Any]) -> str:
    decision = safe_dict(mission_decision)
    content_type = _normalize_content_type(decision.get("content_type"))
    goal = _clean_text(decision.get("goal")).lower()

    if goal in {"reach", "retention", "memorability"}:
        return "hook"
    if goal in {"authority", "engagement"} and content_type in {"carousel", "story"}:
        return "caption"
    if decision.get("continuity_required"):
        return "continuity"
    return "planner"


def build_editorial_execution_brief(
    *,
    trend: str,
    mission_decision: dict[str, Any] | None = None,
    recent_memory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    decision = safe_dict(mission_decision)
    recent_memory = list(recent_memory or [])

    task_type = _infer_task_type(decision)
    target_format = _normalize_content_type(decision.get("content_type"))
    confidence = decision.get("confidence")
    continuity_required = bool(recent_memory) or bool(decision.get("continuity_required"))

    priority = "high" if target_format == "reel" else "medium"
    hypothesis = _clean_text(decision.get("hypothesis")) or None
    planner_selected = _clean_text(decision.get("planner_selected")) or "mission_editorial_bridge_phase_2"

    return {
        "ok": True,
        "trend": _clean_text(trend) or "clareza, disciplina e direção",
        "task_type": task_type if task_type in VALID_EDITORIAL_TASK_TYPES else "planner",
        "target_format": target_format,
        "priority": priority,
        "hypothesis": hypothesis,
        "goal": decision.get("goal") or "authority",
        "style": decision.get("style") or "official_next_visual_foundation_v1",
        "confidence": confidence,
        "continuity_required": continuity_required,
        "recent_memory_present": bool(recent_memory),
        "planner_selected": planner_selected,
        "study_alignment": {
            "clt_density_control": True,
            "steps_narrative": True,
            "attention_engineering": True,
            "serial_continuity": continuity_required,
        },
        "bridge_state": "phase_2_mission_editorial_bridge_ready",
    }


def mission_editorial_bridge_examples() -> dict[str, Any]:
    return {
        "ok": True,
        "planner": build_editorial_execution_brief(
            trend="clareza, disciplina e direção",
            mission_decision={
                "content_type": "reel",
                "goal": "authority",
                "hypothesis": "hook_de_curiosidade_melhora_retenção",
                "planner_selected": "mission_control_phase_2",
                "confidence": 0.84,
            },
            recent_memory=[{"topic": "disciplina"}],
        ),
        "hook": build_editorial_execution_brief(
            trend="prosperidade com disciplina",
            mission_decision={
                "content_type": "reel",
                "goal": "retention",
                "hypothesis": "abertura_forte_melhora_watch_time",
                "confidence": 0.71,
            },
            recent_memory=[],
        ),
    }
