from __future__ import annotations

import os
import textwrap
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from .config import AceNextConfig
from .perceptual_qa import evaluate_perceptual_quality
from .visual_contract import build_visual_contract, prepare_display_copy
from .visual_templates import VisualTemplate, resolve_visual_template

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = None
    ImageDraw = None
    ImageFont = None


PALETTES = {
    "electric_blue": {
        "background": (9, 15, 28),
        "header_band": (13, 23, 42),
        "panel": (248, 250, 255),
        "panel_border": (220, 229, 245),
        "accent": (39, 103, 255),
        "accent_soft": (226, 235, 255),
        "text_primary": (18, 20, 28),
        "text_secondary": (78, 87, 106),
        "text_on_dark": (255, 255, 255),
        "watermark": (177, 192, 226),
    },
    "amber_gold": {
        "background": (26, 20, 12),
        "header_band": (38, 28, 14),
        "panel": (255, 249, 242),
        "panel_border": (241, 225, 197),
        "accent": (212, 142, 34),
        "accent_soft": (248, 234, 202),
        "text_primary": (29, 22, 16),
        "text_secondary": (99, 85, 67),
        "text_on_dark": (255, 255, 255),
        "watermark": (230, 210, 176),
    },
    "editorial_violet": {
        "background": (21, 18, 31),
        "header_band": (31, 25, 45),
        "panel": (248, 246, 255),
        "panel_border": (228, 220, 245),
        "accent": (136, 81, 255),
        "accent_soft": (232, 223, 255),
        "text_primary": (23, 18, 31),
        "text_secondary": (94, 90, 112),
        "text_on_dark": (255, 255, 255),
        "watermark": (203, 193, 236),
    },
}


@dataclass
class VisualIdentity:
    palette_name: str
    series_name: str
    watermark_text: str
    background_color: tuple[int, int, int]
    header_band_color: tuple[int, int, int]
    panel_color: tuple[int, int, int]
    panel_border_color: tuple[int, int, int]
    accent_color: tuple[int, int, int]
    accent_soft_color: tuple[int, int, int]
    text_primary: tuple[int, int, int]
    text_secondary: tuple[int, int, int]
    text_on_dark: tuple[int, int, int]
    watermark_color: tuple[int, int, int]
    safe_margin: int
    panel_radius: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TypographySpec:
    headline_size: int
    hook_size: int
    body_size: int
    support_size: int
    brand_size: int
    cta_size: int
    eyebrow_size: int
    headline_wrap: int
    hook_wrap: int
    body_wrap: int
    support_wrap: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VisualQAResult:
    approved: bool
    final_score: int
    minimum_score: int
    reasons: list[str]
    recommendations: list[str]
    metrics: dict[str, Any]
    breakdown: dict[str, float]
    perceptual_qa: dict[str, Any]
    contract: dict[str, Any]
    template: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CarouselSlide:
    index: int
    role: str
    headline: str
    body: str
    cta: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StoryFrame:
    index: int
    role: str
    text: str
    hint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _bridge_enabled() -> bool:
    raw = os.environ.get("ACE_ENABLE_PREMIUM_VISUAL_BRIDGE", "0")
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _wrap(text: str, width: int) -> list[str]:
    lines = textwrap.wrap((text or "").strip(), width=width, break_long_words=False, break_on_hyphens=False)
    return lines or [""]


def _fit_lines(text: str, width: int, max_lines: int) -> list[str]:
    lines = _wrap(text, width)
    if len(lines) <= max_lines:
        return lines
    clipped = lines[:max_lines]
    last = clipped[-1].rstrip()
    if len(last) > 3:
        last = last[:-3].rstrip()
    clipped[-1] = f"{last}..."
    return clipped


def _load_font(size: int, *, bold: bool = False):
    if ImageFont is None:
        return None
    candidates = [
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def _draw_lines(draw, lines: list[str], *, x: int, y: int, font, fill, line_gap: int = 12) -> int:
    line_height = getattr(font, "size", 24) + line_gap if font else 30
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, fill=fill, font=font)
        current_y += line_height
    return current_y


def _draw_support_chip(draw, *, x: int, y: int, text: str, font, identity: VisualIdentity, width: int) -> int:
    if not text:
        return 0
    lines = _fit_lines(text, 30, 2)
    line_height = getattr(font, "size", 22) + 6 if font else 28
    chip_height = 20 + (len(lines) * line_height)
    draw.rounded_rectangle(
        (x, y, x + width, y + chip_height),
        radius=18,
        fill=identity.accent_soft_color,
        outline=identity.panel_border_color,
        width=2,
    )
    bullet_x = x + 18
    bullet_y = y + 18
    draw.ellipse((bullet_x, bullet_y, bullet_x + 12, bullet_y + 12), fill=identity.accent_color)
    text_x = x + 42
    current_y = y + 10
    for line in lines:
        draw.text((text_x, current_y), line, fill=identity.accent_color, font=font)
        current_y += line_height
    return chip_height


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:
            return {}
    return {}


