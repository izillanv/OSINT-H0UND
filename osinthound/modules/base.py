"""
modules/base.py
===============
Infraestructura de los modulos OSINT (patron plugin).

- `Context`     : estado compartido que el motor pasa a cada modulo (sesion HTTP,
                  capa human-in-the-loop, flags, pais y un REGISTRO de consultas
                  para trazabilidad tipo ENS).
- `BaseModule`  : clase base. Cada fuente OSINT hereda de aqui e implementa
                  `run()`. Declara que entradas usa (`accepts`) y a que categoria
                  pertenece.
- `register`    : decorador que da de alta un modulo en el REGISTRY global.

Anadir una fuente nueva = crear un fichero con una clase `@register` que herede
de `BaseModule`. No hay que tocar el motor (criterio de modularidad de la rubrica).
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Set, Tuple

from .. import config
from ..finding import Finding
from ..validators import Target

# Requests es la unica dependencia de red. Si faltara, el import no debe romper;
# los modulos comprobaran `ctx.session` antes de usarlo.
try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore


# --------------------------------------------------------------------------- #
# Registro global de modulos
# --------------------------------------------------------------------------- #
REGISTRY: List[type] = []


def register(cls: type) -> type:
    """Decorador: da de alta la clase de modulo en el registro."""
    REGISTRY.append(cls)
    return cls


# --------------------------------------------------------------------------- #
# Contexto de ejecucion
# --------------------------------------------------------------------------- #
class Context:
    """
    Estado que comparten todos los modulos durante una investigacion.

    Incluye un registro (`query_log`) de cada URL consultada y cada error, util
    para la trazabilidad de la auditoria (que se miro y cuando) y para depurar.
    """

    def __init__(self, hitl, country: str = config.DEFAULT_COUNTRY,
                 flags: Optional[dict] = None):
        self.hitl = hitl
        self.country = country
        self.flags = flags or {}
        self.query_log: List[dict] = []
        self.session = requests.Session() if requests else None
        if self.session:
            self.session.headers.update(config.DEFAULT_HEADERS)

    # -- Red con control de errores centralizado ------------------------ #
    def get(self, url: str, *, params=None, headers=None, timeout=None,
            allow_redirects=True, delay: float = 0.0):
        """
        GET con cabeceras por defecto, timeout y manejo de errores. Devuelve la
        respuesta o None (nunca lanza). Registra la consulta para trazabilidad.
        """
        self.query_log.append({"ts": time.time(), "url": url})
        if not self.session:
            return None
        try:
            r = self.session.get(
                url, params=params, headers=headers,
                timeout=timeout or config.HTTP_TIMEOUT,
                allow_redirects=allow_redirects,
            )
            if delay:
                time.sleep(delay)
            return r
        except Exception as ex:  # noqa: BLE001
            self.query_log[-1]["error"] = str(ex)
            return None

    def flag(self, name: str, default=False):
        return self.flags.get(name, default)


# --------------------------------------------------------------------------- #
# Clase base de los modulos
# --------------------------------------------------------------------------- #
class BaseModule:
    """Contrato que cumple cada fuente OSINT."""

    name: str = "base"              # identificador corto (sin espacios)
    title: str = "Modulo base"      # titulo legible
    description: str = ""           # que hace, para el selector y la ayuda
    category: str = "General"       # grupo en el informe
    accepts: Set[str] = set()       # {"name","username","email","phone","domain","image"}
    needs_network: bool = True      # informativo
    default_on: bool = True         # si entra marcado por defecto en el selector

    def applicable(self, target: Target) -> bool:
        """True si el objetivo tiene alguna de las entradas que este modulo usa."""
        if "any" in self.accepts:
            return target.has_any()
        if "name" in self.accepts and target.name:
            return True
        if "username" in self.accepts and target.usernames:
            return True
        if "email" in self.accepts and target.emails:
            return True
        if "phone" in self.accepts and target.phones:
            return True
        if "domain" in self.accepts and target.domains:
            return True
        if "image" in self.accepts and target.image:
            return True
        return False

    def availability(self, ctx: Context) -> Tuple[bool, str]:
        """
        (disponible, motivo). Por defecto disponible. Los modulos que dependen
        de una clave de API o de una herramienta externa lo sobreescriben.
        """
        return True, ""

    def run(self, target: Target, ctx: Context) -> List[Finding]:  # pragma: no cover
        raise NotImplementedError
