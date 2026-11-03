# ðŸº OSINT Hound

**Framework modular de recolecciÃ³n OSINT de personas**, con correlaciÃ³n de datos,
grafo de relaciones interactivo (en **Ã¡rbol** o en red), interfaz **web** y
decisiones **human-in-the-loop** en todo el flujo.

> âš–ï¸ **Uso Ã©tico y legal.** Esta herramienta recopila **solo informaciÃ³n de fuentes
> abiertas** (OSINT). Ãšsala con una base legÃ­tima: anÃ¡lisis de tu **propia** huella
> digital, auditorÃ­as de exposiciÃ³n **con autorizaciÃ³n**, o red team con **alcance
> acordado**. No la uses para acosar, vigilar o perfilar a nadie sin consentimiento.
> Eres responsable del cumplimiento del **RGPD/LOPDGDD** y la legislaciÃ³n aplicable.

---

## âœ¨ QuÃ© hace

A partir de **uno o varios identificadores** (nombre, alias, correo, telÃ©fono o
dominio), OSINT Hound recolecta informaciÃ³n de mÃºltiples fuentes, **deja que el
analista confirme quÃ© es real** (descartando homÃ³nimos y falsos positivos),
**correlaciona** las entidades entre sÃ­ y genera un **informe visual** con el grafo
de relaciones.

- ðŸŒ **Alcance mundial** â€” no solo EspaÃ±a. TelÃ©fonos de cualquier paÃ­s (E.164),
  registros oficiales por paÃ­s (BOE/BORME, Companies House, SEC, EUR-Lexâ€¦) y
  cientos de sitios sociales internacionales.
- ðŸ§  **Human-in-the-loop** â€” nada "ruidoso" se lanza sin tu confirmaciÃ³n: una
  puerta de consentimiento, la **selecciÃ³n de mÃ³dulos**, la **revisiÃ³n de
  candidatos** y la elecciÃ³n de pivotes son decisiones tuyas.
- ðŸ•¸ï¸ **Grafo bonito** â€” vista en **Ã¡rbol jerÃ¡rquico** o en **red de fuerzas**,
  inspector de nodos, leyenda, fÃ­sica on/off y exportaciÃ³n a **PNG** y **JSON**
  (y a **Graphviz DOT** desde la CLI).
- ðŸ–¥ï¸ **Interfaz web** â€” flujo guiado en 3 fases (descubrir â†’ confirmar â†’ informe).
- ðŸ§© **Modular y ampliable** â€” cada fuente es un mÃ³dulo independiente; aÃ±adir una
  nueva es crear un fichero. Integra herramientas externas si estÃ¡n instaladas.
- ðŸ”’ **Confirmado vs. POSIBLE** â€” lo verificado se distingue siempre de lo inferido
  (lÃ­nea discontinua Ã¡mbar en el grafo y en el informe).

ðŸ‘‰ **Ejemplo de ejecuciÃ³n** con datos ficticios: abre
[`reports/demo_report.html`](reports/demo_report.html) (o genÃ©ralo con `python demo.py`).

---

## ðŸ”Ž Fuentes y mÃ³dulos

| MÃ³dulo | Entrada | QuÃ© obtiene |
|---|---|---|
| **Huella pÃºblica** (`footprint`) | nombre / alias de nombre | Menciones del nombre (y nombres de soltera/seudÃ³nimos) en la web, clasificadas (oficial/gobierno, acadÃ©mico, medios, redes, documentos) |
| **EnumeraciÃ³n de usuarios** (`username_enum`) | alias | ComprobaciÃ³n del alias en ~80 sitios integrados (incluye redes **geogrÃ¡ficas**: VK, Douban, Qiita, Naverâ€¦) **+ cientos** vÃ­a dataset de **WhatsMyName** (`--wmn`) |
| **AnÃ¡lisis de correo** (`email_recon`) | correo | **Gravatar** (nombre, foto y cuentas vinculadas), registros **MX** y clasificaciÃ³n del proveedor |
| **Brechas de datos** (`breach_check`) | correo | Filtraciones conocidas (**HIBP** con clave / **XposedOrNot** gratis). No muestra contraseÃ±as |
| **AnÃ¡lisis telefÃ³nico** (`phone_check`) | telÃ©fono | PaÃ­s, operador, tipo de lÃ­nea, zona horaria y E.164 (**mundial**, sin red) |
| **AuditorÃ­a de dominio** (`domain_recon`) | dominio | **DNS** (A/MX/NS/TXT), **WHOIS**, **SPF/DMARC**, **subdominios** (crt.sh) + **Wayback Machine, urlscan, DNSDumpster** |
| **Registros oficiales** (`public_records`) | nombre | Accesos a **BOE, BORME, BDNS**, boletines autonÃ³micos y equivalentes por paÃ­s (Companies House, SEC, The Gazette, EUR-Lexâ€¦) |
| **Metadatos de imagen** (`image_recon`) | imagen | **EXIF/GPS** (cÃ¡mara, fecha, mapa) + bÃºsqueda inversa (Google/Yandex/TinEye), **FotoForensics** y geoestimaciÃ³n (**sin reconocimiento facial**) |
| **Google Dorks y pivotes** (`dorks`) | cualquiera | Dorks multi-motor y enlaces OSINT por categorÃ­a (Nombre/Alias/Correo/TelÃ©fono): LinkedIn/directorios, IntelXâ†’Yandex, EmailOSINTâ€¦ |
| **Herramientas externas** (`external_tools`) | alias/correo/dominio | Integra **sherlock, maigret, holehe, theHarvester** si estÃ¡n instaladas |

