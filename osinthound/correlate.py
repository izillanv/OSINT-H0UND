"""
correlate.py
============
Dos responsabilidades:

1. `derive_candidates(target)` — a partir de datos parciales (un nombre, un
   alias, un correo) DERIVA candidatos probables (alias y correos) marcados como
   **POSIBLE**. Esto habilita el pivote: p. ej., de "Ada Lovelace" se proponen
   "adalovelace", "ada.lovelace"... que luego el analista puede enumerar.

2. `build_graph(target, findings)` — construye el grafo de relaciones uniendo el
   objetivo con los hallazgos aceptados y CORRELACIONANDO entidades entre si
   (perfiles que comparten alias, correo cuyo dominio coincide con un dominio
   objetivo, brecha ligada a su correo, etc.).

Lo inferido se distingue siempre de lo confirmado (confianza POSIBLE / linea
discontinua en el grafo), para no "ensuciar" las conclusiones.
"""

from __future__ import annotations

from typing import List

from . import config
from .config import CONF_CONFIRMED, CONF_POSSIBLE
from .entity import Graph
from .finding import Finding, possible as possible_finding
from .validators import Target

# Proveedores de correo mas comunes para proponer correos candidatos.
_COMMON_MAIL = ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "proton.me"]


# --------------------------------------------------------------------------- #
# 1. Derivacion de candidatos (POSIBLE)
# --------------------------------------------------------------------------- #
def _handles_from_name(name: str) -> List[str]:
    """Genera alias plausibles a partir de un nombre completo."""
    parts = [p for p in name.lower().split() if p.isalpha()]
    if not parts:
        return []
    out: List[str] = []
    joined = "".join(parts)
    out.append(joined)                                   # adalovelace
    out.append(".".join(parts))                          # ada.lovelace
    out.append("_".join(parts))                          # ada_lovelace
    if len(parts) >= 2:
        out.append(parts[0] + parts[-1][0])              # adal
        out.append(parts[0][0] + parts[-1])              # alovelace
        out.append(parts[0] + "." + parts[-1])           # ada.lovelace (dup-safe)
    # Dedup conservando orden y longitud razonable.
    seen, uniq = set(), []
    for h in out:
        if 3 <= len(h) <= 30 and h not in seen:
            seen.add(h)
            uniq.append(h)
    return uniq[:6]


def derive_candidates(target: Target) -> List[Finding]:
    """
    Devuelve hallazgos POSIBLE con alias y correos candidatos. No consulta la
    red: solo propone. El analista decide si enumerarlos.
    """
    out: List[Finding] = []
    handles: List[str] = []

    # Alias candidatos desde el nombre.
    if target.name:
        handles = _handles_from_name(target.name)
        for h in handles:
            if h not in target.usernames:
                out.append(possible_finding(
                    kind="username", label=f"Alias candidato: {h}", value=h,
                    source="correlate", category="Candidatos (revisar)",
                    meta={"derived_from": "nombre", "username": h},
                ))

    # Si hay alias confirmados, tambien sirven de base para correos.
    base_handles = list(target.usernames) + handles

    # Correos candidatos desde alias.
    for h in base_handles[:4]:
        for dom in _COMMON_MAIL[:3]:
            cand = f"{h}@{dom}"
            if cand not in target.emails:
                out.append(possible_finding(
                    kind="email", label=f"Correo candidato: {cand}", value=cand,
                    source="correlate", category="Candidatos (revisar)",
                    meta={"derived_from": f"alias:{h}"},
                ))

    # Alias candidato desde la parte local de un correo confirmado.
    for email in target.emails:
        local = email.split("@", 1)[0]
        if local and local not in base_handles and local not in target.usernames:
            out.append(possible_finding(
                kind="username", label=f"Alias candidato: {local}", value=local,
                source="correlate", category="Candidatos (revisar)",
                meta={"derived_from": f"correo:{email}", "username": local},
            ))

    return out


