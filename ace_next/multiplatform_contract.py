from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SUPPORTED_PLATFORM_FAMILIES = {
    "instagram",
    "youtube",
    "tiktok",
    "threads",
    "x",
}

SUPPORTED_CONTENT_TYPES = {
    "image",
    "carousel",
    "story",
    "reel",
    "short",
    "thread",
}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class MultiplatformContract:
    ok: bool
    platform_family: str
    content_type: str
    vertical_video: bool
    requires_cover: bool
    allows_caption: bool
    allows_first_comment: bool
    timing_sensitive: bool
    contract_state: str
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MultiplatformContractBuilder:
    """
    Contrato soberano para expansão multiplataforma.

    Função:
    - padronizar diferenças entre famílias de plataforma
    - separar formato de publicação do núcleo editorial
    - deixar Instagram como prioridade sem travar expansão futura
    """

    def run(
        self,
        *,
        platform_family: str,
        content_type: str,
        vertical_video: Any = None,
    ) -> dict[str, Any]:
        family = _clean_text(platform_family).lower() or "instagram"
        ctype = _clean_text(content_type).lower() or "image"

        if family not in SUPPORTED_PLATFORM_FAMILIES:
            family = "instagram"
        if ctype not in SUPPORTED_CONTENT_TYPES:
            ctype = "image"

        default_vertical = ctype in {"reel", "short", "story"}
        vertical = _safe_bool(vertical_video, default_vertical)

        requires_cover = ctype in {"reel", "short", "carousel"}
        allows_caption = family in {"instagram", "youtube", "tiktok", "threads", "x"}
        allows_first_comment = family in {"instagram", "threads", "x"}
        timing_sensitive = family in {"instagram", "youtube", "tiktok"}

        notes = [
            f"platform_family={family}",
            f"content_type={ctype}",
            f"vertical_video={str(vertical).lower()}",
        ]

        contract = MultiplatformContract(
            ok=True,
            platform_family=family,
            content_type=ctype,
            vertical_video=vertical,
            requires_cover=requires_cover,
            allows_caption=allows_caption,
            allows_first_comment=allows_first_comment,
            timing_sensitive=timing_sensitive,
            contract_state="multiplatform_contract_ready",
            notes=notes,
        )
        return contract.to_dict()


def multiplatform_contract_examples() -> dict[str, Any]:
    builder = MultiplatformContractBuilder()
    return {
        "instagram_reel": builder.run(platform_family="instagram", content_type="reel"),
        "youtube_short": builder.run(platform_family="youtube", content_type="short"),
        "threads_post": builder.run(platform_family="threads", content_type="thread"),
    }
