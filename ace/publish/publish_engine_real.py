import os
import time
import requests
from typing import Dict, List, Optional, Tuple

class PublishEngineReal:
    """
    Publica reels, carrosséis e stories no Instagram (Graph API) ou outro canal real.
    Requer access_token e ig_user_id válidos no runtime ACE.
    """

    def __init__(self, ig_token: Optional[str] = None, ig_user_id: Optional[str] = None) -> None:
        self.ig_token = ig_token or os.getenv("IG_ACCESS_TOKEN")
        self.ig_user_id = ig_user_id or os.getenv("IG_USER_ID")
        self.base_url = "https://graph.facebook.com/v18.0"
        if not self.ig_token or not self.ig_user_id:
            raise ValueError("IG_ACCESS_TOKEN e IG_USER_ID devem estar configurados para publicar.")

    # --------------------------------------------------
    # Helper: criar contêiner de mídia
    # --------------------------------------------------
    def _create_media_container(self, media_type: str, media_path: str, caption: str = "") -> Tuple[bool, str]:
        """
        Carrega mídia para o contêiner. Para reels e carrosséis, usa video ou image.
        Retorna (ok, container_id ou reason).
        """
        # Ler o arquivo para upload
        try:
            with open(media_path, "rb") as f:
                file_data = f.read()
        except Exception as e:
            return (False, f"file_read_error:{e}")

        url = f"{self.base_url}/{self.ig_user_id}/media"
        params = {
            "access_token": self.ig_token,
            "caption": caption or ""
        }

        files = {
            "media": (os.path.basename(media_path), file_data)
        }

        if media_type == "IMAGE":
            params["media_type"] = "IMAGE"
        elif media_type == "VIDEO":
            params["media_type"] = "VIDEO"
        else:
            return (False, "invalid_media_type")

        try:
            response = requests.post(url, params=params, files=files, timeout=60)
            data = response.json()
            if "id" in data:
                return (True, data["id"])
            return (False, data.get("error", {}).get("message", "unknown_error"))
        except Exception as e:
            return (False, f"request_error:{e}")

    # --------------------------------------------------
    # Helper: publicar contêiner
    # --------------------------------------------------
    def _publish_container(self, container_id: str) -> Tuple[bool, str]:
        url = f"{self.base_url}/{self.ig_user_id}/media_publish"
        params = {
            "creation_id": container_id,
            "access_token": self.ig_token
        }
        try:
            response = requests.post(url, params=params, timeout=60)
            data = response.json()
            if "id" in data:
                return (True, data["id"])
            return (False, data.get("error", {}).get("message", "unknown_error"))
        except Exception as e:
            return (False, f"request_error:{e}")

    # --------------------------------------------------
    # Publicar Reel (vídeo)
    # --------------------------------------------------
    def publish_reel(self, video_path: str, caption: str = "") -> Dict:
        """
        Publica um vídeo (reel) com caption. Retorna dict com status e IDs.
        """
        ok, container_or_reason = self._create_media_container("VIDEO", video_path, caption)
        if not ok:
            return {"ok": False, "reason": container_or_reason}
        pub_ok, post_id_or_reason = self._publish_container(container_or_reason)
        return {"ok": pub_ok, "post_id": post_id_or_reason}

    # --------------------------------------------------
    # Publicar imagem (story)
    # --------------------------------------------------
    def publish_image(self, image_path: str, caption: str = "") -> Dict:
        """
        Publica uma imagem simples (story ou feed). 
        """
        ok, container_or_reason = self._create_media_container("IMAGE", image_path, caption)
        if not ok:
            return {"ok": False, "reason": container_or_reason}
        pub_ok, post_id_or_reason = self._publish_container(container_or_reason)
        return {"ok": pub_ok, "post_id": post_id_or_reason}

    # --------------------------------------------------
    # Publicar carrossel
    # --------------------------------------------------
    def publish_carousel(self, image_paths: List[str], caption: str = "") -> Dict:
        """
        Publica carrossel com várias imagens. Cada imagem gera um contêiner filho,
        e o contêiner pai é publicado em seguida.
        """
        child_ids = []
        for img in image_paths:
            ok, container_or_reason = self._create_media_container("IMAGE", img)
            if not ok:
                return {"ok": False, "reason": f"child_error:{container_or_reason}"}
            child_ids.append(container_or_reason)

        # Criar contêiner pai
        url = f"{self.base_url}/{self.ig_user_id}/media"
        params = {
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": caption or "",
            "access_token": self.ig_token
        }
        try:
            response = requests.post(url, params=params, timeout=60)
            data = response.json()
            if "id" not in data:
                return {"ok": False, "reason": data.get("error", {}).get("message", "unknown_error")}
            # Publicar o carrossel
            pub_ok, post_id_or_reason = self._publish_container(data["id"])
            return {"ok": pub_ok, "post_id": post_id_or_reason}
        except Exception as e:
            return {"ok": False, "reason": f"request_error:{e}"}


# Instância global (opcional)
publish_engine_real: Optional[PublishEngineReal] = None

def install_publish_engine_real(ace_runtime: Any, ig_token: Optional[str] = None, ig_user_id: Optional[str] = None) -> PublishEngineReal:
    """
    Instala o publish engine real no runtime do ACE.
    Deve ser chamado no boot, fornecendo token e user_id ou lendo do ambiente.
    """
    global publish_engine_real
    publish_engine_real = PublishEngineReal(ig_token=ig_token, ig_user_id=ig_user_id)
    ace_runtime.publish_engine_real = publish_engine_real
    return publish_engine_real
