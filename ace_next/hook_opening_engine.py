from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


HOOK_PATTERNS = {
    "authority_shock": "começar com uma afirmação forte e imediatamente verificável",
    "curiosity_gap": "abrir uma lacuna de curiosidade com payoff rápido",
    "identity_callout": "chamar a dor ou identidade do público logo no início",
    "tension_then_relief": "criar tensão breve e sinalizar alívio ou solução",
}


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
class HookOpeningDecision:
    ok: bool
    opening_state: str
    opening_pattern: str
    opening_text: str
    first_seconds_goal: str
    micro_payoff_hint: str
    forbidden_opening_traits: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HookOpeningEngine:
    """
    Camada soberana de abertura.

    Funcao:
    - escolher um padrão de abertura
    - orientar os primeiros segundos
    - evitar abertura fraca ou genérica
    """

    def run(
        self,
        *,
        creative_plan: dict[str, Any] | None = None,
        format_hint: str | None = None,
    ) -> dict[str, Any]:
        creative_plan = _safe_dict(creative_plan)
        headline = _clean_text(creative_plan.get("headline") or creative_plan.get("topic_seed") or "")
        hook = _clean_text(creative_plan.get("hook") or "")
        format_hint = _clean_text(format_hint or creative_plan.get("publish_format_now") or "reel").lower()

        if hook:
            opening_text = hook
            opening_pattern = "curiosity_gap"
        elif headline:
            opening_text = headline
            opening_pattern = "authority_shock"
        else:
            opening_text = "Você está perdendo atenção logo no começo sem perceber"
            opening_pattern = "identity_callout"

        if format_hint == "reel":
            first_seconds_goal = "segurar os 2 primeiros segundos com clareza e tensão"
            micro_payoff_hint = "entregar um mini payoff até o segundo 3"
        else:
            first_seconds_goal = "fazer a primeira dobra visual prender o olhar"
            micro_payoff_hint = "entregar uma promessa clara no primeiro impacto"

        decision = HookOpeningDecision(
            ok=True,
            opening_state="hook_opening_ready",
            opening_pattern=opening_pattern,
            opening_text=opening_text,
            first_seconds_goal=first_seconds_goal,
            micro_payoff_hint=micro_payoff_hint,
            forbidden_opening_traits=[
                "abertura morna",
                "frase genérica de coach",
                "contexto demorado",
                "efeito visual sem função",
            ],
            notes=[
                f"format_hint={format_hint}",
                f"pattern={opening_pattern}",
            ],
        )
        return decision.to_dict()


def hook_opening_examples() -> dict[str, Any]:
    engine = HookOpeningEngine()
    return {
        "reel_case": engine.run(
            creative_plan={
                "headline": "O que destrói sua retenção antes dos 3 segundos",
                "hook": "Se você abre assim, o algoritmo te larga rápido",
                "publish_format_now": "reel",
            }
        ),
        "image_case": engine.run(
            creative_plan={
                "headline": "A verdade que quase ninguém percebe no conteúdo fraco",
                "publish_format_now": "image",
            }
        ),
    }
