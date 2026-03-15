import os
import time
import requests

GRAPH_URL = "https://graph.facebook.com/v19.0"

INSTAGRAM_ID = os.environ.get("INSTAGRAM_ID")
INSTAGRAM_TOKEN = os.environ.get("INSTAGRAM_TOKEN")


def create_container(media_url, caption):

    endpoint = f"{GRAPH_URL}/{INSTAGRAM_ID}/media"

    payload = {
        "image_url": media_url,
        "caption": caption,
        "access_token": INSTAGRAM_TOKEN
    }

    r = requests.post(endpoint, data=payload)

    data = r.json()

    if "id" not in data:
        raise Exception(data)

    return data["id"]


def publish_container(container_id):

    endpoint = f"{GRAPH_URL}/{INSTAGRAM_ID}/media_publish"

    payload = {
        "creation_id": container_id,
        "access_token": INSTAGRAM_TOKEN
    }

    r = requests.post(endpoint, data=payload)

    return r.json()


def publish_media(media_package, caption):

    media_url = media_package.get("public_url")

    if not media_url:

        return {
            "status": "failed",
            "reason": "missing_public_url"
        }

    try:

        container_id = create_container(media_url, caption)

        time.sleep(5)

        publish = publish_container(container_id)

        return {
            "status": "published",
            "result": publish
        }

    except Exception as e:

        return {
            "status": "failed",
            "error": str(e)
        }
