# ==========================================================
# 🚀 PASSO 0: DEPENDÊNCIAS
# ==========================================================
!apt-get update && apt-get install -y imagemagick ffmpeg fonts-dejavu
!pip install -q pytrends google-genai flask requests pyngrok moviepy Pillow gTTS numpy

# ==========================================================
# 🏛️ ACE Ω V6000+ CONSOLIDADO
# ==========================================================

import os, time, datetime, gc, requests, threading, random, re, json, sqlite3
import numpy as np
from collections import Counter
from google import genai
from pytrends.request import TrendReq
from flask import Flask, send_from_directory, request
from pyngrok import ngrok
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, AudioFileClip, vfx
from PIL import Image, ImageDraw
from gtts import gTTS

# ==========================================================
# 🔐 SEGREDOS
# ==========================================================

def get_secret(name):
    return os.environ.get(name, "DEMO")

IG_TOKEN = get_secret("IG_TOKEN")
GEMINI_KEY = get_secret("GEMINI_KEY")
IG_ID = get_secret("IG_ID")
NGROK_TOKEN = get_secret("NGROK_TOKEN")
VERIFY_TOKEN = "ACE_SIGILO_2026"

client = genai.Client(api_key=GEMINI_KEY)
app = Flask(__name__)

OUT_PATH = "/content/ace_media/" if os.path.exists("/content/") else "./ace_media/"
os.makedirs(OUT_PATH, exist_ok=True)

# ==========================================================
# 🧠 MEMÓRIA EVOLUTIVA
# ==========================================================

DB_PATH = OUT_PATH + "ace_memory.db"

