from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


@dataclass(frozen=True)
class FirstCommentResult:
    ok: bool
    strategy_state: str
    enabled: bool
    first_comment_text: str
    notes: list[str]
    guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FirstCommentStrategy:
    """
    Camada soberana de primeiro comentário.

    Função:
    - gerar um primeiro comentário útil
    - reforçar descoberta e continuidade
    - manter coerência com a peça principal
    """

    def run(
        self,
        *,
        creative_plan: dict[str, Any] | None = None,
        distribution_heuristics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        creative_plan = _safe_dict(creative_plan)
        distribution_heuristics = _safe_dict(distribution_heuristics)

        enabled = bool(distribution_heuristics.get("first_comment_enabled"))
        headline = _clean_text(creative_plan.get("headline") or creative_plan.get("topic_seed"))
        cta = _clean_text(creative_plan.get("cta"))

        if enabled:
            first_comment_text = _clean_text(f"Ponto-chave: {headline}. {cta}")
        else:
            first_comment_text = ""

        result = FirstCommentResult(
            ok=True,
            strategy_state="first_comment_strategy_ready",
            enabled=enabled,
            first_comment_text=first_comment_text,
            notes=[f"enabled={str(enabled).lower()}"],
            guardrails=[
                "comentario_util_e_curto",
                "sem_excesso_de_repeticao",
                "sem_ruido_desnecessario",
            ],
        )
        return result.to_dict()


def first_comment_strategy_examples() -> dict[str, Any]:
    engine = FirstCommentStrategy()
    return {
        "enabled_case": engine.run(
            creative_plan={
                "headline": "Por que seu conteúdo morre antes de começar",
                "cta": "salve e revise sua próxima abertura",
            },
            distribution_heuristics={"first_comment_enabled": True},
        ),
        "disabled_case": engine.run(
            creative_plan={
                "headline": "Por que seu conteúdo morre antes de começar",
                "cta": "salve e revise sua próxima abertura",
            },
            distribution_heuristics={"first_comment_enabled": False},
        ),
    }
