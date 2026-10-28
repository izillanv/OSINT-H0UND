"""
OSINT Hound
===========
Framework modular de recoleccion OSINT de personas, con correlacion de datos,
grafo de relaciones interactivo (arbol o red), interfaz web y decisiones
human-in-the-loop en todo el flujo.

El paquete esta organizado en:
  - config      : configuracion central (HTTP, claves, paleta del grafo).
  - console     : impresion con color segura en Windows/Linux.
  - validators  : validacion de la entrada sin interrumpir la ejecucion.
  - hitl        : primitivas de confirmacion humana (human-in-the-loop).
  - entity      : modelo de datos del grafo (nodos, aristas y exportaciones).
  - correlate   : derivacion de candidatos y correlacion entre entidades.
  - engine      : orquestacion de modulos + revision humana + grafo.
  - modules/    : una fuente OSINT por fichero (plugins).
  - report/     : generacion del informe (HTML, JSON y Graphviz DOT).
"""

from .config import VERSION, APP_NAME, APP_TAGLINE

__all__ = ["VERSION", "APP_NAME", "APP_TAGLINE"]
__version__ = VERSION
