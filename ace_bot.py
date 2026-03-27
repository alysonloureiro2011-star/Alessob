from __future__ import annotations

from flask import Flask, jsonify, request

from ace_next.config import AceNextConfig
from ace_next.official_runtime import OfficialRuntime

app = Flask(__name__)

_runtime: OfficialRuntime | None = None


def get_runtime() -> OfficialRuntime:
    global _runtime
    if _runtime is None:
        config = AceNextConfig()
        _runtime = OfficialRuntime(config)
    return _runtime


@app.route("/")
def health():
    return {"ok": True, "service": "ACE Ω", "mode": "official_runtime_bridge"}


@app.route("/ext/runtime")
def runtime_snapshot():
    runtime = get_runtime()
    return jsonify(runtime.snapshot())


@app.route("/ext/run", methods=["GET", "POST"])
def run_pipeline():
    runtime = get_runtime()

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
    else:
        data = request.args

    trend = data.get("trend") or "tendência do dia"

    force_placeholder = str(data.get("force_placeholder", "0")).strip().lower() in {
        "1", "true", "yes", "on"
    }
    force_real_probe = str(data.get("force_real_probe", "0")).strip().lower() in {
        "1", "true", "yes", "on"
    }
    probe_state = data.get("probe_state") or "auto"

    result = runtime.run(
        trend=trend,
        force_placeholder=force_placeholder,
        force_real_probe=force_real_probe,
        probe_state=probe_state,
    )
    return jsonify(result)


@app.route("/ext/test/publish")
def test_publish():
    runtime = get_runtime()

    trend = request.args.get("trend") or "teste publicação"
    live = request.args.get("live", "0")

    result = runtime.run(
        trend=trend,
        force_real_probe=(live == "1"),
        force_placeholder=False,
        probe_state="auto",
    )

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
