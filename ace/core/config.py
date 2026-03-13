import os
from pathlib import Path


def ace_env(key, default=None):
    return os.environ.get(key, default)


env = ace_env


APP_NAME = "ACE Ω SUPREME"
PORT = int(ace_env("PORT", "10000"))
VERIFY_TOKEN = ace_env("VERIFY_TOKEN", "ACE_SIGILO_2026")

RENDER_URL = ace_env(
    "RENDER_EXTERNAL_URL",
    f"https://{ace_env('RENDER_EXTERNAL_HOSTNAME', 'localhost')}"
)

BASE_DIR = Path(__file__).resolve().parents[2]
MEMORY_DIR = BASE_DIR / "memory"
TMP_DIR = BASE_DIR / "tmp_ace"
MEDIA_DIR = BASE_DIR / "ace_media"
ENGINES_DIR = BASE_DIR / "engines"

MEMORY_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
ENGINES_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = MEMORY_DIR / "ace_supreme.db"
AUTH_PATH = MEMORY_DIR / "instagram_auth.json"

IG_TOKEN_ENV = ace_env("IG_TOKEN")
IG_ID_ENV = ace_env("IG_ID")
GEMINI_KEY = ace_env("GEMINI_KEY")
OPENAI_API_KEY = ace_env("OPENAI_API_KEY")

INSTAGRAM_APP_ID = (
    ace_env("INSTAGRAM_APP_ID")
    or ace_env("FACEBOOK_APP_ID")
    or ace_env("APP_ID")
    or ""
)

INSTAGRAM_APP_SECRET = (
    ace_env("INSTAGRAM_APP_SECRET")
    or ace_env("FACEBOOK_APP_SECRET")
    or ace_env("APP_SECRET")
    or ""
)

INSTAGRAM_REDIRECT_URI = ace_env(
    "INSTAGRAM_REDIRECT_URI",
    f"{RENDER_URL}/instagram/token"
)

ACE_FAST_MODE = str(ace_env("ACE_FAST_MODE", "1")).strip().lower() in ("1", "true", "yes", "on")
ACE_DISABLE_GEMINI = str(ace_env("ACE_DISABLE_GEMINI", "1")).strip().lower() in ("1", "true", "yes", "on")
ACE_DISABLE_PYTRENDS = str(ace_env("ACE_DISABLE_PYTRENDS", "1")).strip().lower() in ("1", "true", "yes", "on")
ACE_ENABLE_REAL_PUBLISH = str(ace_env("ACE_ENABLE_REAL_PUBLISH", "0")).strip().lower() in ("1", "true", "yes", "on")

ACE_GRAPH_BASE_URL = ace_env("ACE_GRAPH_BASE_URL", "https://graph.facebook.com/v24.0")
ACE_PUBLIC_MEDIA_BASE_URL = ace_env("ACE_PUBLIC_MEDIA_BASE_URL", RENDER_URL)

ACE_RENDER_SAFE_BOOT = str(ace_env("ACE_RENDER_SAFE_BOOT", "1")).strip().lower() in ("1", "true", "yes", "on")
ACE_SKIP_BOOT_FORCE = str(ace_env("ACE_SKIP_BOOT_FORCE", "1")).strip().lower() in ("1", "true", "yes", "on")
ACE_SKIP_FIRST_SUPERVISOR_FORCE = str(ace_env("ACE_SKIP_FIRST_SUPERVISOR_FORCE", "1")).strip().lower() in ("1", "true", "yes", "on")
ACE_ENABLE_PULSE_THREADS = str(ace_env("ACE_ENABLE_PULSE_THREADS", "0")).strip().lower() in ("1", "true", "yes", "on")
ACE_ENABLE_LEGACY_THREADS = str(ace_env("ACE_ENABLE_LEGACY_THREADS", "1")).strip().lower() in ("1", "true", "yes", "on")
ACE_MAX_QUEUE_SIZE = int(ace_env("ACE_MAX_QUEUE_SIZE", "3"))
ACE_FORCE_SECONDARY_TASK = str(ace_env("ACE_FORCE_SECONDARY_TASK", "0")).strip().lower() in ("1", "true", "yes", "on")

ACE_OAUTH_FORCE_REAUTH = str(ace_env("ACE_OAUTH_FORCE_REAUTH", "1")).strip().lower() in ("1", "true", "yes", "on")
ACE_OAUTH_DEFAULT_MODE = str(ace_env("ACE_OAUTH_DEFAULT_MODE", "basic")).strip().lower()
ACE_ENABLE_WEBHOOK_OAUTH_BRIDGE = str(ace_env("ACE_ENABLE_WEBHOOK_OAUTH_BRIDGE", "1")).strip().lower() in ("1", "true", "yes", "on")
