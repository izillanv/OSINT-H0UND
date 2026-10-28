"""
engine.py
=========
Orquesta una investigacion completa, intercalando decisiones humanas:

  Fase 1  Derivacion de candidatos (alias/correos probables) -> POSIBLE.
  Fase 2  Seleccion de modulos a ejecutar (human-in-the-loop).
  Fase 3  Ejecucion de los modulos elegidos (con control de errores por modulo).
  Fase 4  (Opcional) Enumeracion de los alias candidatos.
  Fase 5  Revision humana: el analista confirma que hallazgos son del objetivo
          y descarta homonimos / falsos positivos.
  Fase 6  Construccion del grafo correlacionado con lo aceptado.

Devuelve (grafo, findings, meta) para que el generador de informes haga el resto.
"""

from __future__ import annotations

import time
from typing import Dict, List, Tuple

from . import config, console
from .console import C
from .correlate import build_graph, derive_candidates
from .entity import Graph
from .finding import Finding
from .hitl import HITL
from .modules import get_modules
from .modules.base import Context
from .modules.username_enum import UsernameEnum
from .validators import Target

# Tipos de hallazgo que el analista confirma uno a uno (el resto son pivotes).
_CONFIRMABLE = {"profile", "username", "email", "breach", "domain",
                "record", "image", "location", "phone"}


