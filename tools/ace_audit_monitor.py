#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Check:
    name: str
    ok: bool
    severity: str
    detail: str


TARGETS = {
    "queue_executor": ROOT / "ace/pipeline/queue_executor.py",
    "executor_soberano": ROOT / "ace/core/ace_executor_soberano.py",
    "official_publish": ROOT / "ace_next/official_instagram_publish.py",
    "publish_truth": ROOT / "ace_next/publish_truth_layer.py",
    "state_core": ROOT / "ace/core/state.py",
    "logging_core": ROOT / "ace/core/logging.py",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def has_all(text: str, *tokens: str) -> bool:
    return all(token in text for token in tokens)


def run() -> dict:
    queue_text = read_text(TARGETS["queue_executor"])
    exec_text = read_text(TARGETS["executor_soberano"])
    publish_text = read_text(TARGETS["official_publish"])
    truth_text = read_text(TARGETS["publish_truth"])
    state_text = read_text(TARGETS["state_core"])
    logging_text = read_text(TARGETS["logging_core"])

    checks = [
        Check(
            name="queue_consumption_ready",
            ok=has_all(queue_text, "class QueueExecutor", "def worker", "self.q.get", "task_done"),
            severity="critical",
            detail="Queue worker com consumo e confirmação de task.",
        ),
        Check(
            name="sovereign_executor_ready",
            ok=has_all(exec_text, "class ExecutorSoberano", "def queue_executor_loop_soberano", "def execute_task_soberano"),
            severity="critical",
            detail="Executor soberano com loop e dispatch de tarefas.",
        ),
        Check(
            name="real_publish_path_present",
            ok=has_all(publish_text, "class OfficialInstagramPublishService", "def publish_single", "def publish_carousel"),
            severity="critical",
            detail="Trilha de publish real para single/carousel existe.",
        ),
        Check(
            name="publish_truth_layer_present",
            ok=has_all(truth_text, "class PublishTruthLayer", "publish_truth_confirmed", "build_truth_record"),
            severity="critical",
            detail="Camada de verdade de publicação auditável está presente.",
        ),
        Check(
            name="state_file_not_empty",
            ok=len(state_text.strip()) > 0,
            severity="critical",
            detail="Módulo central de estado não pode estar vazio.",
        ),
        Check(
            name="logging_file_not_empty",
            ok=len(logging_text.strip()) > 0,
            severity="critical",
            detail="Módulo central de logging não pode estar vazio.",
        ),
    ]

    critical_failures = [c.name for c in checks if c.severity == "critical" and not c.ok]
    status = "pass" if not critical_failures else "fail"

    return {
        "ok": status == "pass",
        "status": status,
        "critical_failures": critical_failures,
        "checks": [asdict(c) for c in checks],
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