### CorrelaciÃ³n (extra)
El mÃ³dulo de correlaciÃ³n deriva **alias y correos candidatos** a partir de datos
parciales (p. ej., del nombre â†’ `adaloveking`, `ada.king@gmail.com`â€¦) marcados como
**POSIBLE**, y une las entidades: perfiles que comparten alias, correo cuyo dominio
coincide con un dominio objetivo, brecha ligada a su correo, etc.

---

## ðŸ§± Requisitos previos

- **Python 3.9 o superior**.
- Paquetes de `requirements.txt` (`requests`, `phonenumbers`, `dnspython`,
  `python-whois`, `Pillow`, `Flask`). Todo funciona con estos.
- *(Opcional)* Herramientas externas vÃ­a **pipx**:
  ```bash
  pipx install sherlock-project
  pipx install maigret
  pipx install holehe
  pipx install theHarvester
  ```
- *(Opcional)* **ExifTool** para metadatos de imagen mÃ¡s completos (Pillow ya cubre
  EXIF/GPS bÃ¡sicos).
- *(Opcional)* Claves de API en un fichero `.env` (ver `.env.example`): `HIBP_API_KEY`,
  `HUNTER_API_KEY`. **Ninguna es obligatoria.**

---

## ðŸš€ InstalaciÃ³n

### Linux / macOS
```bash
git clone https://github.com/<tu-usuario>/osint-hound.git
cd osint-hound

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows (PowerShell)
```powershell
git clone https://github.com/<tu-usuario>/osint-hound.git
cd osint-hound

python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```
> En PowerShell, si `activate` da problemas por la *ExecutionPolicy*, puedes
> **saltarte la activaciÃ³n** y llamar al intÃ©rprete del venv directamente:
> `venv\Scripts\python.exe main.py`

---

## ðŸ§­ Uso

### 1) Asistente interactivo (recomendado)
```bash
python main.py            # Windows: venv\Scripts\python.exe main.py
```
Te preguntarÃ¡ los identificadores y, durante la ejecuciÃ³n, confirmarÃ¡s:
la **autorizaciÃ³n**, los **mÃ³dulos** a lanzar y quÃ© **hallazgos** son del objetivo.

### 2) LÃ­nea de comandos (no interactivo)
```bash
# Persona en Reino Unido
python main.py -n "Ada Lovelace King" -l Londres --country GB

# Varios identificadores, modo automÃ¡tico (requiere declarar autorizaciÃ³n)
python main.py -u johndoe -e john@acme.com -d acme.com --auto --yes --wmn

# Permitir herramientas externas en automÃ¡tico
python main.py -u johndoe --auto --yes --external

