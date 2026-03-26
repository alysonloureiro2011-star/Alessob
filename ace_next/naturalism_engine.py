from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


DEFAULT_NATURALISM_RULES = [
    "evitar perfeicao plastica",
    "evitar simetria artificial excessiva",
    "preservar legibilidade acima do efeito",
    "usar variacao controlada em vez de caos",
    "parecer humano sem parecer baguncado",
]


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


@dataclass(frozen=True)
class NaturalismDecision:
    ok: bool
    naturalism_state: str
    apply_micro_variation: bool
    apply_texture_hint: bool
    apply_layout_irregularity: bool
    apply_timing_humanization: bool
    blocked_excesses: list[str]
    notes: list[str]
    guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class NaturalismEngine:
    """
    Camada conservadora de humanizacao.

    Funcao:
    - reduzir cheiro de IA
    - evitar perfeicao plastica
    - preservar naturalidade com controle

    Nesta etapa ele nao renderiza nada.
    Ele apenas devolve decisao e regras para serem usadas depois
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
        format_hint = _clean_text(format_hint or creative_plan.get("publish_format_now") or "image").lower()

        blocked_excesses = [
            "plastic_skin_effect",
            "perfect_centering_everywhere",
            "hyper-clean_ai_pattern",
            "ornament_without_function",
        ]

        notes = [
            f"format_hint={format_hint}",
            "naturalism_mode=controlled",
            "identity_over_polish=true",
        ]

        if format_hint == "reel":
            apply_timing_humanization = True
            apply_layout_irregularity = False
        else:
            apply_timing_humanization = False
            apply_layout_irregularity = True

        decision = NaturalismDecision(
            ok=True,
            naturalism_state="naturalism_engine_ready",
            apply_micro_variation=True,
            apply_texture_hint=True,
            apply_layout_irregularity=apply_layout_irregularity,
            apply_timing_humanization=apply_timing_humanization,
            blocked_excesses=blocked_excesses,
            notes=notes,
            guardrails=DEFAULT_NATURALISM_RULES,
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
