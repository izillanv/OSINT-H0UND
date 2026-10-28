"""
console.py
==========
Impresion por consola con color, segura en Windows (PowerShell/CMD) y Linux.

Se evita cualquier dependencia obligatoria: si `colorama` esta instalado se usa,
y si no, en Windows 10+ se habilita el modo VT (secuencias ANSI nativas). Si
nada de eso funciona, los colores se desactivan y el texto sale en plano, pero
el programa sigue imprimiendo con normalidad.
"""

from __future__ import annotations

import os
import sys

# ---------------------------------------------------------------------------
# Activacion de color multiplataforma
# ---------------------------------------------------------------------------
_COLOR = sys.stdout.isatty() or os.environ.get("FORCE_COLOR") == "1"

try:
    # colorama traduce las secuencias ANSI en Windows. Es opcional.
    import colorama  # type: ignore

    colorama.just_fix_windows_console()
except Exception:
    if os.name == "nt":
        # Fallback: habilitar el procesamiento de secuencias VT en la consola
        # de Windows 10+ sin instalar nada.
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            _COLOR = False


class C:
    """Codigos ANSI. Si el color esta desactivado, todos valen cadena vacia."""

    RESET = "\033[0m" if _COLOR else ""
    BOLD = "\033[1m" if _COLOR else ""
    DIM = "\033[2m" if _COLOR else ""

    RED = "\033[38;5;203m" if _COLOR else ""
    GREEN = "\033[38;5;114m" if _COLOR else ""
    YELLOW = "\033[38;5;221m" if _COLOR else ""
    BLUE = "\033[38;5;111m" if _COLOR else ""
    CYAN = "\033[38;5;80m" if _COLOR else ""
    MAGENTA = "\033[38;5;177m" if _COLOR else ""
    GOLD = "\033[38;5;215m" if _COLOR else ""
    GREY = "\033[38;5;245m" if _COLOR else ""


def banner(text: str) -> None:
    """Imprime el banner ASCII principal en dorado."""
    print(f"{C.GOLD}{text}{C.RESET}")


def rule(char: str = "─", width: int = 70) -> None:
    """Linea separadora tenue de ancho fijo."""
    print(f"{C.GREY}{char * width}{C.RESET}")


def section(title: str) -> None:
    """Cabecera de seccion destacada (usada entre fases del flujo)."""
    print()
    rule()
    print(f"{C.BOLD}{C.CYAN}▸ {title}{C.RESET}")
    rule()


def ok(msg: str) -> None:
    print(f"  {C.GREEN}✔{C.RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {C.YELLOW}▲{C.RESET} {msg}")


def err(msg: str) -> None:
    print(f"  {C.RED}✖{C.RESET} {msg}")


def info(msg: str) -> None:
    print(f"  {C.BLUE}ℹ{C.RESET} {msg}")


def possible(msg: str) -> None:
    """Hallazgo inferido pendiente de revision (ambar)."""
    print(f"  {C.YELLOW}?{C.RESET} {C.DIM}{msg}{C.RESET}")


def item(idx: int, label: str, detail: str = "") -> None:
    """Elemento numerado de una lista (para selecciones)."""
    tail = f"  {C.GREY}{detail}{C.RESET}" if detail else ""
    print(f"   {C.BOLD}[{idx}]{C.RESET} {label}{tail}")


def kv(key: str, value: str) -> None:
    """Par clave/valor alineado."""
    print(f"   {C.GREY}{key:<14}{C.RESET} {value}")
