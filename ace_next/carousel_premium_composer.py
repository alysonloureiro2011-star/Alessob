from __future__ import annotations

from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _split_support_points(items: list[str], chunk_size: int = 2) -> list[list[str]]:
    cleaned = [str(x or "").strip() for x in items if str(x or "").strip()]
    if not cleaned:
        return [[]]
    groups: list[list[str]] = []
    for index in range(0, len(cleaned), chunk_size):
        groups.append(cleaned[index:index + chunk_size])
    return groups


def _slide_payloads_from_plan(creative_plan: dict[str, Any]) -> list[dict[str, Any]]:
    plan = _safe_dict(creative_plan)
    headline = str(plan.get("headline") or "Sem estrutura, a mensagem perde força.")
    hook = str(plan.get("hook") or "Toda peça precisa de tensão clara antes do payoff.")
    body = str(plan.get("body") or "Uma ideia por slide. Menos ruído. Mais progressão.")
    cta = str(plan.get("cta") or "Salve para revisar antes da próxima decisão.")
    support_points = plan.get("support_points")
    if not isinstance(support_points, list):
        support_points = []

    support_groups = _split_support_points(support_points, chunk_size=2)

    slides: list[dict[str, Any]] = [
        {
            "index": 1,
            "role": "cover",
            "headline": headline,
            "hook": hook,
            "body": "",
            "cta": "",
            "support_points": [],
            "series_name": plan.get("series_name") or "Liberta a Verdade",
            "topic_seed": plan.get("topic_seed") or headline,
            "format_recommendation": "carousel",
        },
        {
            "index": 2,
            "role": "thesis",
            "headline": "A ideia central",
            "hook": "",
            "body": body,
            "cta": "",
            "support_points": [],
            "series_name": plan.get("series_name") or "Liberta a Verdade",
            "topic_seed": plan.get("topic_seed") or headline,
            "format_recommendation": "carousel",
        },
    ]

    for group in support_groups[:2]:
        slides.append(
            {
                "index": len(slides) + 1,
                "role": "support",
                "headline": "O que sustenta isso",
                "hook": "",
                "body": group[0] if group else body,
                "cta": "",
                "support_points": group[1:] if len(group) > 1 else [],
                "series_name": plan.get("series_name") or "Liberta a Verdade",
                "topic_seed": plan.get("topic_seed") or headline,
                "format_recommendation": "carousel",
            }
        )

    while len(slides) < 4:
        slides.append(
            {
                "index": len(slides) + 1,
                "role": "support",
                "headline": "A sustentação",
                "hook": "",
                "body": body,
                "cta": "",
                "support_points": [],
                "series_name": plan.get("series_name") or "Liberta a Verdade",
                "topic_seed": plan.get("topic_seed") or headline,
                "format_recommendation": "carousel",
            }
        )

    slides.append(
        {
            "index": len(slides) + 1,
            "role": "closing_cta",
            "headline": "Leve isso com você.",
            "hook": "",
            "body": "Menos volume. Mais direção. Mais critério visual.",
            "cta": cta,
            "support_points": [],
            "series_name": plan.get("series_name") or "Liberta a Verdade",
            "topic_seed": plan.get("topic_seed") or headline,
            "format_recommendation": "carousel",
        }
    )

    return slides


def _render_slide(
    *,
    slide_payload: dict[str, Any],
    visual_identity: dict[str, Any] | None = None,
    visual_contract: dict[str, Any] | None = None,
    capture_mode: str = "safe",
) -> dict[str, Any]:
    try:
        from .visual_payload_compactor import compact_visual_payload
        from .visual_premium_bridge import build_visual_premium_bridge

        compacted = compact_visual_payload(slide_payload, strategic_format="carousel")
        return build_visual_premium_bridge(
            creative_plan=compacted,
            visual_identity=visual_identity,
            visual_contract=visual_contract,
            strategic_format="carousel",
            capture_mode=capture_mode,
        )
    except Exception as exc:
        return {
            "ok": True,
            "engine": "visual_premium_bridge_fallback",
            "enabled": False,
            "strategic_format": "carousel",
            "template": {},
            "render": {},
            "hierarchy_gate": {},
            "brand_dignity_score": {},
            "approved_for_premium_visual": False,
            "selected_template_id": None,
            "premium_render_state": None,
            "reasons": [f"carousel_slide_bridge_error: {type(exc).__name__}: {exc}"],
        }


def _carousel_summary(render_outputs: list[dict[str, Any]]) -> tuple[bool, list[str], list[str]]:
    reasons: list[str] = []
    template_ids: list[str] = []
    approved = True

    for output in render_outputs:
        if not output.get("approved_for_premium_visual"):
            approved = False
        template_id = output.get("selected_template_id")
        if template_id:
            template_ids.append(str(template_id))
        for reason in output.get("reasons") or []:
            text = str(reason).strip()
            if text and text not in reasons:
                reasons.append(text)

    return approved, reasons, template_ids


def compose_premium_carousel(
    *,
    creative_plan: dict,
    visual_identity: dict | None = None,
    visual_contract: dict | None = None,
    capture_mode: str = "safe",
) -> dict:
    plan = _safe_dict(creative_plan)
    slides = _slide_payloads_from_plan(plan)
    render_outputs: list[dict[str, Any]] = []

    for slide in slides:
        render_outputs.append(
            _render_slide(
                slide_payload=slide,
                visual_identity=visual_identity,
                visual_contract=visual_contract,
                capture_mode=capture_mode,
            )
        )

    approved_for_staging, reasons, template_ids = _carousel_summary(render_outputs)

    return {
        "ok": True,
        "engine": "carousel_premium_composer_v1",
        "slides": slides,
        "template_ids": template_ids,
        "render_outputs": render_outputs,
        "strategic_format": "carousel",
        "approved_for_staging": approved_for_staging,
        "reasons": reasons,
    }
