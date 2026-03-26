from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


STRONG_STATES = {
    "brand_live_candidate",
    "publish_truth_confirmed",
    "strong_evidence",
    "resolved_winner",
}


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_text(value: Any) -> str | None:
    text = " ".join(str(value or "").strip().split())
    return text or None


@dataclass(frozen=True)
class LearningSignalRecord:
    ok: bool
    signal_state: str
    recorded_at: str
    learning_priority: str
    case_strength: str
    decision_state: str | None
    evidence_state: str | None
    truth_state: str | None
    recommended_action: str | None
    overall_quality_score: float
    should_promote_to_memory: bool
    should_retest: bool
    should_scale: bool
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LearningSignalBridge:
    """
    Ponte soberana entre decisão premium, verdade de publicação e learning.

    Função:
    - transformar o estado do ciclo em um sinal simples para aprendizado
    - dizer se o caso deve ser reaproveitado, retestado ou escalado
    - reduzir improviso no learning loop

    Nesta etapa ele não grava em banco e não altera o loop oficial.
    Ele devolve um payload limpo para integração posterior.
    """

    def run(
        self,
        *,
        premium_decision: dict[str, Any] | None = None,
        quality_memory: dict[str, Any] | None = None,
        publish_truth: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        premium_decision = _safe_dict(premium_decision)
        quality_memory = _safe_dict(quality_memory)
        publish_truth = _safe_dict(publish_truth)

        decision_state = _clean_text(premium_decision.get("decision_state"))
        evidence_state = _clean_text(premium_decision.get("evidence_state"))
        truth_state = _clean_text(publish_truth.get("truth_state"))
        recommended_action = _clean_text(premium_decision.get("recommended_action"))
        overall_quality_score = _safe_float(premium_decision.get("overall_quality_score"), 0.0)
        promote_for_reuse = bool(quality_memory.get("promote_for_reuse"))

        strong_flags = 0
        for value in [decision_state, evidence_state, truth_state]:
            if value in STRONG_STATES:
                strong_flags += 1

        if overall_quality_score >= 8.8 and strong_flags >= 2:
            case_strength = "strong"
            learning_priority = "high"
            should_scale = True
            should_retest = False
        elif overall_quality_score >= 8.0:
            case_strength = "medium"
            learning_priority = "normal"
            should_scale = False
            should_retest = True
        else:
            case_strength = "weak"
            learning_priority = "high"
            should_scale = False
            should_retest = True

        should_promote_to_memory = bool(promote_for_reuse or case_strength == "strong")

        notes: list[str] = []
        if decision_state:
            notes.append(f"decision_state={decision_state}")
        if evidence_state:
            notes.append(f"evidence_state={evidence_state}")
        if truth_state:
            notes.append(f"truth_state={truth_state}")
        if recommended_action:
            notes.append(f"recommended_action={recommended_action}")
        notes.append(f"case_strength={case_strength}")

        record = LearningSignalRecord(
            ok=True,
            signal_state="learning_signal_bridge_ready",
            recorded_at=datetime.now().isoformat(),
            learning_priority=learning_priority,
            case_strength=case_strength,
            decision_state=decision_state,
            evidence_state=evidence_state,
            truth_state=truth_state,
            recommended_action=recommended_action,
            overall_quality_score=overall_quality_score,
            should_promote_to_memory=should_promote_to_memory,
            should_retest=should_retest,
            should_scale=should_scale,
            notes=notes,
        )
        return record.to_dict()


def learning_signal_bridge_examples() -> dict[str, Any]:
    bridge = LearningSignalBridge()
    return {
        "strong_case": bridge.run(
            premium_decision={
                "decision_state": "brand_live_candidate",
                "evidence_state": "strong_evidence",
                "recommended_action": "repeat_winner",
                "overall_quality_score": 8.9,
            },
            quality_memory={"promote_for_reuse": True},
            publish_truth={"truth_state": "publish_truth_confirmed"},
        ),
        "weak_case": bridge.run(
            premium_decision={
                "decision_state": "blocked",
                "evidence_state": "weak_signal",
                "recommended_action": "repeat_probe",
                "overall_quality_score": 7.2,
            },
            quality_memory={"promote_for_reuse": False},
            publish_truth={"truth_state": "publish_attempt_recorded"},
        ),
    }