def _bridge_bundle(
    *,
    plan: dict[str, Any],
    strategic_format: str,
    visual_identity: dict[str, Any] | None = None,
    visual_contract: dict[str, Any] | None = None,
    capture_mode: str = "safe",
) -> dict[str, Any]:
    if not _bridge_enabled():
        return {
            "ok": True,
            "enabled": False,
            "approved_for_premium_visual": False,
            "selected_template_id": None,
            "premium_render_state": None,
            "reasons": ["premium_visual_bridge_disabled"],
        }

    try:
        from .visual_premium_bridge import build_visual_premium_bridge

        return build_visual_premium_bridge(
            creative_plan=plan,
            visual_identity=visual_identity,
            visual_contract=visual_contract,
            strategic_format=strategic_format,
            capture_mode=capture_mode,
        )
    except Exception as exc:
        return {
            "ok": True,
            "enabled": True,
            "approved_for_premium_visual": False,
            "selected_template_id": None,
            "premium_render_state": None,
            "reasons": [f"premium_visual_bridge_error: {type(exc).__name__}: {exc}"],
        }


def build_visual_identity(plan: dict[str, Any]) -> VisualIdentity:
    palette_name = str(plan.get("color_profile") or "editorial_violet")
    palette = PALETTES.get(palette_name, PALETTES["editorial_violet"])
    return VisualIdentity(
        palette_name=palette_name,
        series_name=str(plan.get("series_name") or "Liberta a Verdade"),
        watermark_text="Liberta a Verdade",
        background_color=palette["background"],
        header_band_color=palette["header_band"],
        panel_color=palette["panel"],
        panel_border_color=palette["panel_border"],
        accent_color=palette["accent"],
        accent_soft_color=palette["accent_soft"],
        text_primary=palette["text_primary"],
        text_secondary=palette["text_secondary"],
        text_on_dark=palette["text_on_dark"],
        watermark_color=palette["watermark"],
        safe_margin=78,
        panel_radius=34,
    )


def build_typography_spec(plan: dict[str, Any]) -> TypographySpec:
    headline = str(plan.get("headline") or "")
    hook = str(plan.get("hook") or "")
    body = str(plan.get("body") or "")

    headline_size = 70 if len(headline) <= 66 else 64
    hook_size = 28 if len(hook) <= 108 else 26
    body_size = 30 if len(body) <= 158 else 28

    return TypographySpec(
        headline_size=headline_size,
        hook_size=hook_size,
        body_size=body_size,
        support_size=24,
        brand_size=26,
        cta_size=26,
        eyebrow_size=22,
        headline_wrap=23,
        hook_wrap=36,
        body_wrap=43,
        support_wrap=32,
    )


def _evaluate_visual_quality_fallback(*, plan: dict[str, Any], identity: VisualIdentity, typography: TypographySpec) -> VisualQAResult:
    contract = build_visual_contract(plan)
    template = resolve_visual_template(plan)
    perceptual = evaluate_perceptual_quality(
        plan=plan,
        contract=contract,
        template=template,
        identity=identity,
        typography=typography,
    )
    metrics = dict(perceptual.metrics)
    metrics.update(
        {
            "safe_margin": identity.safe_margin,
            "panel_radius": identity.panel_radius,
            "headline_wrap": typography.headline_wrap,
            "body_wrap": typography.body_wrap,
        }
    )
    return VisualQAResult(
        approved=perceptual.approved,
        final_score=perceptual.final_score,
        minimum_score=contract.thresholds.minimum_visual_score,
        reasons=list(perceptual.reasons),
        recommendations=list(perceptual.recommendations),
        metrics=metrics,
        breakdown=dict(perceptual.breakdown),
        perceptual_qa=perceptual.to_dict(),
        contract=contract.to_dict(),
        template=template.to_dict(),
    )


def evaluate_visual_quality(*, plan: dict[str, Any], identity: VisualIdentity, typography: TypographySpec):
    try:
        from .visual_qa import evaluate_visual_quality as external_visual_qa

        return external_visual_qa(plan, identity, typography)
    except Exception:
        return _evaluate_visual_quality_fallback(plan=plan, identity=identity, typography=typography)


