from flask import Flask, jsonify, request

from ace_next.official_runtime_v2 import OfficialRuntime
from ace_next.config import load_config

app = Flask(__name__)

config = load_config()
runtime = OfficialRuntime(config)


@app.route("/")
def home():
    return jsonify({"ok": True, "service": "ACE Ω Runtime Online"})


@app.route("/health")
def health():
    return jsonify({"ok": True}), 200


@app.route("/run", methods=["POST"])
def run():
    try:
        data = request.get_json(force=True) or {}

        result = runtime.run(
            trend=data.get("trend", ""),
            force_placeholder=bool(data.get("force_placeholder", False)),
            force_real_probe=bool(data.get("force_real_probe", False)),
            probe_state=data.get("probe_state"),
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        })


@app.route("/snapshot")
def snapshot():
    try:
        return jsonify({"ok": True, "status": "runtime active"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
