from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .study_contracts_soberanos_v1 import (
    HOOK_OPENING_STUDY_CONTRACT_V1,
    NATURALISM_STUDY_CONTRACT_V1,
    validate_naturalism_contract,
)


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        try:
            parsed = value.to_dict()
            return dict(parsed) if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


@dataclass(frozen=True)
class NaturalismDecision:
    ok: bool
    naturalism_state: str
    apply_micro_variation: bool
    apply_texture_hint: bool
    apply_layout_irregularity: bool
    apply_timing_humanization: bool
    grain_luminance_percent: int
    dynamic_range_profile: str
    pitch_variation_percent_min: int
    pitch_variation_percent_max: int
    ambience_foley_db: int
    micro_expression_duration_ms: int
    micro_expression_frame_window: str
    identity_over_polish: bool
    blocked_excesses: list[str]
    notes: list[str]
    guardrails: list[str]
    study_alignment: dict[str, Any]
    validation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class NaturalismEngine:
    """
    Camada soberana de naturalismo.

    v2 endurece a decisao de humanizacao com os contratos dos estudos,
    sem tocar em renderizacao final nem no runtime oficial.

    Objetivo:
    - reduzir cheiro de IA
    - transformar guardrails qualitativos em especificacao reutilizavel
    - preparar a futura ligacao unica no OfficialRuntime
    """

    def run(
        self,
        *,
        creative_plan: dict[str, Any] | None = None,
        visual_context: dict[str, Any] | None = None,
        format_hint: str | None = None,
    ) -> dict[str, Any]:
        creative_plan = _safe_dict(creative_plan)
        visual_context = _safe_dict(visual_context)
        format_hint = _clean_text(
            format_hint or creative_plan.get("publish_format_now") or visual_context.get("format_hint") or "image"
        ).lower()

        blocked_excesses = [
            "plastic_skin_effect",
            "perfect_centering_everywhere",
            "hyper_clean_ai_pattern",
            "ornament_without_function",
            "sterile_voice_texture",
            "uncanny_micro_expression_loop",
        ]

        is_reel = format_hint == "reel"
        apply_timing_humanization = is_reel
        apply_layout_irregularity = not is_reel

        study_alignment = {
            "naturalism_contract": NATURALISM_STUDY_CONTRACT_V1["state"],
            "hook_opening_contract": HOOK_OPENING_STUDY_CONTRACT_V1["state"],
            "grain_luminance_percent": NATURALISM_STUDY_CONTRACT_V1["grain_luminance_percent"],
            "dynamic_range_profile": NATURALISM_STUDY_CONTRACT_V1["dynamic_range_profile"],
            "pitch_variation_percent": [
                NATURALISM_STUDY_CONTRACT_V1["pitch_variation_percent_min"],
                NATURALISM_STUDY_CONTRACT_V1["pitch_variation_percent_max"],
            ],
            "foley_db": NATURALISM_STUDY_CONTRACT_V1["foley_db"],
            "micro_expression_duration_ms": HOOK_OPENING_STUDY_CONTRACT_V1["micro_expression_duration_ms"],
            "micro_expression_frame_window": HOOK_OPENING_STUDY_CONTRACT_V1["micro_expression_frame_window"],
        }

        partial_decision = {
            "naturalism_state": "naturalism_engine_ready_v2",
            "apply_micro_variation": True,
            "apply_texture_hint": True,
        }
        validation = validate_naturalism_contract(partial_decision)

        notes = [
            f"format_hint={format_hint}",
            f"timing_humanization={str(apply_timing_humanization).lower()}",
            f"layout_irregularity={str(apply_layout_irregularity).lower()}",
            "naturalism_mode=study_contracts_v1",
            "identity_over_polish=true",
            "anti_ai_vibe_priority=high",
        ]

        decision = NaturalismDecision(
            ok=True,
            naturalism_state="naturalism_engine_ready_v2",
            apply_micro_variation=True,
            apply_texture_hint=True,
            apply_layout_irregularity=apply_layout_irregularity,
            apply_timing_humanization=apply_timing_humanization,
            grain_luminance_percent=int(NATURALISM_STUDY_CONTRACT_V1["grain_luminance_percent"]),
            dynamic_range_profile=str(NATURALISM_STUDY_CONTRACT_V1["dynamic_range_profile"]),
            pitch_variation_percent_min=int(NATURALISM_STUDY_CONTRACT_V1["pitch_variation_percent_min"]),
            pitch_variation_percent_max=int(NATURALISM_STUDY_CONTRACT_V1["pitch_variation_percent_max"]),
            ambience_foley_db=int(NATURALISM_STUDY_CONTRACT_V1["foley_db"]),
            micro_expression_duration_ms=int(HOOK_OPENING_STUDY_CONTRACT_V1["micro_expression_duration_ms"]),
            micro_expression_frame_window=str(HOOK_OPENING_STUDY_CONTRACT_V1["micro_expression_frame_window"]),
            identity_over_polish=True,
            blocked_excesses=blocked_excesses,
            notes=notes,
            guardrails=list(NATURALISM_STUDY_CONTRACT_V1["guardrails"]),
            study_alignment=study_alignment,
            validation=validation,
        )
        return {
            "creative_plan_used": creative_plan,
            "visual_context_used": visual_context,
            **decision.to_dict(),
        }


def naturalism_engine_v2_examples() -> dict[str, Any]:
    engine = NaturalismEngine()
    return {
        "image_case": engine.run(
            creative_plan={
                "topic_seed": "clareza, disciplina e direcao",
                "publish_format_now": "image",
            },
            visual_context={"template_id": "hero_card_v1"},
        ),
        "reel_case": engine.run(
            creative_plan={
                "topic_seed": "clareza, disciplina e direcao",
                "publish_format_now": "reel",
            },
            visual_context={"template_id": "hook_reel_v1"},
        ),
    }
