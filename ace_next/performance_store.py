from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class PerformanceStoreSummary:
    ok: bool
    path: str
    total_records: int
    last_record_id: str | None
    last_operational_state: str | None
    latest_source_status: str | None
    latest_real_metrics_status: str | None
    latest_collected_at: str | None
    latest_attention_score: float | None
    latest_receipt_id: str | None
    latest_media_id: str | None
    latest_permalink: str | None
    latest_probe_requested: bool
    latest_probe_publish_executed: bool
    latest_ingest_attempted: bool
    latest_evidence_bridge_state: str | None
    records_with_receipt: int
    records_with_media_id: int
    records_with_permalink: int
    records_with_real_metrics: int
    records_without_real_metrics: int
    records_with_ingest_error: int
    records_with_attention_metrics: int
    records_with_probe_publish: int
    source_status_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _source_status(record: dict[str, Any]) -> str:
    real_metrics = dict(record.get("real_metrics") or {})
    return str(real_metrics.get("source_status") or "unknown")


def _receipt(record: dict[str, Any]) -> dict[str, Any]:
    return dict(record.get("receipt") or record.get("publish_result") or {})


def _has_receipt(record: dict[str, Any]) -> bool:
    receipt = _receipt(record)
    return bool(receipt.get("receipt_id"))


def _has_media_id(record: dict[str, Any]) -> bool:
    receipt = _receipt(record)
    return bool(receipt.get("media_id"))


def _has_permalink(record: dict[str, Any]) -> bool:
    receipt = _receipt(record)
    return bool(receipt.get("permalink"))


def _has_real_metrics(record: dict[str, Any]) -> bool:
    return _source_status(record) in {"collected", "partial_collected"}


def _derive_evidence_bridge_state(record: dict[str, Any]) -> str:
    has_receipt = _has_receipt(record)
    has_media_id = _has_media_id(record)
    has_permalink = _has_permalink(record)
    source_status = _source_status(record)
    probe_context = dict(record.get("probe_context") or {})

    if source_status in {"collected", "partial_collected"} and has_media_id:
        return "real_metrics_linked"
    if bool(probe_context.get("publish_executed")) and has_media_id:
        return "receipt_with_media_id_waiting_metrics"
    if has_receipt and has_media_id and has_permalink:
        return "receipt_media_permalink_linked"
    if has_receipt and has_media_id:
        return "receipt_media_linked"
    if has_receipt:
        return "receipt_only"
    if bool(probe_context.get("requested")):
        return "probe_requested_without_receipt"
    return "safe_no_probe"


class PerformanceStore:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.path = Path(config.data_dir) / "ace_next_performance_store.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _empty_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": "measurement_core_v1",
            "records": [],
        }

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty_payload()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return self._empty_payload()
            if not isinstance(payload.get("records"), list):
                payload["records"] = []
            payload.setdefault("ok", True)
            payload.setdefault("version", "measurement_core_v1")
            return payload
        except Exception:
            return self._empty_payload()

    def _save(self, payload: dict[str, Any]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def upsert_record(self, record: dict[str, Any]) -> dict[str, Any]:
        payload = self._load()
        records = list(payload.get("records") or [])
        record_id = record.get("record_id")

        replaced = False
        if record_id:
            for index, existing in enumerate(records):
                if existing.get("record_id") == record_id:
                    records[index] = dict(record)
                    replaced = True
                    break

        if not replaced:
            records.append(dict(record))

        payload["records"] = records[-300:]
        self._save(payload)
        return self.summary().to_dict()

    def append_record(self, record: dict[str, Any]) -> dict[str, Any]:
        return self.upsert_record(record)

    def list_records(self, limit: int = 20) -> list[dict[str, Any]]:
        payload = self._load()
        records = list(payload.get("records") or [])
        if limit <= 0:
            return records
        return records[-limit:]

    def summary(self) -> PerformanceStoreSummary:
        payload = self._load()
        records = list(payload.get("records") or [])
        last = records[-1] if records else {}
        status_counts = dict(Counter(_source_status(record) for record in records))

        with_real = sum(1 for record in records if _has_real_metrics(record))
        with_error = sum(1 for record in records if _source_status(record) == "ingest_error")
        without_real = len(records) - with_real - with_error
        with_attention_metrics = sum(
            1
            for record in records
            if ((record.get("attention_metrics") or {}).get("breakdown") or {}).get("attention_score") is not None
        )
        with_probe_publish = sum(
            1
            for record in records
            if bool((record.get("probe_context") or {}).get("publish_executed"))
        )
        with_receipt = sum(1 for record in records if _has_receipt(record))
        with_media_id = sum(1 for record in records if _has_media_id(record))
        with_permalink = sum(1 for record in records if _has_permalink(record))

        real_metrics = dict(last.get("real_metrics") or {})
        attention_metrics = dict(last.get("attention_metrics") or {})
        receipt = _receipt(last)
        probe_context = dict(last.get("probe_context") or {})
        performance_ingest = dict(last.get("performance_ingest") or {})

        return PerformanceStoreSummary(
            ok=True,
            path=str(self.path),
            total_records=len(records),
            last_record_id=last.get("record_id"),
            last_operational_state=last.get("operational_state"),
            latest_source_status=real_metrics.get("source_status"),
            latest_real_metrics_status=real_metrics.get("source_status"),
            latest_collected_at=real_metrics.get("collected_at"),
            latest_attention_score=(
                (attention_metrics.get("breakdown") or {}).get("attention_score")
                if isinstance(attention_metrics, dict)
                else None
            ),
            latest_receipt_id=receipt.get("receipt_id"),
            latest_media_id=receipt.get("media_id"),
            latest_permalink=receipt.get("permalink"),
            latest_probe_requested=bool(probe_context.get("requested")),
            latest_probe_publish_executed=bool(probe_context.get("publish_executed")),
            latest_ingest_attempted=bool(performance_ingest.get("attempted")),
            latest_evidence_bridge_state=_derive_evidence_bridge_state(last),
            records_with_receipt=with_receipt,
            records_with_media_id=with_media_id,
            records_with_permalink=with_permalink,
            records_with_real_metrics=with_real,
            records_without_real_metrics=without_real,
            records_with_ingest_error=with_error,
            records_with_attention_metrics=with_attention_metrics,
            records_with_probe_publish=with_probe_publish,
            source_status_counts=status_counts,
        )
