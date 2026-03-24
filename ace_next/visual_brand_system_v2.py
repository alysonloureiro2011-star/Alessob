from __future__ import annotations

from typing import Any


def get_visual_brand_system_v2(theme_id: str = "midnight_authority_v2") -> dict[str, Any]:
    themes: dict[str, dict[str, Any]] = {
        "midnight_authority_v2": {
            "theme_id": "midnight_authority_v2",
            "palette": {
                "background": "#08111F",
                "surface": "#0E1728",
                "surface_soft": "#121F36",
                "panel": "#F7FAFF",
                "panel_border": "#D8E1F0",
                "text_primary": "#141A24",
                "text_secondary": "#5E6B82",
                "text_on_dark": "#F8FBFF",
                "accent_primary": "#2D6DFF",
                "accent_soft": "#DDE8FF",
                "accent_secondary": "#7AA2FF",
                "watermark": "#9CB2D9",
                "danger": "#D94E4E",
            },
            "panel_system": {
                "panel_radius": 34,
                "panel_border_width": 2,
                "shadow_style": "soft_elevated",
                "panel_padding_x": 48,
                "panel_padding_y": 42,
            },
            "typography_hierarchy": {
                "eyebrow": {"size": 22, "weight": 700, "tracking": 0.06},
                "headline": {"size": 72, "weight": 800, "tracking": -0.03},
                "hook": {"size": 28, "weight": 600, "tracking": -0.01},
                "body": {"size": 30, "weight": 500, "tracking": 0.0},
                "support": {"size": 24, "weight": 700, "tracking": 0.0},
                "cta": {"size": 26, "weight": 700, "tracking": -0.01},
                "watermark": {"size": 20, "weight": 700, "tracking": 0.02},
            },
            "watermark_discipline": {
                "enabled": True,
                "opacity_mode": "low_visibility",
                "position": "bottom_right",
                "must_never_dominate": True,
            },
            "text_contrast_policy": {
                "headline_on_panel": "strong",
                "hook_on_panel": "accent_led",
                "body_on_panel": "secondary_high_legibility",
                "cta_on_accent_soft": "accent_dominant",
            },
            "brand_dignity_constraints": {
                "anti_generic_identity_rules": [
                    "não usar gradiente genérico como centro estético",
                    "não usar moldura barata tipo template de app",
                    "não usar excesso de elementos decorativos",
                ],
                "anti_cheap_template": True,
                "anti_clutter": True,
                "anti_visual_noise": True,
                "minimum_premium_feel": 8.0,
            },
        },
        "graphite_editorial_v2": {
            "theme_id": "graphite_editorial_v2",
            "palette": {
                "background": "#101114",
                "surface": "#171A20",
                "surface_soft": "#20242C",
                "panel": "#FCFCFD",
                "panel_border": "#E0E3EA",
                "text_primary": "#14161B",
                "text_secondary": "#666E7D",
                "text_on_dark": "#FBFCFE",
                "accent_primary": "#6C7CFF",
                "accent_soft": "#E5E9FF",
                "accent_secondary": "#A3AEFF",
                "watermark": "#AEB7C9",
                "danger": "#D94E4E",
            },
            "panel_system": {
                "panel_radius": 30,
                "panel_border_width": 2,
                "shadow_style": "editorial_soft",
                "panel_padding_x": 46,
                "panel_padding_y": 40,
            },
            "typography_hierarchy": {
                "eyebrow": {"size": 22, "weight": 700, "tracking": 0.06},
                "headline": {"size": 70, "weight": 800, "tracking": -0.03},
                "hook": {"size": 28, "weight": 600, "tracking": -0.01},
                "body": {"size": 30, "weight": 500, "tracking": 0.0},
                "support": {"size": 24, "weight": 700, "tracking": 0.0},
                "cta": {"size": 26, "weight": 700, "tracking": -0.01},
                "watermark": {"size": 20, "weight": 700, "tracking": 0.02},
            },
            "watermark_discipline": {
                "enabled": True,
                "opacity_mode": "low_visibility",
                "position": "bottom_right",
                "must_never_dominate": True,
            },
            "text_contrast_policy": {
                "headline_on_panel": "strong",
                "hook_on_panel": "accent_led",
                "body_on_panel": "secondary_high_legibility",
                "cta_on_accent_soft": "accent_dominant",
            },
            "brand_dignity_constraints": {
                "anti_generic_identity_rules": [
                    "não parecer template de marketing barato",
                    "não usar ornamento sem função",
                    "não parecer slide improvisado",
                ],
                "anti_cheap_template": True,
                "anti_clutter": True,
                "anti_visual_noise": True,
                "minimum_premium_feel": 8.0,
            },
        },
    }
    return dict(themes.get(theme_id, themes["midnight_authority_v2"]))


def build_visual_brand_typography_spec(brand_system: dict[str, Any]) -> dict[str, Any]:
    hierarchy = dict(brand_system.get("typography_hierarchy") or {})
    return {
        "eyebrow_size": hierarchy.get("eyebrow", {}).get("size", 22),
        "headline_size": hierarchy.get("headline", {}).get("size", 72),
        "hook_size": hierarchy.get("hook", {}).get("size", 28),
        "body_size": hierarchy.get("body", {}).get("size", 30),
        "support_size": hierarchy.get("support", {}).get("size", 24),
        "cta_size": hierarchy.get("cta", {}).get("size", 26),
        "watermark_size": hierarchy.get("watermark", {}).get("size", 20),
        "headline_max_lines": 3,
        "hook_max_lines": 2,
        "body_max_lines": 3,
        "support_max_lines": 2,
        "cta_max_lines": 1,
    }


def visual_brand_system_examples() -> dict[str, Any]:
    base = get_visual_brand_system_v2()
    alt = get_visual_brand_system_v2("graphite_editorial_v2")
    return {"ok": True, "default_theme": base, "alternate_theme": alt}
