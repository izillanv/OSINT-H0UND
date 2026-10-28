"""
config.py
=========
Configuracion central de OSINT Hound.

Se define en un unico sitio para que todo el framework comparta los mismos
valores (metadatos, cabeceras HTTP, tiempos de espera, claves de API opcionales
y la paleta/iconos del grafo). Asi, para ajustar un timeout o cambiar un color
solo hay que tocar aqui.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Metadatos del proyecto
# ---------------------------------------------------------------------------
VERSION = "3.0.0"
APP_NAME = "OSINT Hound"
APP_TAGLINE = "Recoleccion OSINT de personas - correlacion, grafo y human-in-the-loop"

# Banner ASCII que se muestra al arrancar el asistente (main.py).
BANNER = r"""
   ____  _____ _____ _   _ _____    _   _                       _
  / __ \/ ____|_   _| \ | |_   _|  | | | |                     | |
 | |  | | (___   | | |  \| | | |    | |_| | ___  _   _ _ __   __| |
 | |  | |\___ \  | | | . ` | | |    |  _  |/ _ \| | | | '_ \ / _` |
 | |__| |____) |_| |_| |\  |_| |_   | | | | (_) | |_| | | | | (_| |
  \____/|_____/|_____|_| \_|_____|  |_| |_|\___/ \__,_|_| |_|\__,_|
"""

# ---------------------------------------------------------------------------
# Peticiones HTTP
# ---------------------------------------------------------------------------
# User-Agent de navegador real: muchos sitios devuelven 403 a "python-requests".
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
)
DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

HTTP_TIMEOUT = 8          # segundos por peticion individual
REQUEST_DELAY = 1.2       # pausa entre peticiones al mismo servicio (buena educacion)
MAX_WORKERS = 12          # hilos para la enumeracion de usuarios


def _load_dotenv(path: str = ".env") -> None:
    """
    Carga un fichero .env minimalista (clave=valor) sin depender de librerias
    externas. Nunca lanza excepcion: si el fichero no existe, no hace nada.
    """
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                value = value.strip().strip('"').strip("'")
                if value:  # solo sobreescribimos si hay valor real
                    os.environ.setdefault(key.strip(), value)
    except Exception:
        # La configuracion nunca debe tumbar el programa.
        pass


_load_dotenv()

# ---------------------------------------------------------------------------
# Claves de API (TODAS opcionales)
# ---------------------------------------------------------------------------
API_KEYS = {
    # HIBP v3 (de pago). Sin ella se usa XposedOrNot (gratis).
    "hibp": os.environ.get("HIBP_API_KEY", "").strip(),
    # Hunter.io (freemium): correos corporativos.
    "hunter": os.environ.get("HUNTER_API_KEY", "").strip(),
    # NumVerify (freemium): enriquecimiento telefonico.
    "numverify": os.environ.get("NUMVERIFY_API_KEY", "").strip(),
}


def has_key(name: str) -> bool:
    """Devuelve True si existe una clave de API no vacia para `name`."""
    return bool(API_KEYS.get(name))


# ---------------------------------------------------------------------------
# Tipos de nodo del grafo -> color + icono.
# Se usan tanto en el informe HTML como en el export a Graphviz DOT.
# ---------------------------------------------------------------------------
NODE_STYLES = {
    # tipo        color       icono (emoji)   etiqueta legible
    "person":   {"color": "#f2b544", "icon": "🎯", "label": "Objetivo"},
    "username": {"color": "#56c5b5", "icon": "🧑", "label": "Alias"},
    "profile":  {"color": "#56c5b5", "icon": "🔗", "label": "Perfil"},
    "email":    {"color": "#6ea8fe", "icon": "✉️", "label": "Correo"},
    "phone":    {"color": "#b98cf0", "icon": "📞", "label": "Telefono"},
    "domain":   {"color": "#6ea8fe", "icon": "🌐", "label": "Dominio"},
    "breach":   {"color": "#e5534b", "icon": "🔥", "label": "Brecha"},
    "record":   {"color": "#9db1c7", "icon": "📄", "label": "Registro publico"},
    "image":    {"color": "#d98c5f", "icon": "🖼️", "label": "Imagen"},
    "location": {"color": "#8fd08c", "icon": "📍", "label": "Ubicacion"},
    "pivot":    {"color": "#7a869a", "icon": "🧭", "label": "Pivote"},
}

# Nivel de confianza de un hallazgo.
CONF_CONFIRMED = "confirmed"   # verificado o confirmado por el analista
CONF_POSSIBLE = "possible"     # derivado/inferido: necesita revision humana

# ---------------------------------------------------------------------------
# Cobertura geografica (mundial).
# Codigos ISO-3166 alpha-2 -> nombre, para la validacion telefonica y los
# registros publicos. No es exhaustivo pero cubre los paises mas habituales;
# phonenumbers soporta de todos modos cualquier pais via prefijo E.164.
# ---------------------------------------------------------------------------
COUNTRIES = {
    "ES": "España", "PT": "Portugal", "FR": "Francia", "IT": "Italia",
    "DE": "Alemania", "GB": "Reino Unido", "IE": "Irlanda", "NL": "Países Bajos",
    "BE": "Bélgica", "CH": "Suiza", "AT": "Austria", "SE": "Suecia",
    "NO": "Noruega", "DK": "Dinamarca", "FI": "Finlandia", "PL": "Polonia",
    "CZ": "Chequia", "GR": "Grecia", "RO": "Rumanía", "HU": "Hungría",
    "US": "Estados Unidos", "CA": "Canadá", "MX": "México", "BR": "Brasil",
    "AR": "Argentina", "CL": "Chile", "CO": "Colombia", "PE": "Perú",
    "UY": "Uruguay", "EC": "Ecuador", "VE": "Venezuela", "BO": "Bolivia",
    "PY": "Paraguay", "CR": "Costa Rica", "PA": "Panamá", "DO": "Rep. Dominicana",
    "GT": "Guatemala", "AU": "Australia", "NZ": "Nueva Zelanda", "JP": "Japón",
    "CN": "China", "KR": "Corea del Sur", "IN": "India", "SG": "Singapur",
    "AE": "Emiratos Árabes", "SA": "Arabia Saudí", "IL": "Israel", "TR": "Turquía",
    "RU": "Rusia", "UA": "Ucrania", "ZA": "Sudáfrica", "MA": "Marruecos",
    "EG": "Egipto", "NG": "Nigeria",
}
DEFAULT_COUNTRY = "ES"


def country_name(code: str) -> str:
    """Nombre legible de un codigo ISO (o el propio codigo si no se conoce)."""
    return COUNTRIES.get((code or "").upper(), (code or "").upper())
