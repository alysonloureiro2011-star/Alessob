from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


DEFAULT_WINDOWS = {
    "instagram": ["09:00", "12:00", "18:00", "21:00"],
    "youtube": ["11:00", "18:00", "20:00"],
    "tiktok": ["08:00", "12:00", "19:00", "22:00"],
    "threads": ["09:00", "13:00", "20:00"],
    "x": ["08:00", "12:00", "17:00"],
}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


@dataclass(frozen=True)
class TimingDecision:
    ok: bool
    timing_state: str
    platform_family: str
    suggested_window: str
    timing_score: float
    timing_mode: str
    notes: list[str]
    guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TimingIntelligence:
    """
    Camada soberana de timing.

    Função:
    - sugerir janela de postagem por plataforma
    - combinar qualidade do caso com sensibilidade de timing
    - preparar a matriz formato-horário sem acoplar ao publish
    """

    def run(
        self,
        *,
        platform_family: str,
        content_type: str,
        learning_signal: dict[str, Any] | None = None,
        premium_decision: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        family = _clean_text(platform_family).lower() or "instagram"
        content_type = _clean_text(content_type).lower() or "image"
        learning_signal = _safe_dict(learning_signal)
        premium_decision = _safe_dict(premium_decision)

        if family not in DEFAULT_WINDOWS:
            family = "instagram"

        windows = DEFAULT_WINDOWS[family]
        quality = _safe_float(premium_decision.get("overall_quality_score"), 0.0)
        case_strength = _clean_text(learning_signal.get("case_strength")) or "weak"

        if family == "instagram" and content_type in {"reel", "story"}:
            suggested_window = windows[-1] if quality >= 8.5 else windows[2]
        elif case_strength == "strong":
            suggested_window = windows[0]
        elif case_strength == "medium":
            suggested_window = windows[1] if len(windows) > 1 else windows[0]
        else:
            suggested_window = windows[-1]

        if quality >= 8.8 and case_strength == "strong":
            timing_mode = "prime_window"
            timing_score = 8.9
        elif quality >= 8.0:
            timing_mode = "recommended_window"
            timing_score = 8.2
        else:
            timing_mode = "safe_window"
            timing_score = 7.4

        decision = TimingDecision(
            ok=True,
            timing_state="timing_intelligence_ready",
            platform_family=family,
            suggested_window=suggested_window,
            timing_score=timing_score,
            timing_mode=timing_mode,
            notes=[
                f"platform_family={family}",
                f"content_type={content_type}",
                f"case_strength={case_strength}",
            ],
            guardrails=[
                "timing_nao_compensa_peca_fraca",
                "qualidade_vem_antes_da_janela",
                "nao_usar_volume_como_muleta",
            ],
        )
        return decision.to_dict()


def timing_intelligence_examples() -> dict[str, Any]:
    engine = TimingIntelligence()
    return {
        "instagram_reel": engine.run(
            platform_family="instagram",
            content_type="reel",
            learning_signal={"case_strength": "strong"},
            premium_decision={"overall_quality_score": 8.9},
        ),
        "threads_post": engine.run(
            platform_family="threads",
            content_type="thread",
            learning_signal={"case_strength": "medium"},
            premium_decision={"overall_quality_score": 8.2},
        ),
    }
