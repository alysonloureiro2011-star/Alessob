from __future__ import annotations

from typing import Any

from .official_runtime_phase4 import OfficialRuntime as OfficialRuntimePhase4
from .runtime_contracts import safe_dict
from .sovereign_gate_bridge import build_sovereign_gate_bundle


class OfficialRuntime(OfficialRuntimePhase4):
    """
    Fase 5 — runtime com Gate Soberano Duro.

    Mantém o runtime phase 4 já ativo,
    mas troca a etapa de autorização por:
    rubric -> brand_veto -> publication_authorization -> decisão soberana única
    """

    def _run_authorization_stack(
        self,
        *,
        force_placeholder: bool,
        plan_dict: dict[str, Any],
        editorial_qa: dict[str, Any],
        visual_qa: dict[str, Any],
        perceptual_qa: dict[str, Any],
        env_flags: dict[str, Any],
        request_flags: dict[str, Any],
        staging_hardener: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        try:
            gate_bundle = build_sovereign_gate_bundle(
                creative_plan=plan_dict,
                editorial_qa=editorial_qa,
                visual_qa=visual_qa,
                perceptual_qa=perceptual_qa,
                env_flags=env_flags,
                request_flags=request_flags,
                staging_hardener=staging_hardener or {},
                force_placeholder=force_placeholder,
            )
            gate_dict = safe_dict(gate_bundle)
            rubric = safe_dict(gate_dict.get("rubric_engine"))
            brand_veto = safe_dict(gate_dict.get("brand_veto_gate"))
            authorization = safe_dict(gate_dict.get("publication_authorization_gate"))

            if rubric and brand_veto and authorization:
                rubric["sovereign_gate_state"] = gate_dict.get("gate_state")
                brand_veto["sovereign_gate_state"] = gate_dict.get("gate_state")
                authorization["sovereign_gate_state"] = gate_dict.get("gate_state")
                authorization["blocked_by_sovereign_gate"] = bool(gate_dict.get("blocked"))
                authorization["block_reasons"] = gate_dict.get("block_reasons") or authorization.get("block_reasons") or []
                return rubric, brand_veto, authorization
        except Exception:
            pass

        return super()._run_authorization_stack(
            force_placeholder=force_placeholder,
            plan_dict=plan_dict,
            editorial_qa=editorial_qa,
            visual_qa=visual_qa,
            perceptual_qa=perceptual_qa,
            env_flags=env_flags,
            request_flags=request_flags,
            staging_hardener=staging_hardener,
        )
