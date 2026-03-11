
import os, time, datetime, gc, requests, threading, random, re, json, sqlite3, math
import numpy as np
from collections import Counter
from google import genai
from pytrends.request import TrendReq
from flask import Flask, send_from_directory, request
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, AudioFileClip, vfx
from PIL import Image, ImageDraw
from gtts import gTTS

# ==========================================================
# 🔐 CONFIGURAÇÕES E AMBIENTE (RENDER-READY)
# ==========================================================

def safe_get_env(key, default="DEMO"):
    return os.environ.get(key, default)

IG_TOKEN = safe_get_env("IG_TOKEN")
GEMINI_KEY = safe_get_env("GEMINI_KEY")
IG_ID = safe_get_env("IG_ID")
VERIFY_TOKEN = "ACE_SIGILO_2026"
PORT = int(os.environ.get("PORT", 5000))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")

client = genai.Client(api_key=GEMINI_KEY)
app = Flask(__name__)

# No Render, /content/ não existe, usamos caminhos persistentes ou /tmp
OUT_PATH = "/tmp/ace_media/" if not os.path.exists("./ace_media/") else "./ace_media/"
os.makedirs(OUT_PATH, exist_ok=True)
DB_PATH = os.path.join(OUT_PATH, "ace_memory.db")

GENES = {"zoom": 0.05, "contraste": 1.1, "caos": 0.2}

# ==========================================================
# 🧠 MEMÓRIA E INTELIGÊNCIA SOCIOCULTURAL
# ==========================================================

