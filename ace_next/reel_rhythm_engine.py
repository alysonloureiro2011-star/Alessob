from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


@dataclass(frozen=True)
class ReelRhythmDecision:
    ok: bool
    rhythm_state: str
    target_cut_density: str
    target_pattern_interrupt_window: str
    dead_air_policy: str
    subtitle_pacing_hint: str
    notes: list[str]
    forbidden_rhythm_traits: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReelRhythmEngine:
    """
    Camada soberana de ritmo para reels.

    Função:
    - orientar cadência de cortes
    - reduzir dead air
    - organizar pattern interrupts
    - preparar legendas e micro-payoffs
    """

    def run(
        self,
        *,
        storyboard: dict[str, Any] | None = None,
        hook_opening: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        storyboard = _safe_dict(storyboard)
        hook_opening = _safe_dict(hook_opening)

        scene_count = int(storyboard.get("scene_count") or 0)
        opening_pattern = str(hook_opening.get("opening_pattern") or "curiosity_gap").strip()

        if scene_count >= 4:
            target_cut_density = "high_controlled"
            target_pattern_interrupt_window = "3_to_5_seconds"
        else:
            target_cut_density = "medium_controlled"
            target_pattern_interrupt_window = "4_to_6_seconds"

        if opening_pattern in {"authority_shock", "curiosity_gap"}:
            subtitle_pacing_hint = "short_emphasis_lines"
        else:
            subtitle_pacing_hint = "balanced_lines"

        decision = ReelRhythmDecision(
            ok=True,
            rhythm_state="reel_rhythm_ready",
            target_cut_density=target_cut_density,
            target_pattern_interrupt_window=target_pattern_interrupt_window,
            dead_air_policy="zero_dead_air",
            subtitle_pacing_hint=subtitle_pacing_hint,
            notes=[
                f"scene_count={scene_count}",
                f"opening_pattern={opening_pattern}",
                "retention_priority=high",
            ],
            forbidden_rhythm_traits=[
                "intro_lenta",
                "explicacao_sem_movimento",
                "corte_aleatorio_sem_funcao",
                "texto_lento_demais",
            ],
        )
        return decision.to_dict()


def reel_rhythm_examples() -> dict[str, Any]:
    engine = ReelRhythmEngine()
    return engine.run(
        storyboard={"scene_count": 4},
        hook_opening={"opening_pattern": "curiosity_gap"},
    )
