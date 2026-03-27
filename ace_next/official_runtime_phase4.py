from __future__ import annotations

from typing import Any

from .official_runtime_phase3 import OfficialRuntime as OfficialRuntimePhase3
from .runtime_contracts import safe_dict
from .reel_execution_bridge import build_reel_execution_bundle


class OfficialRuntime(OfficialRuntimePhase3):
    """
    Fase 4 — runtime com Reel Premium Stack oficial.

    Mantém o runtime phase 3 já ativo,
    mas troca a etapa de reel stack por:
    creative_plan -> reel_task_contract -> hook -> storyboard -> rhythm -> subtitles -> audio -> multimodal QA -> cinematic gate
    """

    def _run_reel_premium_stack(
        self,
        *,
        trend: str,
        creative_plan: dict[str, Any],
        visual_qa: dict[str, Any],
        perceptual_qa: dict[str, Any],
        publication_authorization_gate: dict[str, Any],
        operational_state: str,
        publish_truth_state: str = "publish_truth_absent",
    ) -> dict[str, Any]:
        format_now = str(
            creative_plan.get("publish_format_now")
            or creative_plan.get("strategic_target_format")
            or "image"
        ).strip().lower()

        if format_now != "reel":
            return super()._run_reel_premium_stack(
                trend=trend,
                creative_plan=creative_plan,
                visual_qa=visual_qa,
                perceptual_qa=perceptual_qa,
                publication_authorization_gate=publication_authorization_gate,
                operational_state=operational_state,
                publish_truth_state=publish_truth_state,
            )

        priority = "critical" if format_now == "reel" else "high"

        try:
            bundle = build_reel_execution_bundle(
                creative_plan=creative_plan,
                priority=priority,
            )
            bundle_dict = safe_dict(bundle)
            if bundle_dict:
                cinematic_gate = safe_dict(bundle_dict.get("cinematic_gate"))
                qa = safe_dict(bundle_dict.get("multimodal_qa"))

                release_authority = {
                    "ok": True,
                    "release_state": "READY" if cinematic_gate.get("approved") else "BLOCKED_BY_CINEMATIC_GATE",
                    "approved_for_publish": bool(cinematic_gate.get("approved")),
                    "operation_mode": str(operational_state or "technical_test"),
                }
                publish_guard = {
                    "ok": True,
                    "mode": "ready" if cinematic_gate.get("approved") else "blocked",
                    "state": "publish_ready" if cinematic_gate.get("approved") else "publish_blocked",
                    "can_publish": bool(cinematic_gate.get("approved")),
                    "next_step": "publish" if cinematic_gate.get("approved") else "improve_reel_quality",
                    "publish_truth_state": publish_truth_state,
                }

                return {
                    "ok": True,
                    "stack_state": "phase_4_reel_stack_active",
                    "reel_task_contract": safe_dict(bundle_dict.get("reel_task_contract")),
                    "reel_task_state": bundle_dict.get("reel_task_state"),
                    "hook_opening": safe_dict(bundle_dict.get("hook_opening")),
                    "storyboard": safe_dict(bundle_dict.get("storyboard")),
                    "rhythm": safe_dict(bundle_dict.get("rhythm")),
                    "subtitles": safe_dict(bundle_dict.get("subtitles")),
                    "audio_direction": safe_dict(bundle_dict.get("audio_direction")),
                    "multimodal_qa": qa,
                    "cinematic_gate": cinematic_gate,
                    "release_authority": release_authority,
                    "publish_guard": publish_guard,
                    "summary": safe_dict(bundle_dict.get("summary")),
                    "study_alignment": safe_dict(bundle_dict.get("study_alignment")),
                }
        except Exception:
            pass

        return super()._run_reel_premium_stack(
            trend=trend,
            creative_plan=creative_plan,
            visual_qa=visual_qa,
            perceptual_qa=perceptual_qa,
            publication_authorization_gate=publication_authorization_gate,
            operational_state=operational_state,
            publish_truth_state=publish_truth_state,
        )
