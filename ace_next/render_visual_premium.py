from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from textwrap import wrap
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize_format(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"story", "stories"}:
        return "story"
    if normalized in {"carousel", "image", "reel_cover"}:
        return "image" if normalized == "reel_cover" else normalized
    return "image"


def _hex_to_rgb(value: Any, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    text = str(value or "").strip().lstrip("#")
    if len(text) != 6:
        return fallback
    try:
        return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return fallback


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates = ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"]
    else:
        candidates = ["DejaVuSans.ttf", "Arial.ttf", "arial.ttf"]

    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue

    return ImageFont.load_default()


def _dimensions(strategic_format: str) -> tuple[int, int]:
    if strategic_format == "story":
        return 1080, 1920
    return 1080, 1350


def _line_limit(text: str, chars_per_line: int, max_lines: int) -> str:
    if not text:
        return ""
    lines = wrap(text, width=max(chars_per_line, 10))
    lines = lines[:max(max_lines, 1)]
    return "\n".join(lines)


def _draw_multiline(
    draw: ImageDraw.ImageDraw,
    *,
    text: str,
    x: int,
    y: int,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    spacing: int,
) -> int:
    if not text:
        return y
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=spacing)
    bbox = draw.multiline_textbbox((x, y), text, font=font, spacing=spacing)
    return bbox[3]


def render_visual_premium(
    *,
    creative_plan: dict,
    visual_identity: dict | None = None,
    visual_contract: dict | None = None,
    template_id: str | None = None,
    capture_mode: str = "safe",
) -> dict[str, Any]:
    plan = _safe_dict(creative_plan)
    identity = _safe_dict(visual_identity)
    contract = _safe_dict(visual_contract)

    strategic_format = _normalize_format(
        plan.get("publish_format_now")
        or plan.get("strategic_target_format")
        or plan.get("format_recommendation")
        or "image"
    )

    width, height = _dimensions(strategic_format)

    bg = _hex_to_rgb(identity.get("bg"), (11, 16, 32))
    surface = _hex_to_rgb(identity.get("surface"), (17, 24, 39))
    panel = _hex_to_rgb(identity.get("panel"), (248, 250, 252))
    text_primary = _hex_to_rgb(identity.get("text_primary"), (15, 23, 42))
    text_on_dark = _hex_to_rgb(identity.get("text_on_dark"), (248, 250, 252))
    accent = _hex_to_rgb(identity.get("accent"), (59, 130, 246))

    headline = _clean_text(plan.get("headline") or plan.get("topic_seed"))
    hook = _clean_text(plan.get("hook"))
    body = _clean_text(plan.get("body") or plan.get("payoff"))
    cta = _clean_text(plan.get("cta"))
    support_points = _safe_list(plan.get("support_points"))

    headline_chars_budget = int(contract.get("headline_chars_budget", 62))
    hook_chars_budget = int(contract.get("hook_chars_budget", 90))
    body_chars_budget = int(contract.get("body_chars_budget", 120))
    cta_chars_budget = int(contract.get("cta_chars_budget", 42))

    headline_max_lines = int(contract.get("headline_max_lines", 3))
    hook_max_lines = int(contract.get("hook_max_lines", 2))
    body_max_lines = int(contract.get("body_max_lines", 3))
    cta_max_lines = int(contract.get("cta_max_lines", 1))
    support_points_max = int(contract.get("support_points_max", 2))

    visible_payload = {
        "headline": headline[:headline_chars_budget],
        "hook": hook[:hook_chars_budget],
        "body": body[:body_chars_budget],
        "cta": cta[:cta_chars_budget],
        "support_points": support_points[:support_points_max],
        "format": strategic_format,
        "template_id": template_id,
        "capture_mode": capture_mode,
    }

    headline_text = _line_limit(visible_payload["headline"], 28, headline_max_lines)
    hook_text = _line_limit(visible_payload["hook"], 36, hook_max_lines)
    body_text = _line_limit(visible_payload["body"], 42, body_max_lines)
    cta_text = _line_limit(visible_payload["cta"], 28, cta_max_lines)

    try:
        image = Image.new("RGB", (width, height), color=bg)
        draw = ImageDraw.Draw(image)

        margin_x = 72
        top = 72
        bottom_margin = 72

        draw.rounded_rectangle(
            [(48, 48), (width - 48, height - 48)],
            radius=44,
            fill=surface,
            outline=accent,
            width=3,
        )

        badge_font = _font(26, bold=True)
        headline_font = _font(64, bold=True)
        hook_font = _font(42, bold=True)
        body_font = _font(34, bold=False)
        cta_font = _font(30, bold=True)
        footer_font = _font(22, bold=False)

        draw.rounded_rectangle(
            [(margin_x, top), (margin_x + 260, top + 54)],
            radius=18,
            fill=accent,
        )
        draw.text(
            (margin_x + 18, top + 12),
            "VERDADES QUE LIBERTAM",
            font=badge_font,
            fill=text_on_dark,
        )

        cursor_y = top + 96
        cursor_y = _draw_multiline(
            draw,
            text=headline_text,
            x=margin_x,
            y=cursor_y,
            font=headline_font,
            fill=text_on_dark,
            spacing=10,
        ) + 28

        cursor_y = _draw_multiline(
            draw,
            text=hook_text,
            x=margin_x,
            y=cursor_y,
            font=hook_font,
            fill=panel,
            spacing=8,
        ) + 30

        if body_text:
            cursor_y = _draw_multiline(
                draw,
                text=body_text,
                x=margin_x,
                y=cursor_y,
                font=body_font,
                fill=panel,
                spacing=8,
            ) + 28

        for point in visible_payload["support_points"]:
            point_text = f"• {_clean_text(point)[:72]}"
            cursor_y = _draw_multiline(
                draw,
                text=point_text,
                x=margin_x,
                y=cursor_y,
                font=body_font,
                fill=panel,
                spacing=6,
            ) + 12

        if cta_text:
            cta_y = max(cursor_y + 18, height - bottom_margin - 120)
            draw.rounded_rectangle(
                [(margin_x, cta_y), (width - margin_x, cta_y + 86)],
                radius=24,
                fill=panel,
            )
            draw.text(
                (margin_x + 24, cta_y + 24),
                cta_text,
                font=cta_font,
                fill=text_primary,
            )

        footer_text = f"template={template_id or 'default'} | format={strategic_format}"
        draw.text(
            (margin_x, height - bottom_margin),
            footer_text,
            font=footer_font,
            fill=(180, 188, 204),
        )

        output_dir = Path("ace_media")
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"premium_render_{int(datetime.now(timezone.utc).timestamp())}.png"
        output_path = output_dir / filename
        image.save(output_path)

        return {
            "ok": True,
            "engine": "render_visual_premium_contract_safe_v1",
            "render_state": "premium_render_ready",
            "path": str(output_path),
            "image_path": str(output_path),
            "payload": visible_payload,
            "template_id": template_id,
            "strategic_format": strategic_format,
            "capture_mode": capture_mode,
            "reasons": [],
        }

    except Exception as exc:
        return {
            "ok": False,
            "engine": "render_visual_premium_contract_safe_v1",
            "render_state": "premium_render_failed",
            "path": None,
            "image_path": None,
            "payload": visible_payload,
            "template_id": template_id,
            "strategic_format": strategic_format,
            "capture_mode": capture_mode,
            "reasons": [f"render_visual_premium_error: {type(exc).__name__}: {exc}"],
            "error": str(exc),
        }
