from __future__ import annotations

from typing import Any


class TikTokAdapter:
    platform = "tiktok"
    publish_supported = False
    adapter_state = "future_contract_ready"

    def validate_request(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        errors: list[str] = []

        caption = str(payload.get("caption") or "").strip()
        media_url = str(payload.get("media_url") or "").strip()

        if not caption:
            errors.append("caption_missing")
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
            "caption": str(payload.get("caption") or "").strip(),
            "media_url": str(payload.get("media_url") or "").strip(),
            "disclosure": str(payload.get("disclosure") or "organic").strip() or "organic",
            "validation": validation,
        }

    def run(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        built = self.build_payload(payload)
        return {
            **built,
            "ok": False,
            "reason": "adapter_contract_ready_but_publish_not_enabled",
            "next_step": "ligar autenticação e fluxo real quando a onda multiplataforma for priorizada",
        }
