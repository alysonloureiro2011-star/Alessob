from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


MIN_STAGING_SCORE = 8.0
MIN_BRAND_LIVE_SCORE = 8.8


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


def _avg(values: list[float]) -> float:
    valid = [v for v in values if isinstance(v, (int, float))]
    return round(sum(valid) / len(valid), 2) if valid else 0.0


@dataclass(frozen=True)
class PremiumDecisionResult:
    ok: bool
    decision_state: str
    staging_allowed: bool
    brand_live_candidate: bool
    overall_quality_score: float
    editorial_score: float
    visual_score: float
    audio_score: float
    reel_score: float
    evidence_state: str
    recommended_action: str
    fail_reasons: list[str]
    pass_reasons: list[str]
    guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PremiumDecisionKernel:
    """
    Núcleo soberano de decisão premium.

    Função:
    - juntar gates de áudio, visual e reel
    - considerar contexto editorial e estado da evidência
    - decidir block, staging ou candidato a brand live

    Nesta etapa ele não publica.
    Ele apenas converte qualidade em decisão operacional clara.
    """

    def run(
        self,
        *,
        reel_quality_gate: dict[str, Any] | None = None,
        visual_quality_gate: dict[str, Any] | None = None,
        audio_quality_gate: dict[str, Any] | None = None,
        editorial_context: dict[str, Any] | None = None,
        evidence_interpreter: dict[str, Any] | None = None,
        recommendation_engine: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        reel_quality_gate = _safe_dict(reel_quality_gate)
        visual_quality_gate = _safe_dict(visual_quality_gate)
        audio_quality_gate = _safe_dict(audio_quality_gate)
        editorial_context = _safe_dict(editorial_context)
        evidence_interpreter = _safe_dict(evidence_interpreter)
        recommendation_engine = _safe_dict(recommendation_engine)

        editorial_score = _safe_float(editorial_context.get("editorial_score"), 8.1)
        visual_score = _safe_float(visual_quality_gate.get("global_visual_score"), 0.0)
        audio_score = _safe_float(audio_quality_gate.get("global_audio_score"), 0.0)
        reel_score = _safe_float(reel_quality_gate.get("global_score"), 0.0)
        evidence_state = str(evidence_interpreter.get("evidence_state") or "unknown").strip()
        recommended_action = str(recommendation_engine.get("recommended_action") or "observe").strip()

        overall_quality_score = _avg([
            editorial_score,
            visual_score,
            audio_score,
            reel_score,
        ])

        fail_reasons: list[str] = []
        pass_reasons: list[str] = []

        if editorial_score < MIN_STAGING_SCORE:
            fail_reasons.append("editorial_score_baixo")
        else:
            pass_reasons.append("editorial_ok")

        if visual_score < MIN_STAGING_SCORE:
            fail_reasons.append("visual_gate_baixo")
        else:
            pass_reasons.append("visual_ok")

        if audio_score < MIN_STAGING_SCORE:
            fail_reasons.append("audio_gate_baixo")
        else:
            pass_reasons.append("audio_ok")

        if reel_score < MIN_STAGING_SCORE:
            fail_reasons.append("reel_gate_baixo")
        else:
            pass_reasons.append("reel_ok")

        if overall_quality_score >= MIN_STAGING_SCORE:
            pass_reasons.append("overall_quality_ok")
        else:
            fail_reasons.append("overall_quality_baixa")

        staging_allowed = len(fail_reasons) == 0
        brand_live_candidate = staging_allowed and overall_quality_score >= MIN_BRAND_LIVE_SCORE

        if not staging_allowed:
            decision_state = "blocked"
        elif brand_live_candidate and evidence_state in {"strong_evidence", "resolved_winner", "publish_truth_confirmed"}:
            decision_state = "brand_live_candidate"
        else:
            decision_state = "editorial_staging_candidate"

        result = PremiumDecisionResult(
            ok=True,
            decision_state=decision_state,
            staging_allowed=staging_allowed,
            brand_live_candidate=brand_live_candidate,
            overall_quality_score=overall_quality_score,
            editorial_score=editorial_score,
            visual_score=visual_score,
            audio_score=audio_score,
            reel_score=reel_score,
            evidence_state=evidence_state,
            recommended_action=recommended_action,
            fail_reasons=fail_reasons,
            pass_reasons=pass_reasons,
            guardrails=[
                "qualidade_antes_de_volume",
                "sem_brand_live_sem_qualidade_real",
                "sem_publish_real_sem_prova",
                "marca_protegida_em_primeiro_lugar",
            ],
        )
        return result.to_dict()


def premium_decision_kernel_examples() -> dict[str, Any]:
    kernel = PremiumDecisionKernel()
    return {
        "blocked_case": kernel.run(
            reel_quality_gate={"global_score": 7.1},
            visual_quality_gate={"global_visual_score": 7.4},
            audio_quality_gate={"global_audio_score": 7.2},
            editorial_context={"editorial_score": 7.6},
            evidence_interpreter={"evidence_state": "weak_signal"},
            recommendation_engine={"recommended_action": "repeat_probe"},
        ),
        "staging_case": kernel.run(
            reel_quality_gate={"global_score": 8.3},
            visual_quality_gate={"global_visual_score": 8.2},
            audio_quality_gate={"global_audio_score": 8.1},
            editorial_context={"editorial_score": 8.2},
            evidence_interpreter={"evidence_state": "collecting_more_signal"},
            recommendation_engine={"recommended_action": "test_new_hook"},
        ),
        "brand_live_case": kernel.run(
            reel_quality_gate={"global_score": 9.0},
            visual_quality_gate={"global_visual_score": 8.9},
            audio_quality_gate={"global_audio_score": 8.8},
            editorial_context={"editorial_score": 8.9},
            evidence_interpreter={"evidence_state": "strong_evidence"},
            recommendation_engine={"recommended_action": "repeat_winner"},
        ),
    }
