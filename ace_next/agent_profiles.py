from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    title: str
    purpose: str
    inputs: list[str]
    outputs: list[str]
    guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


TREND_SCOUT = AgentProfile(
    agent_id="trend_scout",
    title="Trend Scout",
    purpose="qualificar sinais, temas e contexto antes da decisão editorial",
    inputs=["trend", "signal_context", "recent_signal_score"],
    outputs=["effective_trend", "signal_strength", "notes"],
    guardrails=[
        "não publica",
        "não muda política da marca",
        "age só como camada de percepção",
    ],
)

EDITORIAL_STRATEGIST = AgentProfile(
    agent_id="editorial_strategist",
    title="Editorial Strategist",
    purpose="transformar sinal em tese, ângulo, hook, payoff e formato sugerido",
    inputs=["effective_trend", "brand_context", "recent_memory"],
    outputs=["mission_decision", "planner_overrides", "creative_plan"],
    guardrails=[
        "anti-clichê",
        "anti-commodity",
        "não autoriza brand live sozinho",
    ],
)

VISUAL_DIRECTOR = AgentProfile(
    agent_id="visual_director",
    title="Visual Director",
    purpose="traduzir o plano editorial em composição visual premium e legível",
    inputs=["creative_plan", "visual_contract", "brand_context"],
    outputs=["template_choice", "visual_identity", "visual_risks"],
    guardrails=[
        "não aprova peça fora do gate visual",
        "não reduz contraste para parecer sofisticado",
        "não mascara baixa qualidade com excesso visual",
    ],
)

RHYTHM_EDITOR = AgentProfile(
    agent_id="rhythm_editor",
    title="Rhythm Editor",
    purpose="controlar hook, ritmo, subtítulo, micro-payoff e cadência de reels",
    inputs=["storyboard", "hook_plan", "caption_plan"],
    outputs=["rhythm_plan", "subtitle_plan", "retention_risks"],
    guardrails=[
        "zero caos gratuito",
        "retenção ética",
        "sem manipulação oculta",
    ],
)

DISTRIBUTION_STRATEGIST = AgentProfile(
    agent_id="distribution_strategist",
    title="Distribution Strategist",
    purpose="definir timing, hipótese de distribuição e próxima jogada do conteúdo",
    inputs=["creative_plan", "performance_memory", "signal_context"],
    outputs=["timing_hypothesis", "next_format", "distribution_notes"],
    guardrails=[
        "não usa urgência falsa",
        "não força spam",
        "prioriza qualidade sobre volume",
    ],
)

REFLECTION_ANALYST = AgentProfile(
    agent_id="reflection_analyst",
    title="Reflection Analyst",
    purpose="ler resultado real e devolver insight conservador para o próximo ciclo",
    inputs=["real_metrics", "attention_metrics", "recommendation_engine"],
    outputs=["insight", "next_hypothesis", "reflection_notes"],
    guardrails=[
        "não muda política da marca",
        "não publica",
        "não autoriza brand live",
    ],
)


def build_agent_profiles() -> dict[str, dict[str, Any]]:
    profiles = [
        TREND_SCOUT,
        EDITORIAL_STRATEGIST,
        VISUAL_DIRECTOR,
        RHYTHM_EDITOR,
        DISTRIBUTION_STRATEGIST,
        REFLECTION_ANALYST,
    ]
    return {profile.agent_id: profile.to_dict() for profile in profiles}
