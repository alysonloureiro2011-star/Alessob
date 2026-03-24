from __future__ import annotations

import math
from typing import Any

from .visual_brand_system_v2 import build_visual_brand_typography_spec, get_visual_brand_system_v2
from .visual_engine_contract import build_visual_engine_contract
from .visual_template_system_v2 import get_visual_template_system_v2, resolve_visual_template_v2


def _truncate_text(value: str, char_budget: int) -> str:
    text = " ".join((value or "").strip().split())
    if len(text) <= char_budget:
        return text
    if char_budget <= 3:
        return text[:char_budget]
    return text[: char_budget - 3].rstrip() + "..."


def _line_count(text: str, wrap: int) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / max(wrap, 1)))


def build_visual_foundation_soberana_v1(
    input_plan: dict[str, Any],
    *,
    theme_id: str = "midnight_authority_v2",
    template_id: str | None = None,
) -> dict[str, Any]:
    input_plan = dict(input_plan or {})
    brand_system = get_visual_brand_system_v2(theme_id)
    template_spec = resolve_visual_template_v2(input_plan, template_id)
    template_registry = get_visual_template_system_v2()
    typography_spec = build_visual_brand_typography_spec(brand_system)

    canvas = dict(template_registry["canvas"])
    safe_margins = dict(template_spec.get("safe_margins") or {"outer_margin": 84, "inner_margin": 36})

    display_payload = {
        "eyebrow": _truncate_text(str(input_plan.get("series_name") or "LIBERTA A VERDADE"), 28).upper(),
        "headline": _truncate_text(str(input_plan.get("headline") or ""), 92),
        "hook": _truncate_text(str(input_plan.get("hook") or ""), 148),
        "body": _truncate_text(str(input_plan.get("body") or ""), 190),
        "support_points": [str(item) for item in (input_plan.get("support_points") or [])[:2]],
        "cta": _truncate_text(str(input_plan.get("cta") or ""), 72),
        "topic_seed": str(input_plan.get("topic_seed") or ""),
        "format_recommendation": str(input_plan.get("format_recommendation") or "image"),
    }

    density_control = {
        "mobile_first": True,
        "density_mode": "mobile_clean",
        "whitespace_discipline": "high",
        "max_visible_blocks": 6,
        "anti_clutter_rules": [
            "headline com no máximo 3 linhas",
            "hook com no máximo 2 linhas",
            "body com no máximo 3 linhas",
            "no máximo 2 support points",
            "CTA curto, nunca parágrafo",
        ],
    }

    hierarchy_model = {
        "primary": "headline",
        "secondary": "hook",
        "tertiary": "body",
        "support": "support_points",
        "action": "cta",
        "eyebrow": "series_name",
    }

    whitespace_discipline = {
        "headline_gap": 18,
        "hook_gap": 18,
        "body_gap": 22,
        "support_gap": 16,
        "footer_gap": 18,
    }

    layout_payload = {
        "canvas": canvas,
        "safe_zones": {
            "outer_margin": safe_margins.get("outer_margin", 84),
            "inner_margin": safe_margins.get("inner_margin", 36),
            "content_top": 210,
            "content_bottom": 1170,
            "content_left": 96,
            "content_right": 984,
            "header_height": 136,
            "footer_height": 120,
        },
        "hierarchy_model": hierarchy_model,
        "whitespace_discipline": whitespace_discipline,
        "density_control": density_control,
        "contrast_rules": {
            "headline": "text_primary_on_panel",
            "hook": "accent_primary_on_panel",
            "body": "text_secondary_on_panel",
            "cta": "accent_primary_on_accent_soft",
        },
        "anti_template_cheap_rules": [
            "sem moldura fake de app",
            "sem sticker decorativo inútil",
            "sem excesso de bullets",
            "sem gradiente genérico como protagonista",
            "sem estética de template commodity",
        ],
        "display_payload": display_payload,
    }

    render_payload = {
        "renderer_mode": "html_card_renderer_v1",
        "render_ready": True,
        "export_mode": "html_only",
        "playwright_live_enabled": False,
        "worker_only_future": True,
        "template_id": template_spec["template_id"],
        "html_container_model": "premium_card_shell_v1",
    }

    gate_payload = {
        "minimum_scores": {
            "brand_dignity_score": 8.0,
            "contrast_score": 7.0,
            "composition_score": 7.0,
            "legibility_score": 7.0,
            "hierarchy_score": 7.0,
            "noise_control_score": 7.5,
        },
        "line_expectations": {
            "headline_lines": 3,
            "hook_lines": 2,
            "body_lines": 3,
            "cta_lines": 1,
            "support_points": 2,
        },
        "computed_line_estimates": {
            "headline_lines": _line_count(display_payload["headline"], 24),
            "hook_lines": _line_count(display_payload["hook"], 42),
            "body_lines": _line_count(display_payload["body"], 46),
            "cta_lines": _line_count(display_payload["cta"], 34),
        },
    }

    audit_payload = {
        "foundation_version": "visual_foundation_soberana_v1",
        "brand_system_version": "visual_brand_system_v2",
        "template_system_version": "visual_template_system_v2",
        "runtime_live_integration": False,
        "publish_flow_integration": False,
        "notes": [
            "sem deploy",
            "sem integração live",
            "renderer preparado apenas como fundação isolada",
        ],
    }

    contract = build_visual_engine_contract(
        input_plan=input_plan,
        brand_system=brand_system,
        template_spec=template_spec,
        typography_spec=typography_spec,
        layout_payload=layout_payload,
        render_payload=render_payload,
        gate_payload=gate_payload,
        audit_payload=audit_payload,
    )
    return contract


def visual_foundation_examples() -> dict[str, Any]:
    approved = build_visual_foundation_soberana_v1(
        {
            "topic_seed": "clareza, disciplina e direção",
            "headline": "Sem disciplina, clareza perde força antes de virar resultado.",
            "hook": "O problema raramente é falta de esforço. Quase sempre é mover muito sem critério suficiente.",
            "body": "Quando estrutura entra, a intenção para de depender do humor do dia e a execução passa a responder a leitura, prioridade e repetição.",
            "support_points": [
                "Clareza sem base vira intenção solta.",
                "Disciplina protege consistência quando o entusiasmo cai.",
            ],
            "cta": "Salve para revisar antes da próxima decisão.",
            "format_recommendation": "image",
            "series_name": "Liberta a Verdade",
        }
    )
    rejected = build_visual_foundation_soberana_v1(
        {
            "topic_seed": "motivação",
            "headline": "Acredite em você e tudo vai mudar hoje mesmo agora para sempre",
            "hook": "Descubra o segredo antes que seja tarde porque ninguém te conta isso",
            "body": "Sua vida pode mudar. Basta querer. Compartilhe com todo mundo.",
            "support_points": [
                "Mais foco.",
                "Mais resultado.",
                "Mais energia.",
            ],
            "cta": "Comente aqui agora",
            "format_recommendation": "image",
            "series_name": "Liberta a Verdade",
        }
    )
    return {"ok": True, "approved_payload": approved, "rejected_payload": rejected}
