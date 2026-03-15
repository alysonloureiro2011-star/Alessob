# ==========================================================
# ACE Ω — PUBLISH ENGINE REAL
# publicação real via Instagram Graph API
# ==========================================================

import os
import requests
import time

# ==========================================================
# CONFIG
# ==========================================================

INSTAGRAM_ID = os.environ.get("INSTAGRAM_ID")
INSTAGRAM_TOKEN = os.environ.get("INSTAGRAM_TOKEN")

GRAPH = "https://graph.facebook.com/v19.0"

# ==========================================================
# VALIDAÇÃO
# ==========================================================

def validate_publish_env():

    if not INSTAGRAM_ID:
        raise Exception("INSTAGRAM_ID não definido")

    if not INSTAGRAM_TOKEN:
        raise Exception("INSTAGRAM_TOKEN não definido")

# ==========================================================
# CRIA CONTAINER
# ==========================================================

def create_image_container(image_url, caption):

    validate_publish_env()

    url = f"{GRAPH}/{INSTAGRAM_ID}/media"

    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": INSTAGRAM_TOKEN
    }

    r = requests.post(url, data=payload)

    data = r.json()

    if "id" not in data:
        raise Exception(f"Erro criando container: {data}")

    return data["id"]

# ==========================================================
# CRIA CONTAINER REEL
# ==========================================================

def create_video_container(video_url, caption):

    validate_publish_env()

    url = f"{GRAPH}/{INSTAGRAM_ID}/media"

    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": INSTAGRAM_TOKEN
    }

    r = requests.post(url, data=payload)

    data = r.json()

    if "id" not in data:
        raise Exception(f"Erro criando container de vídeo: {data}")

    return data["id"]

# ==========================================================
# PUBLICA CONTAINER
# ==========================================================

def publish_container(container_id):

    url = f"{GRAPH}/{INSTAGRAM_ID}/media_publish"

    payload = {
        "creation_id": container_id,
        "access_token": INSTAGRAM_TOKEN
    }

    r = requests.post(url, data=payload)

    return r.json()

# ==========================================================
# PUBLICAÇÃO PRINCIPAL
# ==========================================================

def publish_content(media_path, caption, content_type, **kwargs):

    try:

        # IMPORTANTE
        # media_path precisa ser URL pública

        if content_type == "image":

            container = create_image_container(
                media_path,
                caption
            )

        elif content_type == "reel":

            container = create_video_container(
                media_path,
                caption
            )

        else:

            raise Exception(f"Tipo não suportado: {content_type}")

        time.sleep(5)

        result = publish_container(container)

        return {
            "status": "published",
            "container_id": container,
            "result": result
        }

    except Exception as e:

        return {
            "status": "failed",
            "error": str(e)
        }
