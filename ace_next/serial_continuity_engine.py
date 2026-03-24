from __future__ import annotations

from typing import Any

from .brand_ontology import get_brand_ontology


def build_serial_continuity(
    creative_plan: dict,
    recent_memory: list | None = None,
) -> dict[str, Any]:
    ontology = get_brand_ontology()
    recent_memory = list(recent_memory or [])

    topic_seed = str(creative_plan.get("topic_seed") or "clareza")
    hook_family = str(creative_plan.get("hook_family") or "discipline_reframe")
    format_recommendation = str(creative_plan.get("format_recommendation") or "image")

    if recent_memory:
        episode_role = "follow_up"
        continuation_type = "aprofundamento"
    elif hook_family in {"misread_reality", "identity_break"}:
        episode_role = "origin"
        continuation_type = "contraste"
    else:
        episode_role = "seed"
        continuation_type = "aplicacao"

    next_episode_seed = {
        "aprofundamento": f"o custo de ignorar {topic_seed} por mais 30 dias",
        "contraste": f"o que parece {topic_seed}, mas na prática é falta de estrutura",
        "aplicacao": f"como transformar {topic_seed} em decisão prática sem teatralidade",
    }[continuation_type]

    linked_format_suggestion = "carousel" if format_recommendation == "image" else "reel"

    callback_elements = [
        creative_plan.get("hook_family"),
        creative_plan.get("narrative_tension"),
        creative_plan.get("payoff"),
    ]
    callback_elements = [item for item in callback_elements if item]

    return {
        "ok": True,
        "series_name": creative_plan.get("series_name") or ontology.get("brand_name"),
        "episode_role": episode_role,
        "continuation_type": continuation_type,
        "next_episode_seed": next_episode_seed,
        "callback_elements": callback_elements,
        "linked_format_suggestion": linked_format_suggestion,
    }
