"""
modules/breach_check.py
=======================
Comprueba si un CORREO aparece en brechas de datos conocidas (concienciacion
de exposicion). NO expone contrasenas: solo indica en que brechas publicas
figura el correo y que tipo de datos se filtraron.

Fuentes:
  - HaveIBeenPwned v3 si hay `HIBP_API_KEY` (de pago).
  - XposedOrNot (gratuito, sin clave) como alternativa por defecto.
"""

from __future__ import annotations

import time
from typing import List

from .. import config
from ..finding import Finding
from ..validators import Target
from .base import BaseModule, Context, register

_HIBP_URL = "https://haveibeenpwned.com/api/v3/breachedaccount/{}"
_XON_URL = "https://api.xposedornot.com/v1/check-email/{}"


@register
class BreachCheck(BaseModule):
    name = "breach_check"
    title = "Brechas de datos"
    description = "Comprueba si el correo aparece en filtraciones (HIBP / XposedOrNot)"
    category = "Brechas"
    accepts = {"email"}

    def availability(self, ctx: Context):
        if config.has_key("hibp"):
            return True, "HIBP (clave detectada)"
        return True, "XposedOrNot (gratuito)"

    # ------------------------------------------------------------------ #
    def _via_hibp(self, email: str, ctx: Context) -> List[Finding]:
        headers = {"hibp-api-key": config.API_KEYS["hibp"],
                   "User-Agent": "OSINT-Hound"}
        r = ctx.get(_HIBP_URL.format(email), headers=headers,
                    params={"truncateResponse": "false"})
        if not r or r.status_code == 404:
            return []
        if r.status_code != 200:
            return []
        out = []
        for b in (r.json() or []):
            classes = ", ".join(b.get("DataClasses", [])[:6])
            out.append(Finding(
                kind="breach", label=f"Brecha: {b.get('Name', '?')}",
                value=email, url=f"https://haveibeenpwned.com/PwnedWebsites",
                source=self.name, category=self.category,
                meta={"email": email, "fecha": b.get("BreachDate", "—"),
                      "datos_filtrados": classes,
                      "cuentas_afectadas": b.get("PwnCount")},
            ))
        time.sleep(1.6)  # HIBP exige espaciar peticiones
        return out

    def _via_xon(self, email: str, ctx: Context) -> List[Finding]:
        r = ctx.get(_XON_URL.format(email))
        if not r or r.status_code != 200:
            return []
        try:
            data = r.json()
        except Exception:
            return []
        out = []
        breaches = data.get("breaches") or []
        names = breaches[0] if breaches and isinstance(breaches[0], list) else breaches
        for name in names:
            out.append(Finding(
                kind="breach", label=f"Brecha: {name}", value=email,
                url="https://xposedornot.com/",
                source=self.name, category=self.category,
                meta={"email": email, "fuente": "XposedOrNot"},
            ))
        return out

    # ------------------------------------------------------------------ #
    def run(self, target: Target, ctx: Context) -> List[Finding]:
        out: List[Finding] = []
        use_hibp = config.has_key("hibp")
        for email in target.emails:
            out += self._via_hibp(email, ctx) if use_hibp else self._via_xon(email, ctx)
        return out
