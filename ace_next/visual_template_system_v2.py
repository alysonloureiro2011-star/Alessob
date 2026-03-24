from __future__ import annotations

from typing import Any


CANVAS = {"width": 1080, "height": 1350, "aspect_ratio": "4:5"}


def get_visual_template_system_v2() -> dict[str, Any]:
    templates: dict[str, dict[str, Any]] = {
        "signal_card_premium_v1": {
            "template_id": "signal_card_premium_v1",
            "display_name": "Signal Card Premium V1",
            "use_case": "headline causal + hook claro + leitura rápida mobile-first",
            "block_order": ["eyebrow", "headline", "hook", "body", "support", "cta"],
            "safe_margins": {"outer_margin": 84, "inner_margin": 36},
            "overflow_policy": {
                "headline": "truncate_last_line_soft",
                "hook": "truncate_last_line_soft",
                "body": "truncate_last_line_soft",
                "support": "drop_extra_support",
                "cta": "truncate_last_line_soft",
            },
            "contrast_expectations": {
                "headline": "strong",
                "hook": "accent_high",
                "body": "secondary_high",
                "cta": "accent_soft_high",
            },
            "blocks": {
                "eyebrow": {"x": 132, "y": 242, "width": 300, "height": 42, "priority": 1, "max_lines": 1},
                "headline": {"x": 132, "y": 316, "width": 816, "height": 210, "priority": 2, "max_lines": 3},
                "hook": {"x": 132, "y": 550, "width": 816, "height": 106, "priority": 3, "max_lines": 2},
                "body": {"x": 132, "y": 686, "width": 816, "height": 152, "priority": 4, "max_lines": 3},
                "support": {"x": 132, "y": 864, "width": 816, "height": 156, "priority": 5, "max_lines": 2},
                "cta": {"x": 132, "y": 1038, "width": 816, "height": 68, "priority": 6, "max_lines": 1},
            },
        },
        "authority_card_premium_v1": {
            "template_id": "authority_card_premium_v1",
            "display_name": "Authority Card Premium V1",
            "use_case": "posição forte, tese editorial, autoridade percebida",
            "block_order": ["eyebrow", "headline", "body", "support", "cta"],
            "safe_margins": {"outer_margin": 84, "inner_margin": 38},
            "overflow_policy": {
                "headline": "truncate_last_line_soft",
                "body": "truncate_last_line_soft",
                "support": "drop_extra_support",
                "cta": "truncate_last_line_soft",
            },
            "contrast_expectations": {
                "headline": "strong",
                "body": "secondary_high",
                "cta": "accent_soft_high",
            },
            "blocks": {
                "eyebrow": {"x": 132, "y": 242, "width": 300, "height": 42, "priority": 1, "max_lines": 1},
                "headline": {"x": 132, "y": 320, "width": 816, "height": 250, "priority": 2, "max_lines": 3},
                "body": {"x": 132, "y": 604, "width": 816, "height": 220, "priority": 3, "max_lines": 4},
                "support": {"x": 132, "y": 858, "width": 816, "height": 140, "priority": 4, "max_lines": 2},
                "cta": {"x": 132, "y": 1030, "width": 816, "height": 68, "priority": 5, "max_lines": 1},
            },
        },
        "narrative_card_premium_v1": {
            "template_id": "narrative_card_premium_v1",
            "display_name": "Narrative Card Premium V1",
            "use_case": "tensão, payoff e leitura com progressão",
            "block_order": ["eyebrow", "hook", "headline", "body", "cta"],
            "safe_margins": {"outer_margin": 84, "inner_margin": 38},
            "overflow_policy": {
                "hook": "truncate_last_line_soft",
                "headline": "truncate_last_line_soft",
                "body": "truncate_last_line_soft",
                "cta": "truncate_last_line_soft",
            },
            "contrast_expectations": {
                "hook": "accent_high",
                "headline": "strong",
                "body": "secondary_high",
                "cta": "accent_soft_high",
            },
            "blocks": {
                "eyebrow": {"x": 132, "y": 242, "width": 300, "height": 42, "priority": 1, "max_lines": 1},
                "hook": {"x": 132, "y": 320, "width": 816, "height": 118, "priority": 2, "max_lines": 2},
                "headline": {"x": 132, "y": 466, "width": 816, "height": 194, "priority": 3, "max_lines": 3},
                "body": {"x": 132, "y": 694, "width": 816, "height": 226, "priority": 4, "max_lines": 4},
                "cta": {"x": 132, "y": 1010, "width": 816, "height": 68, "priority": 5, "max_lines": 1},
            },
        },
        "continuation_card_premium_v1": {
            "template_id": "continuation_card_premium_v1",
            "display_name": "Continuation Card Premium V1",
            "use_case": "sequência, parte 2, callback e continuidade",
            "block_order": ["eyebrow", "headline", "hook", "support", "cta"],
            "safe_margins": {"outer_margin": 84, "inner_margin": 38},
            "overflow_policy": {
                "headline": "truncate_last_line_soft",
                "hook": "truncate_last_line_soft",
                "support": "drop_extra_support",
                "cta": "truncate_last_line_soft",
            },
            "contrast_expectations": {
                "headline": "strong",
                "hook": "accent_high",
                "support": "secondary_high",
                "cta": "accent_soft_high",
            },
            "blocks": {
                "eyebrow": {"x": 132, "y": 242, "width": 300, "height": 42, "priority": 1, "max_lines": 1},
                "headline": {"x": 132, "y": 320, "width": 816, "height": 208, "priority": 2, "max_lines": 3},
                "hook": {"x": 132, "y": 556, "width": 816, "height": 118, "priority": 3, "max_lines": 2},
                "support": {"x": 132, "y": 704, "width": 816, "height": 220, "priority": 4, "max_lines": 3},
                "cta": {"x": 132, "y": 1016, "width": 816, "height": 68, "priority": 5, "max_lines": 1},
            },
        },
    }
    return {"canvas": dict(CANVAS), "templates": templates}


def resolve_visual_template_v2(plan: dict[str, Any] | None = None, template_id: str | None = None) -> dict[str, Any]:
    registry = get_visual_template_system_v2()
    templates = dict(registry["templates"])

    if template_id and template_id in templates:
        return dict(templates[template_id])

    plan = dict(plan or {})
    format_hint = str(plan.get("format_recommendation") or "").lower()
    sequel = str(plan.get("sequel_potential") or "").lower()
    topic_seed = str(plan.get("topic_seed") or "").lower()

    if sequel in {"high", "part_2", "continuation"}:
        return dict(templates["continuation_card_premium_v1"])
    if any(term in topic_seed for term in ["marca", "autoridade", "posicionamento"]):
        return dict(templates["authority_card_premium_v1"])
    if format_hint == "reel":
        return dict(templates["narrative_card_premium_v1"])
    return dict(templates["signal_card_premium_v1"])


def visual_template_examples() -> dict[str, Any]:
    registry = get_visual_template_system_v2()
    approved = resolve_visual_template_v2({"topic_seed": "clareza, disciplina e direção"})
    continuation = resolve_visual_template_v2({"topic_seed": "continuação", "sequel_potential": "high"})
    return {
        "ok": True,
        "canvas": registry["canvas"],
        "default_template": approved,
        "continuation_template": continuation,
    }
