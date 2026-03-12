# ==========================================================
# ACE Ω SUPREME - CONSOLIDADO INTEGRAL
# ==========================================================

import os
import gc
import re
import json
import time
import random
import sqlite3
import threading
import datetime
import traceback
import hashlib
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import urlencode
from typing import Any, Dict, List, Optional

import requests
import numpy as np
from flask import Flask, jsonify, request, send_from_directory, redirect

try:
    from pytrends.request import TrendReq
except Exception:
    TrendReq = None

try:
    import google.generativeai as genai
except Exception:
    genai = None

try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None
    ImageDraw = None

try:
    from gtts import gTTS
except Exception:
    gTTS = None

try:
    from moviepy.video.VideoClip import ColorClip, TextClip, ImageClip
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    MOVIEPY_OK = True
except Exception:
    ColorClip = None
    TextClip = None
    ImageClip = None
    CompositeVideoClip = None
    AudioFileClip = None
    MOVIEPY_OK = False


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

def ace_env(key, default=None):
    return os.environ.get(key, default)


APP_NAME = "ACE Ω SUPREME"
PORT = int(ace_env("PORT", "10000"))
VERIFY_TOKEN = ace_env("VERIFY_TOKEN", "ACE_SIGILO_2026")
RENDER_URL = ace_env(
    "RENDER_EXTERNAL_URL",
    f"https://{ace_env('RENDER_EXTERNAL_HOSTNAME', 'localhost')}"
)

BASE_DIR = Path(__file__).resolve().parent
MEMORY_DIR = BASE_DIR / "memory"
TMP_DIR = BASE_DIR / "tmp_ace"
MEDIA_DIR = BASE_DIR / "ace_media"
ENGINES_DIR = BASE_DIR / "engines"

for d in [MEMORY_DIR, TMP_DIR, MEDIA_DIR, ENGINES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DB_PATH = MEMORY_DIR / "ace_supreme.db"
AUTH_PATH = MEMORY_DIR / "instagram_auth.json"

IG_TOKEN_ENV = ace_env("IG_TOKEN")
IG_ID_ENV = ace_env("IG_ID")
GEMINI_KEY = ace_env("GEMINI_KEY")
OPENAI_API_KEY = ace_env("OPENAI_API_KEY")
INSTAGRAM_APP_ID = (
    ace_env("INSTAGRAM_APP_ID")
    or ace_env("FACEBOOK_APP_ID")
    or ace_env("APP_ID")
    or ""
)
INSTAGRAM_APP_SECRET = (
    ace_env("INSTAGRAM_APP_SECRET")
    or ace_env("FACEBOOK_APP_SECRET")
    or ace_env("APP_SECRET")
    or ""
)
INSTAGRAM_REDIRECT_URI = ace_env(
    "INSTAGRAM_REDIRECT_URI",
    f"{RENDER_URL}/instagram/token"
)

ACE_FAST_MODE = ace_env("ACE_FAST_MODE", "1") == "1"
ACE_DISABLE_GEMINI = ace_env("ACE_DISABLE_GEMINI", "1") == "1"
ACE_ENABLE_REAL_PUBLISH = ace_env("ACE_ENABLE_REAL_PUBLISH", "0") == "1"
ACE_GRAPH_BASE_URL = ace_env("ACE_GRAPH_BASE_URL", "https://graph.facebook.com/v24.0")

app = Flask(__name__)

GEMINI_MODEL = None
GEMINI_MODEL_NAMES = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash",
]

if genai and GEMINI_KEY and not ACE_DISABLE_GEMINI:
    try:
        genai.configure(api_key=GEMINI_KEY)
        for m in GEMINI_MODEL_NAMES:
            try:
                GEMINI_MODEL = genai.GenerativeModel(m)
                break
            except Exception:
                continue
    except Exception:
        GEMINI_MODEL = None


# ==========================================================
# AUTH & LOGS
# ==========================================================

IG_TOKEN_RUNTIME = None
IG_ID_RUNTIME = None


def get_ig_token():
    return IG_TOKEN_RUNTIME or IG_TOKEN_ENV


def get_ig_id():
    return IG_ID_RUNTIME or IG_ID_ENV


