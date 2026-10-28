"""
finding.py
==========
Modelo de un HALLAZGO (`Finding`): la unidad de informacion que produce
cualquier modulo OSINT y que consumen el motor, la correlacion y el informe.

Mantenerlo en su propio fichero evita importaciones circulares: los modulos y
el motor dependen de `Finding`, pero `Finding` no depende de nadie.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

from .config import CONF_CONFIRMED, CONF_POSSIBLE

# Tipos de hallazgo -> determinan a que tipo de nodo se mapean en el grafo.
KIND_TO_NODE = {
    "username": "username",
    "profile": "profile",
    "email": "email",
    "phone": "phone",
    "domain": "domain",
    "breach": "breach",
    "record": "record",
    "image": "image",
    "location": "location",
    "pivot": "pivot",
    "note": "pivot",
}


@dataclass
class Finding:
    """
    Un dato individual encontrado por un modulo.

    Campos
    ------
    kind        : tipo (profile, email, breach, domain, record, pivot...).
    label       : titulo corto y legible (p. ej. "GitHub", "Brecha: Adobe").
    value       : valor principal (url, correo, telefono, nombre de brecha...).
    url         : enlace a la fuente/evidencia (opcional).
    source      : nombre del modulo que lo genero.
    category    : grupo al que pertenece en el informe (p. ej. "Perfiles").
    confidence  : CONF_CONFIRMED (verificado) o CONF_POSSIBLE (a revisar).
    meta        : diccionario con detalles extra (evidencia, operador, etc.).
    """

    kind: str
    label: str
    value: str = ""
    url: str = ""
    source: str = ""
    category: str = "General"
    confidence: str = CONF_CONFIRMED
    meta: Dict[str, Any] = field(default_factory=dict)

    # Lo decide el analista en la fase de revision (None = aun sin decidir).
    accepted: Optional[bool] = None

    @property
    def node_type(self) -> str:
        """Tipo de nodo del grafo asociado a este hallazgo."""
        return KIND_TO_NODE.get(self.kind, "pivot")

    @property
    def is_possible(self) -> bool:
        return self.confidence == CONF_POSSIBLE

    def key(self) -> str:
        """Clave de deduplicado (mismo tipo + mismo valor/enlace)."""
        return f"{self.kind}:{(self.value or self.url or self.label).lower()}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def confirmed(**kwargs) -> Finding:
    """Atajo para crear un hallazgo verificado."""
    kwargs.setdefault("confidence", CONF_CONFIRMED)
    return Finding(**kwargs)


def possible(**kwargs) -> Finding:
    """Atajo para crear un hallazgo inferido (pendiente de revision humana)."""
    kwargs["confidence"] = CONF_POSSIBLE
    return Finding(**kwargs)
