import json
from pathlib import Path
import datetime

BASE_DIR = Path(__file__).resolve().parents[2]
MEMORY_FILE = BASE_DIR / "memory" / "ace_evolution.json"

MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_memory():
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text())
        except:
            pass

    return {
        "hooks": {},
        "styles": {},
        "history": []
    }


def save_memory(data):
    MEMORY_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False)
    )


MEM = load_memory()


def learn(content):

    hook = content.get("hook")
    style = content.get("style")

    if hook:
        MEM["hooks"][hook] = MEM["hooks"].get(hook, 0) + 1

    if style:
        MEM["styles"][style] = MEM["styles"].get(style, 0) + 1

    MEM["history"].append({
        "time": datetime.datetime.utcnow().isoformat(),
        "hook": hook,
        "style": style
    })

    MEM["history"] = MEM["history"][-500:]

    save_memory(MEM)
