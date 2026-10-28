# De mis apuntes de OSINT → a OSINT Hound

Este documento traza **cada técnica de personas de mis apuntes** y dónde está
implementada en la herramienta. Sirve de guía de defensa y deja claro qué se
incluye y qué se deja fuera a propósito.

> Los apuntes tienen tres bloques: *(1) fuentes abiertas activa/pasiva* (muy
> orientado a dominios/infraestructura), *(2) preparación/conceptos* y
> *(3) OSINT e ingeniería social* (personas). Como el encargo es **OSINT de
> personas**, implemento el bloque 3 y la parte del bloque 1 que aplica a la
> **huella web** de una persona.

---

## Bloque 3 — OSINT de personas (el núcleo del encargo)

| Técnica del apunte | Estado | Dónde en el código |
|---|---|---|
| Nombres, apellidos, **segundos apellidos / nombres de soltera**, seudónimos | ✅ | Campo `aka` (nombre alternativo) en `validators.py`; variantes de nombre en `correlate.py::_handles_from_name` |
| Correos profesionales y personales | ✅ | `validators.py` (multi-correo), `email_recon.py` |
| Búsquedas en Google/DuckDuckGo con combinaciones de nombres/alias | ✅ | `footprint.py` (menciones, multi-nombre) + `dorks.py` (multi-motor: Google, DuckDuckGo, Bing) |
| Directorios profesionales (empresas) | ✅ | `dorks.py` → `"nombre" site:linkedin.com/in`, Xing, Crunchbase, ZoomInfo; `site:linkedin.com "empresa/ciudad"` |
| **Enumeración de nicknames — WhatsMyName** | ✅ | `username_enum.py` (`--wmn`, dataset externo, cientos de sitios) |
| **Enumeración de nicknames — Sherlock** | ✅ | `external_tools.py` (+ Maigret) |
| Google dorking multi-navegador | ✅ | `dorks.py` (Google/Bing/DuckDuckGo/Yandex) |
| Importancia del alias (conectar perfiles, eliminar falsos positivos) | ✅ | Correlación por alias en `correlate.py::build_graph` + **revisión humana** en `engine.py` |
| Búsqueda de correos: técnica de **"recuperar contraseña / olvidé usuario"** | ✅ (pivote) | `dorks.py` (enlace manual) + `external_tools.py::holehe` (lo hace de forma benigna, sin login) |
| Probar con nicknames de cuentas | ✅ | `correlate.py` deriva correos candidato desde alias |
| **HaveIBeenPwned** (brechas) | ✅ | `breach_check.py` (HIBP con clave / XposedOrNot gratis) |
| DeHashed / Intel X (de pago) | ⚠️ parcial | **IntelX** como pivote manual (`dorks.py`). **DeHashed NO** (ver "excluido") |
| Redes sociales: Facebook, LinkedIn, Twitter, Instagram | ✅ | `username_enum.py` + `dorks.py` |
| **Redes geográficas: VKontakte (RU), WeChat/Douyin (CN)** | ✅ | `sites/sites.json`: VK, OK.ru, Livejournal, Habr (RU); Douban, Bilibili, Gitee (CN); Naver, Velog (KR); Qiita, Note, NicoNico (JP) |
| Búsqueda reversa de imágenes: Google Images | ✅ | `image_recon.py` (pivote) |
| Búsqueda reversa de imágenes: **Yandex** (mejores resultados) | ✅ | `image_recon.py` (pivote, con nota) |
| Búsqueda reversa de imágenes: **PimEyes (reconocimiento facial)** | ❌ excluido | Ver "excluido a propósito" |
| Metadatos: **ExifTool** | ✅ | `image_recon.py` (EXIF/GPS con Pillow; nota recomendando ExifTool para el set completo) |
| FotoForensics | ✅ | `image_recon.py` (pivote ELA, detección de manipulación) |
| Geoestimación | ✅ | `image_recon.py` (pivote de contexto visual) |
| `site:linkedin.com "Nombre de la empresa"` | ✅ | `dorks.py` |
| Dominios gubernamentales `.gov` / contexto | ✅ | `footprint.py` clasifica fuentes (oficial/gobierno, académico…) |
| **Fuentes gubernamentales: boletines, registros mercantiles** | ✅ | `public_records.py` (BOE, BORME + equivalentes por país) |
| **Contratos y subvenciones: Portal de transparencia, BOE** | ✅ | `public_records.py` (BDNS subvenciones, BOE) |
| **Primero IntelX, luego Yandex con comillas** | ✅ | `dorks.py` (grupo Correo: IntelX → "Cruce en Yandex (comillas)") |
| EmailOSINT.org / EPIEOS | ✅ | `dorks.py` (Epieos, EmailRep) |

---

## Bloque 1 — fuentes abiertas (lo que aplica a la huella *web* de una persona)

| Técnica del apunte | Estado | Dónde |
|---|---|---|
| **Wayback Machine** (snapshots) | ✅ | `domain_recon.py` (pivote del dominio asociado) |
| **DNSDumpster** (estructura de subdominios) | ✅ (pivote) + propio | `domain_recon.py`: enumeración de subdominios vía **crt.sh** + enlace a DNSDumpster |
| urlscan.io | ✅ | `domain_recon.py` (pivote) |
| `robots.txt` / `sitemap.xml` | ✅ | `domain_recon.py` (pivote) |
| Google Dorking (operadores, filetype, inurl, intitle) | ✅ | `dorks.py` |
| GitHub / Pastebin (info, API keys) | ✅ | `dorks.py` (GitHub + pastes por nombre/alias/correo) |
| DNS / WHOIS / SPF-DMARC | ✅ | `domain_recon.py` |
| Shodan / Censys / FOFA, Nmap, Amass, fuzzing | ➖ fuera de alcance | Son de *infraestructura/pentest*, no de OSINT de **personas**. No se incluyen para no desviar el foco del encargo |

---

## Excluido a propósito (está en los apuntes, pero cruza la línea)

- **PimEyes / reconocimiento facial.** Identificar a una persona por su cara a
  partir de una foto es una capacidad de vigilancia con alto potencial de abuso.
  La búsqueda inversa que sí incluyo localiza la **misma foto** reutilizada, no
  rostros parecidos.
- **DeHashed / volcados de credenciales en claro (combolists).** Automatizar el
  acceso a contraseñas filtradas convierte la herramienta en algo para comprometer
  cuentas. Me quedo en el nivel de **concienciación**: *en qué brechas* aparece un
  correo (HIBP/XposedOrNot), nunca las contraseñas.

Ambas decisiones **suman** en el criterio de uso ético/legal de la rúbrica y
quedan documentadas en el README y en el informe (panel de limitaciones).

---

## Qué añadió esta ronda (a partir de los apuntes)

1. Campo **`aka`** (nombre de soltera / seudónimo) en CLI (`--aka`), asistente y web.
2. **Variantes de nombre** mucho más ricas (apellidos compuestos, inicial+apellido,
   orden invertido) en la derivación de candidatos.
3. **+29 sitios** en el catálogo integrado, con **redes geográficas** (RU/CN/KR/JP).
4. **Dorks nuevos**: multi-motor, LinkedIn/directorios profesionales, nombre+empresa,
   EmailOSINT/EmailRep, recuperación de cuenta, IntelX→Yandex.
5. **Imagen**: TinEye, **FotoForensics** (ELA) y **geoestimación**; nota de ExifTool.
6. **Huella web**: **Wayback Machine**, **urlscan.io**, DNSDumpster, robots/sitemap.
7. Huella pública, dorks y registros oficiales ahora **también** por los nombres
   alternativos.