def save_instagram_auth(token=None, user_id=None, meta=None):
    global IG_TOKEN_RUNTIME, IG_ID_RUNTIME
    payload = {
        "token": token or get_ig_token(),
        "user_id": user_id or get_ig_id(),
        "saved_at": datetime.datetime.now().isoformat(),
        "meta": meta or {},
    }
    try:
        AUTH_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass

    if payload.get("token"):
        IG_TOKEN_RUNTIME = payload["token"]
    if payload.get("user_id"):
        IG_ID_RUNTIME = str(payload["user_id"])


def load_instagram_auth():
    global IG_TOKEN_RUNTIME, IG_ID_RUNTIME
    if not AUTH_PATH.exists():
        return
    try:
        data = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
        IG_TOKEN_RUNTIME = data.get("token") or IG_TOKEN_RUNTIME
        IG_ID_RUNTIME = str(data.get("user_id")) if data.get("user_id") else IG_ID_RUNTIME
    except Exception:
        pass


load_instagram_auth()


def log(level, event, detail=""):
    stamp = datetime.datetime.now().isoformat()
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT,
                level TEXT,
                event TEXT,
                detail TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO logs (ts, level, event, detail) VALUES (?, ?, ?, ?)",
            (stamp, level, event, str(detail)[:4000]),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    print(f"[{APP_NAME}][{level}] {event} | {detail}")


# ==========================================================
# ESTADO GLOBAL & BANCO
# ==========================================================

ACE_STATE = {
    "boot_at": datetime.datetime.now().isoformat(),
    "last_cycle_at": None,
    "last_action_at": None,
    "last_action_type": None,
    "last_error": None,
    "healthy": True,
    "forced_actions": 0,
    "idle_hits": 0,
    "render_pings": 0,
    "mode": "OBSERVANDO",
    "last_trend": None,
    "last_style": None,
    "symbiosis_level": 0.0,
    "legacy_threads_started": False,
    "instagram_connected": bool(get_ig_token() and get_ig_id()),
    "instagram_last_auth_at": None,
}
STATE_LOCK = threading.Lock()


class ACE_Consciousness:
    def __init__(self):
        self.state = "OBSERVANDO"
        self.ego = 0.85
        self.moral = 0.2
        self.memory_capacity = 10000

    def ponderar(self, input_data):
        return "PROCESSANDO" if len(str(input_data)) >= 3 else "Irrelevante."


ACE_MIND = ACE_Consciousness()


def iniciar_banco():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    tables = [
        "thoughts (id INTEGER PRIMARY KEY, timestamp TEXT, thought TEXT, impact REAL)",
        "dna (gene TEXT PRIMARY KEY, value REAL, generation INTEGER)",
        "viral_logs (id INTEGER PRIMARY KEY, hook TEXT, score REAL, date TEXT)",
        "personalidade (dia TEXT, estilo TEXT, performance REAL)",
        "instagram_stats (data TEXT, alcance REAL, engajamento REAL, seguidores REAL)",
        "comentarios_virais (data TEXT, palavra TEXT, intensidade REAL)",
        "trends_profeticos (data TEXT, tema TEXT, intensidade REAL)",
        "api_usage (api TEXT PRIMARY KEY, qtd INTEGER, limite INTEGER, last_update TEXT)",
        "aprendizado (motor TEXT, acao TEXT, resultado REAL, data TEXT)",
        "posts (id INTEGER PRIMARY KEY, ts TEXT, trend TEXT, estilo TEXT, tipo TEXT, conteudo TEXT, media_path TEXT, status TEXT)",
        "trend_performance (trend TEXT PRIMARY KEY, attempts INTEGER, successes INTEGER, failures INTEGER, avg_score REAL, last_result REAL, last_ts TEXT)",
        "hook_memory (hook TEXT PRIMARY KEY, score REAL, uses INTEGER, last_ts TEXT)",
        "task_memory (id INTEGER PRIMARY KEY, task_type TEXT, trend TEXT, estilo TEXT, priority REAL, retries INTEGER, status TEXT, reason TEXT, ts TEXT)",
        "ace_trend_history (id INTEGER PRIMARY KEY, trend TEXT NOT NULL, trend_norm TEXT NOT NULL, used_at TEXT NOT NULL)",
        "ace_content_history (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, trend TEXT, trend_norm TEXT, content_type TEXT, title TEXT, hook TEXT, body TEXT, content_hash TEXT, score REAL DEFAULT 0, status TEXT DEFAULT 'generated', reason TEXT DEFAULT '')",
        "ace_candidate_posts (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, trend TEXT, trend_norm TEXT, content_type TEXT, title TEXT, hook TEXT, body TEXT, meta_json TEXT, score REAL DEFAULT 0, selected INTEGER DEFAULT 0)",
        "instagram_auth_log (id INTEGER PRIMARY KEY, ts TEXT, action TEXT, detail TEXT)",
    ]

    for t in tables:
        cur.execute(f"CREATE TABLE IF NOT EXISTS {t}")

    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_ace_trend_history_norm_used_at ON ace_trend_history(trend_norm, used_at)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_ace_content_history_created_at ON ace_content_history(created_at)"
    )
    cur.executemany(
        "INSERT OR IGNORE INTO dna VALUES (?,?,?)",
        [("ego", 0.9, 1), ("caos", 0.3, 1), ("sedução", 0.7, 1), ("brutalidade", 0.8, 1)],
    )

    conn.commit()
    conn.close()


