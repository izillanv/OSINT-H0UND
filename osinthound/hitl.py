"""
hitl.py
=======
Human-in-the-loop: primitivas de interaccion para que **una persona decida**
en los puntos clave del flujo, en lugar de automatizarlo todo a ciegas.

Esto no es solo usabilidad: es un control deliberado. OSINT Hound no vuelca
automaticamente "todo sobre alguien"; el analista:
  1. confirma que tiene autorizacion (puerta de consentimiento),
  2. elige que modulos lanzar,
  3. revisa los candidatos y descarta homonimos / falsos positivos,
  4. decide que pivotes seguir.

En modo no interactivo (`--auto`) estas primitivas aplican valores por defecto
razonables, salvo la puerta de consentimiento, que exige una confirmacion
explicita por bandera para no saltarse nunca el paso etico.
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional, Sequence, Tuple

from . import console
from .console import C


class HITL:
    """
    Gestor de decisiones humanas.

    Parametros
    ----------
    interactive : si False, no se pregunta nada por consola (modo --auto).
    authorized  : en modo no interactivo, indica que el usuario ya ha
                  declarado por bandera que tiene autorizacion.
    """

    def __init__(self, interactive: bool = True, authorized: bool = False):
        self.interactive = interactive
        self.authorized = authorized

    # ------------------------------------------------------------------ #
    # Puerta de consentimiento (uso etico/legal)
    # ------------------------------------------------------------------ #
    def consent_gate(self) -> bool:
        """
        Muestra el aviso de uso etico y exige confirmacion explicita.
        Devuelve True si se puede continuar.
        """
        console.section("Uso etico y legal")
        print(f"""  {C.DIM}OSINT Hound recopila SOLO informacion de fuentes abiertas y publicas.
  Usalo unicamente con una base legitima:
    · analisis de tu PROPIA huella digital,
    · auditoria de exposicion con AUTORIZACION por escrito,
    · ejercicio de red team con ALCANCE acordado.
  No lo uses para acosar, vigilar o perfilar sin consentimiento.
  Eres responsable del cumplimiento del RGPD/LOPDGDD y la ley aplicable.{C.RESET}""")
        print()

        if not self.interactive:
            if self.authorized:
                console.ok("Autorizacion declarada por bandera (--yes). Continuo.")
                return True
            console.err(
                "Modo no interactivo sin --yes: no se confirma autorizacion. Abortando."
            )
            return False

        ans = input(
            f"  {C.BOLD}¿Confirmas que tienes una base legitima para esta busqueda? "
            f"[s/N]{C.RESET} "
        ).strip().lower()
        if ans in ("s", "si", "sí", "y", "yes"):
            console.ok("Consentimiento registrado. Continuamos.")
            return True
        console.err("Sin consentimiento. Abortando (es lo correcto).")
        return False

    # ------------------------------------------------------------------ #
    # Confirmacion si/no
    # ------------------------------------------------------------------ #
    def confirm(self, prompt: str, default: bool = True) -> bool:
        """Pregunta si/no. En modo --auto devuelve `default`."""
        if not self.interactive:
            return default
        suffix = "[S/n]" if default else "[s/N]"
        ans = input(f"  {C.BOLD}{prompt}{C.RESET} {suffix} ").strip().lower()
        if not ans:
            return default
        return ans in ("s", "si", "sí", "y", "yes")

    # ------------------------------------------------------------------ #
    # Texto libre
    # ------------------------------------------------------------------ #
    def ask(self, prompt: str, default: str = "") -> str:
        """Pide texto. En modo --auto devuelve `default`."""
        if not self.interactive:
            return default
        hint = f" {C.GREY}({default}){C.RESET}" if default else ""
        ans = input(f"  {C.CYAN}{prompt}{C.RESET}{hint}: ").strip()
        return ans or default

    # ------------------------------------------------------------------ #
    # Seleccion multiple sobre una lista
    # ------------------------------------------------------------------ #
    def select_many(
        self,
        title: str,
        options: Sequence[Any],
        render: Callable[[Any], Tuple[str, str]],
        default_all: bool = True,
    ) -> List[Any]:
        """
        Presenta `options` numeradas y deja elegir cuales conservar.

        El usuario puede escribir:
          · "todos" / "all" / Enter  -> conservar todo (si default_all)
          · "ninguno" / "none"       -> descartar todo
          · "1,3,5" o "1-4 7"        -> conservar esos indices

        `render(opt)` devuelve (etiqueta, detalle) para pintar cada opcion.
        Devuelve la sublista elegida (mismos objetos).
        """
        options = list(options)
        if not options:
            return []

        if not self.interactive:
            return list(options) if default_all else []

        print(f"\n  {C.BOLD}{title}{C.RESET}")
        for i, opt in enumerate(options, 1):
            label, detail = render(opt)
            console.item(i, label, detail)

        tip = "todos" if default_all else "ninguno"
        raw = input(
            f"\n  {C.BOLD}Selecciona (p. ej. 1,3,5 · 2-4 · todos · ninguno) "
            f"[{tip}]{C.RESET} "
        ).strip().lower()

        if not raw:
            return list(options) if default_all else []
        if raw in ("todos", "all", "*"):
            return list(options)
        if raw in ("ninguno", "none", "-"):
            return []

        chosen = _parse_index_spec(raw, len(options))
        return [options[i] for i in chosen]


def _parse_index_spec(spec: str, n: int) -> List[int]:
    """
    Convierte "1,3 5-7" en indices base-0 validos [0,2,4,5,6].
    Ignora en silencio lo que no sea un numero/rango dentro de [1, n].
    """
    out: List[int] = []
    for token in spec.replace(",", " ").split():
        if "-" in token:
            a, _, b = token.partition("-")
            if a.isdigit() and b.isdigit():
                for k in range(int(a), int(b) + 1):
                    if 1 <= k <= n and (k - 1) not in out:
                        out.append(k - 1)
        elif token.isdigit():
            k = int(token)
            if 1 <= k <= n and (k - 1) not in out:
                out.append(k - 1)
    return out
