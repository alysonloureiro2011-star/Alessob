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


def _base_blocks() -> dict[str, TemplateBlock]:
    return {
        "eyebrow": TemplateBlock("eyebrow", 118, 282, 260, 44, 1, "left"),
        "headline": TemplateBlock("headline", 118, 352, 844, 236, 2, "left"),
        "hook": TemplateBlock("hook", 118, 606, 844, 128, 3, "left"),
        "body": TemplateBlock("body", 118, 752, 844, 190, 4, "left"),
        "support": TemplateBlock("support", 118, 964, 844, 132, 5, "left"),
        "cta": TemplateBlock("cta", 118, 1120, 844, 76, 6, "left"),
    }


def build_signal_card_template() -> VisualTemplate:
    blocks = _base_blocks()
    return VisualTemplate(
        template_id="signal_card_v2",
        display_name="Signal Card V2",
        use_case="insight editorial principal",
        density="controlled",
        block_order=["eyebrow", "headline", "hook", "body", "support", "cta"],
        blocks=blocks,
    )


def build_contrast_card_template() -> VisualTemplate:
    blocks = _base_blocks()
    blocks["headline"] = TemplateBlock("headline", 118, 346, 844, 220, 2, "left")
    blocks["body"] = TemplateBlock("body", 118, 744, 844, 170, 4, "left")
    return VisualTemplate(
        template_id="contrast_card_v1",
        display_name="Contrast Card V1",
        use_case="headline mais agressiva com corpo mais enxuto",
        density="controlled",
        block_order=["eyebrow", "headline", "hook", "body", "support", "cta"],
        blocks=blocks,
    )


def resolve_visual_template(plan: dict[str, Any]) -> VisualTemplate:
    headline = str(plan.get("headline") or "")
    if len(headline) > 84:
        return build_signal_card_template()
    return build_contrast_card_template()
