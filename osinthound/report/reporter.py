"""
report/reporter.py
==================
Construye el informe a partir del grafo, los hallazgos y los metadatos.

Genera tres ficheros:
  - <slug>.html : informe visual autocontenido (grafo arbol/red, inspector,
                  pestañas por tipo de dato y seccion de LIMITACIONES).
  - <slug>.json : volcado completo (metadatos + grafo + hallazgos) reutilizable.
  - <slug>.dot  : grafo en Graphviz DOT (render con `dot -Tpng`).
"""

from __future__ import annotations

import html
import json
import os
import re
from typing import Dict, List

from .. import config
from ..config import NODE_STYLES
from ..entity import Graph
from ..finding import Finding
from ..validators import Target
from .template import HTML


def _esc(x) -> str:
    return html.escape(str(x), quote=True)


def _fmt(v) -> str:
    """Formatea un valor de metadato para mostrarlo en una fila."""
    if isinstance(v, (list, tuple)):
        return ", ".join(_esc(x) for x in v) if v else "—"
    if isinstance(v, dict):
        return _esc(json.dumps(v, ensure_ascii=False))
    return _esc(v)


class Reporter:
    def __init__(self, target: Target, graph: Graph,
                 findings: List[Finding], meta: Dict):
        self.target = target
        self.graph = graph
        self.findings = [f for f in findings if f.accepted is not False]
        self.meta = meta

    # ================================================================== #
    # Guardado
    # ================================================================== #
    def save_all(self, outdir: str = "reports", slug: str = "") -> Dict[str, str]:
        os.makedirs(outdir, exist_ok=True)
        slug = slug or self._slug()
        paths = {
            "html": os.path.join(outdir, f"{slug}.html"),
            "json": os.path.join(outdir, f"{slug}.json"),
            "dot": os.path.join(outdir, f"{slug}.dot"),
        }
        with open(paths["html"], "w", encoding="utf-8") as fh:
            fh.write(self.build_html())
        with open(paths["json"], "w", encoding="utf-8") as fh:
            json.dump(self.build_json(), fh, ensure_ascii=False, indent=2)
        with open(paths["dot"], "w", encoding="utf-8") as fh:
            fh.write(self.graph.to_dot())
        return paths

    def _slug(self) -> str:
        base = self.target.name or (self.target.usernames[0]
                                    if self.target.usernames else "objetivo")
        s = re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_")
        import time
        return f"osint_{s}_{time.strftime('%Y%m%d_%H%M')}"

    # ================================================================== #
    # JSON
    # ================================================================== #
    def build_json(self) -> Dict:
        return {
            "herramienta": f"{config.APP_NAME} v{config.VERSION}",
            "metadatos": self.meta,
            "objetivo": {
                "nombre": self.target.name, "alias": self.target.usernames,
                "correos": self.target.emails, "telefonos": self.target.phones,
                "dominios": self.target.domains, "pais": self.target.country,
                "ubicacion": self.target.location,
            },
            "grafo": self.graph.to_dict(),
            "hallazgos": [f.to_dict() for f in self.findings],
        }

    # ================================================================== #
    # HTML
    # ================================================================== #
    def build_html(self) -> str:
        buckets = self._bucket()
        gd = self.graph.to_dict()
        stats = gd["stats"]

        out = HTML
        out = out.replace("{{TITLE}}", _esc(self.target.name or self.target.summary()))
        out = out.replace("{{SUBTITLE}}", _esc(self.target.summary()))
        out = out.replace("{{VERSION}}", config.VERSION)
        out = out.replace("{{GENERATED}}", _esc(self.meta.get("fecha", "")))
        out = out.replace("{{HERO_CHIPS}}", self._hero_chips())

        expo = self._exposure(stats)
        out = out.replace("{{EXPO_LABEL}}", expo[0])
        out = out.replace("{{EXPO_CLASS}}", expo[1])
        out = out.replace("{{EXPO_PCT}}", str(expo[2]))

        out = out.replace("{{STAT_TILES}}", self._tiles(stats))

        nav, content = self._tabs(buckets)
        out = out.replace("{{TABS_NAV}}", nav)
        out = out.replace("{{TABS_CONTENT}}", content)

        out = out.replace("{{GRAPH_JSON}}", json.dumps(gd, ensure_ascii=False))
        out = out.replace("{{META_JSON}}", json.dumps(self.meta, ensure_ascii=False))
        return out

    # ---- Hero / tiles / exposure ------------------------------------- #
    def _hero_chips(self) -> str:
        m = self.meta
        chips = [
            ("🌍", "Pais", m.get("pais", "—")),
            ("📍", "Ubicacion", self.target.location or "—"),
            ("🧩", "Modulos", str(len(m.get("modulos", [])))),
            ("🔎", "Consultas", str(m.get("consultas_realizadas", "—"))),
            ("⏱", "Duracion", f"{m.get('duracion_s', '—')}s"),
        ]
        ext = m.get("herramientas_externas")
        if ext:
            chips.append(("🛠", "Externas", ext))
        return "".join(
            f'<span class="chip">{ic} {lab}: <b>{_esc(val)}</b></span>'
            for ic, lab, val in chips)

    def _tiles(self, s: Dict) -> str:
        data = [
            ("nodes", "Nodos en el grafo", "🕸️", "var(--teal)"),
            ("profiles", "Perfiles / alias", "🔗", "var(--teal)"),
            ("emails", "Correos", "✉️", "var(--blue)"),
            ("phones", "Telefonos", "📞", "var(--violet)"),
            ("domains", "Dominios", "🌐", "var(--blue)"),
            ("breaches", "Brechas", "🔥", "var(--red)"),
            ("records", "Registros publicos", "📄", "var(--muted)"),
        ]
        out = []
        for key, lab, ic, col in data:
            n = s.get(key, 0)
            out.append(
                f'<div class="tile" style="--accent:{col}"><div class="ic">{ic}</div>'
                f'<div class="n">{n}</div><div class="l">{lab}</div></div>')
        return "".join(out)

    def _exposure(self, s: Dict):
        pct = min(100, s.get("breaches", 0) * 22 + min(s.get("profiles", 0), 12) * 4
                  + s.get("emails", 0) * 4 + s.get("domains", 0) * 3
                  + s.get("records", 0))
        if pct >= 60:
            return "Alta", "high", pct
        if pct >= 30:
            return "Media", "med", pct
        if pct >= 12:
            return "Baja", "low", pct
        return "Minima", "min", max(pct, 6)

    # ---- Bucketing --------------------------------------------------- #
    def _bucket(self) -> Dict[str, List[Finding]]:
        b = {k: [] for k in ("perfiles", "correos", "telefono", "dominio",
                             "registros", "huella", "dorks", "candidatos", "imagen")}
        for f in self.findings:
            if f.category == "Candidatos (revisar)":
                b["candidatos"].append(f)
            elif f.kind in ("profile", "username"):
                b["perfiles"].append(f)
            elif f.kind in ("email", "breach"):
                b["correos"].append(f)
            elif f.kind == "phone":
                b["telefono"].append(f)
            elif f.kind == "domain":
                b["dominio"].append(f)
            elif f.category == "Registros publicos":
                b["registros"].append(f)
            elif f.category == "Huella publica":
                b["huella"].append(f)
            elif f.category == "Imagen":
                b["imagen"].append(f)
            elif f.category == "Dominio":
                b["dominio"].append(f)
            else:
                b["dorks"].append(f)
        return b

    # ---- Tabs -------------------------------------------------------- #
    def _tabs(self, b: Dict[str, List[Finding]]):
        # (id, etiqueta, contenido, contador) — Grafo y Limitaciones siempre.
        panels = []
        panels.append(("grafo", "Grafo", self._graph_panel(), None))
        tab_defs = [
            ("perfiles", "Perfiles", b["perfiles"], None),
            ("correos", "Correos y brechas", b["correos"], None),
            ("telefono", "Telefono", b["telefono"], None),
            ("dominio", "Dominio", b["dominio"], None),
            ("registros", "Registros publicos", b["registros"], "grupo"),
            ("huella", "Huella publica", b["huella"], "tipo"),
            ("imagen", "Imagen", b["imagen"], None),
            ("dorks", "Dorks y pivotes", b["dorks"], "grupo"),
            ("candidatos", "Candidatos", b["candidatos"], None),
        ]
        for tid, lab, items, gk in tab_defs:
            if not items:
                continue
            panels.append((tid, lab, self._cards(items, gk), len(items)))
        panels.append(("limitaciones", "Limitaciones", self._limitations(), None))

        nav, content, first = [], [], True
        for tid, lab, html_content, count in panels:
            cls = "tab active" if first else "tab"
            cbadge = f'<span class="c">{count}</span>' if count else ""
            nav.append(f'<button class="{cls}" data-tab="{tid}">{lab}{cbadge}</button>')
            pcls = "panel active" if first else "panel"
            content.append(f'<section id="panel-{tid}" class="{pcls}">{html_content}</section>')
            first = False
        return "".join(nav), "".join(content)

    def _graph_panel(self) -> str:
        legend = "".join(
            f'<span><i style="background:{st["color"]}"></i>{st["label"]}</span>'
            for k, st in NODE_STYLES.items())
        return f"""
        <div class="graph-wrap">
          <div id="graph">
            <div class="toolbar">
              <button class="tbtn" id="b-tree" onclick="toggleTree()">🌳 Arbol</button>
              <button class="tbtn on" id="b-phys" onclick="togglePhysics()">✦ Fisica</button>
              <button class="tbtn" onclick="fitGraph()">⤢ Centrar</button>
              <button class="tbtn" onclick="exportPNG()">⇩ PNG</button>
              <button class="tbtn" onclick="exportJSON()">⇩ JSON</button>
            </div>
            <div class="legend">{legend}</div>
          </div>
          <aside class="inspector" id="insp"></aside>
        </div>"""

    # ---- Cards ------------------------------------------------------- #
    def _cards(self, items: List[Finding], group_key: str = None) -> str:
        if not items:
            return '<div class="empty">Sin resultados en esta categoria.</div>'
        # Confirmados primero.
        items = sorted(items, key=lambda f: (f.is_possible, f.label.lower()))
        if not group_key:
            return '<div class="grid">' + "".join(self._card(f) for f in items) + '</div>'

        groups: Dict[str, List[Finding]] = {}
        for f in items:
            groups.setdefault(f.meta.get(group_key, "Otros"), []).append(f)
        out = []
        for gname in sorted(groups):
            out.append(f'<div class="group-h">{_esc(gname)}</div>')
            out.append('<div class="grid">' +
                       "".join(self._card(f) for f in groups[gname]) + '</div>')
        return "".join(out)

    def _card(self, f: Finding) -> str:
        st = NODE_STYLES.get(f.node_type, NODE_STYLES["pivot"])
        possible = f.is_possible
        if f.kind == "breach":
            badge = '<span class="badge breach">brecha</span>'
        elif possible:
            badge = '<span class="badge maybe">posible</span>'
        else:
            badge = '<span class="badge ok">confirmado</span>'

        rows = self._card_rows(f)
        url = f.url or (f.value if f.value.startswith("http") else "")
        url_html = (f'<div class="cu"><a href="{_esc(url)}" target="_blank" '
                    f'rel="noopener">{_esc(url)}</a></div>') if url else (
                    f'<div class="cu">{_esc(f.value)}</div>' if f.value else "")

        cls = "card possible" if possible else "card"
        return (f'<div class="{cls}"><div class="ct"><span class="em">{st["icon"]}</span>'
                f'<span>{_esc(f.label)}</span>{badge}</div>{url_html}'
                f'{rows}</div>')

    def _card_rows(self, f: Finding) -> str:
        """Filas de metadatos relevantes segun el tipo de hallazgo."""
        m = f.meta or {}
        rows = []

        if f.kind == "email":
            if m.get("foto"):
                rows.append(('Foto Gravatar',
                             f'<img src="{_esc(m["foto"])}" width="40" height="40" '
                             f'style="border-radius:8px;vertical-align:middle">'))
            for k in ("nombre_gravatar", "proveedor", "acepta_correo", "mx", "perfil_gravatar"):
                if m.get(k) not in (None, ""):
                    rows.append((k.replace("_", " "), m[k]))
        elif f.kind == "breach":
            for k in ("fecha", "datos_filtrados", "cuentas_afectadas", "fuente"):
                if m.get(k) not in (None, ""):
                    rows.append((k.replace("_", " "), m[k]))
        elif f.kind == "phone":
            for k in ("pais", "prefijo_pais", "operador", "tipo_linea",
                      "internacional", "zonas_horarias"):
                if m.get(k) not in (None, ""):
                    rows.append((k.replace("_", " "), m[k]))
            piv = m.get("pivotes", {})
            if piv:
                links = " · ".join(f'<a href="{_esc(u)}" target="_blank" rel="noopener">{_esc(k)}</a>'
                                   for k, u in piv.items())
                rows.append(("pivotes", links))
        elif f.kind == "domain":
            for k in ("a", "mx", "ns", "spf", "dmarc", "riesgo_spoofing",
                      "registrador", "creado", "caduca", "servidores_nombres",
                      "contacto_whois"):
                if m.get(k) not in (None, "", []):
                    rows.append((k.replace("_", " "), m[k]))
            subs = m.get("subdominios", [])
            if subs:
                rows.append((f"subdominios ({len(subs)})", ", ".join(subs[:12])))
        else:
            for k in ("site", "grupo", "tipo", "via", "herramienta", "fuente",
                      "nota", "instruccion", "dominio_padre"):
                if m.get(k) not in (None, ""):
                    rows.append((k.replace("_", " "), m[k]))

        if not rows:
            return ""
        body = "".join(
            f'<div><span class="k">{_esc(k)}</span>'
            f'<span class="v">{v if isinstance(v, str) and v.startswith("<") else _fmt(v)}</span></div>'
            for k, v in rows)
        return f'<div class="rows">{body}</div>'

    # ---- Limitations ------------------------------------------------- #
    def _limitations(self) -> str:
        warns = self.meta.get("advertencias", [])
        warns_html = ""
        if warns:
            warns_html = ('<div class="note"><h4>⚠ Incidencias durante la ejecucion</h4><ul>' +
                          "".join(f"<li>{_esc(w)}</li>" for w in warns) + "</ul></div>")
        mods = ", ".join(self.meta.get("modulos", [])) or "—"
        return f"""
        {warns_html}
        <div class="note">
          <h4>Alcance y limitaciones de este informe</h4>
          <ul>
            <li><b>Solo fuentes abiertas (OSINT).</b> No se accede a sistemas privados,
                ni se vulnera ninguna cuenta. La informacion ya era publicamente accesible.</li>
            <li><b>Deteccion heuristica.</b> La existencia de un perfil por codigo de estado
                puede dar <i>falsos positivos</i>; por eso hay una fase de revision humana.</li>
            <li><b>Homonimos.</b> Un nombre puede corresponder a varias personas. Los hallazgos
                marcados <b>POSIBLE</b> no estan confirmados como del objetivo.</li>
            <li><b>Brechas de datos.</b> Indican que un correo aparecio en una filtracion
                conocida; no se muestran ni se recuperan contrasenas.</li>
            <li><b>Datos derivados.</b> Los alias/correos "candidatos" son inferencias para
                pivotar, no hechos verificados.</li>
            <li><b>Temporalidad.</b> La informacion refleja el momento de la consulta y puede
                quedar obsoleta.</li>
            <li><b>Dependencias externas.</b> Algunos modulos requieren claves de API o
                herramientas instaladas; si faltan, esa fuente no aporta datos.</li>
          </ul>
        </div>
        <div class="note" style="border-left-color:var(--teal)">
          <h4>Trazabilidad</h4>
          <ul>
            <li>Modulos ejecutados: {_esc(mods)}</li>
            <li>Consultas de red realizadas: {self.meta.get('consultas_realizadas', '—')}</li>
            <li>Total de hallazgos recogidos: {self.meta.get('total_hallazgos', '—')}</li>
          </ul>
        </div>"""
