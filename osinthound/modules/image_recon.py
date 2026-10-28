"""
modules/image_recon.py
======================
Analiza una IMAGEN local:
  - Metadatos **EXIF** (camara, fecha de captura, software).
  - Coordenadas **GPS** incrustadas -> enlace a Google Maps.
  - Pivotes de **busqueda inversa** (Google / Yandex / Bing) para localizar la
    MISMA foto reutilizada en la web.

IMPORTANTE: NO hay reconocimiento facial. La busqueda inversa solo sirve para
encontrar donde mas aparece ESA foto, nunca para identificar rostros.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

from ..config import CONF_POSSIBLE
from ..finding import Finding
from ..validators import Target
from .base import BaseModule, Context, register

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False


def _to_decimal(dms, ref) -> Optional[float]:
    """Convierte grados/minutos/segundos EXIF a grados decimales."""
    try:
        d, m, s = [float(x) for x in dms]
        val = d + m / 60.0 + s / 3600.0
        if ref in ("S", "W"):
            val = -val
        return round(val, 6)
    except Exception:
        return None


@register
class ImageRecon(BaseModule):
    name = "image_recon"
    title = "Metadatos de imagen"
    description = "EXIF/GPS de una foto + busqueda inversa (sin reconocimiento facial)"
    category = "Imagen"
    accepts = {"image"}

    def availability(self, ctx: Context):
        return (_HAS_PIL, "" if _HAS_PIL else "Falta la libreria Pillow")

    def _exif(self, path: str) -> Tuple[Dict, Optional[Tuple[float, float]]]:
        meta: Dict = {}
        gps_coords = None
        if not _HAS_PIL:
            return meta, None
        try:
            img = Image.open(path)
            exif = img._getexif() or {}
        except Exception:
            return meta, None

        gps_raw = {}
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo":
                for t in value:
                    gps_raw[GPSTAGS.get(t, t)] = value[t]
            elif tag in ("Make", "Model", "DateTimeOriginal", "Software", "Artist"):
                meta[tag] = str(value).strip("\x00 ")

        if gps_raw.get("GPSLatitude") and gps_raw.get("GPSLongitude"):
            lat = _to_decimal(gps_raw["GPSLatitude"], gps_raw.get("GPSLatitudeRef", "N"))
            lon = _to_decimal(gps_raw["GPSLongitude"], gps_raw.get("GPSLongitudeRef", "E"))
            if lat is not None and lon is not None:
                gps_coords = (lat, lon)
        return meta, gps_coords

    def run(self, target: Target, ctx: Context) -> List[Finding]:
        path = target.image
        if not path or not os.path.isfile(path):
            return []
        meta, gps = self._exif(path)
        fname = os.path.basename(path)

        detail = {"fichero": fname,
                  "camara": " ".join(filter(None, [meta.get("Make"), meta.get("Model")])) or "—",
                  "fecha_captura": meta.get("DateTimeOriginal", "—"),
                  "software": meta.get("Software", "—")}
        if gps:
            detail["gps"] = gps
            detail["mapa"] = f"https://www.google.com/maps?q={gps[0]},{gps[1]}"

        out: List[Finding] = [Finding(
            kind="image", label=f"Imagen: {fname}", value=fname,
            source=self.name, category=self.category, meta=detail,
        )]
        # Pivotes de busqueda inversa (benignos): abrir el motor y subir la foto.
        for name, url in (
            ("Google Imagenes (inversa)", "https://images.google.com/"),
            ("Yandex (inversa)", "https://yandex.com/images/"),
            ("Bing Visual Search", "https://www.bing.com/visualsearch"),
        ):
            out.append(Finding(
                kind="pivot", label=f"Busqueda inversa: {name}", value=fname,
                url=url, source=self.name, category="Imagen",
                confidence=CONF_POSSIBLE,
                meta={"instruccion": "Subir la foto manualmente para localizar reutilizaciones"},
            ))
        return out
