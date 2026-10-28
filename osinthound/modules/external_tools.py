"""
modules/external_tools.py
=========================
Integra HERRAMIENTAS EXTERNAS de OSINT ya existentes (requisito explicito de la
rubrica: "integracion con al menos una herramienta externa"). Se detectan solas
en el PATH; si no estan instaladas, el framework sigue funcionando sin ellas.

Herramientas soportadas:
  - sherlock      (alias -> perfiles en redes)
  - maigret       (alias -> perfiles, mas avanzado)
  - holehe        (correo -> sitios donde esta registrado)
  - theHarvester  (dominio -> correos/subdominios)

Lanzar un recon externo es una accion "ruidosa": por eso cada ejecucion se
confirma antes (human-in-the-loop), salvo en modo --auto con --external.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from typing import Callable, List, Tuple

from ..config import CONF_CONFIRMED
from ..finding import Finding
from ..validators import Target
from .base import BaseModule, Context, register

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_FOUND_RE = re.compile(r"\[\+\]\s*([^:]+?):\s*(https?://\S+)")
_HOLEHE_RE = re.compile(r"\[\+\]\s*(\S+)")


@register
class ExternalTools(BaseModule):
    name = "external_tools"
    title = "Herramientas externas"
    description = "Integra sherlock / maigret / holehe / theHarvester si estan instaladas"
    category = "Herramientas externas"
    accepts = {"username", "email", "domain"}

    # ------------------------------------------------------------------ #
    def installed(self) -> dict:
        """Mapa herramienta -> ruta (o None si no esta en el PATH)."""
        return {t: shutil.which(t) for t in
                ("sherlock", "maigret", "holehe", "theHarvester")}

    def availability(self, ctx: Context) -> Tuple[bool, str]:
        found = [t for t, p in self.installed().items() if p]
        if found:
            return True, "instaladas: " + ", ".join(found)
        return True, "ninguna instalada (el modulo se salta)"

    def _run_cmd(self, args: List[str], timeout: int = 120) -> str:
        """Ejecuta un comando y devuelve su salida combinada (nunca lanza)."""
        try:
            proc = subprocess.run(args, capture_output=True, text=True,
                                  timeout=timeout, check=False)
            return (proc.stdout or "") + "\n" + (proc.stderr or "")
        except Exception as ex:  # noqa: BLE001
            return f"__error__ {ex}"

    def _should_run(self, ctx: Context, prompt: str) -> bool:
        if ctx.hitl.interactive:
            return ctx.hitl.confirm(prompt, default=True)
        return bool(ctx.flag("external"))

    # ------------------------------------------------------------------ #
    def run(self, target: Target, ctx: Context) -> List[Finding]:
        tools = self.installed()
        out: List[Finding] = []

        # -- sherlock / maigret: por cada alias --
        for tool in ("sherlock", "maigret"):
            if not tools[tool]:
                continue
            for u in target.usernames:
                if not self._should_run(ctx, f"¿Lanzar {tool} sobre @{u}?"):
                    continue
                if tool == "sherlock":
                    txt = self._run_cmd([tool, u, "--print-found", "--timeout", "8"])
                else:
                    txt = self._run_cmd([tool, u, "--timeout", "8", "--no-color"])
                for site, url in _FOUND_RE.findall(txt):
                    out.append(Finding(
                        kind="profile", label=f"{site.strip()} ({tool})",
                        value=url, url=url, source=tool, category=self.category,
                        confidence=CONF_CONFIRMED,
                        meta={"username": u, "herramienta": tool},
                    ))

        # -- holehe: por cada correo --
        if tools["holehe"]:
            for e in target.emails:
                if not self._should_run(ctx, f"¿Lanzar holehe sobre {e}?"):
                    continue
                txt = self._run_cmd(["holehe", e, "--only-used", "--no-color"])
                for site in _HOLEHE_RE.findall(txt):
                    out.append(Finding(
                        kind="profile", label=f"{site} (holehe)",
                        value=f"{e}@{site}", url="", source="holehe",
                        category=self.category, confidence=CONF_CONFIRMED,
                        meta={"correo": e, "herramienta": "holehe",
                              "nota": "correo registrado en el servicio"},
                    ))

        # -- theHarvester: por cada dominio --
        if tools["theHarvester"]:
            for d in target.domains:
                if not self._should_run(ctx, f"¿Lanzar theHarvester sobre {d}?"):
                    continue
                txt = self._run_cmd(
                    ["theHarvester", "-d", d, "-b", "duckduckgo,bing,crtsh"], timeout=180)
                for email in sorted(set(_EMAIL_RE.findall(txt))):
                    if email.endswith(d):
                        out.append(Finding(
                            kind="email", label=email, value=email, source="theHarvester",
                            category=self.category, confidence=CONF_CONFIRMED,
                            meta={"dominio": d, "herramienta": "theHarvester"},
                        ))
        return out