def init_memory():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY,
        data TEXT,
        tema TEXT,
        hook TEXT,
        score REAL
    )
    """)
    conn.commit()
    conn.close()

init_memory()

# ==========================================================
# 🌍 RADAR GLOBAL
# ==========================================================

def radar_global():
    termos = []
    try:
        pytrend = TrendReq(hl='pt-BR')
        trending = pytrend.trending_searches(pn='brazil')
        termos += list(trending[0])
    except:
        pass
    palavras = []
    for t in termos:
        palavras += re.findall(r'\w+', t.lower())
    freq = Counter(palavras)
    if not freq:
        return "disciplina"
    return freq.most_common(1)[0][0]

# ==========================================================
# ⚡ MOTOR DE DOPAMINA
# ==========================================================

gatilhos = ["segredo","verdade","erro","oculto","alerta","proibido"]

def score_dopamina(texto):
    score = 1.0
    for g in gatilhos:
        if g in texto.lower():
            score *= 1.25
    if "?" in texto:
        score *= 1.1
    return score

# ==========================================================
# 🧠 GERADOR DE HOOKS
# ==========================================================

def gerar_hook(tema):
    hooks = [
        f"A verdade que ninguém aceita sobre {tema}",
        f"O erro silencioso em {tema}",
        f"O segredo oculto de {tema}",
        f"O alerta brutal sobre {tema}"
    ]
    return max(hooks, key=score_dopamina)

# ==========================================================
# 🧬 GENES
# ==========================================================

GENES = {"zoom":0.05,"contraste":1.1,"caos":0.2}

def mutacao(score):
    if score > 1.2:
        GENES["zoom"] *= 1.05
        GENES["contraste"] *= 1.02
    else:
        GENES["zoom"] *= 0.97
        GENES["contraste"] *= 0.99

# ==========================================================
# 🧠 MEMÓRIA
# ==========================================================

def registrar_post(tema,hook,score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO posts(data,tema,hook,score) VALUES(?,?,?,?)",
              (str(datetime.datetime.now()), tema, hook, score))
    conn.commit()
    conn.close()

# ==========================================================
# 🧠 MOTOR OMNI V4000
# ==========================================================

def motor_omni_v4000(entrada):
    try:
        trend = TrendReq(hl='pt-BR').trending_searches(pn='brazil')[0][0]
    except:
        trend = "Dominação Digital"
    instrucao = f"ACE libertaverdades. Trend: {trend}. Brutalidade estoica."
    res = client.models.generate_content(model="gemini-2.0-flash", contents=f"{instrucao}\n\n{entrada}")
    return res.text

# ==========================================================
# 🎨 STUDIO V4000
# ==========================================================

def fabricar_arsenal_v4000():
    print("🎨 STUDIO V4000 ATIVO")
    texto = motor_omni_v4000("Gere 10 verdades.")
    frases = re.split(r'\d\.', texto)[1:11]
    audio_p = OUT_PATH + "voice.mp3"
    gTTS(text=texto[:400], lang='pt-br').save(audio_p)
    bg = ColorClip(size=(1080,1920),color=(5,0,0),duration=15)
    txt = TextClip(texto[:200], fontsize=100, color='yellow', font='DejaVu-Sans-Bold', size=(900,1600), method='caption')
    video = CompositeVideoClip([bg,txt.set_position("center")])
    video.set_audio(AudioFileClip(audio_p)).fx(vfx.lum_contrast, lum=1.03, contrast=1.1).write_videofile(
        OUT_PATH+"reel.mp4", fps=24, codec="libx264"
    )
    for i,f in enumerate(frases,1):
        img = Image.new('RGB',(1080,1080),(2,0,0))
        d = ImageDraw.Draw(img)
        d.rectangle([0,1070,(108*i),1080],fill="red")
        d.text((130,450),f"ALERTA {i}\n\n{f}",fill=(255,255,255))
        img.save(OUT_PATH+f"slide_{i}.jpg")

# ==========================================================
# 🚀 PUBLICAÇÃO
# ==========================================================

def publicar_v4(url_media,legenda):
    res = requests.post(
        f"https://graph.facebook.com/v20.0/{IG_ID}/media",
        data={"video_url":url_media,"media_type":"REELS","caption":legenda,"access_token":IG_TOKEN}
    ).json()
    creation_id = res.get("id")
    if creation_id:
        time.sleep(60)
        requests.post(
            f"https://graph.facebook.com/v20.0/{IG_ID}/media_publish",
            data={"creation_id":creation_id,"access_token":IG_TOKEN}
        )

# ==========================================================
# 🌐 WEBHOOK
# ==========================================================

@app.route('/webhook',methods=['GET'])
def verify():
    if request.args.get("hub.verify_token")==VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Erro",403

@app.route('/media/<path:filename>')
def serve(filename):
    return send_from_directory(OUT_PATH,filename)

# ==========================================================
# 🧠 NOVOS MOTORES
# ==========================================================

RETENTION_WORDS=["ninguém","verdade","segredo","erro","alerta","proibido","revelado","chocante"]

def score_retencao(texto):
    score=1.0
    for w in RETENTION_WORDS:
        if w in texto.lower():
            score*=1.15
    if "?" in texto:
        score*=1.1
    return score

EMOCOES={"curiosidade":["segredo","revelado","verdade"],
         "medo":["alerta","perigo","cuidado"],
         "raiva":["erro","mentira","enganado"]}

def score_emocional(texto):
    score=1.0
    t=texto.lower()
    for grupo in EMOCOES.values():
        for w in grupo:
            if w in t:
                score*=1.12
    return score

def prever_viralidade(hook):
    base=score_dopamina(hook)
    ret=score_retencao(hook)
    ruido=random.uniform(0.9,1.1)
    return base*ret*ruido

def recomendar_tema():
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT tema,AVG(score) FROM posts GROUP BY tema ORDER BY AVG(score) DESC LIMIT 5")
    dados=c.fetchall()
    conn.close()
    if dados:
        return random.choice(dados)[0]
    return radar_global()

def gerar_hook_otimizado(tema):
    hooks=[
        f"A verdade que ninguém aceita sobre {tema}",
        f"O erro silencioso em {tema}",
        f"O segredo oculto de {tema}",
        f"O alerta brutal sobre {tema}",
        f"O que nunca te contaram sobre {tema}",
        f"Isso pode mudar tudo em {tema}"
    ]
    melhor=None
    melhor_score=0
    for h in hooks:
        score=prever_viralidade(h)*score_emocional(h)
        if score>melhor_score:
            melhor=h
            melhor_score=score
    return melhor

# ==========================================================
# 🧠 OMEGA BRAIN
# ==========================================================

def omega_brain():
    tema=recomendar_tema()
    hook=gerar_hook_otimizado(tema)
    score=prever_viralidade(hook)
    return tema,hook,score

# ==========================================================
# 📊 DASHBOARD
# ==========================================================

@app.route("/stats")
def stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM posts")
    total = c.fetchone()[0]
    conn.close()
    return {"posts":total,"genes":GENES}

# ==========================================================
# 🛡 WATCHDOG
# ==========================================================

def watchdog():
    while True:
        try:
            requests.get("http://localhost:5000")
        except:
            threading.Thread(target=lambda:app.run(port=5000),daemon=True).start()
        time.sleep(300)

# ==========================================================
# 🚀 SUPER CICLO ACE
# ==========================================================

def ciclo_mestre():
    try:
        ngrok.set_auth_token(NGROK_TOKEN)
        public_url = ngrok.connect(5000).public_url
        print(f"ACE ONLINE: {public_url}")
        while True:
            agora=datetime.datetime.now()
            if agora.hour in [6,8,10,12,14,16,18,20,22] and agora.minute==0:
                tema,hook,score=omega_brain()
                registrar_post(tema,hook,score)
                mutacao(score)
                fabricar_arsenal_v4000()
                legenda=motor_omni_v4000("Gere legenda viral")
                publicar_v4(f"{public_url}/media/reel.mp4",legenda)
                print("POST GERADO:",tema,GENES)
            time.sleep(60)
    except Exception as e:
        print("ERRO NO CICLO:",e)

# ==========================================================
# 🚀 START
# ==========================================================

if __name__=="__main__":
    threading.Thread(target=lambda:app.run(port=5000),daemon=True).start()
    threading.Thread(target=watchdog,daemon=True).start()
    ciclo_mestre()
# ==========================================================
# ACE Ω EVOLUTIVO — GOVERNANÇA + INTELIGÊNCIA SOCIOCULTURAL
# ==========================================================

# ----------------------------------------------------------
# GOVERNANÇA DE POSTAGENS
# ----------------------------------------------------------

def ace_governance(tema, hook, score):
    """
    Avalia riscos e prioridades antes de postar
    """
    # evitar excesso de posts similares
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM posts WHERE tema=? AND date(data)=date('now')", (tema,))
    count_today = c.fetchone()[0]
    conn.close()

    # se já postou 2 vezes hoje sobre o mesmo tema, espera
    if count_today >= 2:
        print("Governança: Tema já postado hoje, adiando...")
        return False

    # checa genes e score mínimo
    if score < 1.05:
        print("Governança: Hook score baixo, segurando publicação...")
        return False

    return True

# ----------------------------------------------------------
# INTELIGÊNCIA EVOLUTIVA
# ----------------------------------------------------------

def ace_evolve_timing():
    """
    Ajusta horários de postagem com base em engajamento histórico
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT strftime('%H', data) as hour, AVG(score) FROM posts GROUP BY hour")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return [6,8,10,12,14,16,18,20,22]  # padrão

    # seleciona horas com maior score médio
    rows.sort(key=lambda x: x[1], reverse=True)
    top_hours = [int(h) for h,_ in rows[:5]]
    return top_hours