# Listados
python main.py --list-modules
python main.py --list-tools
```
ParÃ¡metros: `-n/--name`, `--aka` (nombre de soltera/seudÃ³nimo), `-u/--username`,
`-e/--email`, `-p/--phone`, `-d/--domain`, `-l/--location`, `--country`, `--image`,
`-o/--output`, `--slug`, `--auto`, `--yes`, `--external`, `--wmn`, `--open`, `--no-color`.

### 3) Interfaz web
```bash
python web/app.py
# Abre http://127.0.0.1:5000
```
Flujo de 3 fases: introduces los datos â†’ el servidor **descubre candidatos** â†’
**confirmas** cuÃ¡les son del objetivo (human-in-the-loop) â†’ se genera el informe
con el grafo embebido y botones de descarga.

### 4) Demo con datos ficticios (sin red)
```bash
python demo.py
# Genera reports/demo_report.html â€” Ã¡brelo en el navegador
```

---

## ðŸ“Š El informe

El HTML generado (`reports/*.html`) es **autocontenido** (solo el grafo carga
vis-network desde CDN) e incluye:

- **Cabecera** con el objetivo, nivel de **exposiciÃ³n** y estadÃ­sticas.
- **Grafo interactivo** con conmutador **Ãrbol âŸ· Red**, fÃ­sica on/off, centrar,
  **exportar PNG** y **exportar JSON**.
- **Inspector** lateral: pulsa un nodo para ver metadatos, evidencia y la fuente.
- **PestaÃ±as** por tipo de dato: Perfiles, Correos y brechas, TelÃ©fono, Dominio,
  Registros pÃºblicos, Huella pÃºblica, Imagen, Dorks y pivotes, Candidatos.
- **Limitaciones y trazabilidad** (alcance OSINT, falsos positivos, homÃ³nimos,
  mÃ³dulos ejecutados y nÂº de consultas).

AdemÃ¡s se exportan:
- `reports/*.json` â€” **volcado completo** (metadatos + grafo + hallazgos), reutilizable.
- `reports/*.dot` â€” grafo en **Graphviz DOT**: `dot -Tpng reports/<archivo>.dot -o grafo.png`
  (o impÃ³rtalo en otras herramientas de grafos / Maltego).

---

## ðŸ—‚ï¸ Arquitectura

```
osint-hound/
â”œâ”€â”€ main.py                 # CLI (asistente + argparse)
â”œâ”€â”€ demo.py                 # informe de ejemplo con datos ficticios
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ .env.example            # claves de API (opcionales)
â”œâ”€â”€ osinthound/
â”‚   â”œâ”€â”€ config.py           # configuraciÃ³n central (HTTP, claves, paleta, paÃ­ses)
â”‚   â”œâ”€â”€ console.py          # salida con color (segura en Windows)
â”‚   â”œâ”€â”€ validators.py       # validaciÃ³n de entrada (no interrumpe la ejecuciÃ³n)
â”‚   â”œâ”€â”€ hitl.py             # primitivas human-in-the-loop
â”‚   â”œâ”€â”€ finding.py          # modelo de hallazgo
â”‚   â”œâ”€â”€ entity.py           # grafo: nodos, aristas y export (dict/DOT)
â”‚   â”œâ”€â”€ correlate.py        # candidatos derivados + construcciÃ³n del grafo
â”‚   â”œâ”€â”€ engine.py           # orquestaciÃ³n + revisiÃ³n
â”‚   â”œâ”€â”€ modules/            # 1 fuente OSINT por fichero (plugins)
â”‚   â”‚   â”œâ”€â”€ base.py         # BaseModule + Context + registro
â”‚   â”‚   â”œâ”€â”€ footprint.py  username_enum.py  email_recon.py  breach_check.py
â”‚   â”‚   â”œâ”€â”€ phone_check.py  domain_recon.py  public_records.py
â”‚   â”‚   â”œâ”€â”€ image_recon.py  dorks.py  external_tools.py
â”‚   â”œâ”€â”€ report/             # generaciÃ³n del informe (HTML/JSON/DOT)
â”‚   â””â”€â”€ sites/sites.json    # catÃ¡logo de sitios (fallback offline)
â””â”€â”€ web/                    # interfaz Flask (templates + static)
```

### AÃ±adir una fuente nueva
1. Crea `osinthound/modules/mi_modulo.py` con una clase `@register` que herede de
   `BaseModule` e implemente `run(target, ctx)`.
2. ImpÃ³rtala en `osinthound/modules/__init__.py`.
3. Listo: aparece sola en el selector de mÃ³dulos, la CLI y la web. **No hay que
   tocar el motor** ni el informe.

---

## ðŸ§© Extras incluidos (fuera de los mÃ­nimos)

- CorrelaciÃ³n de entidades y **perfilado por alias** compartido.
- **Grafo en Ã¡rbol/red** con inspector y exportaciÃ³n PNG/JSON/**Graphviz DOT**.
- **Interfaz web** completa con revisiÃ³n human-in-the-loop.
- **Datos derivados** (alias/correos candidatos) marcados como POSIBLE.
- **Trazabilidad**: registro de consultas realizadas (Ãºtil para auditorÃ­a).
- **ValidaciÃ³n robusta** que descarta entradas invÃ¡lidas sin romper la ejecuciÃ³n.

---

## ðŸ“ TÃ©cnicas de los apuntes
El fichero [`APUNTES.md`](APUNTES.md) traza **cada tÃ©cnica de OSINT de personas**
de los apuntes de clase hasta el punto exacto del cÃ³digo donde estÃ¡ implementada,
y explica quÃ© se deja fuera a propÃ³sito (reconocimiento facial, volcados de
credenciales) y por quÃ©.

## ðŸ“œ Licencia
MIT â€” ver [`LICENSE`](LICENSE). Incluye el aviso de uso Ã©tico y legal.

## Capturas de ejemplo

![Captura 1](docs/consola.png)
![Captura 2](docs/grafo.png)
![Captura 3](docs/web.png)
