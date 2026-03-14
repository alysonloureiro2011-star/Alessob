
import json
from pathlib import Path
import datetime

BASE_DIR = Path(__file__).resolve().parents[2]
MEMORY = BASE_DIR / "memory" / "evolution_memory.json"

MEMORY.parent.mkdir(parents=True, exist_ok=True)


def load_memory():

    if MEMORY.exists():
        try:
            return json.loads(MEMORY.read_text())
        except:
            pass

    return {
        "hooks": {},
        "styles": {},
        "content_types": {},
        "history": []
    }


def save_memory(data):

    MEMORY.write_text(
        json.dumps(data, indent=2, ensure_ascii=False)
    )


EVOLUTION_MEMORY = load_memory()


def register_content(content):

    hook = content.get("hook")
    style = content.get("style")
    content_type = content.get("content_type")

    if hook:
        EVOLUTION_MEMORY["hooks"][hook] = EVOLUTION_MEMORY["hooks"].get(hook, 0) + 1

    if style:
        EVOLUTION_MEMORY["styles"][style] = EVOLUTION_MEMORY["styles"].get(style, 0) + 1

    if content_type:
        EVOLUTION_MEMORY["content_types"][content_type] = EVOLUTION_MEMORY["content_types"].get(content_type, 0) + 1

    EVOLUTION_MEMORY["history"].append({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "hook": hook,
        "style": style,
        "type": content_type
    })

    EVOLUTION_MEMORY["history"] = EVOLUTION_MEMORY["history"][-500:]

    save_memory(EVOLUTION_MEMORY)
