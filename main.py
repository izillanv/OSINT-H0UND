#!/usr/bin/env python3
"""
main.py
=======
Punto de entrada por linea de comandos de OSINT Hound.

Modos:
  - Asistente interactivo (recomendado): `python main.py`
      Pregunta los identificadores y, durante la ejecucion, deja que confirmes
      los modulos a lanzar y los hallazgos que son del objetivo (human-in-the-loop).
  - No interactivo:  `python main.py -n "Ada King" -u adaking --auto --yes`

Ejemplos:
  python main.py -n "Ada Lovelace King" -l Londres --country GB
  python main.py -u johndoe -e john@acme.com -d acme.com --auto --yes --wmn
  python main.py --list-modules
  python main.py --list-tools
"""

from __future__ import annotations

import argparse
import os
import sys
import webbrowser

from osinthound import config, console
from osinthound.console import C
from osinthound.engine import Engine
from osinthound.hitl import HITL
from osinthound.modules import get_modules
from osinthound.modules.external_tools import ExternalTools
from osinthound.report import Reporter
from osinthound.validators import build_target


def parse_args():
    p = argparse.ArgumentParser(
        prog="osint-hound",
        description="Recoleccion OSINT de personas (fuentes abiertas, human-in-the-loop).",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-n", "--name", default="", help="Nombre completo")
    p.add_argument("--aka", default="",
                   help="Nombre(s) alternativo(s)/de soltera/seudonimo (varios con comas)")
    p.add_argument("-u", "--username", default="", help="Alias/username (varios con comas)")
    p.add_argument("-e", "--email", default="", help="Correo (varios con comas)")
    p.add_argument("-p", "--phone", default="", help="Telefono (varios con comas)")
    p.add_argument("-d", "--domain", default="", help="Dominio asociado")
    p.add_argument("-l", "--location", default="", help="Ubicacion (contexto)")
    p.add_argument("--country", default=config.DEFAULT_COUNTRY,
                   help="Codigo de pais ISO-2 (ES, US, GB...). Mundial.")
    p.add_argument("--image", default="", help="Ruta a una imagen local (EXIF/GPS)")
    p.add_argument("-o", "--output", default="reports", help="Carpeta de salida")
    p.add_argument("--slug", default="", help="Nombre base del informe")
    p.add_argument("--auto", action="store_true", help="No interactivo (sin preguntas)")
    p.add_argument("--yes", action="store_true",
                   help="Declara autorizacion en modo --auto (obligatorio con --auto)")
    p.add_argument("--external", action="store_true",
                   help="Permite lanzar herramientas externas en modo --auto")
    p.add_argument("--wmn", action="store_true",
                   help="Usa el dataset WhatsMyName (cientos de sitios)")
    p.add_argument("--open", action="store_true", help="Abre el informe al terminar")
    p.add_argument("--no-color", action="store_true", help="Desactiva el color")
    p.add_argument("--list-modules", action="store_true", help="Lista los modulos y sale")
    p.add_argument("--list-tools", action="store_true",
                   help="Lista las herramientas externas detectadas y sale")
    return p.parse_args()


def list_modules():
    console.section("Modulos disponibles")
    for i, m in enumerate(get_modules(), 1):
        accepts = ", ".join(sorted(m.accepts)) or "cualquiera"
        console.item(i, m.title)
        print(f"      {C.GREY}{m.description}{C.RESET}")
        print(f"      {C.DIM}entradas: {accepts} · categoria: {m.category}{C.RESET}")


def list_tools():
    console.section("Herramientas externas")
    for tool, path in ExternalTools().installed().items():
        if path:
            console.ok(f"{tool:14} {C.GREY}{path}{C.RESET}")
        else:
            console.warn(f"{tool:14} no instalada  (pipx install {tool})")


def wizard(hitl: HITL) -> dict:
    """Pregunta los identificadores de forma interactiva."""
    console.section("Identificadores del objetivo")
    console.info("Introduce lo que tengas (deja en blanco lo que no). Varios valores con comas.")
    return {
        "name": hitl.ask("Nombre completo"),
        "aka": hitl.ask("Nombre alternativo / de soltera / seudonimo"),
        "username": hitl.ask("Alias / username"),
        "email": hitl.ask("Correo(s)"),
        "phone": hitl.ask("Telefono(s)"),
        "domain": hitl.ask("Dominio asociado"),
        "location": hitl.ask("Ubicacion (ciudad/pais)"),
        "country": hitl.ask("Codigo de pais ISO-2", config.DEFAULT_COUNTRY).upper(),
        "image": hitl.ask("Ruta a una imagen local"),
    }


def main():
    args = parse_args()
    if args.no_color:
        os.environ["FORCE_COLOR"] = "0"

    console.banner(config.BANNER)
    print(f"  {C.GREY}{config.APP_NAME} v{config.VERSION} — {config.APP_TAGLINE}{C.RESET}")

    if args.list_modules:
        list_modules(); return
    if args.list_tools:
        list_tools(); return

    hitl = HITL(interactive=not args.auto, authorized=args.yes)

    # --- Reunir identificadores ---
    cli_fields = {"name": args.name, "aka": args.aka, "username": args.username,
                  "email": args.email, "phone": args.phone, "domain": args.domain,
                  "location": args.location, "country": args.country, "image": args.image}
    any_cli = any(cli_fields[k] for k in
                  ("name", "aka", "username", "email", "phone", "domain", "image"))

    if not any_cli:
        if args.auto:
            console.err("Modo --auto sin identificadores. Usa -n/-u/-e/-p/-d.")
            sys.exit(2)
        cli_fields = wizard(hitl)

    target, warnings = build_target(cli_fields, cli_fields.get("country"))
    if warnings:
        console.section("Validacion de entrada")
        for w in warnings:
            console.warn(w)
    if not target.has_any():
        console.err("No hay ningun identificador valido. Nada que investigar.")
        sys.exit(2)

    console.section("Objetivo")
    console.kv("Resumen", target.summary())
    console.kv("Pais", config.country_name(target.country))
    if target.location:
        console.kv("Ubicacion", target.location)

    # --- Consentimiento (human-in-the-loop etico) ---
    if not hitl.consent_gate():
        sys.exit(1)

    # --- Investigacion ---
    flags = {"auto": args.auto, "external": args.external, "wmn": args.wmn}
    engine = Engine(hitl, target.country, flags)
    graph, findings, meta = engine.run(target)

    # --- Informe ---
    console.section("Informe")
    paths = Reporter(target, graph, findings, meta).save_all(args.output, args.slug)
    console.ok(f"HTML : {paths['html']}")
    console.ok(f"JSON : {paths['json']}")
    console.ok(f"DOT  : {paths['dot']}  ({C.GREY}dot -Tpng {paths['dot']} -o grafo.png{C.RESET})")

    if args.open:
        webbrowser.open("file://" + os.path.abspath(paths["html"]))
    else:
        console.info(f"Abre el informe:  {C.BOLD}{os.path.abspath(paths['html'])}{C.RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Interrumpido por el usuario.")
        sys.exit(130)
