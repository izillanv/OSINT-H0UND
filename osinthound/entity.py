"""
entity.py
=========
Modelo del GRAFO de relaciones: nodos (entidades) y aristas (relaciones).

El grafo es el corazon del informe. Se construye a partir del objetivo y de los
hallazgos aceptados por el analista, y sabe exportarse a tres formatos:
  - `to_dict()` : estructura lista para vis-network (informe HTML) y para JSON.
  - `to_dot()`  : texto Graphviz DOT (render con `dot -Tpng`, o import a otras
                  herramientas tipo Maltego/Gephi).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from . import config
from .config import CONF_CONFIRMED, CONF_POSSIBLE, NODE_STYLES


def _slug(text: str) -> str:
    """Normaliza un texto a un identificador estable para nodos."""
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:80] or "n"


@dataclass
class Node:
    id: str
    type: str
    label: str
    confidence: str = CONF_CONFIRMED
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def color(self) -> str:
        return NODE_STYLES.get(self.type, NODE_STYLES["pivot"])["color"]

    @property
    def icon(self) -> str:
        return NODE_STYLES.get(self.type, NODE_STYLES["pivot"])["icon"]


@dataclass
class Edge:
    src: str
    dst: str
    label: str = ""
    confidence: str = CONF_CONFIRMED


class Graph:
    """Contenedor de nodos y aristas con deduplicado por id."""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.root_id: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Construccion
    # ------------------------------------------------------------------ #
    def add_node(self, type_: str, label: str, value: Optional[str] = None,
                 confidence: str = CONF_CONFIRMED, meta: Optional[dict] = None,
                 root: bool = False) -> str:
        """Anade (o reutiliza) un nodo y devuelve su id."""
        node_id = f"{type_}:{_slug(value or label)}"
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(
                id=node_id, type=type_, label=label,
                confidence=confidence, meta=meta or {},
            )
        else:
            # Si llega la version confirmada de un nodo antes inferido, mejora.
            node = self.nodes[node_id]
            if confidence == CONF_CONFIRMED:
                node.confidence = CONF_CONFIRMED
            if meta:
                node.meta.update(meta)
        if root:
            self.root_id = node_id
        return node_id

    def add_edge(self, src: str, dst: str, label: str = "",
                 confidence: str = CONF_CONFIRMED) -> None:
        """Anade una relacion si ambos extremos existen y no esta duplicada."""
        if src not in self.nodes or dst not in self.nodes or src == dst:
            return
        for e in self.edges:
            if e.src == src and e.dst == dst:
                if confidence == CONF_CONFIRMED:
                    e.confidence = CONF_CONFIRMED
                return
        self.edges.append(Edge(src, dst, label, confidence))

    # ------------------------------------------------------------------ #
    # Estadisticas (para la cabecera del informe)
    # ------------------------------------------------------------------ #
    def stats(self) -> Dict[str, int]:
        by_type: Dict[str, int] = {}
        for n in self.nodes.values():
            by_type[n.type] = by_type.get(n.type, 0) + 1
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "profiles": by_type.get("profile", 0) + by_type.get("username", 0),
            "emails": by_type.get("email", 0),
            "phones": by_type.get("phone", 0),
            "domains": by_type.get("domain", 0),
            "breaches": by_type.get("breach", 0),
            "records": by_type.get("record", 0),
        }

    # ------------------------------------------------------------------ #
    # Exportaciones
    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        """
        Estructura para vis-network y para el JSON de salida. Cada nodo lleva
        color/forma segun su tipo y confianza; las aristas/nodos inferidos van
        con linea discontinua.
        """
        vis_nodes = []
        for n in self.nodes.values():
            possible = n.confidence == CONF_POSSIBLE
            vis_nodes.append({
                "id": n.id,
                "label": f"{n.icon} {n.label}",
                "group": n.type,
                "type": n.type,
                "confidence": n.confidence,
                "title": self._tooltip(n),
                "color": {
                    "background": n.color if not possible else "#2a2f3a",
                    "border": n.color,
                },
                "shape": "box" if n.type in ("person",) else "dot",
                "borderWidth": 3 if n.id == self.root_id else 1,
                "shapeProperties": {"borderDashes": [6, 4] if possible else False},
                "value": 30 if n.id == self.root_id else 12,
                "meta": n.meta,
            })
        vis_edges = []
        for e in self.edges:
            possible = e.confidence == CONF_POSSIBLE
            vis_edges.append({
                "from": e.src,
                "to": e.dst,
                "label": e.label,
                "dashes": [6, 4] if possible else False,
                "color": {"color": "#56c5b5" if not possible else "#f2b544",
                          "opacity": 0.55},
            })
        return {
            "root": self.root_id,
            "nodes": vis_nodes,
            "edges": vis_edges,
            "stats": self.stats(),
        }

    def _tooltip(self, n: Node) -> str:
        """Texto emergente del nodo (vis-network)."""
        style = NODE_STYLES.get(n.type, NODE_STYLES["pivot"])
        conf = "Confirmado" if n.confidence == CONF_CONFIRMED else "POSIBLE (revisar)"
        return f"{style['label']} · {conf}\n{n.label}"

    def to_dot(self) -> str:
        """
        Exporta a Graphviz DOT. Render:  dot -Tpng grafo.dot -o grafo.png
        Tambien sirve para importar en otras herramientas de grafos.
        """
        lines = [
            "digraph osint_hound {",
            '  graph [bgcolor="#0d1117", rankdir=TB, splines=true, overlap=false];',
            '  node  [style="filled,rounded", shape=box, fontname="Helvetica", '
            'fontcolor="#0d1117", color="#0d1117"];',
            '  edge  [color="#56c5b5", fontcolor="#9db1c7", fontname="Helvetica"];',
        ]
        for n in self.nodes.values():
            dash = ', style="filled,rounded,dashed"' if n.confidence == CONF_POSSIBLE else ""
            label = n.label.replace('"', "'")
            lines.append(
                f'  "{n.id}" [label="{label}", fillcolor="{n.color}"{dash}];'
            )
        for e in self.edges:
            style = ' [style=dashed]' if e.confidence == CONF_POSSIBLE else ""
            lbl = f' [label="{e.label}"]' if e.label and not style else ""
            lines.append(f'  "{e.src}" -> "{e.dst}"{style or lbl};')
        lines.append("}")
        return "\n".join(lines)
