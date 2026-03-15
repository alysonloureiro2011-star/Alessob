import json
import os
import time
import datetime
from typing import Any, Dict, Optional


class InstagramTokenLifecycle:
    """
    Gerencia o ciclo de vida do token do Instagram:
    - carregar token salvo
    - salvar token novo
    - checar presença
    - checar idade
    - decidir se precisa refresh
    - expor status para o ACE
    """

    def __init__(
        self,
        storage_path: str = "instagram_auth.json",
        refresh_after_days: int = 45,
        hard_expire_days: int = 60
    ):
        self.storage_path = storage_path
        self.refresh_after_days = refresh_after_days
        self.hard_expire_days = hard_expire_days

    # --------------------------------------------------
    # helpers
    # --------------------------------------------------

    def _now_iso(self) -> str:
        return datetime.datetime.utcnow().isoformat()

    def _read_json(self) -> Dict[str, Any]:
        if not os.path.exists(self.storage_path):
            return {}

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_json(self, data: Dict[str, Any]) -> bool:
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def _days_since(self, iso_value: Optional[str]) -> Optional[int]:
        if not iso_value:
            return None

        try:
            dt = datetime.datetime.fromisoformat(iso_value)
            delta = datetime.datetime.utcnow() - dt
            return max(0, int(delta.total_seconds() // 86400))
        except Exception:
            return None

    # --------------------------------------------------
    # leitura principal
    # --------------------------------------------------

    def load_token_data(self) -> Dict[str, Any]:
        data = self._read_json()

        access_token = data.get("access_token") or os.getenv("IG_ACCESS_TOKEN")
        ig_user_id = data.get("ig_user_id") or os.getenv("IG_USER_ID")

        created_at = data.get("created_at")
        last_refresh_at = data.get("last_refresh_at")
        source = "file" if data.get("access_token") else "env"

        return {
            "access_token": access_token,
            "ig_user_id": ig_user_id,
            "created_at": created_at,
            "last_refresh_at": last_refresh_at,
            "source": source,
        }

    # --------------------------------------------------
    # persistência
    # --------------------------------------------------

    def save_token_data(
        self,
        access_token: str,
        ig_user_id: str,
        created_at: Optional[str] = None,
        last_refresh_at: Optional[str] = None
    ) -> Dict[str, Any]:
        created_at = created_at or self._now_iso()
        payload = {
            "access_token": access_token,
            "ig_user_id": ig_user_id,
            "created_at": created_at,
            "last_refresh_at": last_refresh_at or created_at,
        }

        ok = self._write_json(payload)

        return {
            "ok": ok,
            "storage_path": self.storage_path,
            "created_at": payload["created_at"],
            "last_refresh_at": payload["last_refresh_at"],
        }

    # --------------------------------------------------
    # status
    # --------------------------------------------------

    def token_present(self) -> bool:
        data = self.load_token_data()
        return bool(data.get("access_token") and data.get("ig_user_id"))

    def token_age_days(self) -> Optional[int]:
        data = self.load_token_data()
        ref = data.get("last_refresh_at") or data.get("created_at")
        return self._days_since(ref)

    def should_refresh(self) -> bool:
        age = self.token_age_days()
        if age is None:
            return False
        return age >= self.refresh_after_days

    def is_hard_expired(self) -> bool:
        age = self.token_age_days()
        if age is None:
            return False
        return age >= self.hard_expire_days

    def auth_status(self) -> Dict[str, Any]:
        data = self.load_token_data()
        age = self.token_age_days()

        return {
            "token_present": bool(data.get("access_token")),
            "ig_id_present": bool(data.get("ig_user_id")),
            "instagram_connected": bool(data.get("access_token") and data.get("ig_user_id")),
            "storage_path": self.storage_path,
            "source": data.get("source"),
            "created_at": data.get("created_at"),
            "last_refresh_at": data.get("last_refresh_at"),
            "token_age_days": age,
            "refresh_after_days": self.refresh_after_days,
            "hard_expire_days": self.hard_expire_days,
            "should_refresh": self.should_refresh(),
            "hard_expired": self.is_hard_expired(),
        }

    # --------------------------------------------------
    # refresh placeholder
    # --------------------------------------------------

    def refresh_token_if_needed(self) -> Dict[str, Any]:
        """
        Aqui fica a política de refresh.
        Nesta etapa, a função não chama a API da Meta diretamente.
        Ela apenas decide se precisa refresh e retorna o estado.
        O refresh real entra no próximo bloco.
        """
        status = self.auth_status()

        if not status["instagram_connected"]:
            return {
                "ok": False,
                "action": "none",
                "reason": "token_or_ig_id_missing",
                "status": status,
            }

        if status["hard_expired"]:
            return {
                "ok": False,
                "action": "manual_reauth_required",
                "reason": "token_hard_expired",
                "status": status,
            }

        if status["should_refresh"]:
            return {
                "ok": True,
                "action": "refresh_needed",
                "reason": "age_threshold_reached",
                "status": status,
            }

        return {
            "ok": True,
            "action": "no_refresh_needed",
            "reason": "token_still_fresh",
            "status": status,
        }

    # --------------------------------------------------
    # atualização manual em runtime
    # --------------------------------------------------

    def update_runtime_token(
        self,
        ace_runtime: Any,
        access_token: str,
        ig_user_id: str
    ) -> Dict[str, Any]:
        try:
            setattr(ace_runtime, "IG_TOKEN_RUNTIME", access_token)
            setattr(ace_runtime, "IG_ID_RUNTIME", ig_user_id)
            return {
                "ok": True,
                "instagram_connected": True
            }
        except Exception as e:
            return {
                "ok": False,
                "reason": str(e)
            }


instagram_token_lifecycle: Optional[InstagramTokenLifecycle] = None


def install_instagram_token_lifecycle(
    ace_runtime: Any,
    storage_path: str = "instagram_auth.json",
    refresh_after_days: int = 45,
    hard_expire_days: int = 60
) -> InstagramTokenLifecycle:
    global instagram_token_lifecycle

    instagram_token_lifecycle = InstagramTokenLifecycle(
        storage_path=storage_path,
        refresh_after_days=refresh_after_days,
        hard_expire_days=hard_expire_days
    )

    ace_runtime.instagram_token_lifecycle = instagram_token_lifecycle
    return instagram_token_lifecycle
