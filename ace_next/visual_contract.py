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
        }


def build_visual_contract(plan: dict[str, Any]) -> VisualContract:
    headline = str(plan.get("headline") or "")
    body = str(plan.get("body") or "")
    support_points = plan.get("support_points") or []

    headline_lines = 3 if len(headline) <= 92 else 4
    body_lines = 4 if len(body) <= 260 else 5
    support_limit = 3 if len(support_points) >= 3 else max(1, len(support_points) or 1)

    safe = SafeZones(
        outer_margin=68,
        header_height=154,
        footer_height=136,
        content_top=224,
        content_bottom=1188,
        content_left=94,
        content_right=986,
        support_gap=18,
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
        max_headline_lines=headline_lines,
        max_hook_lines=3,
        max_body_lines=body_lines,
        max_support_points=support_limit,
        max_support_chars=76,
        max_cta_lines=2,
        density_target="controlled",
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
    )
