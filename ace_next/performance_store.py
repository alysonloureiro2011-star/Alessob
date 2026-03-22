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
    latest_collected_at: str | None
    records_with_real_metrics: int
    records_without_real_metrics: int
    records_with_ingest_error: int
    source_status_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _source_status(record: dict[str, Any]) -> str:
    real_metrics = dict(record.get("real_metrics") or {})
    return str(real_metrics.get("source_status") or "unknown")


class PerformanceStore:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.path = Path(config.data_dir) / "ace_next_performance_store.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _empty_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": "performance_ingestion_real_base_v1",
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
            payload.setdefault("version", "performance_ingestion_real_base_v1")
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

        payload["records"] = records[-200:]
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

        with_real = sum(
            1 for record in records if _source_status(record) in {"collected", "partial_collected"}
        )
        with_error = sum(
            1 for record in records if _source_status(record) in {"collection_error", "missing_token"}
        )
        without_real = len(records) - with_real - with_error

        real_metrics = dict(last.get("real_metrics") or {})
        return PerformanceStoreSummary(
            ok=True,
            path=str(self.path),
            total_records=len(records),
            last_record_id=last.get("record_id"),
            last_operational_state=last.get("operational_state"),
            latest_source_status=real_metrics.get("source_status"),
            latest_collected_at=real_metrics.get("collected_at"),
            records_with_real_metrics=with_real,
            records_without_real_metrics=without_real,
            records_with_ingest_error=with_error,
            source_status_counts=status_counts,
        )
