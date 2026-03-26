from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


PUBLISH_STATUS_REAL = {
    "published_real_probe",
    "published_real",
}


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        try:
            parsed = value.to_dict()
            return dict(parsed) if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _clean_text(value: Any) -> str | None:
    text = " ".join(str(value or "").strip().split())
    return text or None


@dataclass(frozen=True)
class PublishTruthRecord:
    ok: bool
    truth_state: str
    publish_status: str | None
    has_receipt: bool
    has_media_id: bool
    has_permalink: bool
    receipt_id: str | None
    media_id: str | None
    permalink: str | None
    content_type: str | None
    style: str | None
    created_at: str
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PublishTruthLayer:
    """
    Camada soberana de verdade de publicação.

    Ela não publica.
    Ela apenas traduz o resultado do publish em uma leitura binária e auditável:
    gerou? publicou? recebeu receipt? recebeu media_id? recebeu permalink?
    """

    def build_truth_record(self, publish_result: dict[str, Any] | None = None) -> dict[str, Any]:
        publish_result = _safe_dict(publish_result)

        publish_status = _clean_text(publish_result.get("publish_status"))
        receipt_id = _clean_text(publish_result.get("receipt_id"))
        media_id = _clean_text(publish_result.get("media_id"))
        permalink = _clean_text(publish_result.get("permalink"))
        content_type = _clean_text(publish_result.get("content_type"))
        style = _clean_text(publish_result.get("style"))

        has_receipt = bool(receipt_id)
        has_media_id = bool(media_id)
        has_permalink = bool(permalink)
        publish_real = publish_status in PUBLISH_STATUS_REAL

        if publish_real and has_receipt and has_media_id and has_permalink:
            truth_state = "publish_truth_confirmed"
        elif publish_real and has_receipt and has_media_id:
            truth_state = "publish_truth_partial"
        elif publish_status:
            truth_state = "publish_attempt_recorded"
        else:
            truth_state = "publish_truth_absent"

        notes: list[str] = []
        if publish_status:
            notes.append(f"publish_status={publish_status}")
        if has_receipt:
            notes.append("receipt_present")
        if has_media_id:
            notes.append("media_id_present")
        if has_permalink:
            notes.append("permalink_present")
        if not notes:
            notes.append("no_publish_evidence_yet")

        record = PublishTruthRecord(
            ok=True,
            truth_state=truth_state,
            publish_status=publish_status,
            has_receipt=has_receipt,
            has_media_id=has_media_id,
            has_permalink=has_permalink,
            receipt_id=receipt_id,
            media_id=media_id,
            permalink=permalink,
            content_type=content_type,
            style=style,
            created_at=datetime.now().isoformat(),
            notes=notes,
        )
        return record.to_dict()

    def build_compact_summary(self, publish_result: dict[str, Any] | None = None) -> dict[str, Any]:
        truth = self.build_truth_record(publish_result)
        return {
            "ok": truth.get("ok"),
            "truth_state": truth.get("truth_state"),
            "publish_status": truth.get("publish_status"),
            "has_receipt": truth.get("has_receipt"),
            "has_media_id": truth.get("has_media_id"),
            "has_permalink": truth.get("has_permalink"),
        }


def publish_truth_examples() -> dict[str, Any]:
    layer = PublishTruthLayer()
    return {
        "empty": layer.build_truth_record({}),
        "partial": layer.build_truth_record(
            {
                "publish_status": "published_real_probe",
                "receipt_id": "r_123",
                "media_id": "m_123",
            }
        ),
        "full": layer.build_truth_record(
            {
                "publish_status": "published_real_probe",
                "receipt_id": "r_123",
                "media_id": "m_123",
                "permalink": "https://instagram.com/p/abc",
                "content_type": "image",
                "style": "official_next_visual_foundation_v1",
            }
        ),
    }
