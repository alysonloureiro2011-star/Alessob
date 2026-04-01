from flask import Flask, jsonify, request

from ace_next.config import AceNextConfig
from ace_next.official_runtime import OfficialRuntime

app = Flask(__name__)

config = AceNextConfig()
runtime = OfficialRuntime(config)


@app.route("/health")
def health():
    return jsonify({"ok": True})


@app.route("/snapshot")
def snapshot():
    return jsonify(runtime.snapshot())


@app.route("/compact-summary")
def compact_summary():
    return jsonify(runtime.compact_runtime_summary())


@app.route("/quality")
def quality():
    return jsonify(runtime.quality_gap_summary())


@app.route("/last-publish")
def last_publish():
    return jsonify(runtime.last_publish_compact_summary())


@app.route("/probe", methods=["GET"])
def probe():
    trend = request.args.get("trend", "teste simples")

    result = runtime.run(
        trend=trend,
        force_placeholder=True
    )

    return jsonify(result)


@app.route("/")
def root():
    return jsonify({
        "ok": True,
        "status": "runtime active"
    })
