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
    parts = re.split(r"(?<=[\.\!\?\:\;])\s+", cleaned)
    return [_clean_text(part) for part in parts if _clean_text(part)]


def _trim_punctuation(text: str) -> str:
    return _clean_text(text).rstrip(" ,;:-")


def _soft_replace(text: str, patterns: dict[str, str]) -> tuple[str, bool]:
    cleaned = _clean_text(text)
    changed = False
    for pattern, replacement in patterns.items():
        updated = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        if updated != cleaned:
            changed = True
            cleaned = updated
    cleaned = _clean_text(cleaned)
    return cleaned, changed


def _decommodity_text(text: str) -> tuple[str, bool]:
    replacements = {
        r"\bningu[eé]m te conta\b": "quase ninguém explica com clareza",
        r"\bisso muda tudo\b": "isso muda a leitura do problema",
        r"\bmude sua vida\b": "mude sua leitura do problema",
        r"\bsegredo\b": "ponto central",
        r"\bacredite em voc[eê]\b": "observe o critério",
        r"\bvoc[eê] precisa\b": "vale observar",
    }
    return _soft_replace(text, replacements)


def _elevate_cta(cta: str, fmt: str) -> tuple[str, bool]:
    cleaned = _clean_text(cta)
    changed = False

    low_signal_patterns = {
        r"\bcomente aqui\b": "salve e releia com calma",
        r"\bcorre\b": "guarde isso antes de decidir",
        r"\bchama na dm\b": "envie para quem precisa ler isso",
        r"\bcompra agora\b": "aplique isso com critério",
        r"\bclica no link agora\b": "salve isso para consultar depois",
        r"\bn[aã]o perde\b": "não ignore esse critério",
    }
    cleaned, low_signal_changed = _soft_replace(cleaned, low_signal_patterns)
    changed = changed or low_signal_changed

    if not cleaned:
        changed = True
        if fmt == "story":
            cleaned = "Salve e releia."
        elif fmt == "carousel":
            cleaned = "Salve e envie para quem precisa."
        else:
            cleaned = "Salve e releia antes de decidir."

    cleaned = _trim_punctuation(cleaned)
    if cleaned and not re.search(r"[.!?]$", cleaned):
        cleaned = f"{cleaned}."
    return cleaned, changed


def _headline_fallback(plan: dict[str, Any]) -> str:
    candidates = [
        plan.get("headline"),
        plan.get("angle"),
        plan.get("topic_seed"),
        plan.get("problem"),
        plan.get("insight"),
    ]
    for item in candidates:
        text = _clean_text(item)
        if text:
            return text
    return ""


def _hook_fallback(plan: dict[str, Any]) -> str:
    candidates = [
        plan.get("hook"),
        plan.get("problem"),
        plan.get("angle"),
        plan.get("insight"),
        plan.get("payoff"),
    ]
    for item in candidates:
        text = _clean_text(item)
        if text:
            return text
    return ""


def _body_fallback(plan: dict[str, Any]) -> str:
    candidates = [
        plan.get("body"),
        plan.get("insight"),
        plan.get("payoff"),
        plan.get("problem"),
    ]
    for item in candidates:
        text = _clean_text(item)
        if text:
            return text
    return ""


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

    hidden = ""
    if len(visible) < len(text):
        visible = _trim_punctuation(visible)
        if not visible.endswith(("...", "…")):
            visible = f"{visible}..."
        raw_visible = visible.replace("...", "").replace("…", "").strip()
        hidden = _clean_text(text[len(raw_visible):])

    return visible, hidden


def _keyword_anchors(*parts: str) -> list[str]:
    tokens: list[str] = []
    for part in parts:
        for token in re.findall(r"[A-Za-zÀ-ÿ0-9]{4,}", _clean_text(part).lower()):
            if token not in STOPWORDS and token not in tokens:
                tokens.append(token)
    return tokens[:8]


def _compact_support_points(
    points: list[Any],
    *,
    max_points: int,
    point_budget: int,
) -> tuple[list[str], list[str], bool]:
    visible: list[str] = []
    hidden: list[str] = []
    compacted = False

    for raw in _safe_list(points):
        point = _clean_text(raw)
        if not point:
            continue

        point, changed = _decommodity_text(point)
        compacted = compacted or changed

        compacted_point, overflow = _truncate_soft(point, point_budget)
        compacted = compacted or compacted_point != point

        if len(visible) < max_points:
            visible.append(compacted_point)
            if overflow:
                hidden.append(overflow)
        else:
            hidden.append(point)
            compacted = True

    return visible, hidden, compacted


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
        "headline": _clean_text(_headline_fallback(plan)),
        "hook": _clean_text(_hook_fallback(plan)),
        "body": _clean_text(_body_fallback(plan)),
        "cta": _clean_text(plan.get("cta")),
        "support_points": [_clean_text(x) for x in _safe_list(plan.get("support_points")) if _clean_text(x)],
    }

    cleaned_headline, headline_decommodified = _decommodity_text(original_payload["headline"])
    cleaned_hook, hook_decommodified = _decommodity_text(original_payload["hook"])
    cleaned_body, body_decommodified = _decommodity_text(original_payload["body"])
    cleaned_cta, cta_rewritten = _elevate_cta(original_payload["cta"], fmt)

    headline, hidden_headline = _truncate_soft(cleaned_headline, budgets["headline_chars"])
    hook, hidden_hook = _truncate_soft(cleaned_hook, budgets["hook_chars"])
    body, hidden_body = _truncate_soft(cleaned_body, budgets["body_chars"])
    cta, hidden_cta = _truncate_soft(cleaned_cta, budgets["cta_chars"])

    support_points, hidden_support, support_points_compacted = _compact_support_points(
        original_payload["support_points"],
        max_points=budgets["support_points_max"],
        point_budget=budgets["support_point_chars"],
    )

    hidden_overflow_for_caption = [
        item
        for item in [hidden_headline, hidden_hook, hidden_body, hidden_cta, *hidden_support]
        if _clean_text(item)
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
        "hidden_overflow_for_caption": hidden_overflow_for_caption,
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
        "cta_reescrita_para_padrao_soberano",
        "frases_commodity_suavizadas",
    ]

    hardening_report = {
        "headline_compacted": headline != original_payload["headline"],
        "hook_compacted": hook != original_payload["hook"],
        "body_compacted": body != original_payload["body"],
        "cta_compacted": cta != original_payload["cta"],
        "support_points_compacted": support_points_compacted or support_points != original_payload["support_points"],
        "headline_decommodified": headline_decommodified,
        "hook_decommodified": hook_decommodified,
        "body_decommodified": body_decommodified,
        "cta_rewritten": cta_rewritten,
        "hidden_overflow_count": len(hidden_overflow_for_caption),
    }

    return {
        "ok": True,
        "strategic_format": fmt,
        "original_payload": original_payload,
        "hardened_payload": hardened_payload,
        "hidden_overflow_for_caption": hidden_overflow_for_caption,
        "hardening_report": hardening_report,
        "applied_rules": applied_rules,
        "semantic_anchors_preserved": semantic_anchors_preserved,
        "moved_to_caption": hidden_overflow_for_caption,
        "target_state": EDITORIAL_STAGING,
    }
