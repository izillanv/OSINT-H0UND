"""
modules/dorks.py
================
Genera **Google Dorks** y **enlaces de pivote** a servicios OSINT, agrupados por
categoria (Nombre, Alias, Correo, Telefono, Imagen). No consulta nada: entrega
consultas listas para que el analista revise a mano.

Incluye tecnicas habituales de OSINT de personas (p. ej. buscar un correo en
IntelX y luego cruzar en Yandex, o localizar pastes con el identificador).
"""

from __future__ import annotations

from typing import List
from urllib.parse import quote

from ..config import CONF_POSSIBLE
from ..finding import Finding
from ..validators import Target
from .base import BaseModule, Context, register

G = "https://www.google.com/search?q="


def _g(query: str) -> str:
    return G + quote(query)


@register
class Dorks(BaseModule):
    name = "dorks"
    title = "Google Dorks y pivotes"
    description = "Consultas y enlaces OSINT listos por categoria (revision manual)"
    category = "Dorks y pivotes"
    accepts = {"name", "username", "email", "phone"}
    needs_network = False

    def _for_name(self, name: str) -> List[tuple]:
        return [
            ("Nombre exacto", _g(f'"{name}"')),
            ("Nombre + perfil social", _g(f'"{name}" (site:linkedin.com OR site:x.com OR site:facebook.com)')),
            ("Documentos con el nombre", _g(f'"{name}" (filetype:pdf OR filetype:docx OR filetype:xlsx)')),
            ("Nombre en pastes/filtraciones", _g(f'"{name}" (site:pastebin.com OR site:ghostbin.com OR site:throwbin.io)')),
            ("Nombre en GitHub", f"https://github.com/search?q=%22{quote(name)}%22&type=code"),
        ]

    def _for_username(self, u: str) -> List[tuple]:
        return [
            ("Alias exacto", _g(f'"{u}"')),
            ("WhatsMyName (online)", f"https://whatsmyname.app/?q={quote(u)}"),
            ("Instant Username", f"https://instantusername.com/#/{quote(u)}"),
            ("Alias en GitHub", f"https://github.com/search?q=%22{quote(u)}%22&type=users"),
            ("Alias en pastes", _g(f'"{u}" (site:pastebin.com OR site:ghostbin.com)')),
        ]

    def _for_email(self, e: str) -> List[tuple]:
        return [
            ("Correo exacto", _g(f'"{e}"')),
            ("HaveIBeenPwned", f"https://haveibeenpwned.com/account/{quote(e)}"),
            ("EPIEOS (cuentas por correo)", "https://epieos.com/"),
            ("Correo en pastes", _g(f'"{e}" (site:pastebin.com OR site:ghostbin.com)')),
            ("Tecnica IntelX -> Yandex", "https://intelx.io/"),
            ("Cruce en Yandex", "https://yandex.com/search/?text=" + quote(f'"{e}"')),
        ]

    def _for_phone(self, p: str) -> List[tuple]:
        return [
            ("Telefono exacto", _g(f'"{p}"')),
            ("Formato con espacios", _g(f'"{p[:3]} {p[3:6]} {p[6:]}"') if len(p) > 7 else _g(p)),
            ("Sync.me", f"https://sync.me/search/?number={quote(p)}"),
            ("Telefono en anuncios/pastes", _g(f'"{p}" (site:milanuncios.com OR site:pastebin.com)')),
        ]

    def run(self, target: Target, ctx: Context) -> List[Finding]:
        out: List[Finding] = []

        def emit(group: str, pairs: List[tuple]):
            for label, url in pairs:
                out.append(Finding(
                    kind="pivot", label=f"{label}", value=url, url=url,
                    source=self.name, category=self.category,
                    confidence=CONF_POSSIBLE, meta={"grupo": group},
                ))

        if target.name:
            emit("Nombre", self._for_name(target.name))
        for u in target.usernames:
            emit(f"Alias @{u}", self._for_username(u))
        for e in target.emails:
            emit(f"Correo {e}", self._for_email(e))
        for p in target.phones:
            emit(f"Telefono {p}", self._for_phone(p))
        return out
