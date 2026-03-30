from __future__ import annotations

from typing import Any


class ThreadsAdapter:
    platform = "threads"
    publish_supported = False
    adapter_state = "future_contract_ready"

    def validate_request(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        errors: list[str] = []

        text = str(payload.get("text") or "").strip()
        if not text:
            errors.append("text_missing")

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
            "text": str(payload.get("text") or "").strip(),
            "reply_control": str(payload.get("reply_control") or "everyone").strip() or "everyone",
            "media_url": str(payload.get("media_url") or "").strip(),
            "validation": validation,
        }

    def run(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        built = self.build_payload(payload)
        return {
            **built,
            "ok": False,
            "reason": "adapter_contract_ready_but_publish_not_enabled",
            "next_step": "ligar publicação real quando o bloco multiplataforma entrar na ligação única",
        }
