from __future__ import annotations

import os
from typing import Any

import requests


DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_REST_MODEL", "gemini-2.5-flash").strip()
DEFAULT_PROVIDER = os.getenv("ACE_LLM_PROVIDER", "auto").strip().lower()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_KEY = os.getenv("GEMINI_KEY", "").strip()

ACE_DISABLE_OPENAI = os.getenv("ACE_DISABLE_OPENAI", "0").strip().lower() in ("1", "true", "yes", "on")
ACE_DISABLE_GEMINI = os.getenv("ACE_DISABLE_GEMINI", "0").strip().lower() in ("1", "true", "yes", "on")


def _http_post(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_payload: dict[str, Any] | None = None,
    timeout: int = 90,
) -> dict[str, Any]:
    try:
        response = requests.post(url, headers=headers, json=json_payload, timeout=timeout)
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text[:4000]}

        return {
            "ok": response.status_code < 400,
            "status_code": response.status_code,
            "data": body,
        }
    except Exception as exc:
        return {
            "ok": False,
            "status_code": None,
            "error": str(exc),
            "data": None,
        }


def _extract_openai_text(data: dict[str, Any]) -> str | None:
    if not isinstance(data, dict):
        return None

    direct = data.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    output = data.get("output", [])
    if isinstance(output, list):
        chunks: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and content.get("type") == "output_text":
                    text = content.get("text")
                    if isinstance(text, str) and text.strip():
                        chunks.append(text.strip())
        joined = "\n".join(chunks).strip()
        if joined:
            return joined

    return None


def _extract_gemini_text(data: dict[str, Any]) -> str | None:
    if not isinstance(data, dict):
        return None

    try:
        candidates = data.get("candidates", [])
        if not candidates:
            return None

        parts = candidates[0].get("content", {}).get("parts", [])
        texts = [part.get("text", "").strip() for part in parts if isinstance(part, dict) and part.get("text")]
        joined = "\n".join([text for text in texts if text]).strip()
        return joined or None
    except Exception:
        return None


def openai_generate_text(
    prompt: str,
    *,
    model: str | None = None,
) -> dict[str, Any]:
    if ACE_DISABLE_OPENAI:
        return {
            "ok": False,
            "provider": "openai",
            "reason": "openai_disabled",
            "result": None,
        }

    if not OPENAI_API_KEY:
        return {
            "ok": False,
            "provider": "openai",
            "reason": "openai_key_missing",
            "result": None,
        }

    chosen_model = (model or DEFAULT_OPENAI_MODEL).strip()

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": chosen_model,
        "input": prompt,
    }

    response = _http_post(
        "https://api.openai.com/v1/responses",
        headers=headers,
        json_payload=payload,
        timeout=90,
    )

    if not response.get("ok"):
        return {
            "ok": False,
            "provider": "openai",
            "reason": "openai_http_fail",
            "status_code": response.get("status_code"),
            "error": response.get("error") or response.get("data"),
            "result": None,
        }

    text = _extract_openai_text(response.get("data") or {})
    if not text:
        return {
            "ok": False,
            "provider": "openai",
            "reason": "openai_empty_text",
            "status_code": response.get("status_code"),
            "error": response.get("data"),
            "result": None,
        }

    return {
        "ok": True,
        "provider": "openai",
        "model": chosen_model,
        "fallback_used": False,
        "result": text,
    }


def gemini_generate_text(
    prompt: str,
    *,
    model: str | None = None,
) -> dict[str, Any]:
    if ACE_DISABLE_GEMINI:
        return {
            "ok": False,
            "provider": "gemini",
            "reason": "gemini_disabled",
            "result": None,
        }

    if not GEMINI_KEY:
        return {
            "ok": False,
            "provider": "gemini",
            "reason": "gemini_key_missing",
            "result": None,
        }

    chosen_model = (model or DEFAULT_GEMINI_MODEL).strip()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{chosen_model}:generateContent?key={GEMINI_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = _http_post(url, json_payload=payload, timeout=90)

    if not response.get("ok"):
        return {
            "ok": False,
            "provider": "gemini",
            "reason": "gemini_http_fail",
            "status_code": response.get("status_code"),
            "error": response.get("error") or response.get("data"),
            "result": None,
        }

    text = _extract_gemini_text(response.get("data") or {})
    if not text:
        return {
            "ok": False,
            "provider": "gemini",
            "reason": "gemini_empty_text",
            "status_code": response.get("status_code"),
            "error": response.get("data"),
            "result": None,
        }

    return {
        "ok": True,
        "provider": "gemini",
        "model": chosen_model,
        "fallback_used": False,
        "result": text,
    }


def _critical_task(task_type: str) -> bool:
    normalized = (task_type or "").strip().lower()
    critical_types = {
        "critical",
        "strategy",
        "script",
        "planner",
        "editorial",
        "caption",
        "copy",
        "headline",
        "hook",
    }
    return normalized in critical_types


def _stub_fallback(task_type: str, input_data: Any) -> dict[str, Any]:
    text = str(input_data).strip()
    return {
        "ok": True,
        "provider": "fallback",
        "fallback_used": True,
        "result": f"[FALLBACK::{task_type}] {text[:700]}",
        "reason": "all_providers_unavailable_or_failed",
    }


def generate_text(
    task_type: str,
    input_data: Any,
) -> dict[str, Any]:
    prompt = str(input_data).strip()
    provider_mode = DEFAULT_PROVIDER

    if provider_mode == "openai":
        result = openai_generate_text(prompt)
        return result if result.get("ok") else _stub_fallback(task_type, input_data)

    if provider_mode == "gemini":
        result = gemini_generate_text(prompt)
        return result if result.get("ok") else _stub_fallback(task_type, input_data)

    if provider_mode == "stub":
        return _stub_fallback(task_type, input_data)

    # auto
    if _critical_task(task_type):
        primary = openai_generate_text(prompt)
        if primary.get("ok"):
            return primary

        secondary = gemini_generate_text(prompt)
        if secondary.get("ok"):
            secondary["fallback_used"] = True
            secondary["reason"] = "openai_failed_then_gemini_used"
            return secondary

        return _stub_fallback(task_type, input_data)

    primary = gemini_generate_text(prompt)
    if primary.get("ok"):
        return primary

    secondary = openai_generate_text(prompt)
    if secondary.get("ok"):
        secondary["fallback_used"] = True
        secondary["reason"] = "gemini_failed_then_openai_used"
        return secondary

    return _stub_fallback(task_type, input_data)


def llm_orchestrator_status() -> dict[str, Any]:
    return {
        "ok": True,
        "default_provider_mode": DEFAULT_PROVIDER,
        "openai_enabled": not ACE_DISABLE_OPENAI and bool(OPENAI_API_KEY),
        "gemini_enabled": not ACE_DISABLE_GEMINI and bool(GEMINI_KEY),
        "openai_model": DEFAULT_OPENAI_MODEL,
        "gemini_model": DEFAULT_GEMINI_MODEL,
    }


def llm_orchestrator_examples() -> dict[str, Any]:
    return {
        "ok": True,
        "status": llm_orchestrator_status(),
        "critical_example": {
            "call": "generate_text('critical', 'Crie uma legenda forte sobre disciplina')",
            "expected_priority": "openai_then_gemini_then_fallback",
        },
        "non_critical_example": {
            "call": "generate_text('idea', 'Ideia curta sobre clareza')",
            "expected_priority": "gemini_then_openai_then_fallback",
        },
    }
