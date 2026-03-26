from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


EMPHASIS_MODES = {
    "short_emphasis_lines",
    "balanced_lines",
    "keyword_punch",
}


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _choose_emphasis_mode(hook_opening: dict[str, Any], rhythm: dict[str, Any]) -> str:
    opening_pattern = _clean_text(hook_opening.get("opening_pattern")).lower()
    subtitle_pacing_hint = _clean_text(rhythm.get("subtitle_pacing_hint")).lower()
    if subtitle_pacing_hint in EMPHASIS_MODES:
        return subtitle_pacing_hint
    if opening_pattern in {"authority_shock", "curiosity_gap"}:
        return "keyword_punch"
    return "balanced_lines"


@dataclass(frozen=True)
class ReelSubtitleDecision:
    ok: bool
    subtitle_state: str
    emphasis_mode: str
    max_words_per_line: int
    max_lines_on_screen: int
    highlight_keywords: list[str]
    pacing_rule: str
    guardrails: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReelSubtitleEngine:
    """
    Camada soberana de legenda para reels.

    Função:
    - controlar densidade de texto em tela
    - destacar palavras-chave
    - evitar poluição visual
    - reforçar o ritmo e o payoff
    """

    def run(
        self,
        *,
        creative_plan: dict[str, Any] | None = None,
        hook_opening: dict[str, Any] | None = None,
        rhythm: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        creative_plan = _safe_dict(creative_plan)
        hook_opening = _safe_dict(hook_opening)
        rhythm = _safe_dict(rhythm)

        emphasis_mode = _choose_emphasis_mode(hook_opening, rhythm)
        hook = _clean_text(creative_plan.get("hook"))
        headline = _clean_text(creative_plan.get("headline") or creative_plan.get("topic_seed"))

        keywords: list[str] = []
        for candidate in [hook, headline]:
            if candidate:
                words = [w.strip(".,:;!?()[]{}\"'") for w in candidate.split()]
                for word in words[:4]:
                    word = word.strip()
                    if len(word) >= 4 and word.lower() not in {k.lower() for k in keywords}:
                        keywords.append(word)

        if emphasis_mode == "keyword_punch":
            max_words_per_line = 4
            pacing_rule = "trocas rápidas com destaque de palavras-chave"
        elif emphasis_mode == "short_emphasis_lines":
            max_words_per_line = 5
            pacing_rule = "linhas curtas com pausas frequentes"
        else:
            max_words_per_line = 6
            pacing_rule = "linhas equilibradas sem poluição"

        decision = ReelSubtitleDecision(
            ok=True,
            subtitle_state="reel_subtitle_ready",
            emphasis_mode=emphasis_mode,
            max_words_per_line=max_words_per_line,
            max_lines_on_screen=2,
            highlight_keywords=keywords,
            pacing_rule=pacing_rule,
            guardrails=[
                "não cobrir rosto ou elemento principal",
                "não ultrapassar 2 linhas na maior parte do tempo",
                "não usar texto denso demais",
                "legibilidade acima do efeito",
            ],
            notes=[
                f"emphasis_mode={emphasis_mode}",
                f"keywords={len(keywords)}",
            ],
        )
        return decision.to_dict()


def reel_subtitle_examples() -> dict[str, Any]:
    engine = ReelSubtitleEngine()
    return engine.run(
        creative_plan={
            "hook": "Seu problema pode estar nos 2 primeiros segundos",
            "headline": "A verdade que destrói sua retenção",
        },
        hook_opening={"opening_pattern": "curiosity_gap"},
        rhythm={"subtitle_pacing_hint": "short_emphasis_lines"},
    )
