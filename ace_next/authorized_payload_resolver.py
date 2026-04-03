from __future__ import annotations

from typing import Any, Mapping

_DEFAULT_BUDGET = {
    "image": {"headline": 62, "hook": 90, "body": 120, "cta": 42, "support_points_max": 2, "support_point_chars": 44},
    "carousel": {"headline": 72, "hook": 110, "body": 170, "cta": 48, "support_points_max": 3, "support_point_chars": 56},
    "reel": {"headline": 72, "hook": 110, "body": 140, "cta": 42, "support_points_max": 2, "support_point_chars": 44},
    "story": {"headline": 54, "hook": 72, "body": 90, "cta": 32, "support_points_max": 1, "support_point_chars": 36},
}

_FIELDS = ("headline", "hook", "body", "cta", "caption")


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _ellipsis(text: str, limit: int) -> str:
    text = _clean_text(text)
    if len(text) <= limit:
        return text
    short = text[: max(0, limit - 3)].rstrip(" ,.;:-")
    return f"{short}..." if short else text[:limit]


def _normalize_support_points(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _clean_text(item)
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        items.append(text)
    return items


def _payload_from(source: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _safe_dict(source)
    payload = {field: _clean_text(data.get(field)) for field in _FIELDS}
    payload["support_points"] = _normalize_support_points(data.get("support_points"))
    payload["format"] = _clean_text(data.get("format")).lower()
    payload["template_id"] = _clean_text(data.get("template_id"))
    payload["capture_mode"] = _clean_text(data.get("capture_mode"))
    return payload


def resolve_authorized_payload(
    raw_plan: Mapping[str, Any] | None,
    *,
    hardened_payload: Mapping[str, Any] | None = None,
    render_payload_used: Mapping[str, Any] | None = None,
    strategic_format: str | None = None,
    template_id: str | None = None,
    capture_mode: str = "safe",
) -> dict[str, Any]:
    raw_payload = _payload_from(raw_plan)
    hardened = _payload_from(hardened_payload)
    rendered = _payload_from(render_payload_used)

    resolved_format = _clean_text(strategic_format or rendered.get("format") or hardened.get("format") or raw_payload.get("format") or "image").lower()
    budget = _DEFAULT_BUDGET.get(resolved_format, _DEFAULT_BUDGET["image"])

    merged: dict[str, Any] = {}
    for source in (raw_payload, hardened, rendered):
        for field in _FIELDS:
            if source.get(field):
                merged[field] = source[field]
        if source.get("support_points"):
            merged["support_points"] = source["support_points"]
        if source.get("template_id"):
            merged["template_id"] = source["template_id"]
        if source.get("capture_mode"):
            merged["capture_mode"] = source["capture_mode"]

    support_points = _normalize_support_points(merged.get("support_points"))
    support_points = support_points[: budget["support_points_max"]]
    support_points = [_ellipsis(item, budget["support_point_chars"]) for item in support_points]

    authorized_payload = {
        "headline": _ellipsis(merged.get("headline", ""), budget["headline"]),
        "hook": _ellipsis(merged.get("hook", ""), budget["hook"]),
        "body": _ellipsis(merged.get("body", ""), budget["body"]),
        "cta": _ellipsis(merged.get("cta", ""), budget["cta"]),
        "caption": _clean_text(merged.get("caption", "")),
        "support_points": support_points,
        "format": resolved_format,
        "template_id": _clean_text(template_id or merged.get("template_id") or rendered.get("template_id") or ""),
        "capture_mode": _clean_text(merged.get("capture_mode") or capture_mode or "safe"),
    }

    changed_fields: list[str] = []
    for field in ("headline", "hook", "body", "cta"):
        if _clean_text(merged.get(field, "")) != authorized_payload[field]:
            changed_fields.append(field)
    if _normalize_support_points(merged.get("support_points")) != support_points:
        changed_fields.append("support_points")

    source_used = "raw_plan"
    if hardened_payload:
        source_used = "hardened_payload"
    if render_payload_used:
        source_used = "render_payload_used"

    return {
        "ok": True,
        "resolver_version": "authorized_payload_resolver_v1",
        "authorized_source": source_used,
        "strategic_format": resolved_format,
        "budget": budget,
        "raw_payload": raw_payload,
        "hardened_payload": hardened,
        "render_payload_used": rendered,
        "authorized_payload": authorized_payload,
        "changed_fields": changed_fields,
        "changed_fields_count": len(changed_fields),
        "hardening_report": {
            "headline_compacted": "headline" in changed_fields,
            "hook_compacted": "hook" in changed_fields,
            "body_compacted": "body" in changed_fields,
            "cta_compacted": "cta" in changed_fields,
            "support_points_compacted": "support_points" in changed_fields,
        },
    }
