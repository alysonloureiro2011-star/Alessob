from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class VisualEngineContract:
    input_plan: dict[str, Any]
    brand_system: dict[str, Any]
    template_spec: dict[str, Any]
    typography_spec: dict[str, Any]
    layout_payload: dict[str, Any]
    render_payload: dict[str, Any]
    gate_payload: dict[str, Any]
    audit_payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_visual_engine_contract(
    *,
    input_plan: dict[str, Any],
    brand_system: dict[str, Any],
    template_spec: dict[str, Any],
    typography_spec: dict[str, Any],
    layout_payload: dict[str, Any],
    render_payload: dict[str, Any],
    gate_payload: dict[str, Any],
    audit_payload: dict[str, Any],
) -> dict[str, Any]:
    contract = VisualEngineContract(
        input_plan=dict(input_plan or {}),
        brand_system=dict(brand_system or {}),
        template_spec=dict(template_spec or {}),
        typography_spec=dict(typography_spec or {}),
        layout_payload=dict(layout_payload or {}),
        render_payload=dict(render_payload or {}),
        gate_payload=dict(gate_payload or {}),
        audit_payload=dict(audit_payload or {}),
    )
    return contract.to_dict()


def visual_engine_contract_examples() -> dict[str, Any]:
    approved_contract = build_visual_engine_contract(
        input_plan={
            "topic_seed": "clareza, disciplina e direção",
            "headline": "Sem disciplina, clareza perde força antes de virar resultado.",
            "hook": "O problema raramente é falta de esforço. Quase sempre é mover muito sem critério suficiente.",
            "body": "Quando estrutura entra, intenção para de depender do humor do dia.",
            "cta": "Salve para revisar antes da próxima decisão.",
            "format_recommendation": "image",
        },
        brand_system={
            "theme_id": "midnight_authority_v2",
            "brand_dignity_constraints": {
                "anti_cheap_template": True,
                "anti_clutter": True,
                "anti_visual_noise": True,
            },
        },
        template_spec={
            "template_id": "signal_card_premium_v1",
            "block_order": ["eyebrow", "headline", "hook", "body", "support", "cta"],
        },
        typography_spec={
            "headline_size": 72,
            "headline_max_lines": 3,
            "hook_size": 28,
            "hook_max_lines": 2,
            "body_size": 30,
            "body_max_lines": 3,
            "cta_size": 26,
            "cta_max_lines": 1,
        },
        layout_payload={
            "canvas": {"width": 1080, "height": 1350, "aspect_ratio": "4:5"},
            "safe_zones": {"outer_margin": 84, "content_top": 210, "content_bottom": 1170},
            "density_mode": "mobile_clean",
            "whitespace_discipline": "high",
        },
        render_payload={
            "renderer_mode": "html_card_renderer_v1",
            "render_ready": True,
            "playwright_live_enabled": False,
            "export_mode": "html_only",
        },
        gate_payload={
            "minimum_scores": {
                "brand_dignity_score": 8.0,
                "contrast_score": 7.0,
                "composition_score": 7.0,
                "legibility_score": 7.0,
                "hierarchy_score": 7.0,
                "noise_control_score": 7.5,
            },
        },
        audit_payload={
            "foundation_version": "visual_foundation_soberana_v1",
            "template_system_version": "visual_template_system_v2",
            "runtime_live_integration": False,
            "notes": ["sem deploy", "sem integração no runtime principal"],
        },
    )

    rejected_contract = build_visual_engine_contract(
        input_plan={
            "topic_seed": "motivação",
            "headline": "Acredite em você e tudo vai mudar hoje mesmo agora",
            "hook": "Descubra o segredo antes que seja tarde",
            "body": "Sua vida pode mudar.",
            "cta": "Comente aqui",
            "format_recommendation": "image",
        },
        brand_system={"theme_id": "cheap_template"},
        template_spec={"template_id": "crowded_template"},
        typography_spec={"headline_size": 48, "headline_max_lines": 5},
        layout_payload={"density_mode": "crowded"},
        render_payload={"renderer_mode": "html_card_renderer_v1", "render_ready": False},
        gate_payload={},
        audit_payload={"runtime_live_integration": False},
    )

    return {
        "ok": True,
        "approved_example": approved_contract,
        "rejected_example": rejected_contract,
    }
