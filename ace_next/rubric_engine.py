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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _n(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _r(value: float) -> float:
    return round(float(value), 2)


def evaluate_rubric_engine(
    *,
    plan: dict[str, Any],
    editorial_qa: dict[str, Any],
    visual_qa: dict[str, Any],
    perceptual_qa: dict[str, Any],
) -> RubricEngineResult:
    editorial = dict(editorial_qa.get("breakdown") or {})
    perceptual = dict(perceptual_qa.get("breakdown") or {})

    headline = _n(editorial.get("headline"))
    hook = _n(editorial.get("hook"))
    clarity = _n(editorial.get("clarity"))
    semantic_density = _n(editorial.get("semantic_density"))
    authority = _n(editorial.get("authority"))
    perceived_value_editorial = _n(editorial.get("perceived_value"))
    narrative_tension = _n(editorial.get("narrative_tension"))
    naturalism = _n(editorial.get("naturalism"))
    anti_genericity = _n(editorial.get("anti_generic"))
    anti_commodity = _n(editorial.get("anti_commodity"))

    legibility = _n(perceptual.get("legibility"))
    contrast = _n(perceptual.get("contrast"))
    composition = _n(perceptual.get("composition"))
    brand_fit_visual = _n(perceptual.get("brand_fit_visual"))
    perceived_value_visual = _n(perceptual.get("perceived_value_visual"))
    noise_control = _n(perceptual.get("noise_control"))

    novelty = _r((anti_genericity + semantic_density) / 2.0)
    brand_fit = _r((brand_fit_visual + anti_genericity + anti_commodity) / 3.0)
    perceived_value = _r((perceived_value_editorial + perceived_value_visual) / 2.0)
    visual_impact = _r((contrast + composition + brand_fit_visual) / 3.0)
    shareability = _r((hook + perceived_value + brand_fit) / 3.0)
    saveability = _r((clarity + semantic_density + perceived_value) / 3.0)

    breakdown = {
        "headline": _r(headline),
        "hook": _r(hook),
        "clarity": _r(clarity),
        "semantic_density": _r(semantic_density),
        "authority": _r(authority),
        "perceived_value": _r(perceived_value),
        "narrative_tension": _r(narrative_tension),
        "novelty": _r(novelty),
        "naturalism": _r(naturalism),
        "anti_genericity": _r(anti_genericity),
        "anti_commodity": _r(anti_commodity),
        "legibility": _r(legibility),
        "contrast": _r(contrast),
        "composition": _r(composition),
        "visual_impact": _r(visual_impact),
        "shareability": _r(shareability),
        "saveability": _r(saveability),
        "brand_fit": _r(brand_fit),
        "noise_control": _r(noise_control),
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

    reasons: list[str] = []
    if failed_floors:
        reasons.append("um ou mais pisos soberanos falharam")
    if global_score < floors["minimum_quality_score"]:
        reasons.append("score global abaixo do piso mínimo de qualidade")
    if global_score < floors["brand_live_global_score"]:
        reasons.append("score global ainda insuficiente para brand_live")

    approved_minimum_quality = global_score >= floors["minimum_quality_score"] and not failed_floors
    eligible_for_brand_live = global_score >= floors["brand_live_global_score"] and not failed_floors

    if approved_minimum_quality and not reasons:
        reasons.append("rubrica dentro do mínimo aceitável")
    elif approved_minimum_quality and "score global ainda insuficiente para brand_live" not in reasons:
        reasons.append("peça pode seguir para laboratório ou staging, mas não para brand_live")

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
    )
