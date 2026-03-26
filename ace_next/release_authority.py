from dataclasses import dataclass, asdict
from typing import Any, Dict


def _safe_dict(value: Any) -> Dict:
    return dict(value) if isinstance(value, dict) else {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


@dataclass
class ReleaseAuthorityResult:
    ok: bool
    state: str
    release_state: str
    approved_for_publish: bool
    blocked_by_quality: bool
    cinematic_score: float
    overall_quality_score: float
    operation_state: str
    notes: list

    def to_dict(self):
        return asdict(self)


class ReleaseAuthority:

    def run(
        self,
        *,
        cinematic_gate: Dict | None = None,
        premium_decision: Dict | None = None,
        operation_bridge: Dict | None = None,
    ) -> Dict:
        cinematic_gate = _safe_dict(cinematic_gate)
        premium_decision = _safe_dict(premium_decision)
        operation_bridge = _safe_dict(operation_bridge)

        cinematic_score = _safe_float(cinematic_gate.get("cinematic_score"), 0.0)
        cinematic_approved = bool(cinematic_gate.get("approved"))
        overall_quality_score = _safe_float(premium_decision.get("overall_quality_score"), 0.0)
        operation_state = str(operation_bridge.get("operational_state") or "lab")

        approved_for_publish = bool(
            cinematic_approved
            and overall_quality_score >= 8.5
            and operation_state in {"ready", "staging", "brand_live_ready"}
        )

        blocked_by_quality = not approved_for_publish

        if approved_for_publish:
            release_state = "APPROVED_FOR_PUBLISH"
        elif cinematic_score < 8.5:
            release_state = "BLOCKED_BY_CINEMATIC_GATE"
        elif overall_quality_score < 8.5:
            release_state = "BLOCKED_BY_QUALITY"
        else:
            release_state = "BLOCKED_BY_OPERATION_STATE"

        return ReleaseAuthorityResult(
            ok=True,
            state="release_authority_ready",
            release_state=release_state,
            approved_for_publish=approved_for_publish,
            blocked_by_quality=blocked_by_quality,
            cinematic_score=cinematic_score,
            overall_quality_score=overall_quality_score,
            operation_state=operation_state,
            notes=[
                f"release_state={release_state}",
                f"cinematic_score={cinematic_score}",
                f"overall_quality_score={overall_quality_score}",
                f"operation_state={operation_state}",
            ],
        ).to_dict()