def init_memory():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS posts
                 (id INTEGER PRIMARY KEY, data TEXT, tema TEXT, hook TEXT, score REAL)""")
    conn.commit()
    conn.close()

def registrar_post(tema, hook, score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO posts(data,tema,hook,score) VALUES(?,?,?,?)",
              (str(datetime.datetime.now()), tema, hook, score))
    conn.commit()
    conn.close()

def radar_global():
    try:
        pytrend = TrendReq(hl='pt-BR')
        trending = pytrend.trending_searches(pn='brazil')
        termos = list(trending[0])
        palavras = []
        for t in termos: palavras += re.findall(r'\w+', t.lower())
        return Counter(palavras).most_common(1)[0][0]
    except:
        return "disciplina"

# ==========================================================
# ⚡ MOTORES DE ALTO IMPACTO (DOPAMINA & RETENÇÃO)
# ==========================================================

RETENTION_WORDS = ["ninguém","verdade","segredo","erro","alerta","proibido","revelado","chocante"]
EMOCOES = {"curiosidade":["segredo","revelado","verdade"], "medo":["alerta","perigo","cuidado"], "raiva":["erro","mentira","enganado"]}

def score_dopamina(texto):
    score = 1.0
    for g in ["segredo","verdade","erro","oculto","alerta","proibido"]:
        if g in texto.lower(): score *= 1.25
    if "?" in texto: score *= 1.1
    return score

def score_retencao(texto):
    score = 1.0
    for w in RETENTION_WORDS:
        if w in texto.lower(): score *= 1.15
    return score

def score_emocional(texto):
    score = 1.0
    for grupo in EMOCOES.values():
        for w in grupo:
            if w in texto.lower(): score *= 1.12
    return score

def prever_viralidade(hook):
    return score_dopamina(hook) * score_retencao(hook) * random.uniform(0.9, 1.1)

def recomendar_tema():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT tema, AVG(score) FROM posts GROUP BY tema ORDER BY AVG(score) DESC LIMIT 5")
        dados = c.fetchall()
        conn.close()
        return random.choice(dados)[0] if dados else radar_global()
    except: return radar_global()

def gerar_hook_otimizado(tema):
    hooks = [f"A verdade que ninguém aceita sobre {tema}", f"O erro silencioso em {tema}", 
             f"O segredo oculto de {tema}", f"O alerta brutal sobre {tema}", 
             f"O que nunca te contaram sobre {tema}", f"Isso pode mudar tudo em {tema}"]
    return max(hooks, key=lambda h: prever_viralidade(h) * score_emocional(h))

# ==========================================================
# 🎨 STUDIO & MOTOR OMNI V4000
# ==========================================================

def motor_omni_v4000(entrada):
    try:
        res = client.models.generate_content(model="gemini-2.0-flash", contents=f"ACE libertaverdades. Brutalidade estoica. Contexto: {entrada}")
        return res.text
    except: return "A disciplina é a única liberdade."

def fabricar_arsenal_v4000():
    print("🎨 STUDIO V4000 ATIVO")
    texto = motor_omni_v4000("Gere 10 verdades brutais.")
    frases = re.split(r'\d.', texto)[1:11]
    audio_p = os.path.join(OUT_PATH, "voice.mp3")
    gTTS(text=texto[:400], lang='pt-br').save(audio_p)
    
    bg = ColorClip(size=(1080, 1920), color=(5, 0, 0), duration=10)
    txt = TextClip(texto[:200], fontsize=70, color='yellow', font='DejaVu-Sans-Bold', size=(900, 1600), method='caption')
    video = CompositeVideoClip([bg, txt.set_position("center")])
    video.set_audio(AudioFileClip(audio_p)).fx(vfx.lum_contrast, lum=1.03, contrast=1.1).write_videofile(
        os.path.join(OUT_PATH, "reel.mp4"), fps=24, codec="libx264"
    )
    for i, f in enumerate(frases, 1):
        img = Image.new('RGB', (1080, 1080), (2, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((130, 450), f"ALERTA {i}\n\n{f[:100]}", fill=(255, 255, 255))
        img.save(os.path.join(OUT_PATH, f"slide_{i}.jpg"))

# ==========================================================
# 🚀 GOVERNANÇA E PUBLICAÇÃO
# ==========================================================

def ace_governance(tema, score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM posts WHERE tema=? AND date(data)=date('now')", (tema,))
    count_today = c.fetchone()[0]
    conn.close()
    if count_today >= 2 or score < 1.05: return False
    return True

def publicar_v4(url_media, legenda):
    res = requests.post(f"https://graph.facebook.com/v20.0/{IG_ID}/media",
                        data={"video_url": url_media, "media_type": "REELS", "caption": legenda, "access_token": IG_TOKEN}).json()
    creation_id = res.get("id")
    if creation_id:
        time.sleep(45)
        requests.post(f"https://graph.facebook.com/v20.0/{IG_ID}/media_publish",
                      data={"creation_id": creation_id, "access_token": IG_TOKEN})

# ==========================================================
# 🌐 SERVIDOR FLASK (ENDPOINTS)
# ==========================================================

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Erro", 403

@app.route('/media/<path:filename>')
def serve(filename):
    return send_from_directory(OUT_PATH, filename)

@app.route("/stats")
def stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM posts")
    total = c.fetchone()[0]
    conn.close()
    return {"posts": total, "genes": GENES, "status": "ACE OMEGA ONLINE"}

# ==========================================================
# 🧬 CICLO MESTRE EVOLUTIVO (THREADED)
# ==========================================================

def ciclo_mestre_render():
    init_memory()
    while True:
        try:
            agora = datetime.datetime.now()
            # Postagens em horários de pico (6, 12, 18, 21)
            if agora.minute == 0 and agora.hour in [6, 12, 18, 21]:
                tema = recomendar_tema()
                hook = gerar_hook_otimizado(tema)
                score = prever_viralidade(hook)
                
                if ace_governance(tema, score):
                    fabricar_arsenal_v4000()
                    legenda = motor_omni_v4000(f"Legenda viral para: {hook}")
                    publicar_v4(f"{RENDER_URL}/media/reel.mp4", legenda)
                    registrar_post(tema, hook, score)
                    # Mutação
                    if score > 1.2: GENES["zoom"] *= 1.05
                    else: GENES["zoom"] *= 0.97
                    print(f"✅ POST EXECUTADO: {tema}")
            
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ ERRO NO CICLO: {e}")
            time.sleep(300)

# ==========================================================
# 🚀 START FINAL
# ==========================================================

if __name__ == "__main__":
    # Inicia o ciclo de autonomia em uma thread separada
    threading.Thread(target=ciclo_mestre_render, daemon=True).start()
    # Roda o Flask na porta correta do Render
    app.run(host='0.0.0.0', port=PORT)
