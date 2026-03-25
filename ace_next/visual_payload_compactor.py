from __future__ import annotations

import re
from typing import Any


FORMAT_RULES = {
    "image": {
        "headline_chars": 84,
        "hook_chars": 120,
        "body_chars": 210,
        "cta_chars": 48,
        "support_points_max": 2,
        "support_point_chars": 72,
    },
    "carousel": {
        "headline_chars": 72,
        "hook_chars": 100,
        "body_chars": 160,
        "cta_chars": 44,
        "support_points_max": 2,
        "support_point_chars": 68,
    },
    "story": {
        "headline_chars": 62,
        "hook_chars": 90,
        "body_chars": 120,
        "cta_chars": 42,
        "support_points_max": 1,
        "support_point_chars": 62,
    },
}

DEFAULT_CTA = {
    "image": "Salve para revisar antes da próxima decisão.",
    "carousel": "Deslize e salve a sequência.",
    "story": "Continue essa sequência no próximo story.",
}


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_format(value: Any) -> str:
    normalized = _clean_text(value).lower()
    if normalized in {"story", "stories"}:
        return "story"
    if normalized in {"carousel", "image"}:
        return normalized
    return "image"


def _split_sentences(text: str) -> list[str]:
    cleaned = _clean_text(text)
    if not cleaned:
        return []
    parts = re.split(r"(?<=[\.\!\?\:;])\s+", cleaned)
    return [_clean_text(part) for part in parts if _clean_text(part)]


def _truncate_soft(text: str, budget: int) -> tuple[str, str]:
    text = _clean_text(text)
    if not text:
        return "", ""
    if len(text) <= budget:
        return text, ""

    sentences = _split_sentences(text)
    built: list[str] = []
    for sentence in sentences:
        candidate = _clean_text(" ".join(built + [sentence]))
        if len(candidate) <= budget:
            built.append(sentence)
        else:
            break

    if built:
        visible = _clean_text(" ".join(built))
    else:
        words = text.split()
        kept: list[str] = []
        for word in words:
            candidate = _clean_text(" ".join(kept + [word]))
            if len(candidate) <= max(12, budget - 3):
                kept.append(word)
            else:
                break
        visible = _clean_text(" ".join(kept))

    if len(visible) > budget:
        visible = visible[: max(0, budget - 1)].rstrip()

    if len(visible) < len(text):
        visible = visible.rstrip(" ,;:-")
        if not visible.endswith(("...", "…")):
            visible = f"{visible}..."
        hidden = _clean_text(text[len(visible.replace("...", "").replace("…", "")) :])
    else:
        hidden = ""

    if not hidden and len(text) > len(visible):
        raw_visible = visible.replace("...", "").replace("…", "").strip()
        hidden = _clean_text(text[len(raw_visible) :])

    return visible, hidden


def _dedupe_keep_order(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = _clean_text(item)
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def _compact_support_points(points: list[Any], *, max_points: int, point_chars: int) -> tuple[list[str], list[str]]:
    visible: list[str] = []
    hidden: list[str] = []

    for raw in _safe_list(points):
        point = _clean_text(raw)
        if not point:
            continue
        compacted, overflow = _truncate_soft(point, point_chars)
        if len(visible) < max_points:
            visible.append(compacted)
            if overflow:
                hidden.append(overflow)
        else:
            hidden.append(point)

    return _dedupe_keep_order(visible), _dedupe_keep_order(hidden)


def compact_visual_payload(
    creative_plan: dict | None,
    strategic_format: str | None = None,
) -> dict[str, Any]:
    plan = _safe_dict(creative_plan)
    fmt = _normalize_format(
        strategic_format
        or plan.get("strategic_target_format")
        or plan.get("publish_format_now")
        or plan.get("format_recommendation")
    )
    rules = FORMAT_RULES[fmt]

    raw_headline = _clean_text(plan.get("headline"))
    raw_hook = _clean_text(plan.get("hook"))
    raw_body = _clean_text(plan.get("body"))
    raw_cta = _clean_text(plan.get("cta")) or DEFAULT_CTA[fmt]
    raw_support_points = _safe_list(plan.get("support_points"))

    headline, headline_hidden = _truncate_soft(raw_headline, rules["headline_chars"])
    hook, hook_hidden = _truncate_soft(raw_hook, rules["hook_chars"])
    body, body_hidden = _truncate_soft(raw_body, rules["body_chars"])
    cta, cta_hidden = _truncate_soft(raw_cta, rules["cta_chars"])
    support_points, support_hidden = _compact_support_points(
        raw_support_points,
        max_points=rules["support_points_max"],
        point_chars=rules["support_point_chars"],
    )

    hidden_overflow_for_caption = _dedupe_keep_order(
        [
            headline_hidden,
            hook_hidden,
            body_hidden,
            cta_hidden,
            *support_hidden,
        ]
    )

    compacted = {
        "ok": True,
        "format": fmt,
        "headline": headline or raw_headline[: rules["headline_chars"]],
        "hook": hook,
        "body": body,
        "cta": cta,
        "support_points": support_points,
        "hidden_overflow_for_caption": hidden_overflow_for_caption,
        "compaction_report": {
            "format": fmt,
            "headline_chars_budget": rules["headline_chars"],
            "hook_chars_budget": rules["hook_chars"],
            "body_chars_budget": rules["body_chars"],
            "cta_chars_budget": rules["cta_chars"],
            "support_points_max": rules["support_points_max"],
            "headline_compacted": headline != raw_headline,
            "hook_compacted": hook != raw_hook,
            "body_compacted": body != raw_body,
            "cta_compacted": cta != raw_cta,
            "support_points_compacted": len(support_points) != len([x for x in raw_support_points if _clean_text(x)]),
            "hidden_overflow_count": len(hidden_overflow_for_caption),
        },
        "series_name": _clean_text(plan.get("series_name") or "Liberta a Verdade"),
        "topic_seed": _clean_text(plan.get("topic_seed") or raw_headline or "clareza, disciplina e direção"),
        "publish_style": _clean_text(plan.get("publish_style") or "premium_dark_editorial"),
        "brand_persona": _clean_text(plan.get("brand_persona") or "editorial_soberano"),
        "angle": _clean_text(plan.get("angle")),
        "eyebrow": _clean_text(plan.get("eyebrow") or plan.get("angle") or plan.get("topic_seed")),
        "watermark": _clean_text(plan.get("watermark") or plan.get("series_name") or "Liberta a Verdade"),
        "footer_note": _clean_text(plan.get("footer_note") or cta),
        "strategic_target_format": fmt,
        "publish_format_now": fmt,
        "format_recommendation": fmt,
    }

    for key in ("first_comment", "caption", "narrative_tension", "payoff", "sequel_potential", "problem", "insight"):
        if key in plan:
            compacted[key] = plan.get(key)

    return compacted
