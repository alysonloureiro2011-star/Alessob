from __future__ import annotations

import json
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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PerformanceStore:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.path = Path(config.data_dir) / "ace_next_performance_store.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _empty_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": "learning_loop_real_base_v1",
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
            payload.setdefault("version", "learning_loop_real_base_v1")
            return payload
        except Exception:
            return self._empty_payload()

    def _save(self, payload: dict[str, Any]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def append_record(self, record: dict[str, Any]) -> dict[str, Any]:
        payload = self._load()
        records = list(payload.get("records") or [])
        records.append(dict(record))
        payload["records"] = records[-200:]
        self._save(payload)
        return self.summary().to_dict()

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
        return PerformanceStoreSummary(
            ok=True,
            path=str(self.path),
            total_records=len(records),
            last_record_id=last.get("record_id"),
            last_operational_state=last.get("operational_state"),
        )
