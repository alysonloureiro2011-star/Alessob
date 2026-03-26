from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


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


@dataclass(frozen=True)
class SerialPublishingResult:
    ok: bool
    serial_state: str
    is_serial: bool
    series_id: str
    episode_number: int
    strategy: str
    confidence_band: str
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SerialPublishingEngine:
    """
    Camada soberana de serialidade.

    Função:
    - decidir se o conteúdo deve virar série
    - orientar expansão de vencedor sem virar spam
    - preparar continuidade narrativa acumulativa
    """

    def run(
        self,
        *,
        trend: Any,
        performance_signal: dict[str, Any] | None = None,
        learning_signal: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        performance_signal = _safe_dict(performance_signal)
        learning_signal = _safe_dict(learning_signal)

        trend_text = _clean_text(trend) or "serie_base"
        score = _safe_float(performance_signal.get("score"), 0.0)
        case_strength = _clean_text(learning_signal.get("case_strength")).lower() or "weak"
        seed = trend_text.lower().replace(" ", "_")

        if score >= 8.8 or case_strength == "strong":
            result = SerialPublishingResult(
                ok=True,
                serial_state="serial_expansion",
                is_serial=True,
                series_id=seed,
                episode_number=2,
                strategy="expand_winner",
                confidence_band="high",
                notes=["conteudo_virou_serie", "expandir_sem_spam"],
            )
        elif score >= 8.0 or case_strength == "medium":
            result = SerialPublishingResult(
                ok=True,
                serial_state="serial_test",
                is_serial=True,
                series_id=seed,
                episode_number=1,
                strategy="test_sequence",
                confidence_band="medium",
                notes=["potencial_serial", "validar_continuidade"],
            )
        else:
            result = SerialPublishingResult(
                ok=True,
                serial_state="single_post",
                is_serial=False,
                series_id="",
                episode_number=1,
                strategy="isolated",
                confidence_band="safe",
                notes=["sem_serial", "coletar_mais_sinal"],
            )

        return result.to_dict()


def serial_publishing_examples() -> dict[str, Any]:
    engine = SerialPublishingEngine()
    return {
        "winner_case": engine.run(
            trend="clareza, disciplina e direção",
            performance_signal={"score": 8.9},
            learning_signal={"case_strength": "strong"},
        ),
        "test_case": engine.run(
            trend="clareza, disciplina e direção",
            performance_signal={"score": 8.2},
            learning_signal={"case_strength": "medium"},
        ),
        "single_case": engine.run(
            trend="clareza, disciplina e direção",
            performance_signal={"score": 7.1},
            learning_signal={"case_strength": "weak"},
        ),
    }
