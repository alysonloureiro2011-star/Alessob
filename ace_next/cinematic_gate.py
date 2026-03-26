from dataclasses import dataclass, asdict
from typing import Any, Dict


def _safe_dict(value: Any) -> Dict:
    return dict(value) if isinstance(value, dict) else {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except:
        return default


@dataclass
class CinematicGateResult:
    ok: bool
    state: str
    cinematic_score: float
    approved: bool
    veto_reason: str
    notes: list

    def to_dict(self):
        return asdict(self)


class CinematicGate:

    def run(
        self,
        *,
        multimodal_qa: Dict | None = None,
        reel_director: Dict | None = None,
        premium_decision: Dict | None = None,
    ) -> Dict:
        multimodal_qa = _safe_dict(multimodal_qa)
        reel_director = _safe_dict(reel_director)
        premium_decision = _safe_dict(premium_decision)

        qa_score = _safe_float(multimodal_qa.get("global_score"), 0.0)
        quality_score = _safe_float(premium_decision.get("overall_quality_score"), 0.0)
        visual_mode = str(reel_director.get("visual_mode") or "")
        cut_mode = str(reel_director.get("cut_mode") or "")

        bonus = 0.0
        if visual_mode == "cinematic_retention":
            bonus += 0.3
        if cut_mode == "precision_fast":
            bonus += 0.2

        cinematic_score = round(((qa_score * 0.7) + (quality_score * 0.3) + bonus), 2)
        approved = cinematic_score >= 8.5

        if approved:
            veto_reason = ""
        elif qa_score < 8.2:
            veto_reason = "multimodal_qa_low"
        elif quality_score < 8.0:
            veto_reason = "premium_quality_low"
        else:
            veto_reason = "cinematic_score_low"

        return CinematicGateResult(
            ok=True,
            state="cinematic_gate_ready",
            cinematic_score=cinematic_score,
            approved=approved,
            veto_reason=veto_reason,
            notes=[
                f"qa_score={qa_score}",
                f"quality_score={quality_score}",
                f"approved={str(approved).lower()}"
            ],
        ).to_dict()
