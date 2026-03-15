from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def build_publish_record(
    trend: Optional[str] = None,
    style: Optional[str] = None,
    content_type: Optional[str] = None,
    caption: Optional[str] = None,
    media_path: Optional[str] = None,
    status: str = "generated",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    media_name = Path(media_path).name if media_path else None

    record = {
        "created_at": datetime.datetime.now().isoformat(),
        "trend": _safe_str(trend),
        "style": _safe_str(style),
        "content_type": _safe_str(content_type),
        "caption": _safe_str(caption),
        "media_path": media_path,
        "media_name": media_name,
        "status": status,
    }

    if extra and isinstance(extra, dict):
        record["extra"] = extra

    return record


def publish_content(
    trend: Optional[str] = None,
    style: Optional[str] = None,
    content_type: Optional[str] = None,
    caption: Optional[str] = None,
    media_path: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Função principal de publicação usada pelo ace_bot.py.
    Neste estágio ela monta o registro de publicação sem depender
    de APIs externas para não quebrar o boot do sistema.
    """
    return build_publish_record(
        trend=trend,
        style=style,
        content_type=content_type,
        caption=caption,
        media_path=media_path,
        status="generated",
        extra=kwargs or None,
    )


def publish_media(
    media_path: Optional[str] = None,
    caption: Optional[str] = None,
    trend: Optional[str] = None,
    style: Optional[str] = None,
    content_type: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Função de compatibilidade para o pipeline antigo.
    O run_pipeline.py está tentando importar esta função.
    """
    return build_publish_record(
        trend=trend,
        style=style,
        content_type=content_type or "media",
        caption=caption,
        media_path=media_path,
        status="generated",
        extra=kwargs or None,
    )
