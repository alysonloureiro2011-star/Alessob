from __future__ import annotations

from typing import Any

from .official_runtime_phase5 import OfficialRuntime as OfficialRuntimePhase5
from .publish_cycle_bridge import build_publish_cycle_bundle
from .runtime_contracts import safe_dict


class OfficialRuntime(OfficialRuntimePhase5):
    """
    Fase 6 — runtime com ciclo premium real.

    Mantém o runtime phase 5 já ativo,
    mas fecha o elo:
    publish -> proof -> evidence -> recommendation -> next_best_step
    """

    def _measurement_summary(
        self,
        *,
        publish_result: dict[str, Any] | None,
        creative_plan: dict[str, Any],
        mission_decision: dict[str, Any],
    ) -> dict[str, Any]:
        base = super()._measurement_summary(
            publish_result=publish_result,
            creative_plan=creative_plan,
            mission_decision=mission_decision,
        )

        try:
            cycle_bundle = build_publish_cycle_bundle(
                publish_result=safe_dict(publish_result),
                post_performance_contract=safe_dict(base.get("post_performance_contract")),
                evidence_interpreter=safe_dict(base.get("evidence_interpreter")),
                recommendation_engine=safe_dict(base.get("recommendation_engine")),
            )
            cycle_dict = safe_dict(cycle_bundle)
            if cycle_dict:
                base["publish_cycle"] = cycle_dict
                base["publish_cycle_state"] = cycle_dict.get("cycle_state")
                base["proof_contract"] = cycle_dict.get("proof")
                base["proof_complete"] = bool(cycle_dict.get("proof_complete"))
                base["first_premium_cycle_validated"] = bool(cycle_dict.get("first_premium_cycle_validated"))
                base["wave11_summary"] = {
                    **safe_dict(base.get("wave11_summary")),
                    "cycle_state": cycle_dict.get("cycle_state"),
                    "proof_complete": bool(cycle_dict.get("proof_complete")),
                    "first_premium_cycle_validated": bool(cycle_dict.get("first_premium_cycle_validated")),
                    "next_best_step": cycle_dict.get("next_best_step"),
                }
                base["performance_summary"] = {
                    **safe_dict(base.get("performance_summary")),
                    "publish_cycle_state": cycle_dict.get("cycle_state"),
                    "proof_complete": bool(cycle_dict.get("proof_complete")),
                    "next_best_step": cycle_dict.get("next_best_step"),
                }
        except Exception:
            pass

        return base