class Engine:
    def __init__(self, hitl: HITL, country: str = config.DEFAULT_COUNTRY,
                 flags: dict = None):
        self.hitl = hitl
        self.ctx = Context(hitl, country, flags or {})
        self.modules = get_modules()

    # ------------------------------------------------------------------ #
    @staticmethod
    def _dedup(findings: List[Finding]) -> List[Finding]:
        seen, out = set(), []
        for f in findings:
            k = f.key()
            if k not in seen:
                seen.add(k)
                out.append(f)
        return out

    def _render_module(self, m) -> Tuple[str, str]:
        avail, reason = m.availability(self.ctx)
        tag = f"{C.GREEN}disp.{C.RESET}" if avail else f"{C.RED}no disp.{C.RESET}"
        detail = f"{m.description}" + (f"  [{reason}]" if reason else "")
        return f"{m.title}", detail

    def _render_finding(self, f: Finding) -> Tuple[str, str]:
        mark = (f"{C.GREEN}●{C.RESET}" if not f.is_possible
                else f"{C.YELLOW}◐ POSIBLE{C.RESET}")
        return f"{mark} {f.label}", (f.url or f.value or "")[:60]

    # ------------------------------------------------------------------ #
    def collect(self, target: Target, module_names: List[str] = None
                ) -> Tuple[List[Finding], Dict]:
        """
        Ejecuta los modulos y devuelve (findings, meta) SIN revision ni grafo.
        Lo usa la interfaz web, que hace la revision human-in-the-loop en el
        navegador (y luego llama a `correlate.build_graph`). Los pivotes quedan
        aceptados; los confirmables, pendientes de decidir (accepted=None).
        """
        import time
        started = time.time()
        meta: Dict = {
            "objetivo": target.summary(),
            "pais": config.country_name(target.country),
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
            "modulos": [], "advertencias": [], "herramientas_externas": "",
        }
        findings: List[Finding] = list(derive_candidates(target))
        for m in self.modules:
            if not m.applicable(target):
                continue
            if module_names and m.name not in module_names:
                continue
            avail, reason = m.availability(self.ctx)
            if not avail:
                continue
            try:
                findings += m.run(target, self.ctx)
                meta["modulos"].append(m.title)
            except Exception as ex:  # noqa: BLE001
                meta["advertencias"].append(f"{m.title}: {ex}")
        findings = self._dedup(findings)
        for f in findings:
            if f.kind not in _CONFIRMABLE:
                f.accepted = True
        meta["duracion_s"] = round(time.time() - started, 1)
        meta["consultas_realizadas"] = len(self.ctx.query_log)
        meta["total_hallazgos"] = len(findings)
        return findings, meta

    # ------------------------------------------------------------------ #
    def run(self, target: Target) -> Tuple[Graph, List[Finding], Dict]:
        started = time.time()
        meta: Dict = {
            "objetivo": target.summary(),
            "pais": config.country_name(target.country),
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
            "modulos": [], "advertencias": [], "herramientas_externas": "",
        }

        # --- Fase 1: candidatos derivados (POSIBLE) ---
        console.section("Fase 1 · Derivacion de candidatos")
        candidates = derive_candidates(target)
        cand_handles = [f.meta.get("username") for f in candidates
                        if f.kind == "username" and f.meta.get("username")]
        if candidates:
            console.info(f"Propuestos {len(candidates)} candidatos (alias/correos) a revisar.")
        else:
            console.info("Sin datos suficientes para derivar candidatos.")

        # --- Fase 2: seleccion de modulos ---
        console.section("Fase 2 · Seleccion de modulos")
        applicable = [m for m in self.modules if m.applicable(target)]
        if not applicable:
            console.err("Ningun modulo aplica a los identificadores dados.")
            return build_graph(target, []), candidates, meta
        selected = self.hitl.select_many(
            "Modulos disponibles para este objetivo:", applicable,
            self._render_module, default_all=True)
        if not selected:
            console.warn("No se selecciono ningun modulo.")

        # --- Fase 3: ejecucion ---
        console.section("Fase 3 · Recoleccion")
        findings: List[Finding] = []
        for m in selected:
            avail, reason = m.availability(self.ctx)
            if not avail:
                console.warn(f"{m.title}: {reason} (omitido)")
                continue
            print(f"  {C.CYAN}▸{C.RESET} {m.title} {C.GREY}…{C.RESET}", flush=True)
            try:
                res = m.run(target, self.ctx)
            except Exception as ex:  # noqa: BLE001
                console.err(f"{m.title} fallo: {ex}")
                meta["advertencias"].append(f"{m.title}: {ex}")
                res = []
            findings += res
            meta["modulos"].append(m.title)
            n_conf = sum(1 for f in res if not f.is_possible)
            console.ok(f"{m.title}: {len(res)} hallazgos ({n_conf} confirmados)")

        meta["herramientas_externas"] = next(
            (m.availability(self.ctx)[1] for m in self.modules
             if m.name == "external_tools"), "")

        # --- Fase 4: enumeracion de candidatos (opcional) ---
        if cand_handles and any(m.name == "username_enum" for m in selected):
            if self.hitl.confirm(
                    f"¿Enumerar tambien los {len(cand_handles)} alias candidatos "
                    f"(marcados POSIBLE)?", default=False):
                console.info("Enumerando alias candidatos…")
                enum = UsernameEnum()
                for h in cand_handles:
                    findings += enum.enumerate_handle(h, self.ctx, config.CONF_POSSIBLE)

        # Juntar candidatos derivados y deduplicar.
        findings = self._dedup(findings + candidates)

        # --- Fase 5: revision humana ---
        console.section("Fase 5 · Revision (human-in-the-loop)")
        confirmables = [f for f in findings if f.kind in _CONFIRMABLE]
        pivots = [f for f in findings if f.kind not in _CONFIRMABLE]
        for p in pivots:
            p.accepted = True  # los pivotes son solo enlaces de revision manual

        if confirmables:
            console.info("Marca los hallazgos que SI corresponden al objetivo "
                         "(descarta homonimos y falsos positivos).")
            kept = self.hitl.select_many(
                "Hallazgos a confirmar:", confirmables,
                self._render_finding, default_all=True)
            kept_keys = {id(f) for f in kept}
            for f in confirmables:
                f.accepted = id(f) in kept_keys
            console.ok(f"{len(kept)} confirmados · {len(confirmables) - len(kept)} descartados")
        else:
            console.info("No hay hallazgos que requieran confirmacion.")

        # --- Fase 6: grafo ---
        console.section("Fase 6 · Correlacion y grafo")
        accepted = [f for f in findings if f.accepted is not False]
        graph = build_graph(target, accepted)
        s = graph.stats()
        console.ok(f"Grafo: {s['nodes']} nodos, {s['edges']} relaciones")

        meta["duracion_s"] = round(time.time() - started, 1)
        meta["consultas_realizadas"] = len(self.ctx.query_log)
        meta["total_hallazgos"] = len(findings)
        meta["confirmados"] = sum(1 for f in findings if f.accepted and not f.is_possible)
        return graph, findings, meta
