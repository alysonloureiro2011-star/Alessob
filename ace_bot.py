from __future__ import annotations

from flask import Flask, request, jsonify
from ace_next.official_runtime_phase2b import OfficialRuntime

from ace_next.config import AceNextConfig

app = Flask(__name__)

_runtime = None


def get_runtime():
    global _runtime
    if _runtime is None:
        config = AceNextConfig()
        _runtime = OfficialRuntime(config)
    return _runtime


@app.route("/")
def health():
    return {"ok": True, "service": "ACE Ω", "mode": "thin_shell"}


@app.route("/ext/runtime")
def runtime_snapshot():
    runtime = get_runtime()
    return jsonify(runtime.snapshot())


@app.route("/ext/run", methods=["GET", "POST"])
def run_pipeline():
    runtime = get_runtime()

    data = request.json if request.method == "POST" else request.args
    trend = data.get("trend") or "tendência do dia"

    result = runtime.run(trend=trend)
    return jsonify(result)


@app.route("/ext/test/publish")
def test_publish():
    runtime = get_runtime()

    trend = request.args.get("trend") or "teste publicação"
    live = request.args.get("live", "0")

    result = runtime.run(
        trend=trend,
        force_real_probe=(live == "1"),
    )

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
