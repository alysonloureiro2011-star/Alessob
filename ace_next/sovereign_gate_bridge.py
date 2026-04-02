from __future__ import annotations

from typing import Any

from .runtime_contracts import safe_dict
from .rubric_engine import evaluate_rubric_engine
from .brand_veto_gate import evaluate_brand_veto_gate
from .publication_authorization_gate import authorize_publication


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _enrich_visual_qa_with_staging_hardener(
    visual_qa: dict[str, Any] | None,
    staging_hardener: dict[str, Any] | None,
) -> dict[str, Any]:
    visual = safe_dict(visual_qa)
    hardener = safe_dict(staging_hardener)

    if not hardener:
        return visual

    metrics = safe_dict(visual.get("metrics"))

    hardened_payload = safe_dict(
        hardener.get("hardened_payload")
        or hardener.get("render_payload_used")
    )
    if hardened_payload:
        visual["hardened_visible_payload"] = hardened_payload
        metrics["render_payload_used"] = hardened_payload

    hierarchy_gate = safe_dict(hardener.get("hierarchy_gate"))
    if hierarchy_gate:
        visual["hierarchy_gate"] = hierarchy_gate

    brand_dignity_score = safe_dict(hardener.get("brand_dignity_score"))
    if brand_dignity_score:
        visual["brand_dignity_score"] = brand_dignity_score

    final_score = hardener.get("final_score")
    if final_score is not None:
        visual["final_score"] = final_score

    selected_template_id = hardener.get("selected_template_id")
    if selected_template_id:
        visual["selected_template_id"] = selected_template_id

    hidden_overflow = _safe_list(
        hardener.get("hidden_overflow_for_caption")
        or hardener.get("moved_to_caption")
    )
    if hidden_overflow:
        visual["hidden_overflow_for_caption"] = hidden_overflow

    target_state = hardener.get("target_state")
    if target_state:
        visual["target_state"] = target_state

    semantic_anchors = _safe_list(hardener.get("semantic_anchors_preserved"))
    if semantic_anchors:
        visual["semantic_anchors_preserved"] = semantic_anchors

    applied_rules = _safe_list(hardener.get("applied_rules"))
    if applied_rules:
        visual["hardening_rules_applied"] = applied_rules

    metrics["staging_hardener"] = hardener
    if hierarchy_gate:
        metrics["hierarchy_gate"] = hierarchy_gate
    if brand_dignity_score:
        metrics["brand_dignity_score"] = brand_dignity_score
    if final_score is not None:
        metrics["premium_visual_final_score"] = final_score
    if selected_template_id:
        metrics["selected_template_id"] = selected_template_id

    visual["metrics"] = metrics
    visual["hardening_applied"] = True

    return visual


