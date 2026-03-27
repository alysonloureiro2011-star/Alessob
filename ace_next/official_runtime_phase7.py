
from __future__ import annotations

from typing import Any

from .official_runtime_phase6 import OfficialRuntime as OfficialRuntimePhase6
from .decision_memory_engine import build_decision_memory_summary
from .runtime_contracts import safe_dict


class OfficialRuntime(OfficialRuntimePhase6):
    """
    Fase 7 — Learning que decide.

    Injeta memória real dentro do cérebro editorial.
    """

    def _apply_decision_memory(
        self,
        *,
        creative_plan: dict[str, Any],
        measurement_summary: dict[str, Any],
    ) -> dict[str, Any]:

        try:
            decision_entries = safe_dict(
                measurement_summary.get("decision_memory_entries") or []
            )

            memory_summary = build_decision_memory_summary(
                entries=decision_entries,
                preferred_axis="hook",
            )

            best_hook = memory_summary.get("best_candidate")

            if best_hook:
                creative_plan["hook"] = best_hook
                creative_plan["memory_override"] = True

            creative_plan["decision_memory_summary"] = memory_summary

        except Exception:
            pass

        return creative_plan

    def _build_creative_plan(
        self,
        *,
        trend: str,
        mission_decision: dict[str, Any],
        measurement_summary: dict[str, Any],
    ) -> dict[str, Any]:

        plan = super()._build_creative_plan(
            trend=trend,
            mission_decision=mission_decision,
            measurement_summary=measurement_summary,
        )

        plan = self._apply_decision_memory(
            creative_plan=plan,
            measurement_summary=measurement_summary,
        )

        return plan
