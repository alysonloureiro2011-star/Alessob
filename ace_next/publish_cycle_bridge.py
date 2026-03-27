from __future__ import annotations

from typing import Any

from .runtime_contracts import safe_dict


REQUIRED_PROOF_FIELDS = {"receipt_id", "media_id", "permalink"}


def build_publish_cycle_bundle(
    *,
    publish_result: dict[str, Any] | None = None,
    post_performance_contract: dict[str, Any] | None = None,
    evidence_interpreter: dict[str, Any] | None = None,
    recommendation_engine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    publish_result = safe_dict(publish_result)
    post_performance_contract = safe_dict(post_performance_contract)
    evidence_interpreter = safe_dict(evidence_interpreter)
    recommendation_engine = safe_dict(recommendation_engine)

    publish_status = str(publish_result.get("publish_status") or "").strip()
    proof = {
        "receipt_id": publish_result.get("receipt_id"),
        "media_id": publish_result.get("media_id"),
        "permalink": publish_result.get("permalink"),
    }
    proof_complete = all(bool(proof.get(field)) for field in REQUIRED_PROOF_FIELDS)

    evidence_state = (
        evidence_interpreter.get("evidence_state")
        or safe_dict(post_performance_contract.get("evidence_bridge")).get("evidence_bridge_state")
        or "not_collected_yet"
    )
    recommendation_state = recommendation_engine.get("recommended_action") or "publish_or_improve"

    cycle_state = "phase_6_cycle_incomplete"
    if publish_status == "published_real_probe" and proof_complete:
        cycle_state = "phase_6_cycle_proof_confirmed"
    elif publish_status:
        cycle_state = "phase_6_cycle_publish_attempt_recorded"

    return {
        "ok": True,
        "cycle_state": cycle_state,
        "publish_status": publish_status,
        "proof": proof,
        "proof_complete": proof_complete,
        "evidence_state": evidence_state,
        "recommendation_state": recommendation_state,
        "first_premium_cycle_validated": bool(publish_status == "published_real_probe" and proof_complete),
        "next_best_step": recommendation_engine.get("next_best_step"),
        "study_alignment": {
            "publish_truth": True,
            "evidence": True,
            "proof_before_claim": True,
            "learning_after_publish": True,
        },
    }


def publish_cycle_bridge_examples() -> dict[str, Any]:
    return {
        "ok": True,
        "confirmed": build_publish_cycle_bundle(
            publish_result={
                "publish_status": "published_real_probe",
                "receipt_id": "receipt_123",
                "media_id": "media_123",
                "permalink": "https://instagram.com/p/example",
            },
            post_performance_contract={
                "evidence_bridge": {"evidence_bridge_state": "linked_real_target"},
            },
            evidence_interpreter={"evidence_state": "linked_real_target"},
            recommendation_engine={
                "recommended_action": "measure_now",
                "next_best_step": "coletar métricas reais após publicação",
            },
        ),
        "incomplete": build_publish_cycle_bundle(
            publish_result={
                "publish_status": "not_published_probe_not_allowed",
                "receipt_id": None,
                "media_id": None,
                "permalink": None,
            },
            evidence_interpreter={"evidence_state": "no_receipt"},
            recommendation_engine={
                "recommended_action": "publish_or_improve",
                "next_best_step": "melhorar qualidade premium antes de publicar",
            },
        ),
    }
