from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .study_contracts_soberanos_v1 import (
    HOOK_OPENING_STUDY_CONTRACT_V1,
    RHYTHM_STUDY_CONTRACT_V1,
    validate_rhythm_contract,
)


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
    cadence_pattern: str
    cadence_profile: dict[str, str]
    expected_segment_goals: dict[str, str]
    notes: list[str]
    forbidden_rhythm_traits: list[str]
    study_alignment: dict[str, Any]
    validation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReelRhythmEngine:
    """
    Camada soberana de ritmo para reels.

    v2 endurece a engine com a matematica dos estudos,
    mas preserva o contrato antigo esperado pelo runtime.

    Objetivo:
    - centralizar a cadencia real em um ponto unico
    - eliminar ambiguidade qualitativa como fonte principal
    - manter compatibilidade com o flow atual
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
            target_pattern_interrupt_window = "3_to_5_seconds"

        if opening_pattern in {"authority_shock", "curiosity_gap"}:
            subtitle_pacing_hint = "short_emphasis_lines"
        else:
            subtitle_pacing_hint = "balanced_lines"

        cadence_profile = {
            segment: f"{spec['cut_ms']}ms"
            for segment, spec in RHYTHM_STUDY_CONTRACT_V1["segments"].items()
        }
        expected_segment_goals = {
            segment: str(spec.get("goal") or "")
            for segment, spec in RHYTHM_STUDY_CONTRACT_V1["segments"].items()
        }

        study_alignment = {
            "hook_opening_contract": HOOK_OPENING_STUDY_CONTRACT_V1["state"],
            "rhythm_contract": RHYTHM_STUDY_CONTRACT_V1["state"],
            "opening_visual_interval_ms": HOOK_OPENING_STUDY_CONTRACT_V1["visual_dissonance_interval_ms"],
            "cadence_pattern": RHYTHM_STUDY_CONTRACT_V1["cadence_pattern"],
            "dead_air_policy": RHYTHM_STUDY_CONTRACT_V1["dead_air_policy"],
        }

        partial_decision = {
            "rhythm_state": "reel_rhythm_ready_v2",
            "cadence_profile": cadence_profile,
        }
        validation = validate_rhythm_contract(partial_decision)

        decision = ReelRhythmDecision(
            ok=True,
            rhythm_state="reel_rhythm_ready_v2",
            target_cut_density=target_cut_density,
            target_pattern_interrupt_window=target_pattern_interrupt_window,
            dead_air_policy=str(RHYTHM_STUDY_CONTRACT_V1["dead_air_policy"]),
            subtitle_pacing_hint=subtitle_pacing_hint,
            cadence_pattern=str(RHYTHM_STUDY_CONTRACT_V1["cadence_pattern"]),
            cadence_profile=cadence_profile,
            expected_segment_goals=expected_segment_goals,
            notes=[
                f"scene_count={scene_count}",
                f"opening_pattern={opening_pattern}",
                "retention_priority=high",
                "hardening_mode=study_contracts_v1",
                "opening_contract=0_3s_neuro_hook",
            ],
            forbidden_rhythm_traits=[
                "intro_lenta",
                "explicacao_sem_movimento",
                "corte_aleatorio_sem_funcao",
                "texto_lento_demais",
                "cadencia_generica_sem_segmentacao",
            ],
            study_alignment=study_alignment,
            validation=validation,
        )
        return decision.to_dict()


def reel_rhythm_examples() -> dict[str, Any]:
    engine = ReelRhythmEngine()
    return engine.run(
        storyboard={"scene_count": 4},
        hook_opening={"opening_pattern": "curiosity_gap"},
    )
