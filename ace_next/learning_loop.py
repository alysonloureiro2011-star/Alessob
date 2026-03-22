from __future__ import annotations

from collections import Counter
from typing import Any


def _count_by(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    values = [str(record.get(key) or "unknown") for record in records]
    return dict(Counter(values))


def build_learning_loop_summary(
    *,
    records: list[dict[str, Any]],
    latest_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    records = list(records or [])
    latest = dict(latest_record or (records[-1] if records else {}))

    states = _count_by(records, "operational_state")
    publish_status = _count_by(records, "publish_status")
    evidence_status = _count_by(records, "evidence_status")

    linked_with_receipt = sum(1 for record in records if record.get("receipt"))
    pending_real_metrics = sum(
        1
        for record in records
        if ((record.get("post_performance") or {}).get("status") or "") != "collected"
    )

    suggestions: list[str] = []
    if not records:
        suggestions.append("Ainda não há registros suficientes para aprendizado útil.")
    else:
        suggestions.append("O learning loop está em modo de registro e consolidação, não de governança automática.")
        if pending_real_metrics > 0:
            suggestions.append("Ainda faltam métricas reais externas para fechar o ciclo de performance.")
        if states.get("technical_test", 0) > 0:
            suggestions.append("Há registros de teste técnico; isso não conta como validação de marca.")
        if states.get("editorial_staging", 0) > 0:
            suggestions.append("Existem peças em staging editorial aguardando validação mais forte.")
        if states.get("blocked_quality", 0) > 0 or states.get("blocked_brand", 0) > 0:
            suggestions.append("Há reprovações recentes; usar isso como evidência para refino, não como permissão para live.")

    return {
        "ok": True,
        "mode": "learning_loop_real_base_v1",
        "records_considered": len(records),
        "linked_with_receipt": linked_with_receipt,
        "pending_real_metrics": pending_real_metrics,
        "operational_state_counts": states,
        "publish_status_counts": publish_status,
        "evidence_status_counts": evidence_status,
        "latest_record_id": latest.get("record_id"),
        "latest_operational_state": latest.get("operational_state"),
        "latest_publish_status": latest.get("publish_status"),
        "insight_control": {
            "can_record": True,
            "can_consolidate": True,
            "can_suggest": True,
            "can_change_brand_policy": False,
            "can_change_editorial_policy": False,
            "can_change_visual_policy": False,
            "can_autopublish_brand_live": False,
        },
        "suggestions": suggestions,
    }
