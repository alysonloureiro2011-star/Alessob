from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def _css_vars(brand_system: dict[str, Any]) -> str:
    palette = dict(brand_system.get("palette") or {})
    panel = dict(brand_system.get("panel_system") or {})
    return f"""
:root {{
  --bg: {palette.get("background", "#08111F")};
  --surface: {palette.get("surface", "#0E1728")};
  --surface-soft: {palette.get("surface_soft", "#121F36")};
  --panel: {palette.get("panel", "#F7FAFF")};
  --panel-border: {palette.get("panel_border", "#D8E1F0")};
  --text-primary: {palette.get("text_primary", "#141A24")};
  --text-secondary: {palette.get("text_secondary", "#5E6B82")};
  --text-on-dark: {palette.get("text_on_dark", "#F8FBFF")};
  --accent-primary: {palette.get("accent_primary", "#2D6DFF")};
  --accent-soft: {palette.get("accent_soft", "#DDE8FF")};
  --watermark: {palette.get("watermark", "#9CB2D9")};
  --panel-radius: {int(panel.get("panel_radius", 34))}px;
  --panel-border-width: {int(panel.get("panel_border_width", 2))}px;
}}
""".strip()


def _block_style(block: dict[str, Any]) -> str:
    return (
        f"left:{int(block.get('x', 0))}px;"
        f"top:{int(block.get('y', 0))}px;"
        f"width:{int(block.get('width', 0))}px;"
        f"height:{int(block.get('height', 0))}px;"
    )


def build_html_card_document(contract: dict[str, Any]) -> str:
    contract = dict(contract or {})
    brand_system = dict(contract.get("brand_system") or {})
    template_spec = dict(contract.get("template_spec") or {})
    layout_payload = dict(contract.get("layout_payload") or {})
    typography_spec = dict(contract.get("typography_spec") or {})
    display_payload = dict(layout_payload.get("display_payload") or {})
    blocks = dict(template_spec.get("blocks") or {})
    canvas = dict((layout_payload.get("canvas") or {}) or {"width": 1080, "height": 1350})

    eyebrow = escape(str(display_payload.get("eyebrow") or "LIBERTA A VERDADE"))
    headline = escape(str(display_payload.get("headline") or ""))
    hook = escape(str(display_payload.get("hook") or ""))
    body = escape(str(display_payload.get("body") or ""))
    cta = escape(str(display_payload.get("cta") or ""))
    support_points = [escape(str(item)) for item in (display_payload.get("support_points") or [])[:2]]
    watermark = escape(str(contract.get("input_plan", {}).get("series_name") or "Liberta a Verdade"))

    support_html = "".join(
        f'<div class="support-chip">{item}</div>'
        for item in support_points
        if item
    )

    css = f"""
{_css_vars(brand_system)}

* {{ box-sizing: border-box; }}
html, body {{
  margin: 0;
  padding: 0;
  background: var(--bg);
  font-family: Inter, Arial, Helvetica, sans-serif;
}}

.canvas {{
  position: relative;
  width: {int(canvas.get("width", 1080))}px;
  height: {int(canvas.get("height", 1350))}px;
  background: var(--bg);
  overflow: hidden;
}}

.header-band {{
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 136px;
  background: var(--surface);
}}

.panel {{
  position: absolute;
  left: 84px;
  top: 210px;
  width: 912px;
  height: 960px;
  border-radius: var(--panel-radius);
  background: var(--panel);
  border: var(--panel-border-width) solid var(--panel-border);
  box-shadow: 0 24px 60px rgba(0,0,0,0.18);
}}

.accent-rail {{
  position: absolute;
  left: 108px;
  top: 232px;
  width: 18px;
  height: 920px;
  border-radius: 10px;
  background: var(--accent-primary);
}}

.brand-top {{
  position: absolute;
  left: 84px;
  top: 48px;
  color: var(--text-on-dark);
  font-size: 26px;
  font-weight: 800;
  letter-spacing: 0.02em;
}}

.watermark {{
  position: absolute;
  right: 96px;
  bottom: 30px;
  color: var(--watermark);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.02em;
}}

.block {{
  position: absolute;
  overflow: hidden;
}}

.eyebrow {{
  {_block_style(blocks.get("eyebrow", {}))}
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  padding: 0 16px;
  border-radius: 16px;
  background: var(--accent-soft);
  color: var(--accent-primary);
  font-size: {int(typography_spec.get("eyebrow_size", 22))}px;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}}

.headline {{
  {_block_style(blocks.get("headline", {}))}
  color: var(--text-primary);
  font-size: {int(typography_spec.get("headline_size", 72))}px;
  font-weight: 800;
  line-height: 1.02;
  letter-spacing: -0.03em;
}}

.hook {{
  {_block_style(blocks.get("hook", {}))}
  color: var(--accent-primary);
  font-size: {int(typography_spec.get("hook_size", 28))}px;
  font-weight: 700;
  line-height: 1.22;
}}

.body {{
  {_block_style(blocks.get("body", {}))}
  color: var(--text-secondary);
  font-size: {int(typography_spec.get("body_size", 30))}px;
  font-weight: 500;
  line-height: 1.28;
}}

.support {{
  {_block_style(blocks.get("support", {}))}
  display: flex;
  flex-direction: column;
  gap: 14px;
}}

.support-chip {{
  width: 100%;
  min-height: 54px;
  padding: 14px 18px;
  border-radius: 18px;
  background: var(--accent-soft);
  color: var(--accent-primary);
  border: 1px solid var(--panel-border);
  font-size: {int(typography_spec.get("support_size", 24))}px;
  font-weight: 700;
  line-height: 1.2;
}}

.cta {{
  {_block_style(blocks.get("cta", {}))}
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-radius: 20px;
  background: var(--accent-soft);
  color: var(--accent-primary);
  font-size: {int(typography_spec.get("cta_size", 26))}px;
  font-weight: 800;
  line-height: 1.1;
}}
""".strip()

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width={int(canvas.get("width", 1080))}, initial-scale=1.0" />
  <title>ACE Ω Premium Card</title>
  <style>{css}</style>
