from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .editorial_policy import normalize_text
from .visual_contract import VisualContract
from .visual_templates import VisualTemplate


@dataclass
class PerceptualQAResult:
    approved: bool
    final_score: int
    breakdown: dict[str, float]
    metrics: dict[str, Any]
    reasons: list[str]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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


def _wrap_capacity(width: int, font_size: int) -> int:
    if font_size <= 0:
        return 24
    return max(10, int(width / max(font_size * 0.58, 1)))


def _line_estimate(text: str, width: int, font_size: int) -> int:
    text = (text or "").strip()
    if not text:
        return 1
    capacity = _wrap_capacity(width, font_size)
    return max(1, int((len(text) / capacity) + 0.999))


def evaluate_perceptual_quality(
    *,
    plan: dict[str, Any],
    contract: VisualContract,
    template: VisualTemplate,
    identity: Any,
    typography: Any,
) -> PerceptualQAResult:
    headline = str(plan.get("headline") or "")
    hook = str(plan.get("hook") or "")
    body = str(plan.get("body") or "")
    support_points = [str(item) for item in (plan.get("support_points") or [])][: contract.max_support_points]
    cta = str(plan.get("cta") or "")

    headline_lines = _line_estimate(headline, template.blocks["headline"].width, typography.headline_size)
    hook_lines = _line_estimate(hook, template.blocks["hook"].width, typography.hook_size)
    body_lines = _line_estimate(body, template.blocks["body"].width, typography.body_size)
    cta_lines = _line_estimate(cta, template.blocks["cta"].width, typography.cta_size)

    support_overflow = sum(1 for point in support_points if len(point) > contract.max_support_chars)
    overlap_risk = 0
    if headline_lines > contract.max_headline_lines:
        overlap_risk += 1
    if hook_lines > contract.max_hook_lines:
        overlap_risk += 1
    if body_lines > contract.max_body_lines:
        overlap_risk += 1
    if cta_lines > contract.max_cta_lines:
        overlap_risk += 1
    if support_overflow > 0:
        overlap_risk += 1

    panel_contrast = contrast_ratio(identity.panel_color, identity.text_primary)
    accent_contrast = contrast_ratio(identity.accent_soft_color, identity.accent_color)
    dark_contrast = contrast_ratio(identity.header_band_color, identity.text_on_dark)

    normalized = normalize_text(" ".join([headline, hook, body, cta] + support_points))
    lexical_richness = len(set(normalized.split()))

    legibility = 7.0
    if typography.headline_size >= 74:
        legibility += 0.4
    if typography.body_size >= 34:
        legibility += 0.3
    if contract.safe_zones.outer_margin >= 64:
        legibility += 0.3
    legibility -= min(overlap_risk * 0.5, 1.5)

    composition = 7.0
    if template.density == "controlled":
        composition += 0.5
    if len(support_points) >= 3:
        composition += 0.3
    if body_lines <= contract.max_body_lines:
        composition += 0.3
    composition -= min(overlap_risk * 0.6, 1.8)

    contrast = 7.0
    if panel_contrast >= 10:
        contrast += 0.8
    elif panel_contrast >= 8:
        contrast += 0.5
    if dark_contrast >= 7:
        contrast += 0.3
    if accent_contrast < 2.2:
        contrast -= 0.6

    brand_fit_visual = 7.6
    if template.template_id.startswith("signal"):
        brand_fit_visual += 0.3
    if "viral" not in normalized and "imperdivel" not in normalized:
        brand_fit_visual += 0.2
    if contract.density_target == "controlled":
        brand_fit_visual += 0.2
    brand_fit_visual -= min(overlap_risk * 0.3, 0.9)

    perceived_value_visual = 7.2
    if lexical_richness >= 24:
        perceived_value_visual += 0.4
    if len(body) >= 140:
        perceived_value_visual += 0.3
    if len(support_points) >= 3:
        perceived_value_visual += 0.2
    perceived_value_visual -= min(overlap_risk * 0.3, 0.9)

    noise_control = 8.0
    if len(support_points) > 3:
        noise_control -= 1.0
    if body_lines > contract.max_body_lines:
        noise_control -= 0.8
    if headline_lines > contract.max_headline_lines:
        noise_control -= 0.6

    breakdown = {
        "legibility": round(max(0.0, min(legibility, 10.0)), 2),
        "contrast": round(max(0.0, min(contrast, 10.0)), 2),
        "composition": round(max(0.0, min(composition, 10.0)), 2),
        "brand_fit_visual": round(max(0.0, min(brand_fit_visual, 10.0)), 2),
        "perceived_value_visual": round(max(0.0, min(perceived_value_visual, 10.0)), 2),
        "noise_control": round(max(0.0, min(noise_control, 10.0)), 2),
    }
    final_score = int(
        round(
            (
                breakdown["legibility"] * 0.22
                + breakdown["contrast"] * 0.18
                + breakdown["composition"] * 0.22
                + breakdown["brand_fit_visual"] * 0.20
                + breakdown["perceived_value_visual"] * 0.18
            )
            * 10
        )
    )

    reasons: list[str] = []
    recommendations: list[str] = []

    if overlap_risk > 0:
        reasons.append("há risco estrutural de sobreposição ou excesso de densidade")
        recommendations.append("encurtar headline/body ou reduzir pressão de layout")
    if breakdown["legibility"] < contract.thresholds.minimum_legibility:
        reasons.append("legibilidade abaixo do piso")
        recommendations.append("aumentar respiro, reduzir densidade e manter tamanhos móveis fortes")
    if breakdown["contrast"] < contract.thresholds.minimum_contrast:
        reasons.append("contraste abaixo do piso")
        recommendations.append("fortalecer contraste entre painel, texto e destaque")
    if breakdown["composition"] < contract.thresholds.minimum_composition:
        reasons.append("composição abaixo do piso")
        recommendations.append("redistribuir pesos visuais e reduzir ruído")
    if breakdown["brand_fit_visual"] < contract.thresholds.minimum_brand_fit:
        reasons.append("aderência visual à marca ainda insuficiente")
        recommendations.append("subir sofisticação e coerência do template")
    if breakdown["perceived_value_visual"] < contract.thresholds.minimum_perceived_value:
        reasons.append("valor percebido visual ainda insuficiente")
        recommendations.append("aumentar clareza sem aumentar ruído")

    approved = (
        overlap_risk == 0
        and breakdown["legibility"] >= contract.thresholds.minimum_legibility
        and breakdown["contrast"] >= contract.thresholds.minimum_contrast
        and breakdown["composition"] >= contract.thresholds.minimum_composition
        and breakdown["brand_fit_visual"] >= contract.thresholds.minimum_brand_fit
        and breakdown["perceived_value_visual"] >= contract.thresholds.minimum_perceived_value
        and final_score >= contract.thresholds.minimum_visual_score
    )

    metrics = {
        "headline_lines": headline_lines,
        "hook_lines": hook_lines,
        "body_lines": body_lines,
        "cta_lines": cta_lines,
        "support_points": len(support_points),
        "support_overflow": support_overflow,
        "overlap_risk": overlap_risk,
        "zero_overlap": overlap_risk == 0,
        "panel_text_contrast": round(panel_contrast, 2),
        "accent_contrast": round(accent_contrast, 2),
        "dark_contrast": round(dark_contrast, 2),
        "lexical_richness": lexical_richness,
        "template_id": template.template_id,
    }

    if approved and not reasons:
        reasons.append("visual perceptual dentro do mínimo aceitável para a fase atual")

    return PerceptualQAResult(
        approved=approved,
        final_score=final_score,
        breakdown=breakdown,
        metrics=metrics,
        reasons=reasons,
        recommendations=recommendations,
    )
