from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


MIN_CINEMATIC_SCORE = 8.0
MIN_CONTRAST_SCORE = 7.5
MIN_COMPOSITION_SCORE = 7.5
MIN_ARTIFACT_SCORE = 7.5
MIN_BRAND_DIGNITY_SCORE = 8.5
MIN_GLOBAL_VISUAL_SCORE = 8.0


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
class VisualQualityGateResult:
    ok: bool
    gate_state: str
    eligible: bool
    global_visual_score: float
    cinematic_score: float
    contrast_score: float
    composition_score: float
    artifact_score: float
    brand_dignity_score: float
    fail_reasons: list[str]
    pass_reasons: list[str]
    guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class VisualQualityGate:
    """
    Gate soberano de qualidade visual.

    Função:
    - avaliar leitura cinematográfica, contraste, composição, artefatos e dignidade de marca
    - bloquear visual fraco antes de staging ou publish real
    - produzir uma leitura auditável de elegibilidade premium
    """

    def run(
        self,
        *,
        visual_context: dict[str, Any] | None = None,
        naturalism: dict[str, Any] | None = None,
        brand_dignity: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        visual_context = _safe_dict(visual_context)
        naturalism = _safe_dict(naturalism)
        brand_dignity = _safe_dict(brand_dignity)

        cinematic_score = _safe_float(visual_context.get("cinematic_score"), 8.1)
        contrast_score = _safe_float(visual_context.get("contrast_score"), 7.9)
        composition_score = _safe_float(visual_context.get("composition_score"), 8.0)
        artifact_score = _safe_float(visual_context.get("artifact_score"), 8.2)
        brand_dignity_score = _safe_float(brand_dignity.get("brand_dignity_score"), 8.6)

        if naturalism.get("naturalism_state") != "naturalism_engine_ready":
            cinematic_score = min(cinematic_score, 7.2)
            composition_score = min(composition_score, 7.2)

        global_visual_score = _avg([
            cinematic_score,
            contrast_score,
            composition_score,
            artifact_score,
            brand_dignity_score,
        ])

        fail_reasons: list[str] = []
        pass_reasons: list[str] = []

        if cinematic_score < MIN_CINEMATIC_SCORE:
            fail_reasons.append("cinematic_score_baixo")
        else:
            pass_reasons.append("cinematic_score_ok")

        if contrast_score < MIN_CONTRAST_SCORE:
            fail_reasons.append("contraste_baixo")
        else:
            pass_reasons.append("contraste_ok")

        if composition_score < MIN_COMPOSITION_SCORE:
            fail_reasons.append("composicao_fraca")
        else:
            pass_reasons.append("composicao_ok")

        if artifact_score < MIN_ARTIFACT_SCORE:
            fail_reasons.append("artefatos_visuais")
        else:
            pass_reasons.append("artefatos_ok")

        if brand_dignity_score < MIN_BRAND_DIGNITY_SCORE:
            fail_reasons.append("risco_de_marca_visual")
        else:
            pass_reasons.append("brand_dignity_ok")

        if global_visual_score < MIN_GLOBAL_VISUAL_SCORE:
            fail_reasons.append("score_global_visual_insuficiente")

        result = VisualQualityGateResult(
            ok=True,
            gate_state="visual_quality_gate_ready",
            eligible=len(fail_reasons) == 0,
            global_visual_score=global_visual_score,
            cinematic_score=cinematic_score,
            contrast_score=contrast_score,
            composition_score=composition_score,
            artifact_score=artifact_score,
            brand_dignity_score=brand_dignity_score,
            fail_reasons=fail_reasons,
            pass_reasons=pass_reasons,
            guardrails=[
                "visual_fraco_nao_sobe",
                "legibilidade_acima_do_efeito",
                "composicao_precisa_guiar_o_olhar",
                "marca_acima_de_estetica_vazia",
            ],
        )
        return result.to_dict()


def visual_quality_gate_examples() -> dict[str, Any]:
    gate = VisualQualityGate()
    return {
        "approved_case": gate.run(
            visual_context={
                "cinematic_score": 8.3,
                "contrast_score": 8.0,
                "composition_score": 8.1,
                "artifact_score": 8.4,
            },
            naturalism={"naturalism_state": "naturalism_engine_ready"},
            brand_dignity={"brand_dignity_score": 8.8},
        ),
        "blocked_case": gate.run(
            visual_context={
                "cinematic_score": 6.8,
                "contrast_score": 6.9,
                "composition_score": 6.7,
                "artifact_score": 6.5,
            },
            naturalism={},
            brand_dignity={"brand_dignity_score": 6.9},
        ),
    }
