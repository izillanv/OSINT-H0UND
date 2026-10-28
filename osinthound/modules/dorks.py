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

    def applicable(self, target: Target) -> bool:
        return bool(target.all_names() or target.usernames
                    or target.emails or target.phones)

    def _for_name(self, name: str, context: str = "") -> List[tuple]:
        q = quote(name)
        pairs = [
            ("Nombre exacto (Google)", _g(f'"{name}"')),
            ("Nombre exacto (DuckDuckGo)", f"https://duckduckgo.com/?q={quote(chr(34)+name+chr(34))}"),
            ("Nombre exacto (Bing)", f"https://www.bing.com/search?q=%22{q}%22"),
            ("LinkedIn (perfil)", _g(f'"{name}" site:linkedin.com/in')),
            ("Nombre + otras redes", _g(f'"{name}" (site:x.com OR site:facebook.com OR site:instagram.com)')),
            ("Documentos con el nombre", _g(f'"{name}" (filetype:pdf OR filetype:docx OR filetype:xlsx)')),
            ("Nombre en pastes/filtraciones", _g(f'"{name}" (site:pastebin.com OR site:ghostbin.com OR site:throwbin.io)')),
            ("Nombre en GitHub", f"https://github.com/search?q=%22{q}%22&type=code"),
            ("Directorios profesionales", _g(f'"{name}" (site:linkedin.com OR site:xing.com OR site:crunchbase.com OR site:zoominfo.com)')),
        ]
        if context:
            pairs.append(("Nombre + contexto (empresa/ciudad)",
                          _g(f'"{name}" "{context}" site:linkedin.com')))
        return pairs

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
            ("Correo exacto (Google)", _g(f'"{e}"')),
            ("HaveIBeenPwned", f"https://haveibeenpwned.com/account/{quote(e)}"),
            ("EPIEOS (cuentas por correo)", "https://epieos.com/"),
            ("EmailOSINT.org", "https://emailrep.io/" + quote(e)),
            ("Correo en pastes", _g(f'"{e}" (site:pastebin.com OR site:ghostbin.com)')),
            ("Tecnica IntelX -> Yandex", "https://intelx.io/"),
            ("Cruce en Yandex (comillas)", "https://yandex.com/search/?text=" + quote(f'"{e}"')),
            ("Recuperacion de cuenta (manual)",
             "https://accounts.google.com/signin/recovery"),
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

        for nm in target.all_names():
            emit(f"Nombre: {nm}", self._for_name(nm, target.location or ""))
        for u in target.usernames:
            emit(f"Alias @{u}", self._for_username(u))
        for e in target.emails:
            emit(f"Correo {e}", self._for_email(e))
        for p in target.phones:
            emit(f"Telefono {p}", self._for_phone(p))
        return out
