"""ACE Ω Next — núcleo limpo paralelo ao legado.

Package init leve:
- sem eager import de superfícies Flask
- sem side effects de boot
- exportação lazy de factories
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "create_app",
    "create_official_app",
]


def create_app(*args: Any, **kwargs: Any):
    from .app import create_app as _create_app

    return _create_app(*args, **kwargs)


def create_official_app(*args: Any, **kwargs: Any):
    from .official_app import create_official_app as _create_official_app

    return _create_official_app(*args, **kwargs)
