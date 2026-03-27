from __future__ import annotations

from typing import Any
from .runtime_contracts import safe_dict


def build_distribution_decision(
    *,
    decision_memory: dict[str, Any] | None = None,
    publish_cycle: dict[str, Any] | None = None,
    current_time: str | None = None,
) -> dict[str, Any]:

    decision_memory = safe_dict(decision_memory)
    publish_cycle = safe_dict(publish_cycle)

    proof_complete = bool(publish_cycle.get("proof_complete"))
    cycle_state = publish_cycle.get("cycle_state")

    best_candidate = decision_memory.get("best_candidate")

    if not proof_complete:
        action = "block_publish"
        reason = "sem_prova_real"
    elif cycle_state == "phase_6_cycle_proof_confirmed":
        action = "publish"
        reason = "ciclo_validado"
    else:
        action = "improve_before_publish"
        reason = "qualidade_ou_ciclo_incompleto"

    timing = {
        "recommended_window": "18:00-21:00",
        "timing_confidence": 0.6,
    }

    seo = {
        "caption_structure": "hook + valor + CTA",
        "hashtag_mode": "focused",
        "density": "alta_sem_ruido",
    }

    return {
        "ok": True,
        "distribution_state": "phase_8_distribution_ready",
        "action": action,
        "reason": reason,
        "timing": timing,
        "seo": seo,
        "best_candidate_used": best_candidate,
        "next_best_step": action,
        "study_alignment": {
            "timing_engine": True,
            "social_seo": True,
            "distribution_strategy": True,
        },
    }
