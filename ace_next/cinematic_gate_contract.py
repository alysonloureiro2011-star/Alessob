from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


DEFAULT_VETO_PRIORITY = [
    "multimodal_qa_low",
    "premium_quality_low",
    "vlm_aesthetic_audit_required",
    "rejection_feedback_loop_required",
    "cinematic_score_low",
]

DEFAULT_NOTES = [
    "source=sovereign_annexes",
    "pep_enabled=true",
    "minimum_cinematic_score=8.5",
    "vlm_aesthetic_audit=required",
    "rejection_feedback_loop=required",
    "goal=bloqueio_confiavel_de_peca_mediana",
]


@dataclass(frozen=True)
class CinematicGateContract:
    state: str
    minimum_cinematic_score: float
    minimum_multimodal_qa_score: float
    minimum_premium_quality_score: float
    requires_vlm_aesthetic_audit: bool
    requires_rejection_feedback_loop: bool
    pep_enabled: bool
    veto_priority: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_cinematic_gate_contract() -> dict[str, Any]:
    contract = CinematicGateContract(
        state="cinematic_gate_contract_ready",
        minimum_cinematic_score=8.5,
        minimum_multimodal_qa_score=8.2,
        minimum_premium_quality_score=8.0,
        requires_vlm_aesthetic_audit=True,
        requires_rejection_feedback_loop=True,
        pep_enabled=True,
        veto_priority=list(DEFAULT_VETO_PRIORITY),
        notes=list(DEFAULT_NOTES),
    )
    return contract.to_dict()


def cinematic_gate_contract_examples() -> dict[str, Any]:
    return {
        "default": resolve_cinematic_gate_contract(),
    }
