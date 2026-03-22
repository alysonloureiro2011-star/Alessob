from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SafeZones:
    outer_margin: int
    header_height: int
    footer_height: int
    content_top: int
    content_bottom: int
    content_left: int
    content_right: int
    support_gap: int
    headline_gap: int
    hook_gap: int
    body_gap: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VisualThresholds:
    minimum_visual_score: int
    minimum_legibility: float
    minimum_contrast: float
    minimum_composition: float
    minimum_brand_fit: float
    minimum_perceived_value: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VisualContract:
    canvas_width: int
    canvas_height: int
    aspect_ratio: str
    mobile_first: bool
    safe_zones: SafeZones
    max_headline_lines: int
    max_hook_lines: int
    max_body_lines: int
    max_support_points: int
    max_support_chars: int
    max_cta_lines: int
    density_target: str
    hierarchy_model: list[str]
    thresholds: VisualThresholds
    headline_chars_budget: int
    hook_chars_budget: int
    body_chars_budget: int
    cta_chars_budget: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "aspect_ratio": self.aspect_ratio,
            "mobile_first": self.mobile_first,
            "safe_zones": self.safe_zones.to_dict(),
            "max_headline_lines": self.max_headline_lines,
            "max_hook_lines": self.max_hook_lines,
            "max_body_lines": self.max_body_lines,
            "max_support_points": self.max_support_points,
            "max_support_chars": self.max_support_chars,
            "max_cta_lines": self.max_cta_lines,
            "density_target": self.density_target,
            "hierarchy_model": list(self.hierarchy_model),
            "thresholds": self.thresholds.to_dict(),
            "headline_chars_budget": self.headline_chars_budget,
            "hook_chars_budget": self.hook_chars_budget,
            "body_chars_budget": self.body_chars_budget,
            "cta_chars_budget": self.cta_chars_budget,
        }


def _clean(value: str) -> str:
    return " ".join((value or "").strip().split())


def _trim_words(text: str, limit: int) -> str:
    text = _clean(text)
    if len(text) <= limit:
        return text
    clipped = text[:limit].rsplit(" ", 1)[0].strip()
    if clipped:
        return f"{clipped}..."
    return f"{text[:limit].strip()}..."


def _split_fragments(text: str) -> list[str]:
    if not text:
        return []
    normalized = (
        text.replace("?", ".")
        .replace("!", ".")
        .replace(";", ".")
        .replace(":", ".")
        .replace("—", ".")
    )
    return [part.strip(" -") for part in normalized.split(".") if part.strip(" -")]


def _compact_sentence(text: str, limit: int) -> str:
    text = _clean(text)
    if not text:
        return ""
    parts = _split_fragments(text)
    if parts:
        for part in parts:
            if len(part) >= 24:
                return _trim_words(part, limit)
        return _trim_words(parts[0], limit)
    return _trim_words(text, limit)


def prepare_display_copy(plan: dict[str, Any], contract: VisualContract) -> dict[str, Any]:
    headline = _compact_sentence(str(plan.get("headline") or ""), contract.headline_chars_budget)
    hook = _compact_sentence(str(plan.get("hook") or ""), contract.hook_chars_budget)
    body = _compact_sentence(str(plan.get("body") or ""), contract.body_chars_budget)

    support_points: list[str] = []
    for point in (plan.get("support_points") or [])[: contract.max_support_points]:
        compact = _compact_sentence(str(point), contract.max_support_chars)
        if compact:
            support_points.append(compact)

    cta = _compact_sentence(str(plan.get("cta") or ""), contract.cta_chars_budget)
    if not cta:
        cta = "Salve e releia depois."

    return {
        "headline": headline,
        "hook": hook,
        "body": body,
        "support_points": support_points,
        "cta": cta,
    }


def build_visual_contract(plan: dict[str, Any]) -> VisualContract:
    safe = SafeZones(
        outer_margin=78,
        header_height=136,
        footer_height=120,
        content_top=198,
        content_bottom=1168,
        content_left=98,
        content_right=982,
        support_gap=16,
        headline_gap=16,
        hook_gap=18,
        body_gap=22,
    )
    thresholds = VisualThresholds(
        minimum_visual_score=75,
        minimum_legibility=7.0,
        minimum_contrast=7.0,
        minimum_composition=7.0,
        minimum_brand_fit=8.0,
        minimum_perceived_value=7.5,
    )
    return VisualContract(
        canvas_width=1080,
        canvas_height=1350,
        aspect_ratio="4:5",
        mobile_first=True,
        safe_zones=safe,
        max_headline_lines=3,
        max_hook_lines=2,
        max_body_lines=3,
        max_support_points=2,
        max_support_chars=58,
        max_cta_lines=1,
        density_target="mobile_clean",
        hierarchy_model=[
            "eyebrow",
            "headline",
            "hook",
            "body",
            "support_points",
            "cta",
            "watermark",
        ],
        thresholds=thresholds,
        headline_chars_budget=66,
        hook_chars_budget=108,
        body_chars_budget=158,
        cta_chars_budget=52,
    )