iniciar_banco()


# ==========================================================
# DNA & API MGMT
# ==========================================================

def evoluir_dna(perf):
    conn = sqlite3.connect(DB_PATH)
    mut = 1.05 if perf > 1.2 else 0.95
    conn.execute(
        "UPDATE dna SET value = value * ?, generation = generation + 1",
        (mut,),
    )
    conn.commit()
    conn.close()


def registrar_api(api, qtd, lim):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT OR REPLACE INTO api_usage VALUES (?,?,?,?)",
            (api, qtd, lim, datetime.datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log("WARN", "registrar_api_fail", e)


def verificar_api(api, limite=1000):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT qtd, last_update FROM api_usage WHERE api=?",
        (api,),
    ).fetchone()
    conn.close()

    if row is None:
        registrar_api(api, 0, limite)
        return True

    qtd, last_update = row
    try:
        last_dt = datetime.datetime.fromisoformat(last_update)
    except Exception:
        registrar_api(api, 0, limite)
        return True

    if (datetime.datetime.now() - last_dt).seconds > 3600:
        registrar_api(api, 0, limite)
        return True

    return qtd < limite


def usar_api(api, qtd=1):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT qtd, limite FROM api_usage WHERE api=?",
        (api,),
    ).fetchone()

    if row:
        conn.execute(
            "UPDATE api_usage SET qtd=?, last_update=? WHERE api=?",
            (row[0] + qtd, datetime.datetime.now().isoformat(), api),
        )
    else:
        conn.execute(
            "INSERT OR REPLACE INTO api_usage VALUES (?,?,?,?)",
            (api, qtd, 1000, datetime.datetime.now().isoformat()),
        )

    conn.commit()
    conn.close()


# ==========================================================
# TASK ENGINE STATE
# ==========================================================

TASK_QUEUE: List[Dict[str, Any]] = []
TASK_LOCK = threading.Lock()
PERFORMANCE_STATE = {
    "reel_score": 1.0,
    "carrossel_score": 1.0,
    "best_hour_bias": {},
    "fail_streak": 0,
    "success_streak": 0,
}


# ==========================================================
# PERSONALIDADE & TRENDS
# ==========================================================

def escolher_personalidade():
    dia = datetime.datetime.now().strftime("%A")
    estilos = {
        "Monday": ["motivacional", "estoico"],
        "Tuesday": ["agressivo", "direto"],
        "Wednesday": ["educativo", "estratégico"],
        "Thursday": ["impactante", "profetico"],
        "Friday": ["sarcastico", "reflexivo"],
        "Saturday": ["inspirador", "leve"],
        "Sunday": ["espiritual", "profundo"],
    }
    estilo = random.choice(estilos.get(dia, ["direto"]))
    ACE_STATE["last_style"] = estilo
    return estilo


