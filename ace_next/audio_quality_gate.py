from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


MIN_CLARITY_SCORE = 7.5
MIN_SYNC_SCORE = 7.5
MIN_MIX_SCORE = 7.0
MIN_NATURALNESS_SCORE = 7.5
MIN_GLOBAL_AUDIO_SCORE = 8.0


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
class AudioQualityGateResult:
    ok: bool
    gate_state: str
    eligible: bool
    global_audio_score: float
    clarity_score: float
    sync_score: float
    mix_score: float
    naturalness_score: float
    fail_reasons: list[str]
    pass_reasons: list[str]
    guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AudioQualityGate:
    """
    Gate soberano de qualidade de áudio.

    Função:
    - avaliar clareza, sincronização, mixagem e naturalidade
    - bloquear áudio fraco antes de publish real
    - preparar um score auditável para o pipeline premium
    """

    def run(
        self,
        *,
        voice_context: dict[str, Any] | None = None,
        sound_context: dict[str, Any] | None = None,
        subtitle_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        voice_context = _safe_dict(voice_context)
        sound_context = _safe_dict(sound_context)
        subtitle_context = _safe_dict(subtitle_context)

        clarity_score = _safe_float(voice_context.get("clarity_score"), 8.0)
        sync_score = _safe_float(voice_context.get("sync_score"), 7.9)
        mix_score = _safe_float(sound_context.get("mix_score"), 7.8)
        naturalness_score = _safe_float(voice_context.get("naturalness_score"), 8.0)

        global_audio_score = _avg([
            clarity_score,
            sync_score,
            mix_score,
            naturalness_score,
        ])

        fail_reasons: list[str] = []
        pass_reasons: list[str] = []

        if clarity_score < MIN_CLARITY_SCORE:
            fail_reasons.append("clareza_de_voz_baixa")
        else:
            pass_reasons.append("clareza_ok")

        if sync_score < MIN_SYNC_SCORE:
            fail_reasons.append("sincronizacao_fraca")
        else:
            pass_reasons.append("sync_ok")

        if mix_score < MIN_MIX_SCORE:
            fail_reasons.append("mixagem_fraca")
        else:
            pass_reasons.append("mix_ok")

        if naturalness_score < MIN_NATURALNESS_SCORE:
            fail_reasons.append("naturalidade_de_voz_baixa")
        else:
            pass_reasons.append("naturalidade_ok")

        if global_audio_score < MIN_GLOBAL_AUDIO_SCORE:
            fail_reasons.append("score_global_audio_insuficiente")

        result = AudioQualityGateResult(
            ok=True,
            gate_state="audio_quality_gate_ready",
            eligible=len(fail_reasons) == 0,
            global_audio_score=global_audio_score,
            clarity_score=clarity_score,
            sync_score=sync_score,
            mix_score=mix_score,
            naturalness_score=naturalness_score,
            fail_reasons=fail_reasons,
            pass_reasons=pass_reasons,
            guardrails=[
                "voz_precisa_ser_clara",
                "sincronizacao_nao_pode_parecer_fake",
                "mixagem_nao_pode_encobrir_a_voz",
                "naturalidade_acima_da_limpeza_robotica",
            ],
        )
        return result.to_dict()


def audio_quality_gate_examples() -> dict[str, Any]:
    gate = AudioQualityGate()
    return {
        "approved_case": gate.run(
            voice_context={"clarity_score": 8.4, "sync_score": 8.1, "naturalness_score": 8.2},
            sound_context={"mix_score": 7.9},
            subtitle_context={},
        ),
        "blocked_case": gate.run(
            voice_context={"clarity_score": 6.2, "sync_score": 6.8, "naturalness_score": 6.9},
            sound_context={"mix_score": 6.5},
            subtitle_context={},
        ),
    }
