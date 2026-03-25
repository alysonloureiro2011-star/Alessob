from __future__ import annotations

from typing import Any


FORMAT_LIMITS = {
    "image": {
        "minimum_score": 78,
        "minimum_hierarchy": 7.5,
        "minimum_legibility": 7.5,
        "minimum_contrast": 7.0,
        "minimum_spacing": 7.2,
        "minimum_cognitive_load": 7.2,
        "minimum_premium_feel": 7.5,
        "headline_lines": 3,
        "hook_lines": 2,
        "body_lines": 3,
        "cta_lines": 1,
        "support_points_max": 2,
    },
    "carousel": {
        "minimum_score": 78,
        "minimum_hierarchy": 7.5,
        "minimum_legibility": 7.5,
        "minimum_contrast": 7.0,
        "minimum_spacing": 7.2,
        "minimum_cognitive_load": 7.2,
        "minimum_premium_feel": 7.5,
        "headline_lines": 3,
        "hook_lines": 2,
        "body_lines": 3,
        "cta_lines": 1,
        "support_points_max": 2,
    },
    "story": {
        "minimum_score": 78,
        "minimum_hierarchy": 7.5,
        "minimum_legibility": 7.5,
        "minimum_contrast": 7.0,
        "minimum_spacing": 7.2,
        "minimum_cognitive_load": 7.2,
        "minimum_premium_feel": 7.5,
        "headline_lines": 3,
        "hook_lines": 2,
        "body_lines": 3,
        "cta_lines": 2,
        "support_points_max": 1,
    },
}


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize_format(value: Any) -> str:
    normalized = _clean_text(value).lower()
    if normalized in {"story", "stories"}:
        return "story"
    if normalized in {"carousel", "image"}:
        return normalized
    return "image"


