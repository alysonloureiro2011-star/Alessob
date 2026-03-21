from __future__ import annotations

import os
import textwrap
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from .config import AceNextConfig

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = None
    ImageDraw = None
    ImageFont = None


PALETTES = {
    "electric_blue": {
        "background": (11, 18, 34),
        "header_band": (18, 28, 52),
        "panel": (248, 250, 255),
        "accent": (36, 102, 255),
        "accent_soft": (223, 233, 255),
        "text_primary": (18, 20, 26),
        "text_secondary": (87, 95, 116),
        "text_on_dark": (255, 255, 255),
        "watermark": (183, 196, 224),
    },
    "amber_gold": {
        "background": (32, 23, 13),
        "header_band": (48, 35, 16),
        "panel": (255, 249, 242),
        "accent": (214, 144, 33),
        "accent_soft": (248, 232, 197),
        "text_primary": (28, 21, 14),
        "text_secondary": (102, 87, 67),
        "text_on_dark": (255, 255, 255),
        "watermark": (232, 213, 178),
    },
    "editorial_violet": {
        "background": (24, 19, 35),
        "header_band": (34, 26, 48),
        "panel": (248, 246, 255),
        "accent": (136, 81, 255),
        "accent_soft": (230, 220, 255),
        "text_primary": (22, 18, 28),
        "text_secondary": (98, 93, 114),
        "text_on_dark": (255, 255, 255),
        "watermark": (208, 196, 242),
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
    palette_name = plan.get("color_profile") or "editorial_violet"
    palette = PALETTES.get(str(palette_name), PALETTES["editorial_violet"])

    return VisualIdentity(
        palette_name=str(palette_name),
        series_name=str(plan.get("series_name") or "Liberta a Verdade"),
        watermark_text="Liberta a Verdade",
        background_color=palette["background"],
        header_band_color=palette["header_band"],
        panel_color=palette["panel"],
        accent_color=palette["accent"],
        accent_soft_color=palette["accent_soft"],
        text_primary=palette["text_primary"],
        text_secondary=palette["text_secondary"],
        text_on_dark=palette["text_on_dark"],
        watermark_color=palette["watermark"],
        safe_margin=58,
        panel_radius=42,
    )


def build_typography_spec(plan: dict[str, Any]) -> TypographySpec:
    return TypographySpec(
        headline_size=80,
        hook_size=34,
        body_size=38,
        support_size=28,
        brand_size=28,
        cta_size=30,
        eyebrow_size=26,
        headline_wrap=18,
        hook_wrap=24,
        body_wrap=31,
    )


def _channel(value: int) -> float:
    c = value / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(color: tuple[int, int, int]) -> float:
    r, g, b = color
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    l1 = _luminance(a)
    l2 = _luminance(b)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def evaluate_visual_quality(
    *,
    plan: dict[str, Any],
    identity: VisualIdentity,
    typography: TypographySpec,
) -> VisualQAResult:
    score = int(plan.get("quality_score") or 0)
    minimum_score = int(os.environ.get("ACE_MIN_VISUAL_SCORE", "70"))

    reasons: list[str] = []
    recommendations: list[str] = []

    headline = (plan.get("headline") or "").strip()
    body = (plan.get("body") or "").strip()
    support_points = plan.get("support_points") or []
    trend_input = (plan.get("trend_input") or "").strip().lower()

    panel_contrast = contrast_ratio(identity.panel_color, identity.text_primary)
    accent_contrast = contrast_ratio(identity.accent_soft_color, identity.accent_color)

    if trend_input in {"teste", "teste real", "test", "oi", "hello", "aaa", "123"}:
        score -= 42
        reasons.append("entrada fraca ou de teste")
        recommendations.append("trocar o tema por uma dor real ou insight real")

    if len(headline) < 20:
        score -= 10
        reasons.append("headline curta demais")
        recommendations.append("aumentar especificidade e força da headline")

    if len(body) < 70:
        score -= 10
        reasons.append("corpo editorial curto demais")
        recommendations.append("explicar melhor a ideia central")

    if len(support_points) < 3:
        score -= 8
        reasons.append("poucos pontos de apoio")
        recommendations.append("gerar ao menos 3 pontos visuais de sustentação")

    if panel_contrast < 7:
        score -= 18
        reasons.append("contraste principal abaixo do ideal")
        recommendations.append("aumentar contraste entre painel e texto")

    if accent_contrast < 2.2:
        score -= 8
        reasons.append("contraste do destaque abaixo do ideal")
        recommendations.append("melhorar relação entre cor de destaque e fundo suave")

    if identity.safe_margin < 48:
        score -= 6
        reasons.append("safe zone insuficiente")
        recommendations.append("aumentar margem segura para tela pequena")

    metrics = {
        "panel_text_contrast": round(panel_contrast, 2),
        "accent_contrast": round(accent_contrast, 2),
        "headline_length": len(headline),
        "body_length": len(body),
        "support_points": len(support_points),
        "safe_margin": identity.safe_margin,
        "headline_wrap": typography.headline_wrap,
        "body_wrap": typography.body_wrap,
    }

    approved = score >= minimum_score

    if approved and not reasons:
        reasons.append("visual dentro do mínimo aceitável para a fase atual")

    if not approved and not recommendations:
        recommendations.append("subir força do tema, headline e contraste")

    return VisualQAResult(
        approved=approved,
        final_score=max(score, 0),
        minimum_score=minimum_score,
        reasons=reasons,
        recommendations=recommendations,
        metrics=metrics,
    )


def build_carousel_sequence(plan: dict[str, Any]) -> dict[str, Any]:
    support_points = plan.get("support_points") or []
    slides = [
        CarouselSlide(1, "cover", str(plan.get("headline") or ""), str(plan.get("hook") or ""), ""),
        CarouselSlide(2, "insight", "O ponto central", str(plan.get("body") or ""), ""),
        CarouselSlide(3, "support_1", support_points[0] if len(support_points) > 0 else "", str(plan.get("angle") or ""), ""),
        CarouselSlide(4, "support_2", support_points[1] if len(support_points) > 1 else "", support_points[2] if len(support_points) > 2 else "", ""),
        CarouselSlide(5, "cta", "Leve isso para a prática", str(plan.get("cta") or ""), str(plan.get("first_comment") or "")),
    ]
    return {
        "ok": True,
        "strategic_format": "carousel",
        "slides": [slide.to_dict() for slide in slides],
    }


def build_stories_sequence(plan: dict[str, Any]) -> dict[str, Any]:
    frames = [
        StoryFrame(1, "hook", str(plan.get("hook") or ""), "abertura"),
        StoryFrame(2, "body", str(plan.get("body") or ""), "explicação"),
        StoryFrame(3, "angle", str(plan.get("angle") or ""), "virada"),
        StoryFrame(4, "cta", str(plan.get("cta") or ""), "fechamento"),
    ]
    return {
        "ok": True,
        "strategic_format": "stories",
        "frames": [frame.to_dict() for frame in frames],
    }


def _load_font(size: int, bold: bool = False):
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


def _draw_wrapped(draw, text: str, *, x: int, y: int, width: int, font, fill, line_gap: int = 14) -> int:
    lines = textwrap.wrap((text or "").strip(), width=width) or [""]
    line_height = getattr(font, "size", 24) + line_gap if font else 30
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, fill=fill, font=font)
        current_y += line_height
    return current_y


def _draw_chip(draw, text: str, *, x: int, y: int, font, identity: VisualIdentity) -> int:
    if not text:
        return 0
    bbox = draw.textbbox((0, 0), text, font=font) if font else (0, 0, 180, 34)
    width = (bbox[2] - bbox[0]) + 34
    height = (bbox[3] - bbox[1]) + 18
    draw.rounded_rectangle((x, y, x + width, y + height), radius=18, fill=identity.accent_soft_color)
    draw.text((x + 16, y + 8), text, fill=identity.accent_color, font=font)
    return height


def render_visual_foundation_card(
    *,
    config: AceNextConfig,
    plan: dict[str, Any],
    identity: VisualIdentity,
    typography: TypographySpec,
) -> str:
    config.media_dir.mkdir(parents=True, exist_ok=True)
    out = config.media_dir / f"ace_next_{uuid.uuid4().hex}.png"

    if Image is None or ImageDraw is None:
        out.write_bytes(
            bytes.fromhex(
                "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000D49444154789C63F8FFFFFF7F0009FB03FD2A86E38A0000000049454E44AE426082"
            )
        )
        return str(out)

    img = Image.new("RGB", (1080, 1350), identity.background_color)
    draw = ImageDraw.Draw(img)

    brand_font = _load_font(typography.brand_size, bold=True)
    eyebrow_font = _load_font(typography.eyebrow_size, bold=True)
    headline_font = _load_font(typography.headline_size, bold=True)
    hook_font = _load_font(typography.hook_size, bold=False)
    body_font = _load_font(typography.body_size, bold=False)
    support_font = _load_font(typography.support_size, bold=True)
    cta_font = _load_font(typography.cta_size, bold=False)
    watermark_font = _load_font(24, bold=True)

    draw.rectangle((0, 0, 1080, 220), fill=identity.header_band_color)
    draw.text((identity.safe_margin, 72), "ACE Ω NEXT", fill=identity.text_on_dark, font=brand_font)
    draw.text((735, 72), identity.series_name[:24], fill=identity.watermark_color, font=brand_font)

    left = identity.safe_margin
    right = 1080 - identity.safe_margin
    top = 255
    bottom = 1175

    draw.rounded_rectangle((left, top, right, bottom), radius=identity.panel_radius, fill=identity.panel_color)
    draw.rectangle((left, top, left + 24, bottom), fill=identity.accent_color)

    draw.rounded_rectangle((left + 58, top + 54, left + 390, top + 108), radius=20, fill=identity.accent_soft_color)
    draw.text((left + 82, top + 70), "EDITORIAL SIGNAL", fill=identity.accent_color, font=eyebrow_font)

    y = _draw_wrapped(
        draw,
        str(plan.get("headline") or ""),
        x=left + 58,
        y=top + 150,
        width=typography.headline_wrap,
        font=headline_font,
        fill=identity.text_primary,
        line_gap=18,
    )

    y = _draw_wrapped(
        draw,
        str(plan.get("hook") or ""),
        x=left + 58,
        y=y + 24,
        width=typography.hook_wrap,
        font=hook_font,
        fill=identity.accent_color,
        line_gap=14,
    )

    y = _draw_wrapped(
        draw,
        str(plan.get("body") or ""),
        x=left + 58,
        y=y + 28,
        width=typography.body_wrap,
        font=body_font,
        fill=identity.text_secondary,
        line_gap=14,
    )

    support_points = plan.get("support_points") or []
    chip_y = y + 34
    for point in support_points[:3]:
        chip_height = _draw_chip(
            draw,
            point,
            x=left + 58,
            y=chip_y,
            font=support_font,
            identity=identity,
        )
        chip_y += chip_height + 18

    footer_top = bottom - 165
    draw.rounded_rectangle(
        (left + 58, footer_top, right - 58, bottom - 62),
        radius=26,
        fill=identity.accent_soft_color,
    )
    draw.text((left + 90, footer_top + 28), str(plan.get("cta") or ""), fill=identity.accent_color, font=cta_font)

    watermark = identity.watermark_text
    bbox = draw.textbbox((0, 0), watermark, font=watermark_font) if watermark_font else (0, 0, 180, 24)
    watermark_w = bbox[2] - bbox[0]
    draw.text((right - watermark_w - 58, bottom + 18), watermark, fill=identity.watermark_color, font=watermark_font)

    img.save(out)
    return str(out)
