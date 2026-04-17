from __future__ import annotations
from typing import Any, Dict

class LLMOrchestrator:
    """
    Orquestra um modelo de linguagem para planejar o conteúdo.
    Atualmente funciona como stub. Pode ser adaptado para usar OpenAI ou outro provedor.
    """

    def __init__(self, provider: str | None = None) -> None:
        self.provider = provider or "stub"

    def run_planner(self, trend: str, style_hint: str | None = None) -> Dict[str, Any]:
        """
        Gera um plano criativo básico. Ajuste conforme o provedor real.
        """
        headline = f"Ideias sobre {trend}"
        hook = f"Descubra algo novo sobre {trend} que vai mudar sua forma de pensar!"
        body = f"Explore como {trend} impacta sua rotina e como implementar melhorias práticas."
        cta = "Compartilhe e salve este post se fizer sentido!"
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
            "provider": self.provider,
        }

def llm_orchestrator_status() -> Dict[str, Any]:
    return {
        "ok": True,
        "reason": "llm_orchestrator_stub",
    }
