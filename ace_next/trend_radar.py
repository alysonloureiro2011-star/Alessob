from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


WEAK_TRENDS = {
    "",
    "123",
    "hello",
    "oi",
    "test",
    "teste",
    "teste real",
}

TREND_FALLBACK = "clareza, disciplina e direção"


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize(value: Any) -> str:
    return _clean_text(value).lower()


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


@dataclass(frozen=True)
class TrendRadarInput:
    trend: str
    recent_signal_score: float | None
    signal_context: dict[str, Any]
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrendRadarOutput:
    ok: bool
    raw_trend: str
    normalized_trend: str
    effective_trend: str
    weak_trend: bool
    signal_strength: str
    recent_signal_score: float | None
    source: str
    radar_state: str
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TrendRadar:
    """
    Camada soberana de percepção.

    Função:
    - limpar a tendência recebida
    - detectar tendência fraca
    - aplicar fallback conservador
    - classificar a força do sinal

    Nesta etapa ele ainda não busca tendências externas.
    Ele organiza e qualifica a entrada para o cérebro editorial.
    """

    def build_input(
        self,
        *,
        trend: Any,
        recent_signal_score: Any = None,
        signal_context: dict[str, Any] | None = None,
        source: str = "official_runtime",
    ) -> TrendRadarInput:
        cleaned_trend = _clean_text(trend)
        return TrendRadarInput(
            trend=cleaned_trend,
            recent_signal_score=_safe_float(recent_signal_score),
            signal_context=_safe_dict(signal_context),
            source=_clean_text(source) or "official_runtime",
        )

    def _signal_strength(self, recent_signal_score: float | None) -> str:
        if recent_signal_score is None:
            return "unknown"
        if recent_signal_score < 0.35:
            return "weak"
        if recent_signal_score >= 0.70:
            return "strong"
        return "medium"

    def run(
        self,
        *,
        trend: Any,
        recent_signal_score: Any = None,
        signal_context: dict[str, Any] | None = None,
        source: str = "official_runtime",
    ) -> dict[str, Any]:
        radar_input = self.build_input(
            trend=trend,
            recent_signal_score=recent_signal_score,
            signal_context=signal_context,
            source=source,
        )

        normalized_trend = _normalize(radar_input.trend)
        weak_trend = normalized_trend in WEAK_TRENDS

        effective_trend = TREND_FALLBACK if weak_trend else (radar_input.trend or TREND_FALLBACK)
        signal_strength = self._signal_strength(radar_input.recent_signal_score)

        notes: list[str] = []
        if weak_trend:
            notes.append("trend_weak_fallback_applied")
        if signal_strength == "unknown":
            notes.append("signal_strength_unknown")
        else:
            notes.append(f"signal_strength={signal_strength}")

        output = TrendRadarOutput(
            ok=True,
            raw_trend=radar_input.trend,
            normalized_trend=normalized_trend,
            effective_trend=effective_trend,
            weak_trend=weak_trend,
            signal_strength=signal_strength,
            recent_signal_score=radar_input.recent_signal_score,
            source=radar_input.source,
            radar_state="trend_radar_ready",
            notes=notes,
        )
        return {
            "input": radar_input.to_dict(),
            **output.to_dict(),
        }


def trend_radar_examples() -> dict[str, Any]:
    radar = TrendRadar()
    return {
        "weak_input": radar.run(
            trend="teste real",
            recent_signal_score=None,
            signal_context={"source": "example"},
            source="example",
        ),
        "strong_input": radar.run(
            trend="disciplina e clareza mental",
            recent_signal_score=0.81,
            signal_context={"source": "example"},
            source="example",
        ),
    }
