from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .multiplatform_contract import MultiplatformContractBuilder


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


@dataclass(frozen=True)
class PlatformAdapterResult:
    ok: bool
    platform_family: str
    adapter_state: str
    mode: str
    payload: dict[str, Any]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PlatformAdapters:
    """
    Adaptadores soberanos de plataforma.

    Função:
    - receber payload editorial comum
    - adaptar para contrato de plataforma
    - manter Instagram como alvo principal sem acoplar o núcleo
    """

    def __init__(self) -> None:
        self.contracts = MultiplatformContractBuilder()

    def run(
        self,
        *,
        platform_family: str,
        content_type: str,
        creative_plan: dict[str, Any] | None = None,
        media_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        creative_plan = _safe_dict(creative_plan)
        media_payload = _safe_dict(media_payload)

        contract = self.contracts.run(
            platform_family=platform_family,
            content_type=content_type,
        )

        family = _clean_text(contract.get("platform_family")).lower() or "instagram"
        ctype = _clean_text(contract.get("content_type")).lower() or "image"

        payload = {
            "platform_family": family,
            "content_type": ctype,
            "title": creative_plan.get("headline") or creative_plan.get("topic_seed"),
            "hook": creative_plan.get("hook"),
            "body": creative_plan.get("body"),
            "cta": creative_plan.get("cta"),
            "caption": creative_plan.get("caption_final") or creative_plan.get("body"),
            "media_ref": media_payload.get("media_ref"),
            "cover_ref": media_payload.get("cover_ref"),
            "thumb_ref": media_payload.get("thumb_ref"),
        }

        if family == "instagram":
            mode = "primary"
        elif family in {"youtube", "tiktok"}:
            mode = "vertical_future"
        else:
            mode = "generic_future"

        notes = [
            f"platform_family={family}",
            f"content_type={ctype}",
            f"mode={mode}",
        ]

        result = PlatformAdapterResult(
            ok=True,
            platform_family=family,
            adapter_state="platform_adapters_ready",
            mode=mode,
            payload=payload,
            notes=notes,
        )
        return {
            "contract": contract,
            **result.to_dict(),
        }


def platform_adapters_examples() -> dict[str, Any]:
    adapters = PlatformAdapters()
    return {
        "instagram_reel": adapters.run(
            platform_family="instagram",
            content_type="reel",
            creative_plan={
                "headline": "Por que seu conteúdo morre antes de começar",
                "hook": "Seu problema pode estar nos 2 primeiros segundos",
                "body": "Se a abertura não prende, o resto morre junto.",
                "cta": "salve e revise sua próxima abertura",
            },
            media_payload={
                "media_ref": "video_ref",
                "cover_ref": "cover_ref",
            },
        ),
        "youtube_short": adapters.run(
            platform_family="youtube",
            content_type="short",
            creative_plan={
                "headline": "O erro silencioso que destrói sua retenção",
                "hook": "Você acha que é o algoritmo, mas não é",
                "body": "O problema pode estar no começo fraco e sem contraste.",
                "cta": "veja a próxima análise",
            },
            media_payload={
                "media_ref": "short_ref",
                "thumb_ref": "thumb_ref",
            },
        ),
    }
