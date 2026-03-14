import datetime
import os
import requests

# ==========================================================
# CONFIG
# ==========================================================

IG_USER_ID = os.environ.get("INSTAGRAM_ID")
IG_TOKEN = os.environ.get("INSTAGRAM_TOKEN")

GRAPH_URL = "https://graph.facebook.com/v19.0"


# ==========================================================
# REGISTRO DE PUBLICAÇÃO
# ==========================================================

def build_publish_record(trend, style, content_type, caption, media_path, status):
    return {
        "trend": trend,
        "style": style,
        "content_type": content_type,
        "caption": caption,
        "media_path": media_path,
        "published_at": datetime.datetime.utcnow().isoformat(),
        "status": status
    }


# ==========================================================
# PUBLICAÇÃO REAL INSTAGRAM
# ==========================================================

def publish_to_instagram(media_path, caption):

    if not IG_USER_ID or not IG_TOKEN:
        return False, "instagram_not_configured"

    # Container
    container_url = f"{GRAPH_URL}/{IG_USER_ID}/media"

    payload = {
        "image_url": media_path,
        "caption": caption,
        "access_token": IG_TOKEN
    }

    try:

        r = requests.post(container_url, data=payload)
        data = r.json()

        if "id" not in data:
            return False, data

        creation_id = data["id"]

        publish_url = f"{GRAPH_URL}/{IG_USER_ID}/media_publish"

        publish_payload = {
            "creation_id": creation_id,
            "access_token": IG_TOKEN
        }

        r2 = requests.post(publish_url, data=publish_payload)
        data2 = r2.json()

        if "id" in data2:
            return True, data2

        return False, data2

    except Exception as e:
        return False, str(e)


# ==========================================================
# FUNÇÃO PRINCIPAL DO ACE
# ==========================================================

def publish_content(trend, style, content_type, caption, media_path):

    # tentativa de publicação
    success, result = publish_to_instagram(media_path, caption)

    if success:

        return build_publish_record(
            trend,
            style,
            content_type,
            caption,
            media_path,
            "published"
        )

    # fallback
    return build_publish_record(
        trend,
        style,
        content_type,
        caption,
        media_path,
        "generated"
    )
