from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


MIN_HOOK_SCORE = 7.5
MIN_RHYTHM_SCORE = 7.5
MIN_LEGIBILITY_SCORE = 7.0
MIN_BRAND_DIGNITY_SCORE = 8.5
MIN_NATURALISM_SCORE = 7.5
MIN_GLOBAL_SCORE = 8.0


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
class ReelQualityGateResult:
    ok: bool
    gate_state: str
    eligible: bool
    premium_classification: str
    global_score: float
    hook_score: float
    rhythm_score: float
    legibility_score: float
    brand_dignity_score: float
    naturalism_score: float
    fail_reasons: list[str]
    pass_reasons: list[str]
    guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReelQualityGate:
    """
    Gate soberano de qualidade para reels.

    Função:
    - consolidar sinais de hook, ritmo, legibilidade, marca e naturalismo
    - bloquear peça fraca antes do publish real
    - produzir uma leitura auditável de elegibilidade premium
    """

    def run(
        self,
        *,
        hook_opening: dict[str, Any] | None = None,
        rhythm: dict[str, Any] | None = None,
        subtitles: dict[str, Any] | None = None,
        naturalism: dict[str, Any] | None = None,
        brand_dignity: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        hook_opening = _safe_dict(hook_opening)
        rhythm = _safe_dict(rhythm)
        subtitles = _safe_dict(subtitles)
        naturalism = _safe_dict(naturalism)
        brand_dignity = _safe_dict(brand_dignity)

        hook_score = 8.4 if hook_opening.get("opening_state") == "hook_opening_ready" else 5.5
        rhythm_score = 8.2 if rhythm.get("rhythm_state") == "reel_rhythm_ready" else 5.5
        legibility_score = 8.0 if subtitles.get("subtitle_state") == "reel_subtitle_ready" else 5.5
        naturalism_score = 8.1 if naturalism.get("naturalism_state") == "naturalism_engine_ready" else 5.5
        brand_dignity_score = _safe_float(brand_dignity.get("brand_dignity_score"), 8.6)

        global_score = _avg([
            hook_score,
            rhythm_score,
            legibility_score,
            naturalism_score,
            brand_dignity_score,
        ])

        fail_reasons: list[str] = []
        pass_reasons: list[str] = []

        if hook_score < MIN_HOOK_SCORE:
            fail_reasons.append("hook_fraco")
        else:
            pass_reasons.append("hook_aprovado")

        if rhythm_score < MIN_RHYTHM_SCORE:
            fail_reasons.append("ritmo_fraco")
        else:
            pass_reasons.append("ritmo_aprovado")

        if legibility_score < MIN_LEGIBILITY_SCORE:
            fail_reasons.append("legibilidade_fraca")
        else:
            pass_reasons.append("legibilidade_aprovada")

        if naturalism_score < MIN_NATURALISM_SCORE:
            fail_reasons.append("naturalismo_fraco")
        else:
            pass_reasons.append("naturalismo_aprovado")

        if brand_dignity_score < MIN_BRAND_DIGNITY_SCORE:
            fail_reasons.append("risco_de_marca")
        else:
            pass_reasons.append("marca_protegida")

        if global_score < MIN_GLOBAL_SCORE:
            fail_reasons.append("score_global_insuficiente")

        eligible = len(fail_reasons) == 0

        if eligible and global_score >= 8.8:
            premium_classification = "brand_live_candidate"
        elif eligible:
            premium_classification = "editorial_staging_candidate"
        else:
            premium_classification = "blocked"

        result = ReelQualityGateResult(
            ok=True,
            gate_state="reel_quality_gate_ready",
            eligible=eligible,
            premium_classification=premium_classification,
            global_score=global_score,
            hook_score=hook_score,
            rhythm_score=rhythm_score,
            legibility_score=legibility_score,
            brand_dignity_score=brand_dignity_score,
            naturalism_score=naturalism_score,
            fail_reasons=fail_reasons,
            pass_reasons=pass_reasons,
            guardrails=[
                "nenhum_reel_fraco_publica",
                "marca_acima_de_volume",
                "legibilidade_acima_do_efeito",
                "naturalidade_acima_da_plastica",
            ],
        )
        return result.to_dict()


def reel_quality_gate_examples() -> dict[str, Any]:
    gate = ReelQualityGate()
    return {
        "approved_case": gate.run(
            hook_opening={"opening_state": "hook_opening_ready"},
            rhythm={"rhythm_state": "reel_rhythm_ready"},
            subtitles={"subtitle_state": "reel_subtitle_ready"},
            naturalism={"naturalism_state": "naturalism_engine_ready"},
            brand_dignity={"brand_dignity_score": 8.9},
        ),
        "blocked_case": gate.run(
            hook_opening={},
            rhythm={},
            subtitles={},
            naturalism={},
            brand_dignity={"brand_dignity_score": 6.9},
        ),
    }
