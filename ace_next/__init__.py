"""ACE Ω Next — núcleo limpo paralelo ao legado."""

from .app import create_app
from .official_app import create_official_app

__all__ = [
    "create_app",
    "create_official_app",
]