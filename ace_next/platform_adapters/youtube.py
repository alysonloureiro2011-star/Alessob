from __future__ import annotations

from typing import Any


class YouTubeAdapter:
    platform = "youtube"
    publish_supported = False
    adapter_state = "future_contract_ready"

    def validate_request(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        errors: list[str] = []

        title = str(payload.get("title") or "").strip()
        media_url = str(payload.get("media_url") or "").strip()

        if not title:
            errors.append("title_missing")
        if not media_url:
            errors.append("media_url_missing")

        return {
            "ok": len(errors) == 0,
            "platform": self.platform,
            "errors": errors,
        }

    def build_payload(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        validation = self.validate_request(payload)
        return {
            "ok": validation["ok"],
            "platform": self.platform,
            "adapter_state": self.adapter_state,
            "publish_supported": self.publish_supported,
            "title": str(payload.get("title") or "").strip(),
            "description": str(payload.get("description") or "").strip(),
            "media_url": str(payload.get("media_url") or "").strip(),
            "privacy_status": str(payload.get("privacy_status") or "private").strip() or "private",
            "validation": validation,
        }

    def run(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        built = self.build_payload(payload)
        return {
            **built,
            "ok": False,
            "reason": "adapter_contract_ready_but_publish_not_enabled",
            "next_step": "ligar credenciais e fluxo real em onda multiplataforma",
        }