# ----------------------------------------------------------
# TERMÔMETRO SOCIOCULTURAL
# ----------------------------------------------------------

def ace_sociocultural_thermometer():
    """
    Detecta trends, sentimento e timing ideal
    """
    tema = ace_trend_radar()

    # analisar sentimento do hook
    hook, score = ace_generate_viral_hook(tema)
    emo_score = score_emocional(hook)

    # timing baseado em genes + score + horário atual
    agora = datetime.datetime.now()
    hour_factor = math.cos((agora.hour-12)/12*math.pi) + 1  # pico meio-dia e 20h
    timing_score = score * emo_score * hour_factor

    return tema, hook, timing_score

# ----------------------------------------------------------
# DECISÃO DE POSTAGEM INTELIGENTE
# ----------------------------------------------------------

def ace_intelligent_post():

    try:
        tema, hook, score = ace_sociocultural_thermometer()

        if not ace_governance(tema, hook, score):
            return

        # gerar conteúdo
        fabricar_arsenal_v4000()
        legenda = motor_omni_v4000(f"Legenda viral: {hook}")

        # publicar
        public_url = ngrok.connect(5000).public_url
        ace_post_reel(f"{public_url}/media/reel.mp4", legenda)

        # registrar
        registrar_post(tema, hook, score)
        mutacao(score)

        print("INTELLIGENT POST DONE:", tema, hook, score)

    except Exception as e:
        print("INTELLIGENT POST ERROR:", e)

# ----------------------------------------------------------
# ULTRA MANAGER LOOP COM GOVERNANÇA E TIMING
# ----------------------------------------------------------

def ace_ultra_manager_loop_v2():

    while True:
        try:
            top_hours = ace_evolve_timing()
            agora = datetime.datetime.now()

            # decidir se é hora de postar
            if agora.hour in top_hours and agora.minute == 0:
                ace_intelligent_post()

            # stories reflexivos em horários estratégicos
            if agora.hour in [7,19,22] and agora.minute == 30:
                public_url = ngrok.connect(5000).public_url
                ace_post_story(f"{public_url}/media/slide_1.jpg")

            ace_learn_from_posts()
            time.sleep(60)

        except Exception as e:
            print("ULTRA MANAGER LOOP V2 ERROR:", e)
            time.sleep(60)

# ----------------------------------------------------------
# START ULTRA MANAGER V2
# ----------------------------------------------------------

def ace_start_ultra_manager_v2():

    try:
        threading.Thread(target=ace_ultra_manager_loop_v2, daemon=True).start()
        threading.Thread(target=ace_dm_loop, daemon=True).start()
        print("ACE ULTRA MANAGER V2 ONLINE")
    except Exception as e:
        print("ULTRA MANAGER V2 START ERROR:", e)

# auto-start
try:
    ace_start_ultra_manager_v2()
except:
    pass
