from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .visual_templates_premium import resolve_premium_visual_template


@dataclass(frozen=True)
class TemplateBlock:
    name: str
    x: int
    y: int
    width: int
    height: int
    priority: int
    alignment: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VisualTemplate:
    template_id: str
    display_name: str
    use_case: str
    density: str
    block_order: list[str]
    blocks: dict[str, TemplateBlock]
    premium_tier: str
    render_engine_hint: str
    html_ready: bool
    mobile_first: bool
    style_hints: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "display_name": self.display_name,
            "use_case": self.use_case,
            "density": self.density,
            "block_order": list(self.block_order),
            "blocks": {name: block.to_dict() for name, block in self.blocks.items()},
            "premium_tier": self.premium_tier,
            "render_engine_hint": self.render_engine_hint,
            "html_ready": self.html_ready,
            "mobile_first": self.mobile_first,
            "style_hints": dict(self.style_hints),
        }


def _safe_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _infer_use_case(plan: dict[str, Any]) -> str | None:
    angle = _safe_text(plan.get("angle"))
    headline = _safe_text(plan.get("headline"))
    hook = _safe_text(plan.get("hook"))

    if any(word in " ".join([angle, headline, hook]) for word in ["erro", "contraste", "equívoco", "equivoco", "correção", "correcao"]):
        return "contrast"

    if len(str(plan.get("headline") or "")) >= 60 or "raramente" in hook:
        return "hero"

    return "insight"


def _infer_density(plan: dict[str, Any]) -> str | None:
    body_len = len(str(plan.get("body") or ""))
    support_count = len(plan.get("support_points") or [])
    if body_len < 120 and support_count <= 2:
        return "light"
    if body_len > 260 or support_count > 3:
        return "dense"
    return "balanced"


def _strategic_format(plan: dict[str, Any]) -> str | None:
    return _safe_text(plan.get("strategic_target_format") or plan.get("publish_format_now")) or None


def _fallback_template() -> dict[str, Any]:
    return {
        "ok": True,
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
    }


def resolve_visual_template(plan: dict[str, Any]) -> VisualTemplate:
    plan = dict(plan or {})
    try:
        resolved = resolve_premium_visual_template(
            use_case=_infer_use_case(plan),
            density=_infer_density(plan),
            strategic_format=_strategic_format(plan),
        )
    except Exception:
        resolved = _fallback_template()

    if not isinstance(resolved, dict) or not resolved.get("blocks"):
        resolved = _fallback_template()

    blocks: dict[str, TemplateBlock] = {}
    for name, block in dict(resolved.get("blocks") or {}).items():
        block = dict(block or {})
        blocks[name] = TemplateBlock(
            name=str(block.get("name") or name),
            x=int(block.get("x") or 0),
            y=int(block.get("y") or 0),
            width=int(block.get("width") or 0),
            height=int(block.get("height") or 0),
            priority=int(block.get("priority") or 0),
            alignment=str(block.get("alignment") or "left"),
        )

    return VisualTemplate(
        template_id=str(resolved.get("template_id") or "insight_card_v1"),
        display_name=str(resolved.get("display_name") or "Insight Card V1"),
        use_case=str(resolved.get("use_case") or "insight"),
        density=str(resolved.get("density") or "balanced"),
        block_order=list(resolved.get("block_order") or []),
        blocks=blocks,
        premium_tier=str(resolved.get("premium_tier") or "premium_core"),
        render_engine_hint=str(resolved.get("render_engine_hint") or "html_css_headless"),
        html_ready=bool(resolved.get("html_ready", True)),
        mobile_first=bool(resolved.get("mobile_first", True)),
        style_hints=dict(resolved.get("style_hints") or {}),
    )
