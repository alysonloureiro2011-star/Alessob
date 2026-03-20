# ACE Ω — Runtime Metadata Module
# Production-safe (no subprocess, Render-compatible)

import os
from datetime import datetime


def get_runtime_metadata() -> dict:
    """
    Unified runtime metadata provider.
    Priority order:
      1. Explicit ACE_* environment variables
      2. Render automatic variables
      3. Safe fallbacks
    """

    return {
        "runtime_release": (
            os.getenv("ACE_RUNTIME_RELEASE")
            or os.getenv("RENDER_SERVICE_NAME")
            or "production"
        ),
        "runtime_commit": (
            os.getenv("ACE_RUNTIME_COMMIT")
            or os.getenv("RENDER_GIT_COMMIT")
            or "unknown"
        ),
        "runtime_branch": os.getenv("RENDER_GIT_BRANCH") or "unknown",
        "runtime_build": (
            os.getenv("ACE_RUNTIME_BUILD")
            or os.getenv("RENDER_GIT_COMMIT")
            or datetime.utcnow().isoformat()
        ),
    }
