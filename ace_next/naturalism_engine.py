from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .naturalism_contract import resolve_naturalism_contract


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


def _safe_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _merge_unique(*values: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for group in values:
        for item in group:
            text = _clean_text(item)
            if not text or text in seen:
                continue
            seen.add(text)
            merged.append(text)
    return merged


@dataclass(frozen=True)
class NaturalismDecision:
    ok: bool
    naturalism_state: str
    contract_state: str
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
    notes: list[str]
    guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class NaturalismEngine:
    """
    Camada conservadora de humanização guiada por contrato soberano.

    Função:
    - reduzir cheiro de IA
    - evitar perfeição plástica
    - preservar naturalidade com controle
    - centralizar parâmetros de naturalismo em uma única fonte

    Nesta etapa ele não renderiza nada.
    Ele apenas devolve decisão e regras para serem usadas depois
    no visual premium e no reel stack.
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
        normalized_format = _clean_text(
            format_hint
            or creative_plan.get("publish_format_now")
            or visual_context.get("format_hint")
            or "image"
        ).lower()

        contract = _safe_dict(resolve_naturalism_contract(normalized_format))

        decision = NaturalismDecision(
            ok=True,
            naturalism_state="naturalism_engine_ready",
            contract_state=_clean_text(
                contract.get("state") or "naturalism_contract_unavailable"
            ),
            grain_luminance_percent=int(contract.get("grain_luminance_percent") or 0),
            dynamic_range_profile=_clean_text(
                contract.get("dynamic_range_profile") or "unknown"
            ),
            pitch_variation_percent_min=int(
                contract.get("pitch_variation_percent_min") or 0
            ),
            pitch_variation_percent_max=int(
                contract.get("pitch_variation_percent_max") or 0
            ),
            ambience_foley_db=int(contract.get("ambience_foley_db") or 0),
            micro_expression_duration_ms=int(
                contract.get("micro_expression_duration_ms") or 0
            ),
            micro_expression_frame_window=_clean_text(
                contract.get("micro_expression_frame_window") or "unknown"
            ),
            apply_micro_variation=bool(contract.get("apply_micro_variation")),
            apply_texture_hint=bool(contract.get("apply_texture_hint")),
            apply_layout_irregularity=bool(contract.get("apply_layout_irregularity")),
            apply_timing_humanization=bool(contract.get("apply_timing_humanization")),
            identity_over_polish=bool(contract.get("identity_over_polish")),
            blocked_excesses=_safe_list(contract.get("blocked_excesses")),
            notes=_merge_unique(
                _safe_list(contract.get("notes")),
                [
                    f"engine_format_hint={normalized_format}",
                    "engine_mode=contract_driven",
                    "contract_applied=true",
                ],
            ),
            guardrails=_safe_list(contract.get("guardrails")),
        )
        return {
            "creative_plan_used": creative_plan,
            "visual_context_used": visual_context,
            **decision.to_dict(),
        }


def naturalism_engine_examples() -> dict[str, Any]:
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