</head>
<body>
  <div class="canvas">
    <div class="header-band"></div>
    <div class="panel"></div>
    <div class="accent-rail"></div>
    <div class="brand-top">ACE Ω NEXT</div>

    <div class="block eyebrow">{eyebrow}</div>
    <div class="block headline">{headline}</div>
    <div class="block hook">{hook}</div>
    <div class="block body">{body}</div>
    <div class="block support">{support_html}</div>
    <div class="block cta">{cta}</div>

    <div class="watermark">{watermark}</div>
  </div>
</body>
</html>"""
    return html


def write_html_card_preview(contract: dict[str, Any], output_path: str | Path) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_html_card_document(contract), encoding="utf-8")
    return str(output)


def html_card_renderer_examples() -> dict[str, Any]:
    sample_contract = {
        "input_plan": {"series_name": "Liberta a Verdade"},
        "brand_system": {
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
                "watermark": "#9CB2D9",
            },
            "panel_system": {"panel_radius": 34, "panel_border_width": 2},
        },
        "template_spec": {
            "blocks": {
                "eyebrow": {"x": 132, "y": 242, "width": 300, "height": 42},
                "headline": {"x": 132, "y": 316, "width": 816, "height": 210},
                "hook": {"x": 132, "y": 550, "width": 816, "height": 106},
                "body": {"x": 132, "y": 686, "width": 816, "height": 152},
                "support": {"x": 132, "y": 864, "width": 816, "height": 156},
                "cta": {"x": 132, "y": 1038, "width": 816, "height": 68},
            }
        },
        "typography_spec": {
            "eyebrow_size": 22,
            "headline_size": 72,
            "hook_size": 28,
            "body_size": 30,
            "support_size": 24,
            "cta_size": 26,
        },
        "layout_payload": {
            "canvas": {"width": 1080, "height": 1350},
            "display_payload": {
                "eyebrow": "LIBERTA A VERDADE",
                "headline": "Sem disciplina, clareza perde força antes de virar resultado.",
                "hook": "O problema raramente é falta de esforço. Quase sempre é mover muito sem critério suficiente.",
                "body": "Quando estrutura entra, intenção deixa de depender do humor do dia.",
                "support_points": [
                    "Clareza sem base vira intenção solta.",
                    "Disciplina protege consistência quando o entusiasmo cai.",
                ],
                "cta": "Salve para revisar antes da próxima decisão.",
            },
        },
    }
    html = build_html_card_document(sample_contract)
    return {"ok": True, "html_length": len(html), "html_preview": html[:500]}
