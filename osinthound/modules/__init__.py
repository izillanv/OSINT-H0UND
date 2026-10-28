"""
modules/__init__.py
===================
Importa todos los modulos para que se registren en el REGISTRY global, y expone
`get_modules()` para que el motor obtenga las instancias disponibles.

Para anadir una fuente nueva: crea `modules/mi_modulo.py` con una clase
`@register` que herede de `BaseModule`, e importala aqui. No hay que tocar nada
mas (criterio de modularidad de la rubrica).
"""

from __future__ import annotations

from typing import List

from .base import REGISTRY, BaseModule  # noqa: F401

# El import de cada modulo dispara su decorador @register.
from . import footprint          # noqa: F401,E402
from . import username_enum      # noqa: F401,E402
from . import email_recon        # noqa: F401,E402
from . import breach_check       # noqa: F401,E402
from . import phone_check        # noqa: F401,E402
from . import domain_recon       # noqa: F401,E402
from . import public_records     # noqa: F401,E402
from . import image_recon        # noqa: F401,E402
from . import dorks              # noqa: F401,E402
from . import external_tools     # noqa: F401,E402


def get_modules() -> List[BaseModule]:
    """Devuelve una instancia de cada modulo registrado."""
    return [cls() for cls in REGISTRY]
