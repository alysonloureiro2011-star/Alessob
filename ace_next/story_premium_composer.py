from __future__ import annotations

from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _story_safe_zone_contract(visual_contract: dict[str, Any] | None = None) -> dict[str, Any]:
    visual_contract = _safe_dict(visual_contract)
    return {
        "aspect_ratio": visual_contract.get("aspect_ratio", "9:16"),
        "mobile_first": bool(visual_contract.get("mobile_first", True)),
        "safe_zone_top": int(visual_contract.get("safe_zone_top", 140)),
        "safe_zone_bottom": int(visual_contract.get("safe_zone_bottom", 220)),
        "headline_chars_budget": int(visual_contract.get("headline_chars_budget", 62)),
        "hook_chars_budget": int(visual_contract.get("hook_chars_budget", 90)),
        "body_chars_budget": int(visual_contract.get("body_chars_budget", 120)),
        "cta_chars_budget": int(visual_contract.get("cta_chars_budget", 42)),
        "headline_max_lines": int(visual_contract.get("headline_max_lines", 3)),
        "hook_max_lines": int(visual_contract.get("hook_max_lines", 2)),
        "body_max_lines": int(visual_contract.get("body_max_lines", 3)),
        "cta_max_lines": int(visual_contract.get("cta_max_lines", 2)),
        "support_points_max": int(visual_contract.get("support_points_max", 1)),
    }


def _story_payloads_from_plan(creative_plan: dict[str, Any]) -> list[dict[str, Any]]:
    plan = _safe_dict(creative_plan)
    headline = str(plan.get("headline") or "Sem direção, a clareza não vira ação.")
    hook = str(plan.get("hook") or "Toda mensagem forte precisa de uma abertura limpa.")
    body = str(plan.get("body") or "Stories pedem ritmo, pouco texto e progressão clara.")
    cta = str(plan.get("cta") or "Continue essa sequência no próximo story.")
    support_points = plan.get("support_points")
    if not isinstance(support_points, list):
        support_points = []
    support_points = [str(x or "").strip() for x in support_points if str(x or "").strip()]

    return [
        {
            "index": 1,
            "role": "hook_frame",
            "headline": headline,
            "hook": hook,
            "body": "",
            "cta": "",
            "support_points": [],
            "series_name": plan.get("series_name") or "Liberta a Verdade",
            "topic_seed": plan.get("topic_seed") or headline,
            "format_recommendation": "story",
        },
        {
            "index": 2,
            "role": "thesis_frame",
            "headline": "A tese",
            "hook": "",
            "body": body,
            "cta": "",
            "support_points": [],
            "series_name": plan.get("series_name") or "Liberta a Verdade",
            "topic_seed": plan.get("topic_seed") or headline,
            "format_recommendation": "story",
        },
        {
            "index": 3,
            "role": "support_frame",
            "headline": "O suporte",
            "hook": "",
            "body": support_points[0] if support_points else body,
            "cta": "",
            "support_points": support_points[1:2],
            "series_name": plan.get("series_name") or "Liberta a Verdade",
            "topic_seed": plan.get("topic_seed") or headline,
            "format_recommendation": "story",
        },
        {
            "index": 4,
            "role": "cta_frame",
            "headline": "Continua.",
            "hook": "",
            "body": "A sequência só faz sentido quando cada frame carrega uma ideia central.",
            "cta": cta,
            "support_points": [],
            "series_name": plan.get("series_name") or "Liberta a Verdade",
            "topic_seed": plan.get("topic_seed") or headline,
            "format_recommendation": "story",
        },
    ]


def _render_frame(
    *,
    frame_payload: dict[str, Any],
    visual_identity: dict[str, Any] | None = None,
    visual_contract: dict[str, Any] | None = None,
    capture_mode: str = "safe",
) -> dict[str, Any]:
    try:
        from .visual_payload_compactor import compact_visual_payload
        from .visual_premium_bridge import build_visual_premium_bridge

        compacted = compact_visual_payload(frame_payload, strategic_format="story")
        return build_visual_premium_bridge(
            creative_plan=compacted,
            visual_identity=visual_identity,
            visual_contract=visual_contract,
            strategic_format="story",
            capture_mode=capture_mode,
        )
    except Exception as exc:
        return {
            "ok": True,
            "engine": "visual_premium_bridge_fallback",
            "enabled": False,
            "strategic_format": "story",
            "template": {},
            "render": {},
            "hierarchy_gate": {},
            "brand_dignity_score": {},
            "approved_for_premium_visual": False,
            "selected_template_id": None,
            "premium_render_state": None,
            "reasons": [f"story_frame_bridge_error: {type(exc).__name__}: {exc}"],
        }


def _validate_story_density(frames: list[dict[str, Any]]) -> dict[str, Any]:
    checks = {
        "frame_count_ok": len(frames) >= 4,
        "headline_budget_ok": True,
        "body_budget_ok": True,
        "cta_budget_ok": True,
        "support_budget_ok": True,
    }

    for frame in frames:
        if len(str(frame.get("headline") or "")) > 62:
            checks["headline_budget_ok"] = False
        if len(str(frame.get("body") or "")) > 120:
            checks["body_budget_ok"] = False
        if len(str(frame.get("cta") or "")) > 42:
            checks["cta_budget_ok"] = False
        if len(frame.get("support_points") or []) > 1:
            checks["support_budget_ok"] = False

    checks["approved"] = all(checks.values())
    return checks


def compose_premium_stories(
    *,
    creative_plan: dict,
    visual_identity: dict | None = None,
    visual_contract: dict | None = None,
    capture_mode: str = "safe",
) -> dict:
    plan = _safe_dict(creative_plan)
    story_contract = _story_safe_zone_contract(visual_contract)
    frames = _story_payloads_from_plan(plan)
    safe_zone_checks = _validate_story_density(frames)

    render_outputs: list[dict[str, Any]] = []
    template_ids: list[str] = []
    reasons: list[str] = []

    for frame in frames:
        output = _render_frame(
            frame_payload=frame,
            visual_identity=visual_identity,
            visual_contract=story_contract,
            capture_mode=capture_mode,
        )
        render_outputs.append(output)

        template_id = output.get("selected_template_id")
        if template_id:
            template_ids.append(str(template_id))

        for reason in output.get("reasons") or []:
            text = str(reason).strip()
            if text and text not in reasons:
                reasons.append(text)

    approved_for_staging = safe_zone_checks.get("approved", False) and all(
        bool(output.get("approved_for_premium_visual")) for output in render_outputs
    )

    return {
        "ok": True,
        "engine": "story_premium_composer_v1",
        "frames": frames,
        "template_ids": template_ids,
        "render_outputs": render_outputs,
        "strategic_format": "story",
        "safe_zone_checks": safe_zone_checks,
        "approved_for_staging": approved_for_staging,
        "reasons": reasons,
    }
