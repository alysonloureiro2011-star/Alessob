from __future__ import annotations

import os
from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _normalize_format(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"carousel", "story", "stories", "image", "reel_cover"}:
        if normalized == "stories":
            return "story"
        return normalized
    return "image"


def _default_visual_identity(identity: dict[str, Any] | None = None) -> dict[str, Any]:
    identity = _safe_dict(identity)
    return {
        "bg": identity.get("bg", "#0b1020"),
        "surface": identity.get("surface", "#111827"),
        "panel": identity.get("panel", "#f8fafc"),
        "panel_border": identity.get("panel_border", "rgba(255,255,255,0.12)"),
        "text_primary": identity.get("text_primary", "#0f172a"),
        "text_secondary": identity.get("text_secondary", "#334155"),
        "text_on_dark": identity.get("text_on_dark", "#f8fafc"),
        "accent": identity.get("accent", "#3b82f6"),
        "accent_soft": identity.get("accent_soft", "rgba(59,130,246,0.16)"),
        "watermark": identity.get("watermark", "rgba(255,255,255,0.28)"),
        "shadow": identity.get("shadow", "0 18px 60px rgba(0,0,0,0.34)"),
    }


def _default_visual_contract(
    visual_contract: dict[str, Any] | None = None,
    strategic_format: str = "image",
) -> dict[str, Any]:
    visual_contract = _safe_dict(visual_contract)
    strategic_format = _normalize_format(strategic_format)

    if strategic_format == "story":
        return {
            "aspect_ratio": visual_contract.get("aspect_ratio", "9:16"),
            "mobile_first": bool(visual_contract.get("mobile_first", True)),
            "safe_zone_top": int(visual_contract.get("safe_zone_top", 140)),
            "safe_zone_bottom": int(visual_contract.get("safe_zone_bottom", 220)),
            "headline_chars_budget": int(visual_contract.get("headline_chars_budget", 62)),
            "body_chars_budget": int(visual_contract.get("body_chars_budget", 120)),
            "cta_chars_budget": int(visual_contract.get("cta_chars_budget", 42)),
            "headline_max_lines": int(visual_contract.get("headline_max_lines", 3)),
            "hook_max_lines": int(visual_contract.get("hook_max_lines", 2)),
            "body_max_lines": int(visual_contract.get("body_max_lines", 3)),
            "cta_max_lines": int(visual_contract.get("cta_max_lines", 2)),
        }

    if strategic_format == "carousel":
        return {
            "aspect_ratio": visual_contract.get("aspect_ratio", "4:5"),
            "mobile_first": bool(visual_contract.get("mobile_first", True)),
            "safe_zone_top": int(visual_contract.get("safe_zone_top", 56)),
            "safe_zone_bottom": int(visual_contract.get("safe_zone_bottom", 56)),
            "headline_chars_budget": int(visual_contract.get("headline_chars_budget", 70)),
            "body_chars_budget": int(visual_contract.get("body_chars_budget", 180)),
            "cta_chars_budget": int(visual_contract.get("cta_chars_budget", 56)),
            "headline_max_lines": int(visual_contract.get("headline_max_lines", 3)),
            "hook_max_lines": int(visual_contract.get("hook_max_lines", 2)),
            "body_max_lines": int(visual_contract.get("body_max_lines", 3)),
            "cta_max_lines": int(visual_contract.get("cta_max_lines", 2)),
        }

    return {
        "aspect_ratio": visual_contract.get("aspect_ratio", "4:5"),
        "mobile_first": bool(visual_contract.get("mobile_first", True)),
        "safe_zone_top": int(visual_contract.get("safe_zone_top", 56)),
        "safe_zone_bottom": int(visual_contract.get("safe_zone_bottom", 56)),
        "headline_chars_budget": int(visual_contract.get("headline_chars_budget", 84)),
        "body_chars_budget": int(visual_contract.get("body_chars_budget", 280)),
        "cta_chars_budget": int(visual_contract.get("cta_chars_budget", 72)),
        "headline_max_lines": int(visual_contract.get("headline_max_lines", 3)),
        "hook_max_lines": int(visual_contract.get("hook_max_lines", 2)),
        "body_max_lines": int(visual_contract.get("body_max_lines", 4)),
        "cta_max_lines": int(visual_contract.get("cta_max_lines", 2)),
    }


def _merge_reasons(*items: Any) -> list[str]:
    merged: list[str] = []
    for item in items:
        values = item if isinstance(item, list) else [item]
        for value in values:
            text = str(value or "").strip()
            if text and text not in merged:
                merged.append(text)
    return merged


def _disabled_bundle(strategic_format: str) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": "visual_premium_bridge_v1",
        "enabled": False,
        "strategic_format": strategic_format,
        "template": {},
        "render": {},
        "hierarchy_gate": {},
        "brand_dignity_score": {},
        "approved_for_premium_visual": False,
        "selected_template_id": None,
        "premium_render_state": None,
        "reasons": ["premium_visual_bridge_disabled"],
    }


def _failure_bundle(strategic_format: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "ok": True,
        "engine": "visual_premium_bridge_v1",
        "enabled": True,
        "strategic_format": strategic_format,
        "template": {},
        "render": {},
        "hierarchy_gate": {},
        "brand_dignity_score": {},
        "approved_for_premium_visual": False,
        "selected_template_id": None,
        "premium_render_state": None,
        "reasons": _merge_reasons(reasons),
    }


