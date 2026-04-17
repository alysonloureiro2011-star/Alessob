#!/usr/bin/env python3
"""
Script utilitário para disparar uma publicação real via POST no endpoint /run.
Use: python run_real_publish.py <base_url> <tema>
Ex.: python run_real_publish.py https://ace-f4nb.onrender.com "o poder da disciplina"
"""

from __future__ import annotations

import json
import sys
import requests

def run_real_publish(base_url: str, trend: str, probe_state: str = "internal_lab") -> dict:
    url = f"{base_url.rstrip('/')}/run"
    payload = {
        "trend": trend,
        "force_placeholder": False,
        "force_real_probe": True,
        "probe_state": probe_state,
        "compact": False,
    }
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: run_real_publish.py <base_url> <tema>")
        sys.exit(1)
    base_url = sys.argv[1]
    trend = " ".join(sys.argv[2:])
    result = run_real_publish(base_url, trend)
    print(json.dumps(result, indent=2, ensure_ascii=False))
