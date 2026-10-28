"""
validators.py
=============
Validacion y normalizacion de la ENTRADA del usuario.

Regla de oro (criterio "Entrada de datos" de la rubrica): **ningun dato
invalido debe interrumpir la ejecucion**. Cada validador:
  - normaliza lo que puede (quita esquemas de URL, espacios, etc.),
  - devuelve el valor limpio o None si no es valido,
  - nunca lanza excepcion.

`build_target()` recibe los campos crudos, acepta varios valores separados por
coma (correos, telefonos, alias, dominios), descarta lo invalido avisando y
construye un objeto `Target` con lo que si es valido.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from . import config

# phonenumbers es opcional: si falta, la validacion telefonica degrada a una
# comprobacion de formato basica en vez de romper el import.
try:
    import phonenumbers  # type: ignore

    _HAS_PHONENUMBERS = True
except Exception:  # pragma: no cover
    _HAS_PHONENUMBERS = False


# ---------------------------------------------------------------------------
# Expresiones regulares
# ---------------------------------------------------------------------------
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9._\-]{2,40}$")
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)([A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}$"
)
_NAME_RE = re.compile(r"^[\w .'\-]{2,80}$", re.UNICODE)


# ---------------------------------------------------------------------------
# Validadores individuales
# ---------------------------------------------------------------------------
def validate_name(raw: str) -> Tuple[Optional[str], Optional[str]]:
    """Nombre de persona. Permite letras, espacios, guiones y apostrofes."""
    value = (raw or "").strip()
    if not value:
        return None, None
    value = re.sub(r"\s+", " ", value)
    if not _NAME_RE.match(value):
        return None, f"Nombre descartado (caracteres no validos): {raw!r}"
    return value, None


def validate_username(raw: str) -> Tuple[Optional[str], Optional[str]]:
    """Alias/username. 2-40 chars: letras, numeros, punto, guion y guion bajo."""
    value = (raw or "").strip().lstrip("@")
    if not value:
        return None, None
    if not _USERNAME_RE.match(value):
        return None, f"Alias descartado (formato invalido): {raw!r}"
    return value, None


def validate_email(raw: str) -> Tuple[Optional[str], Optional[str]]:
    """Correo electronico. Se normaliza a minusculas."""
    value = (raw or "").strip().lower()
    if not value:
        return None, None
    if not _EMAIL_RE.match(value):
        return None, f"Correo descartado (formato invalido): {raw!r}"
    return value, None


def validate_domain(raw: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Dominio. Acepta tambien URLs completas y las reduce al host:
    "https://www.ejemplo.com/ruta?x=1"  ->  "ejemplo.com"
    """
    value = (raw or "").strip().lower()
    if not value:
        return None, None
    # Quitar esquema, credenciales, ruta, puerto y "www."
    value = re.sub(r"^[a-z]+://", "", value)
    value = value.split("/")[0].split("@")[-1].split(":")[0]
    if value.startswith("www."):
        value = value[4:]
    if not _DOMAIN_RE.match(value):
        return None, f"Dominio descartado (formato invalido): {raw!r}"
    return value, None


def validate_phone(raw: str, country: str = config.DEFAULT_COUNTRY
                    ) -> Tuple[Optional[str], Optional[str]]:
    """
    Telefono. Con `phonenumbers` valida de verdad a nivel mundial y normaliza a
    E.164 (+34600...). Sin la libreria, cae a una comprobacion de formato basica.
    """
    value = (raw or "").strip()
    if not value:
        return None, None

    if _HAS_PHONENUMBERS:
        try:
            region = None if value.startswith("+") else (country or "ES").upper()
            parsed = phonenumbers.parse(value, region)
            if not phonenumbers.is_valid_number(parsed):
                return None, f"Telefono descartado (no valido): {raw!r}"
            e164 = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
            return e164, None
        except Exception:
            return None, f"Telefono descartado (no se pudo analizar): {raw!r}"

    # Fallback sin phonenumbers.
    digits = re.sub(r"[^\d+]", "", value)
    if re.match(r"^\+?\d{7,15}$", digits):
        return digits, None
    return None, f"Telefono descartado (formato invalido): {raw!r}"


# ---------------------------------------------------------------------------
# Objetivo de la investigacion
# ---------------------------------------------------------------------------
@dataclass
class Target:
    """
    Conjunto de identificadores (ya validados) sobre los que se investiga.
    Las listas permiten varios valores (p. ej. dos correos del objetivo).
    """

    name: Optional[str] = None
    usernames: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    location: Optional[str] = None
    country: str = config.DEFAULT_COUNTRY
    image: Optional[str] = None

    def has_any(self) -> bool:
        """True si hay al menos un identificador utilizable."""
        return any([self.name, self.usernames, self.emails,
                    self.phones, self.domains, self.image])

    def summary(self) -> str:
        """Linea resumen para logs y cabeceras del informe."""
        parts = []
        if self.name:
            parts.append(self.name)
        if self.usernames:
            parts.append("@" + ", @".join(self.usernames))
        if self.emails:
            parts.append(", ".join(self.emails))
        if self.phones:
            parts.append(", ".join(self.phones))
        if self.domains:
            parts.append(", ".join(self.domains))
        return " · ".join(parts) if parts else "(sin identificadores)"


def _split_multi(raw: str) -> List[str]:
    """Divide una cadena por comas o punto y coma en valores no vacios."""
    if not raw:
        return []
    return [p.strip() for p in re.split(r"[;,]", raw) if p.strip()]


def build_target(raw: dict, country: str = config.DEFAULT_COUNTRY
                 ) -> Tuple[Target, List[str]]:
    """
    Construye un `Target` a partir de un diccionario de campos crudos.

    Devuelve (target, warnings). Nunca lanza: lo invalido se descarta y se
    acumula un aviso por cada descarte. El llamador decide que hacer si el
    target queda vacio (en la practica, se pide de nuevo la entrada).
    """
    warnings: List[str] = []
    country = (country or raw.get("country") or config.DEFAULT_COUNTRY).upper()
    target = Target(country=country, location=(raw.get("location") or "").strip() or None)

    # Nombre (unico)
    name, w = validate_name(raw.get("name", ""))
    target.name = name
    if w:
        warnings.append(w)

    # Multi-valor: alias, correos, telefonos, dominios
    for value in _split_multi(raw.get("username", "")):
        clean, w = validate_username(value)
        if clean and clean not in target.usernames:
            target.usernames.append(clean)
        if w:
            warnings.append(w)

    for value in _split_multi(raw.get("email", "")):
        clean, w = validate_email(value)
        if clean and clean not in target.emails:
            target.emails.append(clean)
        if w:
            warnings.append(w)

    for value in _split_multi(raw.get("phone", "")):
        clean, w = validate_phone(value, country)
        if clean and clean not in target.phones:
            target.phones.append(clean)
        if w:
            warnings.append(w)

    for value in _split_multi(raw.get("domain", "")):
        clean, w = validate_domain(value)
        if clean and clean not in target.domains:
            target.domains.append(clean)
        if w:
            warnings.append(w)

    # Imagen: solo comprobamos que el fichero exista.
    img = (raw.get("image") or "").strip()
    if img:
        import os
        if os.path.isfile(img):
            target.image = img
        else:
            warnings.append(f"Imagen descartada (no existe el fichero): {img!r}")

    return target, warnings
