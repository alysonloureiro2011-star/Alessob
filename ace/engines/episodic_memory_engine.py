from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List

EPISODIC_MEMORY_PATH = "ace_data/episodic_memory.json"
MAX_EPISODES = 50


DEFAULT_MEMORY = {
    "episodes": [],
    "updated_at": None,
}


def episodic_now_iso() -> str:
    return datetime.now().isoformat()


def episodic_ensure_dir() -> None:
    folder = os.path.dirname(EPISODIC_MEMORY_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)


def load_episodic_memory() -> Dict[str, Any]:
    try:
        if os.path.exists(EPISODIC_MEMORY_PATH):
            with open(EPISODIC_MEMORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    merged = dict(DEFAULT_MEMORY)
                    merged.update(data)
                    if not isinstance(merged.get("episodes"), list):
                        merged["episodes"] = []
                    return merged
    except Exception:
        pass

    return dict(DEFAULT_MEMORY)


def save_episodic_memory(memory: Dict[str, Any]) -> None:
    try:
        episodic_ensure_dir()
        memory["updated_at"] = episodic_now_iso()
        with open(EPISODIC_MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def trim_episodes(episodes: List[Dict[str, Any]], max_items: int = MAX_EPISODES) -> List[Dict[str, Any]]:
    return episodes[-max_items:]


def safe_short_text(value: Any, max_len: int = 280) -> str:
    text = str(value or "").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "..."


def build_episode_from_pipeline_result(result: Dict[str, Any]) -> Dict[str, Any]:
    result = result or {}

    plan = result.get("plan") or {}
    content = result.get("content") or {}
    media = result.get("media") or {}
    published = result.get("published") or {}
    myth = result.get("myth") or {}

    episode = {
        "at": episodic_now_iso(),
        "trend": result.get("trend"),
        "content_type": plan.get("content_type") or result.get("content_type"),
        "style": plan.get("style") or result.get("style"),
        "myth_tension": myth.get("dominant_tension"),
        "myth_stage": myth.get("chapter_stage"),
        "symbolic_anchor": myth.get("symbolic_anchor"),
        "myth_line": content.get("myth_line"),
        "narrative_direction": content.get("narrative_direction") or plan.get("myth_direction"),
        "caption_preview": safe_short_text(content.get("caption") or result.get("caption")),
        "media_path": media.get("media_path"),
        "publish_status": published.get("status"),
        "pipeline_version": result.get("pipeline_version"),
    }

    return episode


def append_episode(episode: Dict[str, Any]) -> Dict[str, Any]:
    memory = load_episodic_memory()
    episodes = memory.get("episodes", []) or []

    episodes.append(episode)
    memory["episodes"] = trim_episodes(episodes)

    save_episodic_memory(memory)
    return memory


def register_pipeline_result(result: Dict[str, Any]) -> Dict[str, Any]:
    episode = build_episode_from_pipeline_result(result)
    return append_episode(episode)


def get_recent_episodes(limit: int = 10) -> List[Dict[str, Any]]:
    memory = load_episodic_memory()
    episodes = memory.get("episodes", []) or []
    return episodes[-limit:]


def get_last_episode() -> Dict[str, Any] | None:
    recent = get_recent_episodes(limit=1)
    if recent:
        return recent[-1]
    return None


def build_memory_summary() -> Dict[str, Any]:
    memory = load_episodic_memory()
    episodes = memory.get("episodes", []) or []
    last_episode = episodes[-1] if episodes else None

    return {
        "ok": True,
        "episodes_count": len(episodes),
        "updated_at": memory.get("updated_at"),
        "last_episode": last_episode,
        "recent_episodes": episodes[-10:],
    }
