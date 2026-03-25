from __future__ import annotations

from typing import Any


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def _template_registry() -> dict[str, dict[str, Any]]:
    return {
        "hero_card_v1": {
            "template_id": "hero_card_v1",
            "display_name": "Hero Card V1",
            "use_case": "hero",
            "density": "medium",
            "premium_tier": "premium_core",
            "strategic_formats": ["image", "reel_cover"],
            "block_order": ["eyebrow", "headline", "hook", "body", "support_points", "cta"],
            "blocks": {
                "eyebrow": {"name": "eyebrow", "priority": 1, "x": 56, "y": 72, "width": 700, "height": 48, "alignment": "left"},
                "headline": {"name": "headline", "priority": 2, "x": 56, "y": 150, "width": 860, "height": 250, "alignment": "left"},
                "hook": {"name": "hook", "priority": 3, "x": 56, "y": 428, "width": 860, "height": 110, "alignment": "left"},
                "body": {"name": "body", "priority": 4, "x": 56, "y": 570, "width": 860, "height": 180, "alignment": "left"},
                "support_points": {"name": "support_points", "priority": 5, "x": 56, "y": 780, "width": 860, "height": 180, "alignment": "left"},
                "cta": {"name": "cta", "priority": 6, "x": 56, "y": 1230, "width": 860, "height": 70, "alignment": "left"},
            },
            "style_hints": {
                "panel_radius": 32,
                "headline_emphasis": "xl_bold",
                "hook_emphasis": "accent_medium",
                "cta_style": "pill_dark",
                "background_style": "premium_dark_gradient",
                "panel_style": "light_panel_floating",
                "watermark_style": "discreet_upper_right",
                "spacing_model": "hero_air",
            },
            "render_engine_hint": "html_css_headless",
            "html_ready": True,
            "mobile_first": True,
        },
        "insight_card_v1": {
            "template_id": "insight_card_v1",
            "display_name": "Insight Card V1",
            "use_case": "insight",
            "density": "balanced",
            "premium_tier": "premium_core",
            "strategic_formats": ["image"],
            "block_order": ["eyebrow", "hook", "headline", "body", "support_points", "cta"],
            "blocks": {
                "eyebrow": {"name": "eyebrow", "priority": 1, "x": 56, "y": 76, "width": 700, "height": 48, "alignment": "left"},
                "hook": {"name": "hook", "priority": 2, "x": 56, "y": 150, "width": 860, "height": 100, "alignment": "left"},
                "headline": {"name": "headline", "priority": 3, "x": 56, "y": 284, "width": 860, "height": 220, "alignment": "left"},
                "body": {"name": "body", "priority": 4, "x": 56, "y": 534, "width": 860, "height": 190, "alignment": "left"},
                "support_points": {"name": "support_points", "priority": 5, "x": 56, "y": 756, "width": 860, "height": 160, "alignment": "left"},
                "cta": {"name": "cta", "priority": 6, "x": 56, "y": 1222, "width": 860, "height": 68, "alignment": "left"},
            },
            "style_hints": {
                "panel_radius": 30,
                "headline_emphasis": "lg_bold",
                "hook_emphasis": "accent_short",
                "cta_style": "pill_light",
                "background_style": "deep_ink",
                "panel_style": "editorial_panel",
                "watermark_style": "discreet_bottom_right",
                "spacing_model": "balanced_editorial",
            },
            "render_engine_hint": "html_css_headless",
            "html_ready": True,
            "mobile_first": True,
        },
        "contrast_card_v1": {
            "template_id": "contrast_card_v1",
            "display_name": "Contrast Card V1",
            "use_case": "contrast",
            "density": "medium",
            "premium_tier": "premium_core",
            "strategic_formats": ["image", "carousel_cover"],
            "block_order": ["eyebrow", "headline", "body", "support_points", "hook", "cta"],
            "blocks": {
                "eyebrow": {"name": "eyebrow", "priority": 1, "x": 56, "y": 74, "width": 700, "height": 48, "alignment": "left"},
                "headline": {"name": "headline", "priority": 2, "x": 56, "y": 150, "width": 860, "height": 240, "alignment": "left"},
                "body": {"name": "body", "priority": 3, "x": 56, "y": 420, "width": 860, "height": 200, "alignment": "left"},
                "support_points": {"name": "support_points", "priority": 4, "x": 56, "y": 654, "width": 860, "height": 160, "alignment": "left"},
                "hook": {"name": "hook", "priority": 5, "x": 56, "y": 846, "width": 860, "height": 90, "alignment": "left"},
                "cta": {"name": "cta", "priority": 6, "x": 56, "y": 1224, "width": 860, "height": 68, "alignment": "left"},
            },
            "style_hints": {
                "panel_radius": 32,
                "headline_emphasis": "xl_impact",
                "hook_emphasis": "subdued_after_contrast",
                "cta_style": "underline_dark",
                "background_style": "split_contrast_dark",
                "panel_style": "hard_contrast_panel",
                "watermark_style": "discreet_upper_right",
                "spacing_model": "contrast_breathing",
            },
            "render_engine_hint": "html_css_headless",
            "html_ready": True,
            "mobile_first": True,
        },
        "carousel_editorial_v1": {
            "template_id": "carousel_editorial_v1",
            "display_name": "Carousel Editorial V1",
            "use_case": "carousel",
            "density": "balanced",
            "premium_tier": "premium_sequence",
            "strategic_formats": ["carousel"],
            "block_order": ["eyebrow", "headline", "body", "support_points", "cta"],
            "blocks": {
                "eyebrow": {"name": "eyebrow", "priority": 1, "x": 60, "y": 76, "width": 680, "height": 44, "alignment": "left"},
                "headline": {"name": "headline", "priority": 2, "x": 60, "y": 146, "width": 820, "height": 210, "alignment": "left"},
                "body": {"name": "body", "priority": 3, "x": 60, "y": 388, "width": 820, "height": 220, "alignment": "left"},
                "support_points": {"name": "support_points", "priority": 4, "x": 60, "y": 648, "width": 820, "height": 210, "alignment": "left"},
                "cta": {"name": "cta", "priority": 5, "x": 60, "y": 1218, "width": 820, "height": 64, "alignment": "left"},
            },
            "style_hints": {
                "panel_radius": 28,
                "headline_emphasis": "lg_sequence",
                "hook_emphasis": "none",
                "cta_style": "quiet_footer",
                "background_style": "editorial_dark_grid",
                "panel_style": "sequence_panel",
                "watermark_style": "discreet_bottom_right",
                "spacing_model": "sequence_reading",
            },
            "render_engine_hint": "html_css_headless",
            "html_ready": True,
            "mobile_first": True,
        },
        "story_editorial_v1": {
            "template_id": "story_editorial_v1",
            "display_name": "Story Editorial V1",
            "use_case": "story",
            "density": "light",
            "premium_tier": "premium_story",
            "strategic_formats": ["story"],
            "block_order": ["eyebrow", "headline", "hook", "cta"],
            "blocks": {
                "eyebrow": {"name": "eyebrow", "priority": 1, "x": 56, "y": 120, "width": 720, "height": 42, "alignment": "left"},
                "headline": {"name": "headline", "priority": 2, "x": 56, "y": 210, "width": 860, "height": 260, "alignment": "left"},
                "hook": {"name": "hook", "priority": 3, "x": 56, "y": 520, "width": 860, "height": 130, "alignment": "left"},
                "cta": {"name": "cta", "priority": 4, "x": 56, "y": 1700, "width": 860, "height": 84, "alignment": "left"},
            },
            "style_hints": {
                "panel_radius": 24,
                "headline_emphasis": "xl_story",
                "hook_emphasis": "accent_story",
                "cta_style": "story_pill",
                "background_style": "vertical_dark_soft",
                "panel_style": "minimal_story_panel",
                "watermark_style": "discreet_top_right",
                "spacing_model": "story_safe_zone",
            },
            "render_engine_hint": "html_css_headless",
            "html_ready": True,
            "mobile_first": True,
        },
    }


