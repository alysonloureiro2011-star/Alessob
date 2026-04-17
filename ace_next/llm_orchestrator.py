from __future__ import annotations

from typing import Any, Dict

# Este módulo é um orquestrador de LLM simples. Ele pode ser estendido para usar GPT ou outros modelos.
class LLMOrchestrator:
    """
    Organiza chamadas a um modelo de linguagem para planejar conteúdo criativo.
    """

    def __init__(self, provider: str | None = None):
        """
        provider: Nome do provedor de LLM (openai, anthropic etc.). Não usado no stub.
        """
        self.provider = provider

    def run_planner(self, trend: str, style_hint: str | None = None) -> Dict[str, Any]:
        """
        Usa LLM para gerar um plano de conteúdo a partir da tendência.
        No stub, retorna uma estrutura simplificada.
        """
        # Enquanto não há acesso real a LLM, usar um planejamento simples
        headline = f"Ideias sobre {trend}"
        hook = f"Descubra algo novo sobre {trend} que vai mudar sua forma de pensar!"
        body = f"Explore como {trend} impacta sua rotina e como implementar melhorias práticas."
        cta = "Compartilhe e salve este post se você curtir!"
        return {
            "ok": True,
            "creative_plan": {
                "topic_seed": trend,
                "headline": headline,
                "hook": hook,
                "body": body,
                "cta": cta,
                "format": "image",
                "style": style_hint or "default",
                "goal": "explore",
            },
            "provider": self.provider or "stub",
        }

def llm_orchestrator_status() -> Dict[str, Any]:
    """
    Retorna o status simplificado do orquestrador.
    """
    return {
        "ok": True,
        "reason": "llm_orchestrator_stub",
    }
