from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class RubricEngineResult:
    approved_minimum_quality: bool
    eligible_for_brand_live: bool
    global_score: float
    global_score_100: int
    breakdown: dict[str, float]
    floors: dict[str, float]
    failed_floors: list[str]
    reasons: list[str]
    weights: dict[str, float]
    authority_payload_source: str | None
    hardening_considered: bool
    post_hardening_scores: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _n(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _r(value: float) -> float:
    return round(float(value), 2)


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:
            return {}
    return {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _avg(*values: Any) -> float:
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return 0.0
    return sum(nums) / len(nums)


def _scale_score_0_10(value: Any) -> float:
    score = _n(value, 0.0)
    if score > 10:
        score = score / 10.0
    return max(0.0, min(score, 10.0))


def _resolve_authority_payload(
    plan: dict[str, Any],
    visual_qa: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], str]:
    visual_qa = _safe_dict(visual_qa)
    metrics = _safe_dict(visual_qa.get("metrics"))
    render = _safe_dict(visual_qa.get("render"))
    staging_hardener = _safe_dict(metrics.get("staging_hardener"))

    render_payload_used = _safe_dict(metrics.get("render_payload_used"))
    if render_payload_used:
        return render_payload_used, staging_hardener, "visual_qa.metrics.render_payload_used"

    hardened_visible_payload = _safe_dict(visual_qa.get("hardened_visible_payload"))
    if hardened_visible_payload:
        return hardened_visible_payload, staging_hardener, "visual_qa.hardened_visible_payload"

    render_payload = _safe_dict(render.get("payload"))
    if render_payload:
        return render_payload, staging_hardener, "visual_qa.render.payload"

    hardened_payload = _safe_dict(staging_hardener.get("hardened_payload"))
    if hardened_payload:
        return hardened_payload, staging_hardener, "visual_qa.metrics.staging_hardener.hardened_payload"

    direct_render_payload = _safe_dict(visual_qa.get("render_payload_used"))
    if direct_render_payload:
        return direct_render_payload, staging_hardener, "visual_qa.render_payload_used"

    return _safe_dict(plan), staging_hardener, "creative_plan"


def _visible_text_score(text: str, *, min_chars: int, ideal_max: int, hard_max: int) -> float:
    length = len(_clean_text(text))
    if length == 0:
        return 4.5
    if length < min_chars:
        return 6.8
    if length <= ideal_max:
        return 8.9
    if length <= hard_max:
        return 7.9
    return 6.2


def _generic_penalty(text: str) -> float:
    lowered = _clean_text(text).lower()
    bad_patterns = {
        "segredo",
        "ninguém te conta",
        "ninguem te conta",
        "isso muda tudo",
        "mude sua vida",
        "acredite em você",
        "acredite em voce",
        "viral",
        "imperdível",
        "imperdivel",
        "comente aqui",
        "corre",
        "chama na dm",
    }
    return 1.0 if any(token in lowered for token in bad_patterns) else 0.0


def evaluate_rubric_engine(
    *,
    plan: dict[str, Any],
    editorial_qa: dict[str, Any],
    visual_qa: dict[str, Any],
    perceptual_qa: dict[str, Any],
) -> RubricEngineResult:
    editorial = _safe_dict(_safe_dict(editorial_qa).get("breakdown"))
    perceptual = _safe_dict(_safe_dict(perceptual_qa).get("breakdown"))
    visual = _safe_dict(visual_qa)
    hierarchy_gate = _safe_dict(visual.get("hierarchy_gate"))
    dignity_score = _safe_dict(visual.get("brand_dignity_score"))
    dignity_breakdown = _safe_dict(dignity_score.get("breakdown"))

    authority_payload, staging_hardener, authority_payload_source = _resolve_authority_payload(
        _safe_dict(plan),
        visual,
    )

    headline_text = _clean_text(authority_payload.get("headline"))
    hook_text = _clean_text(authority_payload.get("hook"))
    body_text = _clean_text(authority_payload.get("body"))
    cta_text = _clean_text(authority_payload.get("cta"))
    support_points = [_clean_text(x) for x in _safe_list(authority_payload.get("support_points")) if _clean_text(x)]

    hidden_overflow = _safe_list(
        authority_payload.get("hidden_overflow_for_caption")
        or visual.get("hidden_overflow_for_caption")
        or staging_hardener.get("hidden_overflow_for_caption")
    )

    hardening_considered = bool(staging_hardener) or authority_payload_source != "creative_plan"

    headline_visible = _visible_text_score(headline_text, min_chars=18, ideal_max=56, hard_max=62)
    hook_visible = _visible_text_score(hook_text, min_chars=28, ideal_max=72, hard_max=90)
    body_visible = _visible_text_score(body_text, min_chars=48, ideal_max=90, hard_max=120)
    cta_visible = _visible_text_score(cta_text, min_chars=10, ideal_max=32, hard_max=42)
    support_visible = 8.8 if len(support_points) <= 2 else (7.3 if len(support_points) == 3 else 6.0)

    generic_penalty = _generic_penalty(" ".join([headline_text, hook_text, body_text, cta_text]))
    hierarchy_score = _scale_score_0_10(hierarchy_gate.get("final_score"))
    dignity_final = _scale_score_0_10(dignity_score.get("final_score"))
    visual_final = _scale_score_0_10(visual.get("final_score"))

    headline = _r(_avg(_n(editorial.get("headline")), headline_visible) - generic_penalty * 0.2)
    hook = _r(_avg(_n(editorial.get("hook")), hook_visible) - generic_penalty * 0.25)
    clarity = _r(_avg(_n(editorial.get("clarity")), body_visible, cta_visible, hierarchy_score))
    semantic_density = _r(_avg(_n(editorial.get("semantic_density")), 8.1 if hardening_considered else 7.4))
    authority = _r(_avg(_n(editorial.get("authority")), clarity, _n(dignity_breakdown.get("brand_fit"))))
    perceived_value = _r(
        _avg(
            _n(editorial.get("perceived_value")),
            _n(perceptual.get("perceived_value_visual")),
            body_visible,
            8.2 if hidden_overflow else None,
        )
    )
    narrative_tension = _r(_avg(_n(editorial.get("narrative_tension")), hook, perceived_value))
    novelty = _r(_avg(_n(editorial.get("anti_generic")), semantic_density) - generic_penalty)
    naturalism = _r(_avg(_n(editorial.get("naturalism")), _n(dignity_breakdown.get("naturality")), support_visible))
    anti_genericity = _r(_avg(_n(editorial.get("anti_generic")), headline_visible, hook_visible) - generic_penalty)
    anti_commodity = _r(
        _avg(
            _n(editorial.get("anti_commodity")),
            _n(dignity_breakdown.get("anti_commodity")),
            support_visible,
            cta_visible,
        )
        - generic_penalty
    )

    legibility = _r(_avg(_n(perceptual.get("legibility")), hierarchy_score))
    contrast = _r(_avg(_n(perceptual.get("contrast")), _n(_safe_dict(hierarchy_gate.get("breakdown")).get("contrast"))))
    composition = _r(_avg(_n(perceptual.get("composition")), hierarchy_score))
    brand_fit_visual = _r(_avg(_n(perceptual.get("brand_fit_visual")), _n(dignity_breakdown.get("brand_fit")), visual_final))
    perceived_value_visual = _r(_avg(_n(perceptual.get("perceived_value_visual")), perceived_value, dignity_final))
    noise_control = _r(_avg(_n(perceptual.get("noise_control")), support_visible, hierarchy_score))

    brand_fit = _r(_avg(brand_fit_visual, _n(dignity_breakdown.get("brand_fit")), anti_genericity, anti_commodity, hierarchy_score))
    visual_impact = _r(_avg(contrast, composition, visual_final, hierarchy_score))
    shareability = _r(_avg(hook, perceived_value, brand_fit))
    saveability = _r(_avg(clarity, semantic_density, perceived_value))

    breakdown = {
        "headline": max(0.0, headline),
        "hook": max(0.0, hook),
        "clarity": max(0.0, clarity),
        "semantic_density": max(0.0, semantic_density),
        "authority": max(0.0, authority),
        "perceived_value": max(0.0, perceived_value),
        "narrative_tension": max(0.0, narrative_tension),
        "novelty": max(0.0, novelty),
        "naturalism": max(0.0, naturalism),
        "anti_genericity": max(0.0, anti_genericity),
        "anti_commodity": max(0.0, anti_commodity),
        "legibility": max(0.0, legibility),
        "contrast": max(0.0, contrast),
        "composition": max(0.0, composition),
        "visual_impact": max(0.0, visual_impact),
        "shareability": max(0.0, shareability),
        "saveability": max(0.0, saveability),
        "brand_fit": max(0.0, brand_fit),
        "noise_control": max(0.0, noise_control),
    }

    editorial_cluster = (
        breakdown["headline"]
        + breakdown["hook"]
        + breakdown["clarity"]
        + breakdown["semantic_density"]
        + breakdown["authority"]
        + breakdown["perceived_value"]
        + breakdown["narrative_tension"]
        + breakdown["novelty"]
        + breakdown["naturalism"]
        + breakdown["anti_genericity"]
        + breakdown["anti_commodity"]
    ) / 11.0

    visual_cluster = (
        breakdown["legibility"]
        + breakdown["contrast"]
        + breakdown["composition"]
        + breakdown["visual_impact"]
    ) / 4.0

    brand_cluster = (
        breakdown["brand_fit"]
        + breakdown["perceived_value"]
        + breakdown["authority"]
    ) / 3.0

    distribution_cluster = (
        breakdown["shareability"]
        + breakdown["saveability"]
    ) / 2.0

    weights = {
        "editorial_text": 0.40,
        "visual_composition": 0.30,
        "brand_perception": 0.20,
        "distribution_potential": 0.10,
    }

    global_score = _r(
        editorial_cluster * weights["editorial_text"]
        + visual_cluster * weights["visual_composition"]
        + brand_cluster * weights["brand_perception"]
        + distribution_cluster * weights["distribution_potential"]
    )
    global_score_100 = int(round(global_score * 10))

    floors = {
        "brand_fit": 8.5,
        "anti_commodity": 8.0,
        "anti_genericity": 8.0,
        "naturalism": 7.5,
        "hook": 7.5,
        "headline": 7.5,
        "legibility": 7.0,
        "composition": 7.0,
        "contrast": 7.0,
        "minimum_quality_score": 7.5,
        "brand_live_global_score": 8.8,
    }

    failed_floors: list[str] = []
    if breakdown["brand_fit"] < floors["brand_fit"]:
        failed_floors.append("brand_fit")
    if breakdown["anti_commodity"] < floors["anti_commodity"]:
        failed_floors.append("anti_commodity")
    if breakdown["anti_genericity"] < floors["anti_genericity"]:
        failed_floors.append("anti_genericity")
    if breakdown["naturalism"] < floors["naturalism"]:
        failed_floors.append("naturalism")
    if breakdown["hook"] < floors["hook"]:
        failed_floors.append("hook")
    if breakdown["headline"] < floors["headline"]:
        failed_floors.append("headline")
    if breakdown["legibility"] < floors["legibility"]:
        failed_floors.append("legibility")
    if breakdown["composition"] < floors["composition"]:
        failed_floors.append("composition")
    if breakdown["contrast"] < floors["contrast"]:
        failed_floors.append("contrast")

    reasons: list[str] = [f"rubric_payload_source={authority_payload_source}"]
    if hardening_considered:
        reasons.append("rubrica recalculada com payload endurecido/visível")
    if failed_floors:
        reasons.append("um ou mais pisos soberanos falharam")
    if global_score < floors["minimum_quality_score"]:
        reasons.append("score global abaixo do piso mínimo de qualidade")
    if global_score < floors["brand_live_global_score"]:
        reasons.append("score global ainda insuficiente para brand_live")

    approved_minimum_quality = global_score >= floors["minimum_quality_score"] and not failed_floors
    eligible_for_brand_live = global_score >= floors["brand_live_global_score"] and not failed_floors

    if approved_minimum_quality and "score global ainda insuficiente para brand_live" not in reasons:
        reasons.append("peça pode seguir para laboratório ou staging, mas não para brand_live")

    post_hardening_scores = {
        "visible_headline_chars": len(headline_text),
        "visible_hook_chars": len(hook_text),
        "visible_body_chars": len(body_text),
        "visible_cta_chars": len(cta_text),
        "visible_support_points_count": len(support_points),
        "hidden_overflow_count": len(hidden_overflow),
        "visual_final_score": visual.get("final_score"),
        "hierarchy_final_score": hierarchy_gate.get("final_score"),
        "brand_dignity_final_score": dignity_score.get("final_score"),
    }

    return RubricEngineResult(
        approved_minimum_quality=approved_minimum_quality,
        eligible_for_brand_live=eligible_for_brand_live,
        global_score=global_score,
        global_score_100=global_score_100,
        breakdown=breakdown,
        floors=floors,
        failed_floors=failed_floors,
        reasons=reasons,
        weights=weights,
        authority_payload_source=authority_payload_source,
        hardening_considered=hardening_considered,
        post_hardening_scores=post_hardening_scores,
    )