def _safe_template(template: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(template, dict):
        return {}
    return {
        "ok": True,
        "template_id": template.get("template_id"),
        "display_name": template.get("display_name"),
        "use_case": template.get("use_case"),
        "density": template.get("density"),
        "premium_tier": template.get("premium_tier"),
        "strategic_formats": list(template.get("strategic_formats") or []),
        "block_order": list(template.get("block_order") or []),
        "blocks": dict(template.get("blocks") or {}),
        "style_hints": dict(template.get("style_hints") or {}),
        "render_engine_hint": template.get("render_engine_hint", "html_css_headless"),
        "html_ready": bool(template.get("html_ready", True)),
        "mobile_first": bool(template.get("mobile_first", True)),
    }


def _match_template_by_use_case(use_case: str | None) -> str | None:
    normalized = _normalize(use_case)
    if normalized == "contrast":
        return "contrast_card_v1"
    if normalized == "hero":
        return "hero_card_v1"
    if normalized == "carousel":
        return "carousel_editorial_v1"
    if normalized == "story":
        return "story_editorial_v1"
    return None


def _match_template_by_format(strategic_format: str | None) -> str | None:
    normalized = _normalize(strategic_format)
    if normalized == "carousel":
        return "carousel_editorial_v1"
    if normalized == "story":
        return "story_editorial_v1"
    if normalized in {"image", "reel_cover"}:
        return None
    return None


def _choose_default_template(
    *,
    use_case: str | None = None,
    density: str | None = None,
    strategic_format: str | None = None,
) -> str:
    by_format = _match_template_by_format(strategic_format)
    if by_format:
        return by_format

    by_use_case = _match_template_by_use_case(use_case)
    if by_use_case:
        return by_use_case

    if _normalize(density) == "light":
        return "insight_card_v1"

    return "insight_card_v1"


def resolve_premium_visual_template(
    *,
    template_id: str | None = None,
    use_case: str | None = None,
    density: str | None = None,
    strategic_format: str | None = None,
) -> dict:
    registry = _template_registry()

    normalized_template_id = _normalize(template_id)
    if normalized_template_id and normalized_template_id in registry:
        return _safe_template(registry[normalized_template_id])

    chosen = _choose_default_template(
        use_case=use_case,
        density=density,
        strategic_format=strategic_format,
    )

    return _safe_template(registry[chosen])


def premium_visual_templates_catalog() -> dict:
    registry = _template_registry()
    return {
        "ok": True,
        "count": len(registry),
        "templates": {key: _safe_template(value) for key, value in registry.items()},
    }


def premium_visual_template_examples() -> dict:
    return {
        "ok": True,
        "hero": resolve_premium_visual_template(template_id="hero_card_v1"),
        "contrast": resolve_premium_visual_template(use_case="contrast"),
        "carousel": resolve_premium_visual_template(strategic_format="carousel"),
        "story": resolve_premium_visual_template(strategic_format="story"),
        "default": resolve_premium_visual_template(),
    }
