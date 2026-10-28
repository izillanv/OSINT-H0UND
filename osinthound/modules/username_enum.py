"""
modules/username_enum.py
========================
Comprueba la existencia de un ALIAS en muchos sitios del mundo.

Dos fuentes de sitios:
  1. Catalogo integrado (`sites/sites.json`, ~50 sitios globales + regionales).
     Funciona sin red adicional y es el modo por defecto.
  2. Dataset de **WhatsMyName** (cientos de sitios, deteccion por regex),
     descargado de GitHub si se activa `--wmn`. Es la "integracion externa"
     de datos mas potente del proyecto.

La deteccion por codigo de estado es heuristica (puede dar falsos positivos),
por eso cada hallazgo pasa luego por la revision humana.
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from .. import config
from ..config import CONF_CONFIRMED
from ..finding import Finding
from ..validators import Target
from .base import BaseModule, Context, register

_SITES_FILE = os.path.join(os.path.dirname(__file__), "..", "sites", "sites.json")
# Dataset WhatsMyName (proyecto OSINT abierto y muy conocido).
_WMN_URL = ("https://raw.githubusercontent.com/WebBreacher/WhatsMyName/main/"
            "wmn-data.json")


@register
class UsernameEnum(BaseModule):
    name = "username_enum"
    title = "Enumeracion de usuarios"
    description = "Busca el alias en decenas/cientos de sitios (catalogo + WhatsMyName)"
    category = "Perfiles sociales"
    accepts = {"username"}

    # ------------------------------------------------------------------ #
    def _load_builtin(self) -> List[dict]:
        try:
            with open(os.path.abspath(_SITES_FILE), "r", encoding="utf-8") as fh:
                return json.load(fh).get("sites", [])
        except Exception:
            return []

    def _load_wmn(self, ctx: Context) -> List[dict]:
        """Descarga y adapta el dataset de WhatsMyName al formato interno."""
        r = ctx.get(_WMN_URL, timeout=15)
        if not r or r.status_code != 200:
            return []
        try:
            data = r.json()
        except Exception:
            return []
        out = []
        for s in data.get("sites", []):
            uri = s.get("uri_check", "")
            if "{account}" not in uri:
                continue
            out.append({
                "name": s.get("name", "?"),
                "cat": s.get("cat", "WhatsMyName"),
                "url": uri.replace("{account}", "{}"),
                "check": "wmn",
                "e_code": s.get("e_code"),
                "e_string": s.get("e_string", ""),
                "m_string": s.get("m_string", ""),
                "country": "global",
            })
        return out

    def load_sites(self, ctx: Context) -> List[dict]:
        sites = self._load_builtin()
        if ctx.flag("wmn"):
            wmn = self._load_wmn(ctx)
            # Evitar duplicados por nombre.
            seen = {s["name"].lower() for s in sites}
            sites += [s for s in wmn if s["name"].lower() not in seen]
        return sites

    # ------------------------------------------------------------------ #
    @staticmethod
    def _exists(site: dict, r) -> bool:
        """Deteccion de existencia segun el tipo de comprobacion del sitio."""
        if r is None:
            return False
        code = r.status_code
        check = site.get("check", "status")
        if check == "wmn":
            # Formato WhatsMyName: coincidir e_code + e_string, descartar m_string.
            if site.get("e_code") and code != site["e_code"]:
                return False
            body = r.text
            if site.get("m_string") and site["m_string"] in body:
                return False
            if site.get("e_string"):
                return site["e_string"] in body
            return code == 200
        if code != 200:
            return False
        if check == "not_found_text":
            return site.get("nf", "").lower() not in r.text.lower()
        return True

    def _check_one(self, site: dict, handle: str, ctx: Context):
        url = site["url"].format(handle)
        r = ctx.get(url, timeout=8)
        if self._exists(site, r):
            return site, url
        return None

    # ------------------------------------------------------------------ #
    def enumerate_handle(self, handle: str, ctx: Context,
                         confidence: str = CONF_CONFIRMED) -> List[Finding]:
        """Comprueba `handle` en todos los sitios y devuelve los perfiles hallados."""
        sites = self.load_sites(ctx)
        found: List[Finding] = []
        if not sites or not ctx.session:
            return found

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as pool:
            futs = {pool.submit(self._check_one, s, handle, ctx): s for s in sites}
            for fut in as_completed(futs):
                res = fut.result()
                if not res:
                    continue
                site, url = res
                found.append(Finding(
                    kind="profile",
                    label=f"{site['name']} (@{handle})",
                    value=url,
                    url=url,
                    source=self.name,
                    category=self.category,
                    confidence=confidence,
                    meta={"username": handle, "site": site["name"],
                          "grupo": site.get("cat", "")},
                ))
        found.sort(key=lambda f: f.meta.get("site", ""))
        return found

    def run(self, target: Target, ctx: Context) -> List[Finding]:
        out: List[Finding] = []
        for handle in target.usernames:
            out += self.enumerate_handle(handle, ctx, CONF_CONFIRMED)
        return out
