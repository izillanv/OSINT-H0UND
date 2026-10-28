#!/usr/bin/env python3
"""
web/app.py
==========
Interfaz web de OSINT Hound (Flask). Flujo guiado en 3 fases con human-in-the-loop:

    1. /            Formulario de identificadores + consentimiento.
    2. /discover    Ejecuta los modulos y muestra los CANDIDATOS para que el
                    analista marque cuales son del objetivo (revision humana).
    3. /report/...  Construye el grafo con lo confirmado y genera el informe,
                    que se muestra embebido con enlaces de descarga.

Arranque:
    python web/app.py        # http://127.0.0.1:5000
"""

from __future__ import annotations

import os
import sys
import uuid

# Permitir importar el paquete `osinthound` estando en web/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import (Flask, abort, render_template, request,  # noqa: E402
                   send_file, send_from_directory)

from osinthound import config  # noqa: E402
from osinthound.correlate import build_graph  # noqa: E402
from osinthound.engine import Engine, _CONFIRMABLE  # noqa: E402
from osinthound.hitl import HITL  # noqa: E402
from osinthound.report import Reporter  # noqa: E402
from osinthound.validators import build_target  # noqa: E402

app = Flask(__name__)

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(_BASE, "reports")

# Almacen en memoria de investigaciones en curso (herramienta local, 1 usuario).
JOBS: dict = {}

_FIELDS = ("name", "username", "email", "phone", "domain", "location",
           "country", "image")


@app.route("/")
def index():
    return render_template("index.html",
                           countries=sorted(config.COUNTRIES.items(),
                                            key=lambda kv: kv[1]),
                           default=config.DEFAULT_COUNTRY)


@app.route("/discover", methods=["POST"])
def discover():
    if not request.form.get("consent"):
        return render_template("index.html",
                               countries=sorted(config.COUNTRIES.items(),
                                                key=lambda kv: kv[1]),
                               default=config.DEFAULT_COUNTRY,
                               error="Debes confirmar el uso etico/legal para continuar.")

    raw = {k: request.form.get(k, "").strip() for k in _FIELDS}
    target, warnings = build_target(raw, raw.get("country"))
    if not target.has_any():
        return render_template("index.html",
                               countries=sorted(config.COUNTRIES.items(),
                                                key=lambda kv: kv[1]),
                               default=config.DEFAULT_COUNTRY,
                               error="Introduce al menos un identificador valido.",
                               warnings=warnings)

    hitl = HITL(interactive=False, authorized=True)
    flags = {"auto": True, "external": False, "wmn": bool(request.form.get("wmn"))}
    engine = Engine(hitl, target.country, flags)
    findings, meta = engine.collect(target)

    token = uuid.uuid4().hex[:12]
    JOBS[token] = {"target": target, "findings": findings, "meta": meta,
                   "warnings": warnings}

    confirmables = [(i, f) for i, f in enumerate(findings) if f.kind in _CONFIRMABLE]
    pivots = [f for f in findings if f.kind not in _CONFIRMABLE]
    return render_template("review.html", token=token, target=target, meta=meta,
                           warnings=warnings, confirmables=confirmables,
                           n_pivots=len(pivots))


@app.route("/report/<token>", methods=["POST"])
def report(token):
    job = JOBS.get(token)
    if not job:
        abort(404)
    keep = set(request.form.getlist("keep"))
    for i, f in enumerate(job["findings"]):
        if f.kind in _CONFIRMABLE:
            f.accepted = str(i) in keep

    accepted = [f for f in job["findings"] if f.accepted is not False]
    graph = build_graph(job["target"], accepted)
    slug = f"web_{token}"
    Reporter(job["target"], graph, job["findings"], job["meta"]).save_all(
        REPORTS_DIR, slug)
    return render_template("results.html", slug=slug, stats=graph.stats(),
                           meta=job["meta"], target=job["target"])


@app.route("/r/<slug>.html")
def serve_report(slug):
    path = os.path.join(REPORTS_DIR, f"{slug}.html")
    if not os.path.isfile(path):
        abort(404)
    return send_file(path)


@app.route("/r/<slug>.json")
def serve_json(slug):
    path = os.path.join(REPORTS_DIR, f"{slug}.json")
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=True,
                     download_name=f"{slug}.json")


@app.route("/static/<path:fname>")
def static_files(fname):
    return send_from_directory(os.path.join(_BASE, "web", "static"), fname)


if __name__ == "__main__":
    print(f"  {config.APP_NAME} web  →  http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
