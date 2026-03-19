import os
import json
from datetime import datetime


def get_runtime_commit():
    """
    Returns runtime commit metadata for ACE Ω.

    Priority order:
    1. Environment variable RENDER_GIT_COMMIT
    2. Environment variable GITHUB_SHA
    3. runtime_commit.json file (if exists)
    4. 'unknown'
    """

    # 1. Render commit (if available)
    render_commit = os.getenv("RENDER_GIT_COMMIT")
    if render_commit:
        return {
            "commit": render_commit,
            "source": "render_env",
            "checked_at": datetime.utcnow().isoformat() + "Z",
        }

    # 2. GitHub Actions SHA
    github_sha = os.getenv("GITHUB_SHA")
    if github_sha:
        return {
            "commit": github_sha,
            "source": "github_env",
            "checked_at": datetime.utcnow().isoformat() + "Z",
        }

    # 3. Local file fallback
    if os.path.exists("runtime_commit.json"):
        try:
            with open("runtime_commit.json", "r") as f:
                data = json.load(f)
                data["source"] = "file"
                return data
        except Exception:
            pass

    # 4. Unknown fallback
    return {
        "commit": "unknown",
        "source": "fallback",
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }
