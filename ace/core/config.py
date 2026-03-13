
import os

def env(key, default=None):
    return os.environ.get(key, default)

APP_NAME = "ACE"

PORT = int(env("PORT", 10000))

VERIFY_TOKEN = env("VERIFY_TOKEN", "ACE_SIGILO_2026")

RENDER_URL = env("ACE_RENDER_URL", "")

# INSTAGRAM
IG_TOKEN = env("IG_TOKEN")
IG_ID = env("IG_ID")

# AI
OPENAI_API_KEY = env("OPENAI_API_KEY")
GEMINI_KEY = env("GEMINI_KEY")

# PATHS
BASE_DIR = os.getcwd()

MEDIA_DIR = os.path.join(BASE_DIR, "ace_media")

DB_PATH = os.path.join(BASE_DIR, "ace_memory.db")

TMP_DIR = os.path.join(BASE_DIR, "tmp")
