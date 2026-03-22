from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TemplateBlock:
    name: str
    x: int
    y: int
    width: int
    height: int
    priority: int
    alignment: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VisualTemplate:
    template_id: str
    display_name: str
    use_case: str
    density: str
    block_order: list[str]
    blocks: dict[str, TemplateBlock]

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "display_name": self.display_name,
            "use_case": self.use_case,
            "density": self.density,
            "block_order": list(self.block_order),
            "blocks": {name: block.to_dict() for name, block in self.blocks.items()},
        }


def build_signal_card_clean_template() -> VisualTemplate:
    blocks = {
        "eyebrow": TemplateBlock("eyebrow", 132, 244, 280, 40, 1, "left"),
        "headline": TemplateBlock("headline", 132, 314, 816, 196, 2, "left"),
        "hook": TemplateBlock("hook", 132, 538, 816, 96, 3, "left"),
        "body": TemplateBlock("body", 132, 666, 816, 132, 4, "left"),
        "support": TemplateBlock("support", 132, 832, 816, 118, 5, "left"),
        "cta": TemplateBlock("cta", 132, 1000, 816, 62, 6, "left"),
    }
    return VisualTemplate(
        template_id="signal_card_clean_v3",
        display_name="Signal Card Clean V3",
        use_case="card principal mobile-first com menor densidade",
        density="mobile_clean",
        block_order=["eyebrow", "headline", "hook", "body", "support", "cta"],
        blocks=blocks,
    )


def build_contrast_card_clean_template() -> VisualTemplate:
    blocks = {
        "eyebrow": TemplateBlock("eyebrow", 132, 244, 280, 40, 1, "left"),
        "headline": TemplateBlock("headline", 132, 308, 816, 180, 2, "left"),
        "hook": TemplateBlock("hook", 132, 506, 816, 92, 3, "left"),
        "body": TemplateBlock("body", 132, 630, 816, 120, 4, "left"),
        "support": TemplateBlock("support", 132, 786, 816, 112, 5, "left"),
        "cta": TemplateBlock("cta", 132, 958, 816, 58, 6, "left"),
    }
    return VisualTemplate(
        template_id="contrast_card_clean_v2",
        display_name="Contrast Card Clean V2",
        use_case="headline forte com corpo compacto e mais respiro",
        density="mobile_clean",
        block_order=["eyebrow", "headline", "hook", "body", "support", "cta"],
        blocks=blocks,
    )


def resolve_visual_template(plan: dict[str, Any]) -> VisualTemplate:
    headline = str(plan.get("headline") or "")
    hook = str(plan.get("hook") or "")

    if len(headline) > 78 or len(hook) > 118:
        return build_signal_card_clean_template()
    return build_contrast_card_clean_template()
