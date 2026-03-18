# ACE Ω — Runtime Auto Injection Helper
# This module centralizes runtime metadata detection without
# requiring manual environment variable configuration.

import os
import subprocess


def detect_git_commit():
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return commit
    except Exception:
        return "unknown"


def detect_git_build():
    try:
        build = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return build
    except Exception:
        return "unknown"


def inject_runtime_env():
    if not os.getenv("ACE_RUNTIME_COMMIT"):
        os.environ["ACE_RUNTIME_COMMIT"] = detect_git_commit()

    if not os.getenv("ACE_RUNTIME_BUILD"):
        os.environ["ACE_RUNTIME_BUILD"] = detect_git_build()

    if not os.getenv("ACE_RUNTIME_RELEASE"):
        os.environ["ACE_RUNTIME_RELEASE"] = "ACE_SUPREME_AUTO"
