from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any


def _stable_id(*parts: str) -> str:
    base = "||".join(parts)
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]
    return f"plr_{digest}"


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
    media_id = str(receipt.get("media_id") or "")
    permalink = str(receipt.get("permalink") or "")
    record_id = _stable_id(
        trend.strip(),
        created_at,
        operational_state,
        creation_id,
        media_id,
        permalink,
    )

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
        "evidence_status": "receipt_linked" if receipt else "no_publish_receipt",
        "creative_plan": creative_plan,
        "editorial_qa": editorial_qa,
        "visual_qa": visual_qa,
        "publication_authorization_gate": publication_authorization_gate,
        "receipt": receipt,
        "publish_result": receipt,
        "post_performance": post_performance,
        "linkage": {
            "creation_id": creation_id or None,
            "media_id": media_id or None,
            "permalink": permalink or None,
            "style": receipt.get("style"),
            "content_type": receipt.get("content_type"),
        },
        "insight_control": {
            "can_record": True,
            "can_suggest": True,
            "can_change_policy": False,
            "can_authorize_brand_live": False,
        },
    }
