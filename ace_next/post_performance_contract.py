from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any


def _stable_id(*parts: str) -> str:
    base = "||".join(parts)
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]
    return f"plr_{digest}"


def _derive_evidence_bridge_state(
    *,
    has_receipt: bool,
    has_media_id: bool,
    has_permalink: bool,
) -> str:
    if has_receipt and has_media_id and has_permalink:
        return "receipt_with_permalink"
    if has_receipt and has_media_id:
        return "receipt_with_media_id"
    if has_receipt:
        return "receipt_linked"
    return "no_receipt"


def build_post_performance_contract(
    *,
    trend: str,
    operational_state: str,
    brand_live_allowed: bool,
    creative_plan: dict[str, Any],
    editorial_qa: dict[str, Any],
    visual_qa: dict[str, Any],
    publish_result: dict[str, Any] | None,
    publication_authorization_gate: dict[str, Any],
) -> dict[str, Any]:
    now = datetime.utcnow().isoformat()
    receipt = dict(publish_result or {})

    publish_status = str(receipt.get("publish_status") or "not_executed")
    created_at = str(receipt.get("created_at") or now)
    creation_id = str(receipt.get("creation_id") or "")
    receipt_id = str(receipt.get("receipt_id") or "")
    media_id = str(receipt.get("media_id") or "")
    permalink = str(receipt.get("permalink") or "")
    content_type = receipt.get("content_type")
    style = receipt.get("style")

    has_receipt = bool(receipt_id)
    has_media_id = bool(media_id)
    has_permalink = bool(permalink)

    record_id = _stable_id(
        trend.strip(),
        created_at,
        operational_state,
        creation_id,
        media_id,
        permalink,
    )

    publish_receipt_bridge = {
        "publish_status": publish_status,
        "receipt_id": receipt_id or None,
        "media_id": media_id or None,
        "permalink": permalink or None,
        "content_type": content_type,
        "style": style,
        "operational_state": operational_state,
        "created_at": created_at,
    }

    evidence_bridge = {
        "has_real_receipt": has_receipt,
        "has_media_id": has_media_id,
        "has_permalink": has_permalink,
        "latest_real_metrics_status": None,
        "latest_source_status": None,
        "evidence_bridge_state": _derive_evidence_bridge_state(
            has_receipt=has_receipt,
            has_media_id=has_media_id,
            has_permalink=has_permalink,
        ),
    }

    post_performance = {
        "status": "not_collected_yet",
        "source": "awaiting_real_metrics",
        "metrics": {},
        "notes": [
            "registro criado sem métricas falsas",
            "nenhuma política editorial/visual/marca foi alterada automaticamente",
        ],
    }

    return {
        "record_id": record_id,
        "created_at": now,
        "operational_state": operational_state,
        "brand_live_allowed": bool(brand_live_allowed),
        "trend": trend,
        "publish_status": publish_status,
        "evidence_status": "receipt_linked" if has_receipt else "no_receipt",
        "creative_plan": creative_plan,
        "editorial_qa": editorial_qa,
        "visual_qa": visual_qa,
        "publication_authorization_gate": publication_authorization_gate,
        "receipt": receipt,
        "publish_result": receipt,
        "post_performance": post_performance,
        "publish_receipt_bridge": publish_receipt_bridge,
        "evidence_bridge": evidence_bridge,
        "resonance_engine": {},
        "reward_prediction": {},
        "sampler_decision": {},
        "decision_core_summary": {},
        "evidence_interpreter": {},
        "experiment_resolution": {},
        "recommendation_engine": {},
        "wave10_summary": {},
        "wave11_summary": {},
        "variant_context": {
            "headline": creative_plan.get("headline"),
            "hook": creative_plan.get("hook"),
            "operational_state": operational_state,
            "trend": trend,
            "content_type": content_type,
            "style": style,
        },
        "resolution_context": {
            "evidence_state": None,
            "evidence_strength": None,
            "resolution_state": None,
            "recommended_action": None,
        },
        "linkage": {
            "creation_id": creation_id or None,
            "receipt_id": receipt_id or None,
            "media_id": media_id or None,
            "permalink": permalink or None,
            "style": style,
            "content_type": content_type,
        },
        "insight_control": {
            "can_record": True,
            "can_suggest": True,
            "can_change_policy": False,
            "can_authorize_brand_live": False,
        },
    }
