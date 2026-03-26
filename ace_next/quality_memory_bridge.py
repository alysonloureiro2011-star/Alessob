from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


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
class QualityMemoryRecord:
    ok: bool
    memory_state: str
    recorded_at: str
    decision_state: str | None
    recommended_action: str | None
    topic_seed: str | None
    format_now: str | None
    overall_quality_score: float
    evidence_state: str | None
    truth_state: str | None
    promote_for_reuse: bool
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QualityMemoryBridge:
    """
    Ponte soberana entre qualidade, decisão e memória.

    Função:
    - transformar a decisão premium em memória reutilizável
    - registrar o que merece reaproveitamento
    - preparar o learning loop para trabalhar com casos fortes e fracos

    Nesta etapa ele não grava em banco.
    Ele devolve um payload limpo e auditável para ser plugado depois.
    """

    def run(
        self,
        *,
        premium_decision: dict[str, Any] | None = None,
        creative_plan: dict[str, Any] | None = None,
        publish_truth: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        premium_decision = _safe_dict(premium_decision)
        creative_plan = _safe_dict(creative_plan)
        publish_truth = _safe_dict(publish_truth)

        decision_state = _clean_text(premium_decision.get("decision_state"))
        recommended_action = _clean_text(premium_decision.get("recommended_action"))
        overall_quality_score = _safe_float(premium_decision.get("overall_quality_score"), 0.0)
        evidence_state = _clean_text(premium_decision.get("evidence_state"))
        truth_state = _clean_text(publish_truth.get("truth_state"))
        topic_seed = _clean_text(creative_plan.get("topic_seed") or creative_plan.get("headline"))
        format_now = _clean_text(
            creative_plan.get("publish_format_now") or creative_plan.get("format_recommendation")
        )

        promote_for_reuse = bool(
            overall_quality_score >= 8.5
            and decision_state in {"editorial_staging_candidate", "brand_live_candidate"}
        )

        notes: list[str] = []
        if decision_state:
            notes.append(f"decision_state={decision_state}")
        if recommended_action:
            notes.append(f"recommended_action={recommended_action}")
        if evidence_state:
            notes.append(f"evidence_state={evidence_state}")
        if truth_state:
            notes.append(f"truth_state={truth_state}")
        if promote_for_reuse:
            notes.append("promote_for_reuse=true")
        else:
            notes.append("promote_for_reuse=false")

        record = QualityMemoryRecord(
            ok=True,
            memory_state="quality_memory_bridge_ready",
            recorded_at=datetime.now().isoformat(),
            decision_state=decision_state,
            recommended_action=recommended_action,
            topic_seed=topic_seed,
            format_now=format_now,
            overall_quality_score=overall_quality_score,
            evidence_state=evidence_state,
            truth_state=truth_state,
            promote_for_reuse=promote_for_reuse,
            notes=notes,
        )
        return record.to_dict()


def quality_memory_bridge_examples() -> dict[str, Any]:
    bridge = QualityMemoryBridge()
    return {
        "staging_case": bridge.run(
            premium_decision={
                "decision_state": "editorial_staging_candidate",
                "recommended_action": "test_new_hook",
                "overall_quality_score": 8.4,
                "evidence_state": "collecting_more_signal",
            },
            creative_plan={
                "topic_seed": "clareza, disciplina e direção",
                "publish_format_now": "reel",
            },
            publish_truth={"truth_state": "publish_attempt_recorded"},
        ),
        "strong_case": bridge.run(
            premium_decision={
                "decision_state": "brand_live_candidate",
                "recommended_action": "repeat_winner",
                "overall_quality_score": 8.9,
                "evidence_state": "strong_evidence",
            },
            creative_plan={
                "topic_seed": "clareza, disciplina e direção",
                "publish_format_now": "reel",
            },
            publish_truth={"truth_state": "publish_truth_confirmed"},
        ),
    }
