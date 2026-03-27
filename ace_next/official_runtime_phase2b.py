from __future__ import annotations

from typing import Any

from .official_runtime_phase2 import OfficialRuntime as OfficialRuntimePhase2
from .mission_editorial_bridge import build_editorial_execution_brief
from .runtime_contracts import safe_dict


class OfficialRuntime(OfficialRuntimePhase2):
    """
    Fase 2B — runtime editorial com missão conectada ao router.

    Mantém o runtime phase 2 já ativo, mas agora liga:
    mission_control -> mission_editorial_bridge -> editorial_router -> planner
    """

    def _creative_plan(self, trend: str, mission_decision: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        recent_memory = self._recent_memory_for_planner(limit=5)
        brief = build_editorial_execution_brief(
            trend=trend,
            mission_decision=mission_decision.get("raw") or mission_decision,
            recent_memory=recent_memory,
        )
        brief_dict = safe_dict(brief)

        target_format = str(brief_dict.get("target_format") or "image").strip().lower() or "image"
        task_type = str(brief_dict.get("task_type") or "planner").strip().lower() or "planner"
        priority = str(brief_dict.get("priority") or "medium").strip().lower() or "medium"
        hypothesis = brief_dict.get("hypothesis")
        continuity_required = bool(brief_dict.get("continuity_required"))

        try:
            from .editorial_router import run_editorial_task

            router_result = run_editorial_task(
                task_type=task_type,
                topic_seed=brief_dict.get("trend") or trend,
                target_format=target_format,
                priority=priority,
                hypothesis=hypothesis,
                continuity_required=continuity_required,
                mission_decision=mission_decision.get("raw") or mission_decision,
                recent_memory=recent_memory,
            )
            router_dict = safe_dict(router_result)
            plan_dict = safe_dict(router_dict.get("creative_plan"))

            if plan_dict:
                plan_dict.setdefault("study_tags", self.snapshot().get("study_tags", {}))
                plan_dict.setdefault("serial_continuity_hint", continuity_required)
                plan_dict.setdefault("attention_target", "save_share_replay_retention")
                plan_dict.setdefault("ethical_boundary", "no_hidden_manipulation")
                plan_dict["editorial_task_contract"] = safe_dict(router_dict.get("task_contract"))
                plan_dict["editorial_router_state"] = "phase_2b_active"
                plan_dict["editorial_router_hypothesis"] = router_dict.get("hypothesis")
                plan_dict["editorial_router_priority"] = router_dict.get("priority")
                plan_dict["mission_editorial_bridge"] = brief_dict
                plan_dict["mission_editorial_bridge_state"] = brief_dict.get("bridge_state")
                return True, plan_dict
        except Exception:
            pass

        return super()._creative_plan(trend, mission_decision)