def build_sovereign_gate_bundle(
    *,
    creative_plan: dict[str, Any] | None = None,
    editorial_qa: dict[str, Any] | None = None,
    visual_qa: dict[str, Any] | None = None,
    perceptual_qa: dict[str, Any] | None = None,
    env_flags: dict[str, Any] | None = None,
    request_flags: dict[str, Any] | None = None,
    staging_hardener: dict[str, Any] | None = None,
    force_placeholder: bool = False,
) -> dict[str, Any]:
    plan = safe_dict(creative_plan)
    editorial = safe_dict(editorial_qa)
    visual = _enrich_visual_qa_with_staging_hardener(visual_qa, staging_hardener)
    perceptual = safe_dict(perceptual_qa)
    hardener = safe_dict(staging_hardener)

    rubric = evaluate_rubric_engine(
        plan=plan,
        editorial_qa=editorial,
        visual_qa=visual,
        perceptual_qa=perceptual,
    )
    rubric_dict = rubric.to_dict() if hasattr(rubric, "to_dict") else safe_dict(rubric)

    brand_veto = evaluate_brand_veto_gate(
        plan=plan,
        editorial_qa=editorial,
        visual_qa=visual,
        perceptual_qa=perceptual,
        rubric=rubric,
    )
    brand_veto_dict = brand_veto.to_dict() if hasattr(brand_veto, "to_dict") else safe_dict(brand_veto)

    authorization = authorize_publication(
        force_placeholder=force_placeholder,
        editorial_qa=editorial,
        visual_qa=visual,
        perceptual_qa=perceptual,
        rubric=rubric,
        brand_veto=brand_veto,
        env_flags=env_flags or {},
        request_flags=request_flags or {},
        staging_hardener=hardener,
        authority_payload_source="sovereign_gate_bridge_phase_5",
    )
    authorization_dict = authorization.to_dict() if hasattr(authorization, "to_dict") else safe_dict(authorization)

    blocked = bool(brand_veto_dict.get("blocked")) or authorization_dict.get("selected_state") in {
        "blocked_quality",
        "blocked_brand",
    }

    return {
        "ok": True,
        "gate_state": "phase_5_sovereign_gate_ready",
        "rubric_engine": rubric_dict,
        "brand_veto_gate": brand_veto_dict,
        "publication_authorization_gate": authorization_dict,
        "blocked": blocked,
        "approved_minimum_quality": bool(rubric_dict.get("approved_minimum_quality")),
        "eligible_for_editorial_staging": bool(authorization_dict.get("eligible_for_editorial_staging")),
        "eligible_for_brand_live_candidate": bool(authorization_dict.get("eligible_for_brand_live_candidate")),
        "block_reasons": authorization_dict.get("block_reasons") or brand_veto_dict.get("reasons") or [],
        "staging_hardener_seen": bool(hardener),
        "study_alignment": {
            "rubric_engine": True,
            "brand_veto": True,
            "publication_authorization": True,
            "anti_mediocrity": True,
        },
    }


def sovereign_gate_bridge_examples() -> dict[str, Any]:
    return {
        "ok": True,
        "example": build_sovereign_gate_bundle(
            creative_plan={
                "headline": "clareza vence ruído",
                "hook": "o problema não é falta de informação",
                "body": "é excesso sem hierarquia e sem tensão",
                "cta": "salve isso para revisar depois",
            },
            editorial_qa={
                "breakdown": {
                    "headline": 8.6,
                    "hook": 8.4,
                    "clarity": 8.5,
                    "semantic_density": 8.3,
                    "authority": 8.4,
                    "perceived_value": 8.5,
                    "narrative_tension": 8.2,
                    "anti_generic": 8.4,
                    "anti_commodity": 8.5,
                    "naturalism": 8.2,
                }
            },
            visual_qa={
                "final_score": 84,
                "hierarchy_gate": {
                    "approved": True,
                    "final_score": 8.3,
                    "breakdown": {"contrast": 8.2},
                },
                "brand_dignity_score": {
                    "approved": True,
                    "final_score": 8.4,
                    "breakdown": {
                        "brand_fit": 8.5,
                        "naturality": 8.2,
                        "anti_commodity": 8.3,
                    },
                },
            },
            perceptual_qa={
                "breakdown": {
                    "legibility": 8.4,
                    "contrast": 8.3,
                    "composition": 8.2,
                    "brand_fit_visual": 8.4,
                    "perceived_value_visual": 8.3,
                    "noise_control": 8.1,
                }
            },
            env_flags={"ACE_REQUIRE_HUMAN_REVIEW_FOR_BRAND_LIVE": True},
            request_flags={},
            staging_hardener={
                "hardened_payload": {
                    "headline": "clareza vence ruído",
                    "hook": "o problema não é falta de informação",
                    "body": "é excesso sem hierarquia e sem tensão",
                    "cta": "salve isso para revisar depois",
                    "support_points": [],
                },
                "hidden_overflow_for_caption": [],
                "target_state": "editorial_staging",
                "final_score": 8.3,
                "selected_template_id": "premium_editorial_v1",
                "hierarchy_gate": {
                    "approved": True,
                    "final_score": 8.3,
                    "breakdown": {"contrast": 8.2},
                },
                "brand_dignity_score": {
                    "approved": True,
                    "final_score": 8.4,
                    "breakdown": {
                        "brand_fit": 8.5,
                        "naturality": 8.2,
                        "anti_commodity": 8.3,
                    },
                },
            },
            force_placeholder=False,
        ),
    }
