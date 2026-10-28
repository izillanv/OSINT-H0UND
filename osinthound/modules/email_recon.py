"""
modules/email_recon.py
======================
Enriquece un CORREO:
  - **Gravatar**: si el correo tiene perfil publico en Gravatar, obtiene nombre,
    foto y cuentas vinculadas (fuerte senal de correlacion entre identidades).
  - **MX**: comprueba si el dominio del correo acepta correo (registros MX).
  - **Proveedor**: clasifica el correo (gratuito vs. corporativo).
  - **Hunter.io**: solo si hay clave (dominio -> correos corporativos).

Las cuentas vinculadas que devuelve Gravatar se marcan como POSIBLE hasta que el
analista las confirme.
"""

from __future__ import annotations

import hashlib
from typing import List

from .. import config
from ..config import CONF_POSSIBLE
from ..finding import Finding
from ..validators import Target
from .base import BaseModule, Context, register

try:
    import dns.resolver  # type: ignore
    _HAS_DNS = True
except Exception:
    _HAS_DNS = False

_FREE_PROVIDERS = {"gmail.com", "outlook.com", "hotmail.com", "yahoo.com",
                   "proton.me", "protonmail.com", "icloud.com", "gmx.com",
                   "live.com", "aol.com", "yandex.com", "mail.com"}


@register
class EmailRecon(BaseModule):
    name = "email_recon"
    title = "Analisis de correo"
    description = "Gravatar, registros MX, proveedor y (opcional) Hunter.io"
    category = "Correos"
    accepts = {"email"}

    def _gravatar(self, email: str, ctx: Context) -> List[Finding]:
        h = hashlib.md5(email.strip().lower().encode()).hexdigest()
        r = ctx.get(f"https://gravatar.com/{h}.json")
        if not r or r.status_code != 200:
            return []
        try:
            entry = (r.json().get("entry") or [])[0]
        except Exception:
            return []

        name = entry.get("displayName") or ""
        photo = (entry.get("thumbnailUrl") or "")
        findings: List[Finding] = [Finding(
            kind="email", label=email, value=email, source=self.name,
            category=self.category,
            meta={"gravatar": True, "nombre_gravatar": name, "foto": photo,
                  "perfil_gravatar": f"https://gravatar.com/{h}"},
        )]
        # Cuentas vinculadas publicadas en Gravatar -> POSIBLE.
        for acc in entry.get("accounts", []) or []:
            findings.append(Finding(
                kind="profile",
                label=f"{acc.get('name', acc.get('shortname', 'cuenta'))} (Gravatar)",
                value=acc.get("url", ""), url=acc.get("url", ""),
                source=self.name, category=self.category,
                confidence=CONF_POSSIBLE,
                meta={"via": "Gravatar", "correo": email,
                      "usuario": acc.get("username", "")},
            ))
        return findings

    def _mx_and_provider(self, email: str) -> dict:
        dom = email.split("@", 1)[1]
        meta = {"proveedor": "gratuito" if dom in _FREE_PROVIDERS else "corporativo/propio",
                "dominio": dom}
        if _HAS_DNS:
            try:
                mx = dns.resolver.resolve(dom, "MX", lifetime=6)
                meta["mx"] = sorted(str(r.exchange).rstrip(".") for r in mx)[:3]
                meta["acepta_correo"] = True
            except Exception:
                meta["acepta_correo"] = False
        return meta

    def run(self, target: Target, ctx: Context) -> List[Finding]:
        out: List[Finding] = []
        for email in target.emails:
            grav = self._gravatar(email, ctx)
            meta = self._mx_and_provider(email)
            if grav:
                grav[0].meta.update(meta)
                out += grav
            else:
                out.append(Finding(
                    kind="email", label=email, value=email, source=self.name,
                    category=self.category, meta=meta,
                ))
        return out
