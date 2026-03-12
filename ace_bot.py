import os
import json
import time
import random
import sqlite3
import threading
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from flask import Flask, jsonify, request, send_from_directory, redirect

# ==========================================================
# CONFIG
# ==========================================================

def env(key, default=None):
    return os.environ.get(key, default)

APP_NAME = "ACE SUPREME"
PORT = int(env("PORT", "10000"))

BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = BASE_DIR / "ace_media"
MEMORY_DIR = BASE_DIR / "memory"

MEDIA_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)

DB_PATH = MEMORY_DIR / "ace.db"

ACE_ENABLE_REAL_PUBLISH = env("ACE_ENABLE_REAL_PUBLISH", "0") == "1"

app = Flask(__name__)

# ==========================================================
# DATABASE
# ==========================================================

def init_db():

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY,
        ts TEXT,
        trend TEXT,
        tipo TEXT,
        conteudo TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ==========================================================
# STATE
# ==========================================================

STATE = {
    "boot": datetime.datetime.now().isoformat(),
    "last_action": None
}

TASK_QUEUE: List[Dict[str,Any]] = []
TASK_LOCK = threading.Lock()

# ==========================================================
# SIMPLE TREND ENGINE
# ==========================================================

def capturar_trend():

    trends = [
        "fé e propósito",
        "mentalidade vencedora",
        "disciplina",
        "prosperidade",
        "transformação de vida"
    ]

    return random.choice(trends)

# ==========================================================
# TEXT ENGINE
# ==========================================================

def gerar_texto(prompt):

    return f"{prompt}. Desenvolva disciplina diária. O crescimento começa quando você decide mudar."

# ==========================================================
# MEDIA
# ==========================================================

def gerar_poster(text):

    filename = f"poster_{int(time.time())}.txt"
    path = MEDIA_DIR / filename

    with open(path,"w") as f:
        f.write(text)

    return str(path)

# ==========================================================
# INSTAGRAM (FALLBACK)
# ==========================================================

def postar_instagram(conteudo):

    print("POST SIMULADO")
    print(conteudo[:120])

    return {"ok":False,"fallback":True}

# ==========================================================
# CONTENT
# ==========================================================

def gerar_reel():

    trend = capturar_trend()

    body = gerar_texto(f"Reel sobre {trend}")

    media = gerar_poster(body)

    postar_instagram(body)

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "INSERT INTO posts VALUES(NULL,?,?,?,?)",
        (
            datetime.datetime.now().isoformat(),
            trend,
            "reel",
            body
        )
    )

    conn.commit()
    conn.close()

    STATE["last_action"] = "reel"

    return {
        "ok":True,
        "trend":trend,
        "content":body,
        "media":media
    }

def gerar_carrossel():

    trend = capturar_trend()

    body = gerar_texto(f"Carrossel sobre {trend}")

    media = gerar_poster(body)

    postar_instagram(body)

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "INSERT INTO posts VALUES(NULL,?,?,?,?)",
        (
            datetime.datetime.now().isoformat(),
            trend,
            "carrossel",
            body
        )
    )

    conn.commit()
    conn.close()

    STATE["last_action"] = "carrossel"

    return {
        "ok":True,
        "trend":trend,
        "content":body,
        "media":media
    }

# ==========================================================
# TASK ENGINE
# ==========================================================

def queue_task(tipo):

    with TASK_LOCK:

        TASK_QUEUE.append({
            "type":tipo
        })

def worker():

    while True:

        task=None

        with TASK_LOCK:

            if TASK_QUEUE:
                task=TASK_QUEUE.pop(0)

        if task:

            if task["type"]=="reel":
                gerar_reel()

            if task["type"]=="carrossel":
                gerar_carrossel()

        time.sleep(5)

# ==========================================================
# ROUTES
# ==========================================================

@app.route("/")
def home():

    return jsonify({
        "status":APP_NAME,
        "online":True
    })

@app.route("/status")
def status():

    return jsonify({
        "state":STATE,
        "queue":len(TASK_QUEUE)
    })

@app.route("/generate/reel")
def route_reel():

    return jsonify(gerar_reel())

@app.route("/generate/carrossel")
def route_carrossel():

    return jsonify(gerar_carrossel())

@app.route("/force")
def force():

    queue_task("reel")

    return jsonify({"queued":True})

@app.route("/media/<path:filename>")
def media(filename):

    return send_from_directory(str(MEDIA_DIR),filename)

# ==========================================================
# BOOT
# ==========================================================

def boot():

    t=threading.Thread(target=worker,daemon=True)
    t.start()

boot()

# ==========================================================

if __name__ == "__main__":

    app.run(host="0.0.0.0",port=PORT)
