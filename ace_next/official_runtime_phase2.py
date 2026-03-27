from __future__ import annotations

from typing import Any

from .official_runtime import OfficialRuntime as OfficialRuntimeBase
from .editorial_router import run_editorial_task
from .runtime_contracts import safe_dict


class OfficialRuntime(OfficialRuntimeBase):
    """
    Fase 2 — ponte soberana do cérebro editorial.

    Mantém todo o runtime oficial existente,
    mas troca a etapa de creative plan para passar pelo editorial_router.
    """

    def _creative_plan(self, trend: str, mission_decision: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        overrides = self._planner_overrides_from_mission_decision(mission_decision)
        recent_memory = self._recent_memory_for_planner(limit=5)

        task_type = "planner"
        target_format = str(
            overrides.get("publish_format_now")
            or mission_decision.get("content_type")
            or "image"
        ).strip().lower() or "image"

        hypothesis = (
            overrides.get("hypothesis")
            or safe_dict(mission_decision.get("raw")).get("hypothesis")
        )

        continuity_required = bool(recent_memory)
        priority = "high" if target_format == "reel" else "medium"

        try:
            router_result = run_editorial_task(
                task_type=task_type,
                topic_seed=trend,
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
                plan_dict["editorial_router_state"] = "phase_2_active"
                plan_dict["editorial_router_hypothesis"] = router_dict.get("hypothesis")
                plan_dict["editorial_router_priority"] = router_dict.get("priority")
                return True, plan_dict
        except Exception:
            pass

        return super()._creative_plan(trend, mission_decision)