def build_carousel_sequence(plan: dict[str, Any]) -> dict[str, Any]:
    bridge = _bridge_bundle(plan=plan, strategic_format="carousel", capture_mode="safe")

    if _bridge_enabled():
        try:
            from .carousel_premium_composer import compose_premium_carousel

            premium = compose_premium_carousel(
                creative_plan=plan,
                visual_identity=None,
                visual_contract=None,
                capture_mode="safe",
            )
            if premium.get("ok"):
                premium["premium_visual_bridge"] = bridge
                premium["premium_visual_enabled"] = bridge.get("enabled", False)
                premium["premium_visual_selected"] = premium.get("approved_for_staging", False)
                premium["premium_template_id"] = premium.get("template_ids", [None])[0] if premium.get("template_ids") else None
                premium["premium_render_state"] = (premium.get("render_outputs") or [{}])[0].get("premium_render_state") if premium.get("render_outputs") else None
                return premium
        except Exception:
            pass

    contract = build_visual_contract(plan)
    display = prepare_display_copy(plan, contract)
    support = display["support_points"]
    slides = [
        CarouselSlide(1, "cover", display["headline"], display["hook"], ""),
        CarouselSlide(2, "thesis", "A ideia central", display["body"], ""),
        CarouselSlide(3, "support", support[0] if len(support) > 0 else "", support[1] if len(support) > 1 else "", ""),
        CarouselSlide(4, "cta", "Leve isso para a prática", display["cta"], str(plan.get("first_comment") or "")),
    ]
    return {
        "ok": True,
        "strategic_format": "carousel",
        "template_id": resolve_visual_template(plan).template_id,
        "slides": [slide.to_dict() for slide in slides],
        "premium_visual_bridge": bridge,
        "premium_visual_enabled": bridge.get("enabled", False),
        "premium_visual_selected": False,
        "premium_template_id": bridge.get("selected_template_id"),
        "premium_render_state": bridge.get("premium_render_state"),
    }


def build_stories_sequence(plan: dict[str, Any]) -> dict[str, Any]:
    bridge = _bridge_bundle(plan=plan, strategic_format="story", capture_mode="safe")

    if _bridge_enabled():
        try:
            from .story_premium_composer import compose_premium_stories

            premium = compose_premium_stories(
                creative_plan=plan,
                visual_identity=None,
                visual_contract=None,
                capture_mode="safe",
            )
            if premium.get("ok"):
                premium["premium_visual_bridge"] = bridge
                premium["premium_visual_enabled"] = bridge.get("enabled", False)
                premium["premium_visual_selected"] = premium.get("approved_for_staging", False)
                premium["premium_template_id"] = premium.get("template_ids", [None])[0] if premium.get("template_ids") else None
                premium["premium_render_state"] = (premium.get("render_outputs") or [{}])[0].get("premium_render_state") if premium.get("render_outputs") else None
                return premium
        except Exception:
            pass

    contract = build_visual_contract(plan)
    display = prepare_display_copy(plan, contract)
    frames = [
        StoryFrame(1, "hook", display["hook"], "abertura"),
        StoryFrame(2, "thesis", display["headline"], "tese"),
        StoryFrame(3, "body", display["body"], "explicação"),
        StoryFrame(4, "cta", display["cta"], "fechamento"),
    ]
    return {
        "ok": True,
        "strategic_format": "stories",
        "template_id": resolve_visual_template(plan).template_id,
        "frames": [frame.to_dict() for frame in frames],
        "premium_visual_bridge": bridge,
        "premium_visual_enabled": bridge.get("enabled", False),
        "premium_visual_selected": False,
        "premium_template_id": bridge.get("selected_template_id"),
        "premium_render_state": bridge.get("premium_render_state"),
    }


