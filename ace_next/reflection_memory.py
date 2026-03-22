from __future__ import annotations

from typing import Any


def build_reflection_memory(*, record: dict[str, Any]) -> dict[str, Any]:
    real_metrics = dict(record.get("real_metrics") or {})
    status = str(real_metrics.get("source_status") or "not_available_yet")

    notes: list[str] = []
    if status in {"collected", "partial_collected"}:
        notes.append("Dados reais de performance foram registrados.")
        if real_metrics.get("reach") is not None:
            notes.append(f"reach real observado: {real_metrics.get('reach')}")
        if real_metrics.get("impressions") is not None:
            notes.append(f"impressions reais observadas: {real_metrics.get('impressions')}")
        if real_metrics.get("engagement_proxy") is not None:
            notes.append(f"engagement_proxy derivado de dados reais: {real_metrics.get('engagement_proxy')}")
    elif status in {"collection_error", "missing_token"}:
        notes.append("A coleta real falhou ou ficou indisponível.")
        reason = real_metrics.get("source_reason")
        if reason:
            notes.append(str(reason))
    else:
        notes.append("Ainda não existem métricas reais suficientes para leitura de performance.")

    return {
        "ok": True,
        "status": status,
        "notes": notes,
        "guardrails": {
            "can_change_brand_policy": False,
            "can_change_editorial_policy": False,
            "can_change_visual_policy": False,
            "can_authorize_brand_live": False,
            "can_autopublish": False,
        },
    }
