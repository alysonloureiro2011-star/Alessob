from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


DEFAULT_BLOCKED_EXCESSES = [
    "plastic_skin_effect",
    "perfect_centering_everywhere",
    "hyper_clean_ai_pattern",
    "ornament_without_function",
    "sterile_voice_texture",
    "uncanny_micro_expression_loop",
]

DEFAULT_GUARDRAILS = [
    "evitar perfeicao plastica",
    "evitar simetria artificial excessiva",
    "preservar identidade acima do polimento",
    "preservar legibilidade acima do efeito",
    "parecer humano sem parecer baguncado",
]


@dataclass(frozen=True)
class NaturalismContract:
    state: str
    grain_luminance_percent: int
    dynamic_range_profile: str
    pitch_variation_percent_min: int
    pitch_variation_percent_max: int
    ambience_foley_db: int
    micro_expression_duration_ms: int
    micro_expression_frame_window: str
    apply_micro_variation: bool
    apply_texture_hint: bool
    apply_layout_irregularity: bool
    apply_timing_humanization: bool
    identity_over_polish: bool
    blocked_excesses: list[str]
    guardrails: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def resolve_naturalism_contract(format_hint: str | None = None) -> dict[str, Any]:
    normalized_format = _clean_text(format_hint or "image").lower()
    is_reel = normalized_format == "reel"

    contract = NaturalismContract(
        state="naturalism_contract_ready",
        grain_luminance_percent=2,
        dynamic_range_profile="hdr10_plus",
        pitch_variation_percent_min=15,
        pitch_variation_percent_max=20,
        ambience_foley_db=-40,
        micro_expression_duration_ms=120,
        micro_expression_frame_window="15-22",
        apply_micro_variation=True,
        apply_texture_hint=True,
        apply_layout_irregularity=not is_reel,
        apply_timing_humanization=is_reel,
        identity_over_polish=True,
        blocked_excesses=list(DEFAULT_BLOCKED_EXCESSES),
        guardrails=list(DEFAULT_GUARDRAILS),
        notes=[
            f"format_hint={normalized_format}",
            "source=sovereign_annexes",
            "grain=2_percent",
            "dynamic_range=hdr10_plus",
            "pitch_variation=15_20_percent",
            "ambience_foley=-40db",
            "micro_expression=120ms_frames_15_22",
            "identity_over_polish=true",
        ],
    )
    return contract.to_dict()


def naturalism_contract_examples() -> dict[str, Any]:
    return {
        "image_case": resolve_naturalism_contract("image"),
        "reel_case": resolve_naturalism_contract("reel"),
    }