def render_visual_foundation_card(
    *,
    config: AceNextConfig,
    plan: dict[str, Any],
    identity: VisualIdentity,
    typography: TypographySpec,
) -> str:
    bridge = _bridge_bundle(
        plan=plan,
        strategic_format="image",
        visual_identity=identity.to_dict(),
        visual_contract=None,
        capture_mode="safe",
    )

    if bridge.get("enabled") and bridge.get("approved_for_premium_visual"):
        render = _safe_dict(bridge.get("render"))
        premium_path = render.get("screenshot_path") or render.get("html_path")
        if isinstance(premium_path, str) and premium_path.strip():
            return premium_path

    contract = build_visual_contract(plan)
    template = resolve_visual_template(plan)
    display = prepare_display_copy(plan, contract)

    config.media_dir.mkdir(parents=True, exist_ok=True)
    out = config.media_dir / f"ace_next_visual_{uuid.uuid4().hex}.png"

    if Image is None or ImageDraw is None:
        out.write_bytes(
            bytes.fromhex(
                "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000D49444154789C63F8FFFFFF7F0009FB03FD2A86E38A0000000049454E44AE426082"
            )
        )
        return str(out)

    img = Image.new("RGB", (contract.canvas_width, contract.canvas_height), identity.background_color)
    draw = ImageDraw.Draw(img)

    brand_font = _load_font(typography.brand_size, bold=True)
    eyebrow_font = _load_font(typography.eyebrow_size, bold=True)
    headline_font = _load_font(typography.headline_size, bold=True)
    hook_font = _load_font(typography.hook_size, bold=False)
    body_font = _load_font(typography.body_size, bold=False)
    support_font = _load_font(typography.support_size, bold=True)
    cta_font = _load_font(typography.cta_size, bold=True)
    watermark_font = _load_font(20, bold=True)

    safe = contract.safe_zones
    panel_left = safe.outer_margin
    panel_top = safe.content_top
    panel_right = contract.canvas_width - safe.outer_margin
    panel_bottom = safe.content_bottom

    draw.rectangle((0, 0, contract.canvas_width, safe.header_height), fill=identity.header_band_color)
    draw.text((safe.outer_margin, 52), "ACE Ω NEXT", fill=identity.text_on_dark, font=brand_font)

    series_text = identity.series_name[:28]
    series_bbox = draw.textbbox((0, 0), series_text, font=brand_font) if brand_font else (0, 0, 160, 28)
    series_width = series_bbox[2] - series_bbox[0]
    draw.text(
        (contract.canvas_width - safe.outer_margin - series_width, 52),
        series_text,
        fill=identity.watermark_color,
        font=brand_font,
    )

    draw.rounded_rectangle(
        (panel_left, panel_top, panel_right, panel_bottom),
        radius=identity.panel_radius,
        fill=identity.panel_color,
        outline=identity.panel_border_color,
        width=3,
    )

    draw.rounded_rectangle(
        (panel_left + 20, panel_top + 22, panel_left + 38, panel_bottom - 22),
        radius=10,
        fill=identity.accent_color,
    )

    eyebrow = template.blocks["eyebrow"]
    headline = template.blocks["headline"]
    hook = template.blocks["hook"]
    body = template.blocks["body"]
    support = template.blocks["support"]
    cta = template.blocks["cta"]

    eyebrow_text = "VISUAL SIGNAL"
    draw.rounded_rectangle(
        (eyebrow.x, eyebrow.y, eyebrow.x + 232, eyebrow.y + 36),
        radius=16,
        fill=identity.accent_soft_color,
    )
    draw.text((eyebrow.x + 16, eyebrow.y + 8), eyebrow_text, fill=identity.accent_color, font=eyebrow_font)

    headline_lines = _fit_lines(display["headline"], typography.headline_wrap, contract.max_headline_lines)
    hook_lines = _fit_lines(display["hook"], typography.hook_wrap, contract.max_hook_lines)
    body_lines = _fit_lines(display["body"], typography.body_wrap, contract.max_body_lines)
    cta_lines = _fit_lines(display["cta"], 34, contract.max_cta_lines)

    current_y = _draw_lines(
        draw,
        headline_lines,
        x=headline.x,
        y=headline.y,
        font=headline_font,
        fill=identity.text_primary,
        line_gap=14,
    )

    current_y = _draw_lines(
        draw,
        hook_lines,
        x=hook.x,
        y=max(current_y + safe.headline_gap, hook.y),
        font=hook_font,
        fill=identity.accent_color,
        line_gap=10,
    )

    current_y = _draw_lines(
        draw,
        body_lines,
        x=body.x,
        y=max(current_y + safe.hook_gap, body.y),
        font=body_font,
        fill=identity.text_secondary,
        line_gap=10,
    )

    chip_y = max(current_y + safe.body_gap, support.y)
    chip_width = support.width
    for point in display["support_points"][: contract.max_support_points]:
        chip_height = _draw_support_chip(
            draw,
            x=support.x,
            y=chip_y,
            text=point,
            font=support_font,
            identity=identity,
            width=chip_width,
        )
        chip_y += chip_height + safe.support_gap

    cta_y = max(chip_y + 18, cta.y)
    draw.rounded_rectangle(
        (cta.x, cta_y, cta.x + cta.width, cta_y + 64),
        radius=20,
        fill=identity.accent_soft_color,
        outline=identity.panel_border_color,
        width=2,
    )
    _draw_lines(
        draw,
        cta_lines,
        x=cta.x + 20,
        y=cta_y + 14,
        font=cta_font,
        fill=identity.accent_color,
        line_gap=6,
    )

    watermark = identity.watermark_text
    watermark_bbox = draw.textbbox((0, 0), watermark, font=watermark_font) if watermark_font else (0, 0, 180, 24)
    watermark_w = watermark_bbox[2] - watermark_bbox[0]
    draw.text(
        (panel_right - watermark_w - 12, panel_bottom + 16),
        watermark,
        fill=identity.watermark_color,
        font=watermark_font,
    )

    img.save(out)
    return str(out)
