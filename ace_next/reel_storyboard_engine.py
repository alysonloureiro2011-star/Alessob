from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


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
class StoryboardScene:
    index: int
    role: str
    objective: str
    screen_text: str
    motion_hint: str
    payoff_hint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReelStoryboardEngine:
    """
    Camada soberana de storyboard para reels.

    Função:
    - quebrar a ideia em cenas
    - organizar abertura, desenvolvimento, payoff e fechamento
    - preparar a próxima camada de ritmo e edição
    """

    def run(
        self,
        *,
        creative_plan: dict[str, Any] | None = None,
        hook_opening: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        creative_plan = _safe_dict(creative_plan)
        hook_opening = _safe_dict(hook_opening)

        headline = _clean_text(creative_plan.get("headline") or creative_plan.get("topic_seed") or "Abertura forte")
        hook = _clean_text(creative_plan.get("hook") or hook_opening.get("opening_text") or headline)
        body = _clean_text(creative_plan.get("body") or "desenvolvimento central")
        cta = _clean_text(creative_plan.get("cta") or "salve isso para rever depois")

        scenes = [
            StoryboardScene(
                index=1,
                role="hook",
                objective="prender nos primeiros 2 segundos",
                screen_text=hook,
                motion_hint="cut-in rápido com texto forte",
                payoff_hint="lacuna de curiosidade aberta",
            ),
            StoryboardScene(
                index=2,
                role="thesis",
                objective="entregar a tese principal sem enrolar",
                screen_text=headline,
                motion_hint="troca limpa de enquadramento",
                payoff_hint="clareza imediata",
            ),
            StoryboardScene(
                index=3,
                role="development",
                objective="aprofundar sem perder ritmo",
                screen_text=body,
                motion_hint="micro zoom ou mudança de camada",
                payoff_hint="micro-payoff cognitivo",
            ),
            StoryboardScene(
                index=4,
                role="cta",
                objective="fechar com direção clara",
                screen_text=cta,
                motion_hint="fechamento limpo com respiração",
                payoff_hint="ação prática ou replay mental",
            ),
        ]

        return {
            "ok": True,
            "storyboard_state": "reel_storyboard_ready",
            "scene_count": len(scenes),
            "scenes": [scene.to_dict() for scene in scenes],
            "notes": [
                "hook_first=true",
                "development_without_dead_air=true",
                "cta_last=true",
            ],
        }


def reel_storyboard_examples() -> dict[str, Any]:
    engine = ReelStoryboardEngine()
    return engine.run(
        creative_plan={
            "headline": "Por que seu conteúdo morre antes de começar",
            "hook": "Seu problema pode estar nos 2 primeiros segundos",
            "body": "Se a abertura não cria tensão clara, a retenção cai antes do payoff.",
            "cta": "salve isso e revise sua próxima abertura",
        },
        hook_opening={
            "opening_text": "Seu problema pode estar nos 2 primeiros segundos",
        },
    )
