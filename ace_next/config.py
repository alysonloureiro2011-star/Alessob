from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


@dataclass(frozen=True)
class AceNextConfig:
    app_name: str
    port: int
    render_url: str
    graph_base_url: str
    public_media_base_url: str
    verify_token: str
    ig_token: str | None
    ig_id: str | None
    gemini_key: str | None
    openai_api_key: str | None
    instagram_app_id: str | None
    instagram_app_secret: str | None
    instagram_redirect_uri: str
    enable_real_publish: bool
    base_dir: Path
    data_dir: Path
    media_dir: Path


def load_config() -> AceNextConfig:
    render_url = env(
        "RENDER_EXTERNAL_URL",
        f"https://{env('RENDER_EXTERNAL_HOSTNAME', 'localhost')}"
    )

    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "ace_data"
    media_dir = base_dir / "ace_media"
    data_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)

    instagram_app_id = env("INSTAGRAM_APP_ID") or env("FACEBOOK_APP_ID") or env("APP_ID")
    instagram_app_secret = env("INSTAGRAM_APP_SECRET") or env("FACEBOOK_APP_SECRET") or env("APP_SECRET")

    return AceNextConfig(
        app_name="ACE Ω NEXT",
        port=int(env("PORT", "10000") or "10000"),
        render_url=render_url,
        graph_base_url=env("ACE_GRAPH_BASE_URL", "https://graph.facebook.com/v24.0") or "https://graph.facebook.com/v24.0",
        public_media_base_url=env("ACE_PUBLIC_MEDIA_BASE_URL", render_url) or render_url,
        verify_token=env("VERIFY_TOKEN", "ACE_SIGILO_2026") or "ACE_SIGILO_2026",
        ig_token=env("IG_TOKEN") or env("IG_ACCESS_TOKEN") or env("INSTAGRAM_TOKEN"),
        ig_id=env("IG_ID") or env("IG_USER_ID"),
        gemini_key=env("GEMINI_KEY"),
        openai_api_key=env("OPENAI_API_KEY"),
        instagram_app_id=instagram_app_id,
        instagram_app_secret=instagram_app_secret,
        instagram_redirect_uri=env("INSTAGRAM_REDIRECT_URI", f"{render_url}/instagram/token") or f"{render_url}/instagram/token",
        enable_real_publish=str(env("ACE_ENABLE_REAL_PUBLISH", "0")).strip().lower() in ("1", "true", "yes", "on"),
        base_dir=base_dir,
        data_dir=data_dir,
        media_dir=media_dir,
    )
