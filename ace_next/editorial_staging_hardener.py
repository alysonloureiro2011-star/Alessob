from __future__ import annotations

import re
from typing import Any


EDITORIAL_STAGING = "editorial_staging"

FORMAT_BUDGETS = {
    "image": {
        "headline_chars": 62,
        "hook_chars": 90,
        "body_chars": 120,
        "cta_chars": 42,
        "support_points_max": 2,
        "support_point_chars": 44,
    },
    "carousel": {
        "headline_chars": 56,
        "hook_chars": 72,
        "body_chars": 90,
        "cta_chars": 36,
        "support_points_max": 2,
        "support_point_chars": 40,
    },
    "story": {
        "headline_chars": 56,
        "hook_chars": 72,
        "body_chars": 90,
        "cta_chars": 32,
        "support_points_max": 1,
        "support_point_chars": 36,
    },
}

STOPWORDS = {
    "para", "como", "mais", "menos", "sobre", "antes", "depois", "muito", "mesmo",
    "porque", "quando", "onde", "essa", "esse", "isso", "com", "sem", "das", "dos",
    "uma", "um", "por", "que", "sua", "seu", "só", "ela", "ele",
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
    kept: list[str] = []
    for sentence in sentences:
        candidate = _clean_text(" ".join(kept + [sentence]))
        if len(candidate) <= budget:
            kept.append(sentence)
        else:
            break

    if kept:
        visible = _clean_text(" ".join(kept))
    else:
        words = text.split()
        compacted: list[str] = []
        for word in words:
            candidate = _clean_text(" ".join(compacted + [word]))
            if len(candidate) <= max(12, budget - 3):
                compacted.append(word)
            else:
                break
        visible = _clean_text(" ".join(compacted))

    if len(visible) > budget:
        visible = visible[: max(0, budget - 1)].rstrip()

    if len(visible) < len(text):
        visible = visible.rstrip(" ,;:-")
        if not visible.endswith(("...", "…")):
            visible = f"{visible}..."
        raw_visible = visible.replace("...", "").replace("…", "").strip()
        hidden = _clean_text(text[len(raw_visible) :])
    else:
        hidden = ""

    return visible, hidden


def _keyword_anchors(*parts: str) -> list[str]:
    tokens: list[str] = []
    for part in parts:
        for token in re.findall(r"[A-Za-zÀ-ÿ0-9]{4,}", _clean_text(part).lower()):
            if token not in STOPWORDS and token not in tokens:
                tokens.append(token)
    return tokens[:8]


def _compact_support_points(points: list[Any], *, max_points: int, point_budget: int) -> tuple[list[str], list[str]]:
    visible: list[str] = []
    hidden: list[str] = []
    for raw in _safe_list(points):
        point = _clean_text(raw)
        if not point:
            continue
        compacted, overflow = _truncate_soft(point, point_budget)
        if len(visible) < max_points:
            visible.append(compacted)
            if overflow:
                hidden.append(overflow)
        else:
            hidden.append(point)
    return visible, hidden


def harden_winner_for_staging(
    creative_plan: dict | None,
    strategic_format: str = "image",
) -> dict[str, Any]:
    plan = _safe_dict(creative_plan)
    fmt = _normalize_format(
        strategic_format
        or plan.get("strategic_target_format")
        or plan.get("publish_format_now")
        or plan.get("format_recommendation")
    )
    budgets = FORMAT_BUDGETS[fmt]

    original_payload = {
        "headline": _clean_text(plan.get("headline")),
        "hook": _clean_text(plan.get("hook")),
        "body": _clean_text(plan.get("body")),
        "cta": _clean_text(plan.get("cta")),
        "support_points": [_clean_text(x) for x in _safe_list(plan.get("support_points")) if _clean_text(x)],
    }

    headline, hidden_headline = _truncate_soft(original_payload["headline"], budgets["headline_chars"])
    hook, hidden_hook = _truncate_soft(original_payload["hook"], budgets["hook_chars"])
    body, hidden_body = _truncate_soft(original_payload["body"], budgets["body_chars"])
    cta, hidden_cta = _truncate_soft(original_payload["cta"], budgets["cta_chars"])
    support_points, hidden_support = _compact_support_points(
        original_payload["support_points"],
        max_points=budgets["support_points_max"],
        point_budget=budgets["support_point_chars"],
    )

    hidden_overflow_for_caption = [
        item for item in [hidden_headline, hidden_hook, hidden_body, hidden_cta, *hidden_support] if _clean_text(item)
    ]

    hardened_payload = {
        **plan,
        "headline": headline,
        "hook": hook,
        "body": body,
        "cta": cta,
        "support_points": support_points,
        "strategic_target_format": fmt,
        "publish_format_now": fmt,
        "format_recommendation": fmt,
        "hardening_applied": True,
        "hardening_target_state": EDITORIAL_STAGING,
    }

    semantic_anchors_preserved = _keyword_anchors(
        original_payload["headline"],
        original_payload["hook"],
        original_payload["body"],
        " ".join(original_payload["support_points"]),
    )

    applied_rules = [
        f"headline<={budgets['headline_chars']}",
        f"hook<={budgets['hook_chars']}",
        f"body<={budgets['body_chars']}",
        f"cta<={budgets['cta_chars']}",
        f"support_points<={budgets['support_points_max']}",
        f"support_point_chars<={budgets['support_point_chars']}",
        "overflow_movido_para_caption",
    ]

    return {
        "ok": True,
        "strategic_format": fmt,
        "original_payload": original_payload,
        "hardened_payload": hardened_payload,
        "hidden_overflow_for_caption": hidden_overflow_for_caption,
        "hardening_report": {
            "headline_compacted": headline != original_payload["headline"],
            "hook_compacted": hook != original_payload["hook"],
            "body_compacted": body != original_payload["body"],
            "cta_compacted": cta != original_payload["cta"],
            "support_points_compacted": support_points != original_payload["support_points"],
            "hidden_overflow_count": len(hidden_overflow_for_caption),
        },
        "applied_rules": applied_rules,
        "semantic_anchors_preserved": semantic_anchors_preserved,
        "moved_to_caption": hidden_overflow_for_caption,
        "target_state": EDITORIAL_STAGING,
    }
