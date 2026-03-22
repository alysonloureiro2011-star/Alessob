from __future__ import annotations

import textwrap
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from .config import AceNextConfig
from .perceptual_qa import evaluate_perceptual_quality
from .visual_contract import VisualContract, build_visual_contract
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
        safe_margin=68,
        panel_radius=36,
    )


def build_typography_spec(plan: dict[str, Any]) -> TypographySpec:
    headline = str(plan.get("headline") or "")
    hook = str(plan.get("hook") or "")
    body = str(plan.get("body") or "")

    headline_size = 82 if len(headline) <= 72 else 74
    hook_size = 34 if len(hook) <= 140 else 32
    body_size = 36 if len(body) <= 220 else 34

    return TypographySpec(
        headline_size=headline_size,
        hook_size=hook_size,
        body_size=body_size,
        support_size=28,
        brand_size=28,
        cta_size=30,
        eyebrow_size=24,
        headline_wrap=18,
        hook_wrap=26,
        body_wrap=32,
        support_wrap=28,
    )


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
    lines = _fit_lines(text, width, 2)
    line_height = getattr(font, "size", 24) + 8 if font else 28
    chip_height = 22 + (len(lines) * line_height)
    draw.rounded_rectangle(
        (x, y, x + width, y + chip_height),
        radius=22,
        fill=identity.accent_soft_color,
        outline=identity.panel_border_color,
        width=2,
    )
    bullet_r = 8
    bullet_x = x + 20
    bullet_y = y + 24
    draw.ellipse((bullet_x, bullet_y, bullet_x + bullet_r * 2, bullet_y + bullet_r * 2), fill=identity.accent_color)
    text_x = x + 44
    current_y = y + 16
    for line in lines:
        draw.text((text_x, current_y), line, fill=identity.accent_color, font=font)
        current_y += line_height
    return chip_height


def evaluate_visual_quality(*, plan: dict[str, Any], identity: VisualIdentity, typography: TypographySpec) -> VisualQAResult:
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


def build_carousel_sequence(plan: dict[str, Any]) -> dict[str, Any]:
    support_points = [str(item) for item in (plan.get("support_points") or [])][:3]
    slides = [
        CarouselSlide(1, "cover", str(plan.get("headline") or ""), str(plan.get("hook") or ""), ""),
        CarouselSlide(2, "thesis", "A ideia central", str(plan.get("body") or ""), ""),
        CarouselSlide(3, "support", support_points[0] if len(support_points) > 0 else "", support_points[1] if len(support_points) > 1 else str(plan.get("angle") or ""), ""),
        CarouselSlide(4, "support", support_points[2] if len(support_points) > 2 else str(plan.get("angle") or ""), str(plan.get("first_comment") or ""), ""),
        CarouselSlide(5, "cta", "Leve isso para a prática", str(plan.get("cta") or ""), str(plan.get("first_comment") or "")),
    ]
    return {
        "ok": True,
        "strategic_format": "carousel",
        "template_id": resolve_visual_template(plan).template_id,
        "slides": [slide.to_dict() for slide in slides],
    }


def build_stories_sequence(plan: dict[str, Any]) -> dict[str, Any]:
    frames = [
        StoryFrame(1, "hook", str(plan.get("hook") or ""), "abertura"),
        StoryFrame(2, "thesis", str(plan.get("headline") or ""), "tese"),
        StoryFrame(3, "body", str(plan.get("body") or ""), "explicação"),
        StoryFrame(4, "cta", str(plan.get("cta") or ""), "fechamento"),
    ]
    return {
        "ok": True,
        "strategic_format": "stories",
        "template_id": resolve_visual_template(plan).template_id,
        "frames": [frame.to_dict() for frame in frames],
    }