def capturar_trend_brasil():
    if TrendReq is None or ACE_FAST_MODE:
        trend = "fé e propósito"
    else:
        try:
            pytrends = TrendReq(hl="pt-BR", tz=360)
            df = pytrends.trending_searches(pn="brazil")
            trend = str(df[0][0]).strip()
        except Exception as e:
            log("WARN", "trend_fail", e)
            trend = "fé e propósito"

    ACE_STATE["last_trend"] = trend
    return trend


def capturar_trend_brasil_v6():
    return capturar_trend_brasil()


def capturar_trend_do_momento():
    return capturar_trend_brasil()


def obter_trend_brasil():
    return capturar_trend_brasil()


def analisar_comentarios():
    coms = [random.choice(["verdade", "ninguém fala", "mudou minha vida"]) for _ in range(10)]
    conn = sqlite3.connect(DB_PATH)
    for c in coms:
        for p in ["verdade", "vida", "sentido"]:
            if p in c.lower():
                conn.execute(
                    "INSERT INTO comentarios_virais VALUES (?,?,?)",
                    (datetime.datetime.now().isoformat(), p, random.uniform(0.4, 1.0)),
                )
    conn.commit()
    conn.close()


def detectar_trend_emergente():
    conn = sqlite3.connect(DB_PATH)
    results = conn.execute(
        """
        SELECT palavra, AVG(intensidade)
        FROM comentarios_virais
        GROUP BY palavra
        ORDER BY AVG(intensidade) DESC
        LIMIT 5
        """
    ).fetchall()

    for p, intensidade in results:
        if intensidade and intensidade > 0.7:
            conn.execute(
                "INSERT INTO trends_profeticos VALUES (?,?,?)",
                (datetime.datetime.now().isoformat(), p, intensidade),
            )

    conn.commit()
    conn.close()


def get_recent_signal_score():
    try:
        conn = sqlite3.connect(DB_PATH)
        c_sig = conn.execute(
            "SELECT AVG(intensidade) FROM comentarios_virais WHERE data >= datetime('now', '-6 hours')"
        ).fetchone()[0] or 0.5
        t_sig = conn.execute(
            "SELECT AVG(intensidade) FROM trends_profeticos WHERE data >= datetime('now', '-12 hours')"
        ).fetchone()[0] or 0.5
        conn.close()
        return float(c_sig) * 0.55 + float(t_sig) * 0.45
    except Exception:
        return 0.5


# ==========================================================
# IA TEXTO
# ==========================================================

def gerar_texto_gpt(prompt):
    if not verificar_api("GPT", 200):
        return f"[LIMIT] {prompt[:50]}"
    usar_api("GPT")
    return f"[GPT] Resposta para: {prompt[:100]}"


def gerar_ideia_gemini(trend):
    if ACE_DISABLE_GEMINI:
        return f"Ideia para {trend}"

    if not verificar_api("Gemini", 300):
        return f"Ideia para {trend}"

    usar_api("Gemini")
    if GEMINI_MODEL:
        for m in GEMINI_MODEL_NAMES:
            try:
                res = genai.GenerativeModel(m).generate_content(
                    f"Ideia curta e forte em PT-BR sobre: {trend}"
                )
                if getattr(res, "text", None):
                    return res.text.strip()
            except Exception:
                continue
    return f"Ideia para {trend}"


def motor_radar_v7():
    t = capturar_trend_brasil().lower()
    return t, gerar_ideia_gemini(t)


# ==========================================================
# HOOKS & PERFORMANCE
# ==========================================================

def ace_brain_upgrade(tema):
    h = random.choice(
        [
            f"A verdade sobre {tema}",
            f"O erro em {tema}",
            f"Segredo de {tema}",
        ]
    )
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO viral_logs (hook, score, date) VALUES (?,?,?)",
        (h, 1.0, datetime.datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return h


def score_hook_memory(hook, delta):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT score, uses FROM hook_memory WHERE hook=?",
        (hook,),
    ).fetchone()

    s, u = (float(row[0]) + delta, row[1] + 1) if row else (1.0 + delta, 1)

    conn.execute(
        "INSERT OR REPLACE INTO hook_memory (hook, score, uses, last_ts) VALUES (?,?,?,?)",
        (hook, s, u, datetime.datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_best_saved_hook(trend):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT hook FROM hook_memory WHERE hook LIKE ? ORDER BY score DESC LIMIT 1",
        (f"%{trend}%",),
    ).fetchone()
    conn.close()
    return row[0] if row else ace_brain_upgrade(trend)


def get_trend_memory(trend):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT attempts, successes, failures, avg_score, last_result FROM trend_performance WHERE trend = ?",
        (trend,),
    ).fetchone()
    conn.close()

    if row:
        return {
            "attempts": row[0],
            "successes": row[1],
            "failures": row[2],
            "avg_score": row[3] or 1.0,
            "last_result": row[4] or 1.0,
        }

    return {
        "attempts": 0,
        "successes": 0,
        "failures": 0,
        "avg_score": 1.0,
        "last_result": 1.0,
    }


