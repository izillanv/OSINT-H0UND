"""
modules/footprint.py
====================
Huella publica por NOMBRE: busca menciones de la persona en la web (via el
endpoint HTML de DuckDuckGo, que no requiere clave) y las CLASIFICA por tipo de
fuente (oficial/gobierno, academico, medios, redes, documentos, otros).

Cada mencion es un candidato: se marca POSIBLE y el analista decide cuales
corresponden realmente al objetivo (clave para descartar homonimos).
"""

from __future__ import annotations

import re
from html import unescape
from typing import List
from urllib.parse import quote, urlparse

from ..config import CONF_POSSIBLE
from ..finding import Finding
from ..validators import Target
from .base import BaseModule, Context, register

_DDG = "https://html.duckduckgo.com/html/?q="

# Clasificacion por dominio/TLD.
_CLASIF = [
    ("Oficial / gobierno", ("gob.", ".gov", ".gob.es", "boe.es", ".gov.uk", "europa.eu")),
    ("Academico", (".edu", ".ac.", "scholar.google", "researchgate", "dialnet", "orcid")),
    ("Profesional", ("linkedin.com", "xing.com")),
    ("Medios", ("elpais.com", "elmundo.es", "bbc.", "nytimes.com", "reuters.com", "lavanguardia")),
    ("Redes sociales", ("x.com", "twitter.com", "facebook.com", "instagram.com",
                        "tiktok.com", "youtube.com", "reddit.com")),
    ("Documentos", (".pdf", ".docx", ".pptx")),
]


def _classify(url: str) -> str:
    low = url.lower()
    for label, needles in _CLASIF:
        if any(n in low for n in needles):
            return label
    return "Otros"


@register
class Footprint(BaseModule):
    name = "footprint"
    title = "Huella publica (menciones)"
    description = "Menciones del nombre en la web, clasificadas por tipo de fuente"
    category = "Huella publica"
    accepts = {"name"}

    def run(self, target: Target, ctx: Context) -> List[Finding]:
        if not target.name or not ctx.session:
            return []
        query = f'"{target.name}"'
        if target.location:
            query += f" {target.location}"
        r = ctx.get(_DDG + quote(query), delay=1.0)
        if not r or r.status_code != 200:
            return []

        # Extraer enlaces de resultados del HTML de DuckDuckGo.
        results = re.findall(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            r.text, re.DOTALL)
        out: List[Finding] = []
        seen = set()
        for href, title in results[:25]:
            title = unescape(re.sub(r"<[^>]+>", "", title)).strip()
            host = urlparse(href).netloc.replace("www.", "")
            if not host or host in seen:
                continue
            seen.add(host)
            out.append(Finding(
                kind="pivot", label=title[:90] or host, value=href, url=href,
                source=self.name, category=self.category,
                confidence=CONF_POSSIBLE,
                meta={"fuente": host, "tipo": _classify(href)},
            ))
        return out