def render_visual_foundation_card(
    *,
    config: AceNextConfig,
    plan: dict[str, Any],
    identity: VisualIdentity,
    typography: TypographySpec,
) -> str:
    contract = build_visual_contract(plan)
    template = resolve_visual_template(plan)
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
    cta_font = _load_font(typography.cta_size, bold=False)
    watermark_font = _load_font(22, bold=True)

    safe = contract.safe_zones
    panel_left = safe.outer_margin
    panel_top = safe.content_top
    panel_right = contract.canvas_width - safe.outer_margin
    panel_bottom = safe.content_bottom

    draw.rectangle((0, 0, contract.canvas_width, safe.header_height), fill=identity.header_band_color)
    draw.text((safe.outer_margin, 58), "ACE Ω NEXT", fill=identity.text_on_dark, font=brand_font)

    series_text = identity.series_name[:28]
    series_bbox = draw.textbbox((0, 0), series_text, font=brand_font) if brand_font else (0, 0, 160, 28)
    series_width = series_bbox[2] - series_bbox[0]
    draw.text((contract.canvas_width - safe.outer_margin - series_width, 58), series_text, fill=identity.watermark_color, font=brand_font)

    draw.rounded_rectangle(
        (panel_left, panel_top, panel_right, panel_bottom),
        radius=identity.panel_radius,
        fill=identity.panel_color,
        outline=identity.panel_border_color,
        width=3,
    )
    draw.rounded_rectangle(
        (panel_left + 22, panel_top + 22, panel_left + 42, panel_bottom - 22),
        radius=12,
        fill=identity.accent_color,
    )

    blocks = template.blocks
    eyebrow_block = blocks["eyebrow"]
    headline_block = blocks["headline"]
    hook_block = blocks["hook"]
    body_block = blocks["body"]
    support_block = blocks["support"]
    cta_block = blocks["cta"]

    eyebrow_text = "EDITORIAL SIGNAL"
    eyebrow_width = 292
    eyebrow_height = 42
    draw.rounded_rectangle(
        (eyebrow_block.x, eyebrow_block.y, eyebrow_block.x + eyebrow_width, eyebrow_block.y + eyebrow_height),
        radius=18,
        fill=identity.accent_soft_color,
    )
    draw.text((eyebrow_block.x + 18, eyebrow_block.y + 10), eyebrow_text, fill=identity.accent_color, font=eyebrow_font)

    headline_lines = _fit_lines(str(plan.get("headline") or ""), typography.headline_wrap, contract.max_headline_lines)
    hook_lines = _fit_lines(str(plan.get("hook") or ""), typography.hook_wrap, contract.max_hook_lines)
    body_lines = _fit_lines(str(plan.get("body") or ""), typography.body_wrap, contract.max_body_lines)
    cta_lines = _fit_lines(str(plan.get("cta") or ""), 34, contract.max_cta_lines)

    current_y = _draw_lines(
        draw,
        headline_lines,
        x=headline_block.x,
        y=headline_block.y,
        font=headline_font,
        fill=identity.text_primary,
        line_gap=16,
    )
    current_y = _draw_lines(
        draw,
        hook_lines,
        x=hook_block.x,
        y=max(current_y + 10, hook_block.y),
        font=hook_font,
        fill=identity.accent_color,
        line_gap=12,
    )
    current_y = _draw_lines(
        draw,
        body_lines,
        x=body_block.x,
        y=max(current_y + 16, body_block.y),
        font=body_font,
        fill=identity.text_secondary,
        line_gap=12,
    )

    support_points = [str(item) for item in (plan.get("support_points") or [])][: contract.max_support_points]
    chip_y = max(current_y + 22, support_block.y)
    chip_width = support_block.width
    for point in support_points:
        chip_height = _draw_support_chip(
            draw,
            x=support_block.x,
            y=chip_y,
            text=point[: contract.max_support_chars + 12],
            font=support_font,
            identity=identity,
            width=chip_width,
        )
        chip_y += chip_height + safe.support_gap

    cta_top = max(cta_block.y, min(chip_y + 18, panel_bottom - safe.footer_height))
    draw.rounded_rectangle(
        (cta_block.x, cta_top, cta_block.x + cta_block.width, cta_top + 88),
        radius=24,
        fill=identity.accent_soft_color,
        outline=identity.panel_border_color,
        width=2,
    )
    _draw_lines(
        draw,
        cta_lines,
        x=cta_block.x + 24,
        y=cta_top + 18,
        font=cta_font,
        fill=identity.accent_color,
        line_gap=8,
    )

    watermark = identity.watermark_text
    watermark_bbox = draw.textbbox((0, 0), watermark, font=watermark_font) if watermark_font else (0, 0, 180, 24)
    watermark_w = watermark_bbox[2] - watermark_bbox[0]
    draw.text(
        (panel_right - watermark_w - 12, panel_bottom + 18),
        watermark,
        fill=identity.watermark_color,
        font=watermark_font,
    )

    img.save(out)
    return str(out)