def update_trend_memory(trend, success, score):
    m = get_trend_memory(trend)
    att = m["attempts"] + 1
    avg = ((m["avg_score"] * m["attempts"]) + score) / att

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO trend_performance VALUES (?,?,?,?,?,?,?)",
        (
            trend,
            att,
            m["successes"] + (1 if success else 0),
            m["failures"] + (0 if success else 1),
            avg,
            score,
            datetime.datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


# ==========================================================
# CAMADA 4: GOVERNANÇA
# ==========================================================

ACE_LAYER4_CONFIG = {
    "cooldown_minutes": int(ace_env("ACE_COOLDOWN_MINUTES", "60")),
    "max_posts_per_hour": int(ace_env("ACE_MAX_POSTS_PER_HOUR", "4")),
    "min_trend_chars": 4,
    "min_trend_words": 2,
    "similarity_threshold": 0.8,
    "history_compare_limit": 50,
}
ACE_LAYER4_LOCK = threading.Lock()
ACE_STOPWORDS = {"a", "o", "e", "de", "do", "da", "em", "um", "para", "com", "que", "se"}


def ace_normalize_text(t):
    t = "".join(
        c
        for c in unicodedata.normalize("NFKD", (t or "").lower())
        if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", t)).strip()


def ace_compact_signature(t):
    return hashlib.sha256(ace_normalize_text(t).encode()).hexdigest()


def ace_govern_post(trend, content_type, title, hook, body):
    norm = ace_normalize_text(trend)
    if len(norm) < 4:
        return {"approved": False, "reason": "trend_curta"}

    conn = sqlite3.connect(DB_PATH)
    limit_time = (datetime.datetime.now() - datetime.timedelta(minutes=60)).isoformat()

    if conn.execute(
        "SELECT 1 FROM ace_trend_history WHERE trend_norm=? AND used_at>=?",
        (norm, limit_time),
    ).fetchone():
        conn.close()
        return {"approved": False, "reason": "cooldown"}

    recent = conn.execute(
        "SELECT COUNT(*) FROM ace_content_history WHERE created_at >= ?",
        (limit_time,),
    ).fetchone()[0]

    if recent >= ACE_LAYER4_CONFIG["max_posts_per_hour"]:
        conn.close()
        return {"approved": False, "reason": "rate_limit"}

    h_cand = ace_compact_signature(f"{title} {hook} {body}")
    if conn.execute(
        "SELECT 1 FROM ace_content_history WHERE content_hash=?",
        (h_cand,),
    ).fetchone():
        conn.close()
        return {"approved": False, "reason": "duplicado"}

    score = round(random.uniform(0.7, 1.0), 4)
    now = datetime.datetime.now().isoformat()

    conn.execute(
        """
        INSERT INTO ace_content_history
        (created_at, trend, trend_norm, content_type, title, hook, body, content_hash, score, status, reason)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (now, trend, norm, content_type, title, hook, body, h_cand, score, "approved", "ok"),
    )
    conn.execute(
        "INSERT INTO ace_trend_history (trend, trend_norm, used_at) VALUES (?,?,?)",
        (trend, norm, now),
    )
    conn.commit()
    conn.close()
    return {"approved": True, "score": score}


# ==========================================================
# GERAÇÃO DE MÍDIA
# ==========================================================

def make_audio(text):
    if gTTS is None:
        return None
    try:
        p = MEDIA_DIR / f"vox_{int(time.time())}.mp3"
        gTTS(text=text[:450], lang="pt-br").save(str(p))
        return str(p)
    except Exception:
        return None


def make_poster(text):
    if Image is None or ImageDraw is None:
        return None
    try:
        out = MEDIA_DIR / f"poster_{int(time.time())}.png"
        img = Image.new("RGB", (1080, 1920), (8, 8, 12))
        d = ImageDraw.Draw(img)
        lines = [text[i:i + 28] for i in range(0, len(text), 28)]
        y = 220
        for l in lines[:12]:
            d.text((80, y), l, fill=(255, 215, 0))
            y += 90
        img.save(out)
        return str(out)
    except Exception:
        return None


def make_reel(text, audio_path=None):
    if not MOVIEPY_OK:
        return None
    try:
        bg = ColorClip(size=(1080, 1920), color=(5, 0, 5), duration=12)
        out = MEDIA_DIR / f"reel_{int(time.time())}.mp4"
        if audio_path and os.path.exists(audio_path):
            bg = bg.with_audio(AudioFileClip(audio_path))
        bg.write_videofile(str(out), fps=24, codec="libx264", logger=None)
        return str(out)
    except Exception:
        return None


# ==========================================================
# ORQUESTRAÇÃO DE PUBLICAÇÃO
# ==========================================================

def processar_publicacao_governada(trend, style, tipo, title, hook, body, media_path=None):
    govern = ace_govern_post(trend, tipo, title, hook, body)

    if not govern.get("approved"):
        return {
            "ok": False,
            "reason": govern.get("reason"),
            "blocked": True,
        }

    publish = postar_instagram(body, tipo=tipo, media_path=media_path)

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO posts (ts, trend, estilo, tipo, conteudo, media_path, status) VALUES (?,?,?,?,?,?,?)",
        (
            datetime.datetime.now().isoformat(),
            trend,
            style,
            tipo,
            body,
            media_path or "",
            "published" if publish.get("ok") else "generated",
        ),
    )
    conn.commit()
    conn.close()

    ACE_STATE["last_action_at"] = datetime.datetime.now().isoformat()
    ACE_STATE["last_action_type"] = tipo

    return {
        "ok": True,
        "score": govern.get("score", 0.0),
        "publish": publish,
    }


# ==========================================================
# TASK ENGINE
# ==========================================================

def queue_task(task_type, trend=None, style=None, priority=1.0, retries=0):
    trend = trend or capturar_trend_brasil()
    style = style or escolher_personalidade()
    with TASK_LOCK:
        TASK_QUEUE.append(
            {
                "id": int(time.time() * 1000),
                "type": task_type,
                "trend": trend,
                "style": style,
                "priority": priority,
                "retries": retries,
            }
        )
        TASK_QUEUE.sort(key=lambda x: x["priority"], reverse=True)


def execute_task(task):
    trend, style, t_type = task["trend"], task["style"], task["type"]
    try:
        if t_type in ["reel", "carrossel"]:
            hook = get_best_saved_hook(trend)
            body = gerar_texto_gpt(f"Conteúdo {t_type} sobre {trend}")
            res = processar_publicacao_governada(
                trend,
                style,
                t_type,
                hook,
                hook,
                body,
                make_poster(body),
            )
            if res.get("ok"):
                update_trend_memory(trend, True, 1.0)
                return {"ok": True}
        return {"ok": False, "error": "blocked or unknown"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def queue_executor_loop():
    while True:
        task = None
        with TASK_LOCK:
            if TASK_QUEUE:
                task = TASK_QUEUE.pop(0)
        if task:
            execute_task(task)
        time.sleep(5)


# ==========================================================
# INSTAGRAM & OAUTH
# ==========================================================

def postar_instagram(conteudo, tipo="reel", media_path=None):
    if ACE_ENABLE_REAL_PUBLISH:
        res = ace_real_publish_if_possible(conteudo, tipo, media_path)
        if res.get("ok"):
            return res
    print(f"[FALLBACK {tipo}] {conteudo[:100]}")
    return {"ok": False, "fallback": True}


def exchange_code_for_token(code):
    if not INSTAGRAM_APP_ID:
        return {"ok": False, "error": "No ID"}
    try:
        r = requests.post(
            "https://api.instagram.com/oauth/access_token",
            data={
                "client_id": INSTAGRAM_APP_ID,
                "client_secret": INSTAGRAM_APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": INSTAGRAM_REDIRECT_URI,
                "code": code,
            },
            timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            save_instagram_auth(data.get("access_token"), data.get("user_id"))
            return {"ok": True, "data": data}
        return {"ok": False, "error": r.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ==========================================================
# EXTENSION PACK INTEGRADO
# ==========================================================

def ace_real_publish_if_possible(conteudo, tipo, media_path):
    ig_id, token = get_ig_id(), get_ig_token()
    if not ig_id or not token or not media_path:
        return {"ok": False, "reason": "missing_data"}

    m_url = f"{RENDER_URL}/media/{Path(media_path).name}"
    m_kind = "REELS" if tipo == "reel" else "IMAGE"

    try:
        res = requests.post(
            f"{ACE_GRAPH_BASE_URL}/{ig_id}/media",
            data={
                "access_token": token,
                "caption": conteudo,
                "video_url" if tipo == "reel" else "image_url": m_url,
                "media_type": m_kind,
            },
            timeout=30,
        )
        c_id = res.json().get("id")
        if c_id:
            pub = requests.post(
                f"{ACE_GRAPH_BASE_URL}/{ig_id}/media_publish",
                data={"access_token": token, "creation_id": c_id},
                timeout=30,
            )
            return {"ok": pub.status_code == 200, "data": pub.json()}
        return {"ok": False, "error": res.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ==========================================================
# ROTAS FLASK
# ==========================================================

@app.route("/")
def home():
    return jsonify({"status": APP_NAME, "online": True, "instagram": bool(get_ig_id())})


@app.route("/status")
def status():
    return jsonify({"app": APP_NAME, "state": ACE_STATE, "tasks": len(TASK_QUEUE)})


@app.route("/instagram/auth")
def instagram_auth():
    params = {
        "client_id": INSTAGRAM_APP_ID,
        "redirect_uri": INSTAGRAM_REDIRECT_URI,
        "response_type": "code",
        "scope": "instagram_business_basic,instagram_business_content_publish",
    }
    return redirect(f"https://www.instagram.com/oauth/authorize?{urlencode(params)}")


@app.route("/instagram/token")
def instagram_token_callback():
    code = request.args.get("code")
    if not code:
        return "No code", 400
    res = exchange_code_for_token(code)
    return jsonify(res)


@app.route("/media/<path:filename>")
def serve_static(filename):
    return send_from_directory(str(MEDIA_DIR), filename)


@app.route("/force")
def force_route():
    queue_task("reel", priority=2.0)
    return jsonify({"status": "queued"})


@app.route("/generate/reel")
def generate_reel_route():
    trend = capturar_trend_brasil()
    style = escolher_personalidade()
    hook = get_best_saved_hook(trend)
    body = gerar_texto_gpt(f"Conteúdo reel sobre {trend}")
    audio_path = make_audio(body)
    media_path = make_reel(body, audio_path=audio_path) or make_poster(body)
    res = processar_publicacao_governada(trend, style, "reel", hook, hook, body, media_path)
    return jsonify(res)


@app.route("/generate/carrossel")
def generate_carrossel_route():
    trend = capturar_trend_brasil()
    style = escolher_personalidade()
    hook = get_best_saved_hook(trend)
    body = gerar_texto_gpt(f"Conteúdo carrossel sobre {trend}")
    media_path = make_poster(body)
    res = processar_publicacao_governada(trend, style, "carrossel", hook, hook, body, media_path)
    return jsonify(res)


# ==========================================================
# WATCHDOGS & BOOT
# ==========================================================

def supervisor_loop():
    while True:
        ACE_STATE["last_cycle_at"] = datetime.datetime.now().isoformat()
        if not TASK_QUEUE and random.random() > 0.7:
            queue_task("reel")
        time.sleep(60)


def boot():
    log("INFO", "boot", "ACE Iniciando...")
    threading.Thread(target=queue_executor_loop, daemon=True).start()
    threading.Thread(target=supervisor_loop, daemon=True).start()


if __name__ == "__main__":
    boot()
    app.run(host="0.0.0.0", port=PORT)
