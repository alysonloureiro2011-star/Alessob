import requests
import os


class PublishService:

    def __init__(self, config):
        self.ig_user_id = config.ig_id
        self.access_token = config.ig_token

    def publish(self, media_path: str, caption: str):

        if not os.path.exists(media_path):
            return {"ok": False, "error": "media not found"}

        # STEP 1 — CREATE MEDIA CONTAINER
        url = f"https://graph.facebook.com/v19.0/{self.ig_user_id}/media"

        files = {
            "image_url": open(media_path, "rb")
        }

        data = {
            "caption": caption,
            "access_token": self.access_token
        }

        response = requests.post(url, data=data, files=files)
        result = response.json()

        if "id" not in result:
            return {"ok": False, "error": result}

        creation_id = result["id"]

        # STEP 2 — PUBLISH MEDIA
        publish_url = f"https://graph.facebook.com/v19.0/{self.ig_user_id}/media_publish"

        publish_response = requests.post(publish_url, data={
            "creation_id": creation_id,
            "access_token": self.access_token
        })

        publish_result = publish_response.json()

        if "id" not in publish_result:
            return {"ok": False, "error": publish_result}

        media_id = publish_result["id"]

        # STEP 3 — GET PERMALINK
        permalink_url = f"https://graph.facebook.com/v19.0/{media_id}?fields=permalink&access_token={self.access_token}"

        permalink_response = requests.get(permalink_url)
        permalink_result = permalink_response.json()

        return {
            "ok": True,
            "media_id": media_id,
            "permalink": permalink_result.get("permalink")
        }