def _enabled() -> bool:
    raw = os.environ.get("ACE_ENABLE_PREMIUM_VISUAL_BRIDGE", "0")
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _line_estimate(text: Any, chars_per_line: int) -> int:
    text = " ".join(str(text or "").strip().split())
    if not text:
        return 0
    return max(1, (len(text) + chars_per_line - 1) // chars_per_line)


def _infer_use_case(plan: dict[str, Any]) -> str | None:
    joined = " ".join(
        [
            str(plan.get("angle") or ""),
            str(plan.get("headline") or ""),
            str(plan.get("hook") or ""),
        ]
    ).lower()

    if any(token in joined for token in ["erro", "equívoco", "equivoco", "contraste", "correção", "correcao"]):
        return "contrast"
    if len(str(plan.get("headline") or "")) >= 60:
        return "hero"
    return "insight"


def _infer_density(plan: dict[str, Any]) -> str | None:
    body_len = len(str(plan.get("body") or ""))
    support_points = plan.get("support_points")
    support_count = len(support_points) if isinstance(support_points, list) else 0
    if body_len <= 120 and support_count <= 2:
        return "light"
    if body_len >= 240 or support_count >= 4:
        return "dense"
    return "balanced"


def _hierarchy_contract(
    *,
    render_payload: dict[str, Any],
    template_meta: dict[str, Any],
) -> dict[str, Any]:
    headline = str(render_payload.get("headline") or "")
    hook = str(render_payload.get("hook") or "")
    body = str(render_payload.get("body") or "")
    cta = str(render_payload.get("cta") or "")
    support_points = render_payload.get("support_points")
    if not isinstance(support_points, list):
        support_points = []

    return {
        "brand_system": {
            "text_contrast_policy": "premium_high_contrast",
            "brand_dignity_constraints": {
                "anti_generic_identity_rules": [
                    "evitar template barato",
                    "evitar copy commodity",
                    "evitar excesso visual",
                ]
            },
        },
        "template_spec": template_meta,
        "layout_payload": {
            "display_payload": {
                "headline": headline,
                "hook": hook,
                "body": body,
                "cta": cta,
                "support_points": support_points,
            }
        },
        "gate_payload": {
            "computed_line_estimates": {
                "headline_lines": _line_estimate(headline, 28),
                "hook_lines": _line_estimate(hook, 36),
                "body_lines": _line_estimate(body, 46),
                "cta_lines": _line_estimate(cta, 34),
            },
            "line_expectations": {
                "headline_lines": 3,
                "hook_lines": 2,
                "body_lines": 4,
                "cta_lines": 2,
            },
            "minimum_scores": {
                "brand_dignity_score": 7.8,
                "contrast_score": 7.0,
                "composition_score": 7.4,
                "legibility_score": 7.5,
                "hierarchy_score": 7.5,
                "noise_control_score": 7.2,
            },
        },
    }


def build_visual_premium_bridge(
    *,
    creative_plan: dict,
    visual_identity: dict | None = None,
    visual_contract: dict | None = None,
    strategic_format: str | None = None,
    template_id: str | None = None,
    capture_mode: str = "safe",
) -> dict:
    plan = _safe_dict(creative_plan)
    strategic_format = _normalize_format(
        strategic_format
        or plan.get("strategic_target_format")
        or plan.get("publish_format_now")
        or plan.get("format_recommendation")
    )

    if not _enabled():
        return _disabled_bundle(strategic_format)

    try:
        from .brand_dignity_score import evaluate_brand_dignity_score
        from .render_visual_premium import render_visual_premium
        from .visual_hierarchy_gate import evaluate_visual_hierarchy_gate
        from .visual_templates_premium import resolve_premium_visual_template
    except Exception as exc:
        return _failure_bundle(
            strategic_format,
            [f"premium_visual_bridge_import_error: {type(exc).__name__}: {exc}"],
        )

    try:
        identity = _default_visual_identity(visual_identity)
        contract = _default_visual_contract(visual_contract, strategic_format)
        template = resolve_premium_visual_template(
            template_id=template_id,
            use_case=_infer_use_case(plan),
            density=_infer_density(plan),
            strategic_format=strategic_format,
        )

        selected_template_id = template.get("template_id")
        render = render_visual_premium(
            creative_plan=plan,
            visual_identity=identity,
            visual_contract=contract,
            template_id=selected_template_id,
            capture_mode=capture_mode,
        )

        render_payload = _safe_dict(render.get("payload"))
        hierarchy_gate = evaluate_visual_hierarchy_gate(
            _hierarchy_contract(
                render_payload=render_payload or plan,
                template_meta=template,
            )
        )

        brand_dignity_score = evaluate_brand_dignity_score(
            creative_plan=plan,
            visual_qa={"final_score": hierarchy_gate.get("final_score")},
            hierarchy_gate=hierarchy_gate,
            template_meta=template,
        )

        approved = (
            bool(render.get("ok"))
            and bool(hierarchy_gate.get("approved"))
            and bool(brand_dignity_score.get("approved"))
            and brand_dignity_score.get("classification") != "brand_indignity"
        )

        reasons = _merge_reasons(
            render.get("reasons") or [],
            hierarchy_gate.get("rejection_reasons") or [],
            brand_dignity_score.get("reasons") or [],
        )

        if not approved and not reasons:
            reasons = ["premium_visual_bridge_not_approved"]

        return {
            "ok": True,
            "engine": "visual_premium_bridge_v1",
            "enabled": True,
            "strategic_format": strategic_format,
            "template": template,
            "render": render,
            "hierarchy_gate": hierarchy_gate,
            "brand_dignity_score": brand_dignity_score,
            "approved_for_premium_visual": approved,
            "selected_template_id": selected_template_id,
            "premium_render_state": render.get("render_state"),
            "reasons": reasons,
        }
    except Exception as exc:
        return _failure_bundle(
            strategic_format,
            [f"premium_visual_bridge_runtime_error: {type(exc).__name__}: {exc}"],
        )
