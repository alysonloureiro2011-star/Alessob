import os, time, datetime, gc, requests, threading
from flask import Flask, send_from_directory, request
from google import genai
from gtts import gTTS

# Configurações de ambiente
IG_TOKEN = os.environ.get("IG_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_KEY")
IG_ID = os.environ.get("IG_ID")
VERIFY_TOKEN = "ACE_SIGILO_2026"

client = genai.Client(api_key=GEMINI_KEY)
app = Flask(__name__)
OUT_PATH = "./ace_media/"
os.makedirs(OUT_PATH, exist_ok=True)

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Erro", 403

@app.route('/media/<path:filename>')
def serve(filename): return send_from_directory(OUT_PATH, filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
