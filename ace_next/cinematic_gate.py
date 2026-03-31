from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

from .cinematic_gate_contract import resolve_cinematic_gate_contract


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "sim"}:
        return True
    if text in {"false", "0", "no", "n", "nao", "não"}:
        return False
    return default


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _merge_unique(*groups: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for group in groups:
        for item in group:
            text = _clean_text(item)
            if not text or text in seen:
                continue
            seen.add(text)
            merged.append(text)
    return merged


@dataclass(frozen=True)
class CinematicGateResult:
    ok: bool
    state: str
    contract_state: str
    cinematic_score: float
    approved: bool
    veto_reason: str
    minimum_cinematic_score: float
    minimum_multimodal_qa_score: float
    minimum_premium_quality_score: float
    requires_vlm_aesthetic_audit: bool
    requires_rejection_feedback_loop: bool
    pep_enabled: bool
    veto_priority: list[str]
    notes: list[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CinematicGate:
    def run(
        self,
        *,
        multimodal_qa: Dict[str, Any] | None = None,
        reel_director: Dict[str, Any] | None = None,
        premium_decision: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        multimodal_qa = _safe_dict(multimodal_qa)
        reel_director = _safe_dict(reel_director)
        premium_decision = _safe_dict(premium_decision)

        contract = _safe_dict(resolve_cinematic_gate_contract())

        qa_score = _safe_float(
            multimodal_qa.get("global_score", multimodal_qa.get("overall_score")),
            0.0,
        )
        quality_score = _safe_float(
            premium_decision.get("overall_quality_score"),
            0.0,
        )

        visual_mode = _clean_text(reel_director.get("visual_mode")).lower()
        cut_mode = _clean_text(reel_director.get("cut_mode")).lower()

        bonus = 0.0
        if visual_mode == "cinematic_retention":
            bonus += 0.3
        if cut_mode == "precision_fast":
            bonus += 0.2

        cinematic_score = round(((qa_score * 0.7) + (quality_score * 0.3) + bonus), 2)

        minimum_cinematic_score = _safe_float(
            contract.get("minimum_cinematic_score"),
            8.5,
        )
        minimum_multimodal_qa_score = _safe_float(
            contract.get("minimum_multimodal_qa_score"),
            8.2,
        )
        minimum_premium_quality_score = _safe_float(
            contract.get("minimum_premium_quality_score"),
            8.0,
        )

        requires_vlm_aesthetic_audit = _safe_bool(
            contract.get("requires_vlm_aesthetic_audit"),
            True,
        )
        requires_rejection_feedback_loop = _safe_bool(
            contract.get("requires_rejection_feedback_loop"),
            True,
        )
        pep_enabled = _safe_bool(contract.get("pep_enabled"), True)
        veto_priority = _safe_list(contract.get("veto_priority"))

        vlm_aesthetic_audit_passed = multimodal_qa.get("vlm_aesthetic_audit_passed")
        rejection_feedback_loop_ready = premium_decision.get(
            "rejection_feedback_loop_ready"
        )

        approved = (
            cinematic_score >= minimum_cinematic_score
            and qa_score >= minimum_multimodal_qa_score
            and quality_score >= minimum_premium_quality_score
        )

        veto_reason = ""
        for candidate in veto_priority:
            if candidate == "multimodal_qa_low" and qa_score < minimum_multimodal_qa_score:
                veto_reason = candidate
                approved = False
                break
            if candidate == "premium_quality_low" and quality_score < minimum_premium_quality_score:
                veto_reason = candidate
                approved = False
                break
            if (
                candidate == "vlm_aesthetic_audit_required"
                and requires_vlm_aesthetic_audit
                and vlm_aesthetic_audit_passed is False
            ):
                veto_reason = candidate
                approved = False
                break
            if (
                candidate == "rejection_feedback_loop_required"
                and requires_rejection_feedback_loop
                and rejection_feedback_loop_ready is False
            ):
                veto_reason = candidate
                approved = False
                break
            if candidate == "cinematic_score_low" and cinematic_score < minimum_cinematic_score:
                veto_reason = candidate
                approved = False
                break

        notes = _merge_unique(
            _safe_list(contract.get("notes")),
            [
                f"qa_score={qa_score}",
                f"quality_score={quality_score}",
                f"cinematic_score={cinematic_score}",
                f"visual_mode={visual_mode or 'none'}",
                f"cut_mode={cut_mode or 'none'}",
                f"approved={str(approved).lower()}",
                "gate_mode=contract_driven",
            ],
        )

        if requires_vlm_aesthetic_audit and vlm_aesthetic_audit_passed is None:
            notes.append("vlm_aesthetic_audit=pending_signal")
        if requires_rejection_feedback_loop and rejection_feedback_loop_ready is None:
            notes.append("rejection_feedback_loop=pending_signal")

        return CinematicGateResult(
            ok=True,
            state="cinematic_gate_ready",
            contract_state=_clean_text(
                contract.get("state") or "cinematic_gate_contract_unavailable"
            ),
            cinematic_score=cinematic_score,
            approved=approved,
            veto_reason=veto_reason,
            minimum_cinematic_score=minimum_cinematic_score,
            minimum_multimodal_qa_score=minimum_multimodal_qa_score,
            minimum_premium_quality_score=minimum_premium_quality_score,
            requires_vlm_aesthetic_audit=requires_vlm_aesthetic_audit,
            requires_rejection_feedback_loop=requires_rejection_feedback_loop,
            pep_enabled=pep_enabled,
            veto_priority=veto_priority,
            notes=notes,
        ).to_dict()
