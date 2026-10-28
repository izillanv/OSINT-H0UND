"""
modules/phone_check.py
======================
Analiza un TELEFONO a nivel mundial con la libreria `phonenumbers` (datos
incluidos, no necesita red): validez, pais, operador, tipo de linea, zona
horaria y formato internacional/E.164.

Tambien genera enlaces de pivote para revisar manualmente el numero en apps de
mensajeria y servicios de reputacion (no automatiza nada contra ellos).
"""

from __future__ import annotations

from typing import Dict, List

from .. import config
from ..finding import Finding
from ..validators import Target
from .base import BaseModule, Context, register

try:
    import phonenumbers
    from phonenumbers import carrier, geocoder, timezone
    _HAS = True
except Exception:
    _HAS = False

_LINE_TYPES = {
    0: "Fijo", 1: "Movil", 2: "Fijo o movil", 3: "Gratuito (0800)",
    4: "Tarificacion especial", 5: "Coste compartido", 6: "VoIP",
    7: "Numero personal", 8: "Buscapersonas", 9: "UAN", 10: "Desconocido",
    27: "Emergencias", 28: "Buzon de voz",
}


@register
class PhoneCheck(BaseModule):
    name = "phone_check"
    title = "Analisis telefonico"
    description = "Pais, operador, tipo de linea y zona horaria (mundial)"
    category = "Telefono"
    accepts = {"phone"}

    def availability(self, ctx: Context):
        return (_HAS, "" if _HAS else "Falta la libreria phonenumbers")

    def analyze(self, number: str, region: str = "ES") -> Dict:
        """Devuelve un dict con el analisis del numero (o valid=False)."""
        if not _HAS:
            return {"valid": False, "error": "phonenumbers no disponible"}
        try:
            parsed = phonenumbers.parse(
                number, None if number.startswith("+") else region)
        except Exception:
            return {"valid": False, "error": "no se pudo analizar"}
        if not phonenumbers.is_valid_number(parsed):
            return {"valid": False}
        return {
            "valid": True,
            "e164": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164),
            "internacional": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "pais": geocoder.description_for_number(parsed, "es") or "—",
            "prefijo_pais": f"+{parsed.country_code}",
            "operador": carrier.name_for_number(parsed, "es") or "—",
            "tipo_linea": _LINE_TYPES.get(
                phonenumbers.number_type(parsed), "Desconocido"),
            "zonas_horarias": list(timezone.time_zones_for_number(parsed)),
        }

    def run(self, target: Target, ctx: Context) -> List[Finding]:
        out: List[Finding] = []
        for num in target.phones:
            info = self.analyze(num, target.country)
            if not info.get("valid"):
                continue
            pivots = {
                "WhatsApp (abrir chat)": f"https://wa.me/{info['e164'].lstrip('+')}",
                "Telegram": f"https://t.me/{info['e164']}",
                "Buscar en Google": f"https://www.google.com/search?q=%22{info['e164']}%22",
            }
            out.append(Finding(
                kind="phone", label=info["internacional"], value=info["e164"],
                source=self.name, category=self.category,
                meta={k: v for k, v in info.items() if k != "valid"} | {"pivotes": pivots},
            ))
        return out
