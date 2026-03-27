from __future__ import annotations

from typing import Any

from .official_runtime_phase2b import OfficialRuntime as OfficialRuntimePhase2B
from .runtime_contracts import safe_dict
from .visual_execution_bridge import build_visual_execution_bundle


class OfficialRuntime(OfficialRuntimePhase2B):
    """
    Fase 3 — runtime visual premium.

    Mantém o runtime phase 2b já ativo,
    mas troca a etapa visual premium direta por:
    creative_plan -> visual_task_contract -> visual_premium_bridge -> hierarchy_gate -> brand_dignity
    """

    def _premium_visual(
        self,
        plan_dict: dict[str, Any],
        visual_identity: dict[str, Any],
        visual_contract: dict[str, Any],
    ) -> dict[str, Any]:
        strategic_format = (
            plan_dict.get("publish_format_now")
            or plan_dict.get("strategic_target_format")
            or "image"
        )
        priority = "critical" if str(strategic_format).strip().lower() in {"reel", "reel_cover", "story"} else "high"

        try:
            bundle = build_visual_execution_bundle(
                creative_plan=plan_dict,
                visual_identity=visual_identity,
                visual_contract=visual_contract,
                strategic_format=str(strategic_format),
                priority=priority,
                capture_mode="safe",
            )
            bundle_dict = safe_dict(bundle)
            premium_visual = safe_dict(bundle_dict.get("premium_visual"))

            if premium_visual:
                premium_visual["visual_task_contract"] = safe_dict(bundle_dict.get("visual_task_contract"))
                premium_visual["visual_task_state"] = bundle_dict.get("visual_task_state")
                premium_visual["hierarchy_gate"] = safe_dict(bundle_dict.get("hierarchy_gate"))
                premium_visual["brand_dignity_score"] = safe_dict(bundle_dict.get("brand_dignity_score"))
                premium_visual["visual_execution_bridge_state"] = "phase_3_active"
                premium_visual["approved_for_premium_visual"] = bool(bundle_dict.get("approved_for_premium_visual"))
                premium_visual["selected_template_id"] = bundle_dict.get("selected_template_id")
                premium_visual["premium_render_state"] = bundle_dict.get("premium_render_state")
                premium_visual["hardening_applied"] = bundle_dict.get("hardening_applied")
                premium_visual["hardening_report"] = bundle_dict.get("hardening_report")
                premium_visual["study_alignment"] = bundle_dict.get("study_alignment")
                return premium_visual
        except Exception:
            pass

        return super()._premium_visual(plan_dict, visual_identity, visual_contract)
