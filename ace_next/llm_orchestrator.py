from __future__ import annotations

import os
from typing import Any


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _limit_words(text: str, max_words: int) -> str:
    words = _clean_text(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).strip()


class LLMOrchestrator:
    """
    Stub soberano:
    - entrega a classe esperada pelo runtime/registry
    - gera plano
    - repara plano antes do gate
    """

    def __init__(self, provider: str | None = None) -> None:
        self.provider = provider or os.environ.get("ACE_LLM_PROVIDER") or "stub"

    def run_planner(
        self,
        trend: str,
        style_hint: str | None = None,
    ) -> dict[str, Any]:
        trend = _clean_text(trend)
        return {
            "ok": True,
            "provider": self.provider,
            "creative_plan": {
                "topic_seed": trend,
                "headline": _limit_words(f"{trend}: o ponto que quase ninguém percebe", 10),
                "hook": _limit_words(f"O erro escondido por trás de {trend}", 10),
                "body": _limit_words(
                    f"{trend} afeta atenção, decisão e resultado. Quando a mensagem fica clara, curta e com valor percebido, a retenção sobe e o conteúdo deixa de parecer genérico.",
                    42,
                ),
                "payoff": _limit_words(
                    f"Entender {trend} com clareza para agir melhor e evitar ruído, distração e perda de resultado.",
                    18,
                ),
                "cta": "Salve e envie para alguém que precisa disto.",
                "publish_format_now": "image",
                "publish_style": style_hint or "official_next_visual_foundation_v1",
                "goal": "authority",
            },
        }

    def repair_plan(
        self,
        *,
        trend: str,
        creative_plan: dict[str, Any],
        rewrite_targets: dict[str, bool],
        platform: str = "instagram",
    ) -> dict[str, Any]:
        plan = dict(creative_plan or {})
        trend = _clean_text(trend or plan.get("topic_seed") or "tema")

        if rewrite_targets.get("rewrite_hook"):
            plan["hook"] = _limit_words(f"O erro escondido por trás de {trend}", 10)

        if rewrite_targets.get("rewrite_body"):
            plan["body"] = _limit_words(
                f"{trend} afeta atenção, decisão e resultado. A correção é cortar ruído, aumentar clareza e transformar a mensagem em valor percebido imediato.",
                38,
            )

        if rewrite_targets.get("rewrite_cta"):
            plan["cta"] = "Salve e envie para alguém que precisa disto."

        if rewrite_targets.get("rewrite_payoff"):
            plan["payoff"] = _limit_words(
                f"Ganhar clareza sobre {trend} para decidir melhor e perder menos atenção.",
                16,
            )

        if not _clean_text(plan.get("headline")):
            plan["headline"] = _limit_words(f"{trend}: o ponto que quase ninguém vê", 11)

        return {
            "ok": True,
            "provider": self.provider,
            "creative_plan": plan,
            "repair_mode": "safe_stub_rewrite",
            "platform": platform,
        }


def llm_orchestrator_status() -> dict[str, Any]:
    return {
        "ok": True,
        "reason": "llm_orchestrator_class_ready",
        "provider": os.environ.get("ACE_LLM_PROVIDER") or "stub",
        "real_llm_configured": bool(os.environ.get("ACE_LLM_API_KEY")),
    }