# --------------------------------------------------------------------------- #
# 2. Construccion del grafo
# --------------------------------------------------------------------------- #
def build_graph(target: Target, findings: List[Finding]) -> Graph:
    """Monta el grafo correlacionado a partir del objetivo y los hallazgos."""
    g = Graph()

    # --- Nodo raiz: la persona ---
    root_label = target.name or (target.usernames[0] if target.usernames
                                 else target.summary())
    root = g.add_node("person", root_label, value=root_label, root=True,
                      meta={"resumen": target.summary(),
                            "pais": config.country_name(target.country),
                            "ubicacion": target.location or "—"})

    # --- Identificadores base del objetivo ---
    uname_nodes = {}
    for u in target.usernames:
        nid = g.add_node("username", f"@{u}", value=u)
        g.add_edge(root, nid, "alias")
        uname_nodes[u] = nid

    email_nodes = {}
    for e in target.emails:
        nid = g.add_node("email", e, value=e)
        g.add_edge(root, nid, "correo")
        email_nodes[e] = nid

    domain_nodes = {}
    for d in target.domains:
        nid = g.add_node("domain", d, value=d)
        g.add_edge(root, nid, "dominio")
        domain_nodes[d] = nid

    for p in target.phones:
        nid = g.add_node("phone", p, value=p)
        g.add_edge(root, nid, "telefono")

    if target.location:
        lid = g.add_node("location", target.location, value=target.location)
        g.add_edge(root, lid, "ubicacion")

    # --- Hallazgos aceptados ---
    for f in findings:
        if f.accepted is False:
            continue  # descartado explicitamente por el analista
        conf = f.confidence

        if f.kind in ("profile", "username"):
            # Perfil social -> cuelga del alias que lo origino (o de la persona).
            uname = f.meta.get("username")
            if uname and uname not in uname_nodes:
                uname_nodes[uname] = g.add_node(
                    "username", f"@{uname}", value=uname, confidence=conf)
                g.add_edge(root, uname_nodes[uname], "alias", conf)
            parent = uname_nodes.get(uname, root)
            pid = g.add_node("profile", f.label, value=f.url or f.value,
                             confidence=conf,
                             meta={"url": f.url, **f.meta})
            g.add_edge(parent, pid, "perfil", conf)

        elif f.kind == "email":
            nid = g.add_node("email", f.value or f.label, value=f.value or f.label,
                             confidence=conf, meta=f.meta)
            g.add_edge(root, nid, "correo", conf)
            email_nodes.setdefault(f.value, nid)

        elif f.kind == "breach":
            email = f.meta.get("email")
            parent = email_nodes.get(email, root)
            bid = g.add_node("breach", f.label, value=f"{f.label}:{email}",
                             confidence=conf, meta=f.meta)
            g.add_edge(parent, bid, "expuesto en", conf)

        elif f.kind == "phone":
            nid = g.add_node("phone", f.value or f.label, value=f.value or f.label,
                             confidence=conf, meta=f.meta)
            g.add_edge(root, nid, "telefono", conf)

        elif f.kind == "domain":
            nid = g.add_node("domain", f.value or f.label, value=f.value or f.label,
                             confidence=conf, meta=f.meta)
            g.add_edge(root, nid, "dominio", conf)
            domain_nodes.setdefault(f.value, nid)

        elif f.kind == "record":
            rid = g.add_node("record", f.label, value=f.url or f.label,
                             confidence=conf, meta={"url": f.url, **f.meta})
            g.add_edge(root, rid, "registro", conf)

        elif f.kind == "image":
            iid = g.add_node("image", f.label, value=f.value or f.label,
                             confidence=conf, meta=f.meta)
            g.add_edge(root, iid, "imagen", conf)
            gps = f.meta.get("gps")
            if gps:
                lid = g.add_node("location", f"GPS {gps}", value=str(gps),
                                 confidence=conf)
                g.add_edge(iid, lid, "capturada en", conf)

        elif f.kind == "location":
            lid = g.add_node("location", f.label, value=f.value or f.label,
                             confidence=conf, meta=f.meta)
            g.add_edge(root, lid, "ubicacion", conf)
        # Los pivotes/notas no entran al grafo: van en una pestana del informe.

    # --- Correlacion cruzada: correo cuyo dominio coincide con un dominio objetivo ---
    for email, enode in email_nodes.items():
        if not email or "@" not in email:
            continue
        dom = email.split("@", 1)[1]
        if dom in domain_nodes:
            g.add_edge(enode, domain_nodes[dom], "mismo dominio", CONF_POSSIBLE)

    return g