def _line_estimate(text: str, chars_per_line: int) -> int:
    cleaned = _clean_text(text)
    if not cleaned:
        return 0
    return max(1, (len(cleaned) + chars_per_line - 1) // chars_per_line)


def _chars_per_line_estimate(format_name: str, field: str) -> int:
    if format_name == "story":
        return {"headline": 24, "hook": 34, "body": 40, "cta": 26}.get(field, 34)
    if format_name == "carousel":
        return {"headline": 28, "hook": 34, "body": 40, "cta": 28}.get(field, 34)
    return {"headline": 28, "hook": 36, "body": 42, "cta": 28}.get(field, 34)


def _redundancy_ratio(parts: list[str]) -> float:
    cleaned = [_clean_text(part).lower() for part in parts if _clean_text(part)]
    if len(cleaned) < 2:
        return 0.0
    total_words = 0
    unique_words: set[str] = set()
    for part in cleaned:
        words = [word for word in part.split() if word]
        total_words += len(words)
        unique_words.update(words)
    if total_words == 0:
        return 0.0
    return round(1.0 - (len(unique_words) / total_words), 2)


def _score_hierarchy(metrics: dict[str, Any], limits: dict[str, Any], has_block_order: bool) -> float:
    score = 8.8
    if not has_block_order:
        score -= 0.6
    if metrics["headline_lines"] > limits["headline_lines"]:
        score -= 1.1
    if metrics["hook_lines"] > limits["hook_lines"]:
        score -= 0.8
    if metrics["cta_lines"] > limits["cta_lines"]:
        score -= 0.8
    if metrics["support_points_count"] > limits["support_points_max"]:
        score -= 0.8
    return max(0.0, min(10.0, round(score, 2)))


def _score_legibility(metrics: dict[str, Any], limits: dict[str, Any]) -> float:
    score = 8.9
    if metrics["headline_lines"] > limits["headline_lines"]:
        score -= 1.0
    if metrics["body_lines"] > limits["body_lines"]:
        score -= 1.0
    if metrics["cta_lines"] > limits["cta_lines"]:
        score -= 0.7
    return max(0.0, min(10.0, round(score, 2)))


def _score_contrast(template_meta: dict[str, Any], brand_system: dict[str, Any]) -> float:
    score = 7.2
    if brand_system.get("text_contrast_policy"):
        score += 0.6
    if template_meta.get("premium_tier"):
        score += 0.5
    if template_meta.get("html_ready") is True:
        score += 0.3
    return max(0.0, min(10.0, round(score, 2)))


def _score_spacing(metrics: dict[str, Any], limits: dict[str, Any]) -> float:
    score = 8.6
    if metrics["support_points_count"] > limits["support_points_max"]:
        score -= 1.0
    if metrics["body_lines"] > limits["body_lines"]:
        score -= 0.9
    if metrics["headline_lines"] + metrics["hook_lines"] + metrics["body_lines"] > 8:
        score -= 0.8
    return max(0.0, min(10.0, round(score, 2)))


def _score_cognitive_load(metrics: dict[str, Any], limits: dict[str, Any]) -> float:
    score = 8.7
    if metrics["redundancy_ratio"] > 0.45:
        score -= 1.0
    if metrics["density_signal"] == "high":
        score -= 1.2
    if metrics["support_points_count"] > limits["support_points_max"]:
        score -= 0.8
    if metrics["body_lines"] > limits["body_lines"]:
        score -= 0.8
    return max(0.0, min(10.0, round(score, 2)))


def _score_premium_feel(payload: dict[str, Any], template_meta: dict[str, Any], metrics: dict[str, Any]) -> float:
    text = " ".join(
        [
            _clean_text(payload.get("headline")),
            _clean_text(payload.get("hook")),
            _clean_text(payload.get("body")),
            _clean_text(payload.get("cta")),
        ]
    ).lower()

    score = 8.5
    if template_meta.get("premium_tier"):
        score += 0.4
    if any(token in text for token in {"segredo", "ninguém te conta", "ninguem te conta", "comente aqui", "corre"}):
        score -= 1.4
    if metrics["support_points_count"] > 2:
        score -= 0.8
    if metrics["density_signal"] == "high":
        score -= 0.7
    return max(0.0, min(10.0, round(score, 2)))


def evaluate_visual_hierarchy_gate(contract: dict[str, Any]) -> dict[str, Any]:
    contract = _safe_dict(contract)
    brand_system = _safe_dict(contract.get("brand_system"))
    template_spec = _safe_dict(contract.get("template_spec"))
    layout_payload = _safe_dict(contract.get("layout_payload"))
    gate_payload = _safe_dict(contract.get("gate_payload"))
    display_payload = _safe_dict(layout_payload.get("display_payload"))

    format_name = _normalize_format(
        gate_payload.get("format")
        or display_payload.get("format")
        or template_spec.get("strategic_format")
    )
    limits = dict(FORMAT_LIMITS[format_name])

    support_points = display_payload.get("support_points")
    if not isinstance(support_points, list):
        support_points = []

    metrics = {
        "headline_chars": len(_clean_text(display_payload.get("headline"))),
        "hook_chars": len(_clean_text(display_payload.get("hook"))),
        "body_chars": len(_clean_text(display_payload.get("body"))),
        "cta_chars": len(_clean_text(display_payload.get("cta"))),
        "support_points_count": len([x for x in support_points if _clean_text(x)]),
        "headline_lines": _line_estimate(display_payload.get("headline"), _chars_per_line_estimate(format_name, "headline")),
        "hook_lines": _line_estimate(display_payload.get("hook"), _chars_per_line_estimate(format_name, "hook")),
        "body_lines": _line_estimate(display_payload.get("body"), _chars_per_line_estimate(format_name, "body")),
        "cta_lines": _line_estimate(display_payload.get("cta"), _chars_per_line_estimate(format_name, "cta")),
        "redundancy_ratio": _redundancy_ratio(
            [
                display_payload.get("headline"),
                display_payload.get("hook"),
                display_payload.get("body"),
                *support_points,
                display_payload.get("cta"),
            ]
        ),
        "density_signal": "low",
        "format": format_name,
        "template_id": template_spec.get("template_id"),
    }

    total_lines = metrics["headline_lines"] + metrics["hook_lines"] + metrics["body_lines"] + metrics["cta_lines"]
    if total_lines >= 10 or metrics["support_points_count"] > limits["support_points_max"]:
        metrics["density_signal"] = "high"
    elif total_lines >= 7:
        metrics["density_signal"] = "medium"

    has_block_order = bool(template_spec.get("block_order"))
    hierarchy = _score_hierarchy(metrics, limits, has_block_order)
    legibility = _score_legibility(metrics, limits)
    contrast = _score_contrast(template_spec, brand_system)
    spacing = _score_spacing(metrics, limits)
    cognitive_load = _score_cognitive_load(metrics, limits)
    premium_feel = _score_premium_feel(display_payload, template_spec, metrics)

    composition_score = round((hierarchy + spacing) / 2.0, 2)
    noise_control_score = cognitive_load
    brand_dignity_score = premium_feel

    breakdown = {
        "hierarchy": hierarchy,
        "legibility": legibility,
        "contrast": contrast,
        "spacing": spacing,
        "cognitive_load": cognitive_load,
        "premium_feel": premium_feel,
        "brand_dignity_score": brand_dignity_score,
        "contrast_score": contrast,
        "composition_score": composition_score,
        "legibility_score": legibility,
        "hierarchy_score": hierarchy,
        "noise_control_score": noise_control_score,
    }

    final_score = round(
        (
            hierarchy * 0.22
            + legibility * 0.22
            + contrast * 0.14
            + spacing * 0.14
            + cognitive_load * 0.14
            + premium_feel * 0.14
        )
        * 10,
        2,
    )

    failed_floors: list[str] = []
    if hierarchy < limits["minimum_hierarchy"]:
        failed_floors.append("hierarchy")
    if legibility < limits["minimum_legibility"]:
        failed_floors.append("legibility")
    if contrast < limits["minimum_contrast"]:
        failed_floors.append("contrast")
    if spacing < limits["minimum_spacing"]:
        failed_floors.append("spacing")
    if cognitive_load < limits["minimum_cognitive_load"]:
        failed_floors.append("cognitive_load")
    if premium_feel < limits["minimum_premium_feel"]:
        failed_floors.append("premium_feel")
    if final_score < limits["minimum_score"]:
        failed_floors.append("minimum_score")

    rejection_reasons: list[str] = []
    recommendations: list[str] = []

    if metrics["headline_lines"] > limits["headline_lines"]:
        rejection_reasons.append("headline excedeu line budget")
        recommendations.append("reduzir headline")
    if metrics["hook_lines"] > limits["hook_lines"]:
        rejection_reasons.append("hook excedeu line budget")
        recommendations.append("encurtar hook")
    if metrics["body_lines"] > limits["body_lines"]:
        rejection_reasons.append("body excedeu line budget")
        recommendations.append("cortar body")
    if metrics["cta_lines"] > limits["cta_lines"]:
        rejection_reasons.append("CTA longa demais")
        recommendations.append("encurtar CTA")
    if metrics["support_points_count"] > limits["support_points_max"]:
        rejection_reasons.append("support points em excesso")
        recommendations.append("reduzir support points")
    if metrics["redundancy_ratio"] > 0.45:
        rejection_reasons.append("redundância textual elevada")
        recommendations.append("separar melhor hook e body")
    if metrics["density_signal"] == "high":
        rejection_reasons.append("densidade cognitiva alta")
        recommendations.append("baixar densidade cognitiva")

    approved = len(failed_floors) == 0

    if approved and not rejection_reasons:
        rejection_reasons.append("visual dentro do piso soberano para fundação premium")

    return {
        "ok": True,
        "approved": approved,
        "final_score": final_score,
        "minimum_score": limits["minimum_score"],
        "breakdown": breakdown,
        "failed_floors": failed_floors,
        "rejection_reasons": rejection_reasons,
        "recommendations": recommendations,
        "brand_dignity_score": brand_dignity_score,
        "contrast_score": contrast,
        "composition_score": composition_score,
        "legibility_score": legibility,
        "hierarchy_score": hierarchy,
        "noise_control_score": noise_control_score,
        "metrics": metrics,
        "contract": limits,
    }
