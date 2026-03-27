from __future__ import annotations

from typing import Any

from .creative_planner import build_creative_plan
from .editorial_task_contract import build_editorial_task_contract


VALID_TASK_TYPES = {"planner", "hook", "headline", "caption", "continuity", "distribution"}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _infer_objective(task_type: str, topic_seed: str) -> str:
    base = _clean_text(topic_seed) or "clareza, disciplina e direção"
    mapping = {
        "planner": f"definir peça premium completa sobre {base}",
        "hook": f"gerar hook premium com tensão narrativa sobre {base}",
        "headline": f"gerar headline premium, clara e memorável sobre {base}",
        "caption": f"gerar legenda premium anti-clichê sobre {base}",
        "continuity": f"definir continuidade serial premium sobre {base}",
        "distribution": f"definir melhor adaptação e distribuição para {base}",
    }
    return mapping.get(task_type, f"definir peça editorial premium sobre {base}")


def _extract_task_output(task_type: str, plan: dict[str, Any]) -> dict[str, Any]:
    if task_type == "hook":
        return {
            "hook": plan.get("hook"),
            "hook_family": plan.get("hook_family"),
            "narrative_tension": plan.get("narrative_tension"),
            "payoff": plan.get("payoff"),
        }
    if task_type == "headline":
        return {
            "headline": plan.get("headline"),
            "hook": plan.get("hook"),
            "payoff": plan.get("payoff"),
        }
    if task_type == "caption":
        return {
            "caption": plan.get("caption"),
            "cta": plan.get("cta"),
            "hashtags": plan.get("hashtags"),
            "first_comment": plan.get("first_comment"),
        }
    if task_type == "continuity":
        return {
            "serial_continuity": plan.get("serial_continuity"),
            "continuation_candidate": plan.get("continuation_candidate"),
            "distribution_context": plan.get("distribution_context"),
        }
    if task_type == "distribution":
        return {
            "distribution_context": plan.get("distribution_context"),
            "timing_hypothesis": plan.get("timing_hypothesis"),
            "publish_format_now": plan.get("publish_format_now"),
        }
    return plan


def run_editorial_task(
    *,
    task_type: str,
    topic_seed: str,
    target_format: str = "image",
    priority: str = "medium",
    hypothesis: str | None = None,
    continuity_required: bool = False,
    mission_decision: dict[str, Any] | None = None,
    recent_memory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    clean_task_type = _clean_text(task_type).lower() or "planner"
    if clean_task_type not in VALID_TASK_TYPES:
        clean_task_type = "planner"

    contract = build_editorial_task_contract(
        task_type=clean_task_type,
        topic_seed=topic_seed,
        objective=_infer_objective(clean_task_type, topic_seed),
        target_format=target_format,
        priority=priority,
        hypothesis=hypothesis,
        continuity_required=continuity_required,
        serial_context={"series_name": "Liberta a Verdade"} if continuity_required else {},
        distribution_context={},
        notes=["phase_2_editorial_router"],
    )

    planner = build_creative_plan(
        contract.topic_seed,
        overrides={
            "publish_format_now": contract.target_format,
            "goal": contract.objective,
            "hypothesis": contract.hypothesis,
            "planner_selected": "editorial_router_phase_2",
        },
        mission_decision=mission_decision or {},
        recent_memory=recent_memory or [],
    )
    plan_dict = planner.to_dict() if hasattr(planner, "to_dict") else dict(planner)

    return {
        "ok": True,
        "task_contract": contract.to_dict(),
        "planner_selected": plan_dict.get("planner_selected"),
        "task_type": clean_task_type,
        "target_format": contract.target_format,
        "priority": contract.priority,
        "hypothesis": contract.hypothesis,
        "output": _extract_task_output(clean_task_type, plan_dict),
        "creative_plan": plan_dict,
    }


def editorial_router_examples() -> dict[str, Any]:
    return {
        "ok": True,
        "planner": run_editorial_task(
            task_type="planner",
            topic_seed="clareza, disciplina e direção",
            target_format="reel",
            priority="high",
            hypothesis="hook_de_curiosidade_com_payoff_concreto_melhora_retenção",
            continuity_required=True,
        ),
        "hook": run_editorial_task(
            task_type="hook",
            topic_seed="prosperidade com disciplina",
            target_format="carousel",
            priority="medium",
            continuity_required=False,
        ),
    }
