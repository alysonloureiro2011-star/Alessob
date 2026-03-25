from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _slug(value: Any) -> str:
    text = _clean_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "render"


def _safe_output_dir(output_dir: str | None, payload: dict[str, Any]) -> Path:
    if output_dir:
        return Path(output_dir)
    base_slug = _slug(
        payload.get("topic_seed")
        or payload.get("headline")
        or payload.get("series_name")
        or "render-visual-premium"
    )
    return Path("ace_media") / "render_visual_premium" / base_slug


def _build_render_payload(
    creative_plan: dict[str, Any],
    visual_identity: dict[str, Any] | None = None,
    visual_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    creative_plan = _safe_dict(creative_plan)
    visual_identity = _safe_dict(visual_identity)
    visual_contract = _safe_dict(visual_contract)

    headline = _clean_text(creative_plan.get("headline"))
    hook = _clean_text(creative_plan.get("hook"))
    body = _clean_text(creative_plan.get("body"))
    cta = _clean_text(creative_plan.get("cta"))
    support_points = creative_plan.get("support_points")
    if not isinstance(support_points, list):
        support_points = []
    support_points = [_clean_text(x) for x in support_points if _clean_text(x)][:4]

    series_name = _clean_text(creative_plan.get("series_name") or "Liberta a Verdade")
    topic_seed = _clean_text(creative_plan.get("topic_seed") or headline or "clareza, disciplina e direção")
    publish_style = _clean_text(creative_plan.get("publish_style") or "premium_dark_editorial")
    brand_persona = _clean_text(creative_plan.get("brand_persona") or "editorial_soberano")

    eyebrow = _clean_text(
        creative_plan.get("eyebrow")
        or creative_plan.get("angle")
        or topic_seed
    )
    watermark = _clean_text(creative_plan.get("watermark") or series_name)
    footer_note = _clean_text(creative_plan.get("footer_note") or cta)

    identity = {
        "bg": visual_identity.get("bg", "#0b1020"),
        "surface": visual_identity.get("surface", "#111827"),
        "panel": visual_identity.get("panel", "#f8fafc"),
        "panel_border": visual_identity.get("panel_border", "rgba(255,255,255,0.12)"),
        "text_primary": visual_identity.get("text_primary", "#0f172a"),
        "text_secondary": visual_identity.get("text_secondary", "#334155"),
        "text_on_dark": visual_identity.get("text_on_dark", "#f8fafc"),
        "accent": visual_identity.get("accent", "#3b82f6"),
        "accent_soft": visual_identity.get("accent_soft", "rgba(59,130,246,0.16)"),
        "watermark": visual_identity.get("watermark", "rgba(255,255,255,0.28)"),
        "shadow": visual_identity.get("shadow", "0 18px 60px rgba(0,0,0,0.34)"),
    }

    contract = {
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

    return {
        "headline": headline,
        "hook": hook,
        "body": body,
        "cta": cta,
        "support_points": support_points,
        "eyebrow": eyebrow,
        "series_name": series_name,
        "topic_seed": topic_seed,
        "publish_style": publish_style,
        "brand_persona": brand_persona,
        "watermark": watermark,
        "footer_note": footer_note,
        "identity": identity,
        "contract": contract,
    }


def _select_template(template_id: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    chosen = _clean_text(template_id or payload.get("template_id") or "hero_card_v1")
    if chosen not in {"hero_card_v1", "insight_card_v1", "contrast_card_v1"}:
        chosen = "hero_card_v1"

    templates = {
        "hero_card_v1": {
            "template_id": "hero_card_v1",
            "title_scale": "xl",
            "density": "balanced",
            "use_case": "headline_hero",
            "block_order": ["eyebrow", "headline", "hook", "body", "support_points", "cta"],
        },
        "insight_card_v1": {
            "template_id": "insight_card_v1",
            "title_scale": "lg",
            "density": "light",
            "use_case": "insight_editorial",
            "block_order": ["eyebrow", "hook", "headline", "body", "support_points", "cta"],
        },
        "contrast_card_v1": {
            "template_id": "contrast_card_v1",
            "title_scale": "xl",
            "density": "medium",
            "use_case": "contrast_statement",
            "block_order": ["eyebrow", "headline", "body", "support_points", "hook", "cta"],
        },
    }
    return templates[chosen]


def _build_css_document(payload: dict[str, Any], template_meta: dict[str, Any]) -> str:
    identity = _safe_dict(payload.get("identity"))
    contract = _safe_dict(payload.get("contract"))

    return f"""
:root {{
  --bg: {identity.get("bg")};
  --surface: {identity.get("surface")};
  --panel: {identity.get("panel")};
  --panel-border: {identity.get("panel_border")};
  --text-primary: {identity.get("text_primary")};
  --text-secondary: {identity.get("text_secondary")};
  --text-on-dark: {identity.get("text_on_dark")};
  --accent: {identity.get("accent")};
  --accent-soft: {identity.get("accent_soft")};
  --watermark: {identity.get("watermark")};
  --shadow: {identity.get("shadow")};
}}

* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

html, body {{
  width: 100%;
  min-height: 100%;
  background:
    radial-gradient(circle at top right, rgba(59,130,246,0.22), transparent 28%),
    radial-gradient(circle at bottom left, rgba(37,99,235,0.18), transparent 32%),
    var(--bg);
  font-family: Inter, Arial, Helvetica, sans-serif;
}}

body {{
  padding: 24px;
}}

.canvas {{
  width: 1080px;
  height: 1350px;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
  border-radius: 40px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0)),
    var(--surface);
  box-shadow: var(--shadow);
  border: 1px solid rgba(255,255,255,0.08);
}}

.safe-zone {{
  position: absolute;
  inset: {contract.get("safe_zone_top")}px 56px {contract.get("safe_zone_bottom")}px 56px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}

.header-band {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}}

.eyebrow {{
  display: inline-flex;
  max-width: 78%;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-on-dark);
  opacity: 0.92;
}}

.series-name {{
  font-size: 18px;
  font-weight: 700;
  color: var(--accent);
  padding: 10px 14px;
  border-radius: 999px;
  background: var(--accent-soft);
  border: 1px solid rgba(255,255,255,0.10);
}}

.panel {{
  background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,250,252,0.98));
  color: var(--text-primary);
  border-radius: 32px;
  padding: 44px 40px 34px;
  border: 1px solid var(--panel-border);
  display: flex;
  flex-direction: column;
  gap: 22px;
}}

.headline {{
  font-size: 64px;
  line-height: 1.02;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--text-primary);
}}

.hook {{
  font-size: 28px;
  line-height: 1.25;
  font-weight: 700;
  color: var(--accent);
}}

.body {{
  font-size: 27px;
  line-height: 1.38;
  font-weight: 500;
  color: var(--text-secondary);
}}

.support-list {{
  list-style: none;
  display: grid;
  gap: 14px;
}}

.support-item {{
  display: flex;
  gap: 14px;
  align-items: flex-start;
  font-size: 24px;
  line-height: 1.3;
  color: var(--text-secondary);
}}

.support-item::before {{
  content: "";
  width: 10px;
  height: 10px;
  margin-top: 11px;
  border-radius: 999px;
  background: var(--accent);
  flex: 0 0 auto;
}}

.footer-row {{
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
}}

.cta {{
  max-width: 74%;
  font-size: 24px;
  line-height: 1.25;
  font-weight: 700;
  color: var(--text-on-dark);
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  padding: 18px 20px;
  border-radius: 20px;
}}

.footer-note {{
  font-size: 16px;
  line-height: 1.2;
  color: var(--text-on-dark);
  opacity: 0.72;
  text-align: right;
}}

.watermark {{
  position: absolute;
  right: 28px;
  bottom: 22px;
  font-size: 14px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--watermark);
}}

.template-{template_meta.get("template_id")} .headline {{
  font-size: {"68px" if template_meta.get("title_scale") == "xl" else "58px"};
}}

.template-contrast_card_v1 .hook {{
  color: var(--text-secondary);
}}

.template-insight_card_v1 .panel {{
  gap: 18px;
}}

@media (max-width: 1200px) {{
  body {{ padding: 0; }}
  .canvas {{
    width: 100vw;
    height: calc(100vw * 1.25);
    border-radius: 0;
  }}
}}
""".strip()


def _build_html_document(payload: dict[str, Any], template_meta: dict[str, Any], css_filename: str) -> str:
    support_points = payload.get("support_points") or []
    support_html = "\n".join(
        f'<li class="support-item">{point}</li>' for point in support_points
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{payload.get("headline") or payload.get("series_name")}</title>
  <link rel="stylesheet" href="./{css_filename}" />
</head>
<body>
  <div class="canvas template-{template_meta.get("template_id")}">
    <div class="safe-zone">
      <div class="header-band">
        <div class="eyebrow">{payload.get("eyebrow")}</div>
        <div class="series-name">{payload.get("series_name")}</div>
      </div>

      <div class="panel">
        <div class="headline">{payload.get("headline")}</div>
        <div class="hook">{payload.get("hook")}</div>
        <div class="body">{payload.get("body")}</div>
        <ul class="support-list">
          {support_html}
        </ul>
      </div>

      <div class="footer-row">
        <div class="cta">{payload.get("cta")}</div>
        <div class="footer-note">{payload.get("footer_note")}</div>
      </div>
    </div>

    <div class="watermark">{payload.get("watermark")}</div>
  </div>
</body>
</html>
""".strip()


def _build_render_manifest(
    payload: dict[str, Any],
    template_meta: dict[str, Any],
    capture_mode: str,
    output_paths: dict[str, str | None],
) -> dict[str, Any]:
    identity = _safe_dict(payload.get("identity"))
    contract = _safe_dict(payload.get("contract"))

    return {
        "engine_version": "render_visual_premium_v1",
        "template_id": template_meta.get("template_id"),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "capture_mode": capture_mode,
        "payload_summary": {
            "headline": payload.get("headline"),
            "hook": payload.get("hook"),
            "body": payload.get("body"),
            "cta": payload.get("cta"),
            "support_points_count": len(payload.get("support_points") or []),
            "eyebrow": payload.get("eyebrow"),
            "series_name": payload.get("series_name"),
            "topic_seed": payload.get("topic_seed"),
        },
        "identity_summary": {
            "bg": identity.get("bg"),
            "surface": identity.get("surface"),
            "panel": identity.get("panel"),
            "accent": identity.get("accent"),
        },
        "contract_summary": {
            "aspect_ratio": contract.get("aspect_ratio"),
            "mobile_first": contract.get("mobile_first"),
            "headline_chars_budget": contract.get("headline_chars_budget"),
            "body_chars_budget": contract.get("body_chars_budget"),
            "cta_chars_budget": contract.get("cta_chars_budget"),
        },
        "output_paths": output_paths,
    }


def _write_render_artifacts(
    output_dir: Path,
    html_document: str,
    css_document: str,
    manifest: dict[str, Any],
) -> dict[str, str | None]:
    output_dir.mkdir(parents=True, exist_ok=True)

    html_path = output_dir / "render.html"
    css_path = output_dir / "render.css"
    manifest_path = output_dir / "render_manifest.json"

    html_path.write_text(html_document, encoding="utf-8")
    css_path.write_text(css_document, encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "html_path": str(html_path),
        "css_path": str(css_path),
        "manifest_path": str(manifest_path),
        "screenshot_path": None,
    }


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except Exception:
        return False


def _capture_with_playwright(html_path: str, screenshot_path: str) -> tuple[bool, str | None]:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
            page.goto(Path(html_path).resolve().as_uri(), wait_until="networkidle")
            page.screenshot(path=screenshot_path, full_page=True)
            browser.close()
        return True, None
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def render_visual_premium(
    *,
    creative_plan: dict,
    visual_identity: dict | None = None,
    visual_contract: dict | None = None,
    output_dir: str | None = None,
    template_id: str | None = None,
    capture_mode: str = "safe",
) -> dict:
    creative_plan = _safe_dict(creative_plan)
    payload = _build_render_payload(
        creative_plan=creative_plan,
        visual_identity=visual_identity,
        visual_contract=visual_contract,
    )
    template_meta = _select_template(template_id, payload)
    output_base = _safe_output_dir(output_dir, payload)

    css_document = _build_css_document(payload, template_meta)
    html_document = _build_html_document(payload, template_meta, "render.css")

    reasons: list[str] = []
    capture_mode_normalized = _clean_text(capture_mode).lower() or "safe"
    if capture_mode_normalized not in {"safe", "html_only", "capture"}:
        capture_mode_normalized = "safe"
        reasons.append("capture_mode inválido; usado safe")

    output_paths = {
        "html_path": None,
        "css_path": None,
        "manifest_path": None,
        "screenshot_path": None,
    }

    manifest = _build_render_manifest(
        payload=payload,
        template_meta=template_meta,
        capture_mode=capture_mode_normalized,
        output_paths=output_paths,
    )

    output_paths = _write_render_artifacts(
        output_dir=output_base,
        html_document=html_document,
        css_document=css_document,
        manifest=manifest,
    )

    manifest = _build_render_manifest(
        payload=payload,
        template_meta=template_meta,
        capture_mode=capture_mode_normalized,
        output_paths=output_paths,
    )
    Path(output_paths["manifest_path"]).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    available = _playwright_available()
    capture_attempted = False
    capture_succeeded = False
    screenshot_path = None

    if capture_mode_normalized == "html_only":
        reasons.append("modo html_only: captura não solicitada")
        render_state = "html_generated"
    elif not available:
        reasons.append("playwright não disponível; captura ignorada")
        render_state = "html_generated_capture_skipped"
    else:
        capture_attempted = True
        target_png = str(output_base / "render_preview.png")
        ok, error = _capture_with_playwright(output_paths["html_path"], target_png)
        if ok:
            capture_succeeded = True
            screenshot_path = target_png
            output_paths["screenshot_path"] = target_png
            reasons.append("captura premium gerada com playwright")
            render_state = "captured"
        else:
            reasons.append(f"captura falhou: {error}")
            render_state = "html_generated_capture_failed"

    manifest = _build_render_manifest(
        payload=payload,
        template_meta=template_meta,
        capture_mode=capture_mode_normalized,
        output_paths=output_paths,
    )
    Path(output_paths["manifest_path"]).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "ok": True,
        "engine": "render_visual_premium_v1",
        "template_id": template_meta.get("template_id"),
        "capture_mode": capture_mode_normalized,
        "capture_attempted": capture_attempted,
        "capture_succeeded": capture_succeeded,
        "playwright_available": available,
        "html_path": output_paths["html_path"],
        "css_path": output_paths["css_path"],
        "screenshot_path": screenshot_path,
        "manifest_path": output_paths["manifest_path"],
        "render_state": render_state,
        "reasons": reasons,
        "payload": {
            "headline": payload.get("headline"),
            "hook": payload.get("hook"),
            "body": payload.get("body"),
            "cta": payload.get("cta"),
            "support_points": payload.get("support_points"),
            "eyebrow": payload.get("eyebrow"),
            "series_name": payload.get("series_name"),
        },
    }


def render_visual_premium_examples() -> dict:
    example_plan = {
        "topic_seed": "clareza, disciplina e direção",
        "headline": "Sem disciplina, clareza perde força antes de virar resultado.",
        "hook": "O problema raramente é falta de esforço. Quase sempre é mover muito sem critério suficiente.",
        "body": "Quando estrutura entra, intenção deixa de depender do humor do dia e a execução passa a responder a processo.",
        "cta": "Salve para revisar antes da próxima decisão.",
        "support_points": [
            "Clareza sem base vira intenção solta.",
            "Disciplina protege consistência quando o entusiasmo cai.",
        ],
        "series_name": "Liberta a Verdade",
        "publish_style": "premium_dark_editorial",
        "brand_persona": "editorial_soberano",
    }

    return {
        "ok": True,
        "hero_card": render_visual_premium(
            creative_plan=example_plan,
            template_id="hero_card_v1",
            capture_mode="html_only",
        ),
        "insight_card": render_visual_premium(
            creative_plan=example_plan,
            template_id="insight_card_v1",
            capture_mode="html_only",
        ),
        "contrast_card": render_visual_premium(
            creative_plan=example_plan,
            template_id="contrast_card_v1",
            capture_mode="html_only",
        ),
    }
