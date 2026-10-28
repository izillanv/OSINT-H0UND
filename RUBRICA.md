# OSINT Hound — Cumplimiento de la rúbrica

Los **4 criterios** pesan **25% cada uno**. Para cada uno se indica por qué el
proyecto alcanza el nivel **Excelente (4/4)** y **en qué fichero se comprueba**.

---

## 1. Entrada de datos — Excelente (4/4)
> *Acepta ≥4 tipos de entrada, valida los datos y gestiona errores sin interrumpir la ejecución.*

- **5 tipos de entrada** (supera los 4): **nombre, alias, correo, teléfono y dominio**
  (+ ubicación, país e imagen como contexto). → `osinthound/validators.py`, `main.py`.
- **Validación real** de cada campo en `validators.py`:
  - correo y alias por *regex*; dominio que **normaliza URLs** (`https://www.x.com/a` → `x.com`);
  - teléfono **mundial** validado con `phonenumbers` (E.164); nombre con caracteres permitidos.
- **Gestión de errores sin romper**: `build_target()` **descarta** lo inválido,
  acumula un **aviso** por cada descarte y **nunca lanza excepción**; la ejecución
  continúa con lo que sí es válido.
- **Multi-valor**: admite **varios** correos/alias/teléfonos/dominios separados por comas.
- **Prueba**: `python main.py` (o la web) con basura mezclada → la entrada mala se
  descarta con aviso y el resto sigue.

---

## 2. Integración de herramientas — Excelente (4/4)
> *Integra ≥1 herramienta externa y ≥3 módulos/fuentes OSINT, combinando resultados con control de errores y respetando el uso legal/ético.*

- **Herramienta(s) externa(s)**: `osinthound/modules/external_tools.py` integra
  **sherlock, maigret, holehe y theHarvester** (detección en PATH + *parseo* de salida).
  Además, `username_enum.py` usa el **dataset externo de WhatsMyName** (cientos de sitios).
- **Muy por encima de 3 fuentes/módulos**: hay **10 módulos** OSINT
  (huella, enumeración, correo/Gravatar, brechas, teléfono, dominio DNS/WHOIS/crt.sh,
  registros oficiales, imagen EXIF, dorks, externas).
- **Combinación de resultados**: `correlate.py` + `engine.py` unen todo en un **grafo
  correlacionado** (perfiles por alias, brecha↔correo, correo↔dominio…).
- **Control de errores**: cada módulo se ejecuta en `try/except` dentro del motor;
  un fallo se registra como advertencia y **no detiene** la investigación
  (`engine.py`, `modules/base.py::Context.get`).
- **Uso legal/ético**: **puerta de consentimiento** (`hitl.py`), avisos en README/LICENSE,
  *rate-limit* y User-Agent honesto, **exclusión deliberada** de reconocimiento facial y
  de volcados de credenciales en claro.

---

## 3. Modularidad del código — Excelente (4/4)
> *Código en módulos reutilizables, bien organizados y comentados, nombres claros, configuración separada y fácil de ampliar.*

- **Arquitectura por capas**: `config / console / validators / hitl / finding / entity /
  correlate / engine / modules/ / report/ / web/` — responsabilidades separadas.
- **Patrón plugin**: todos los módulos heredan de `BaseModule` y se dan de alta con el
  decorador `@register` (`modules/base.py`). **Añadir una fuente = crear un fichero**
  e importarlo en `modules/__init__.py`; no se toca el motor ni el informe.
- **Configuración separada**: `config.py` centraliza HTTP, claves de API, paleta del
  grafo y países; los secretos van en `.env` (no en el código).
- **Nombres claros y comentarios**: cada fichero tiene *docstring* de propósito y
  comentarios en español explicando el *por qué*.
- **Reutilización**: `Context`, `Finding`, `Graph`, `Reporter` y `HITL` los usan por
  igual la CLI y la web.

---

## 4. Estructura del informe — Excelente (4/4)
> *Informe estructurado en HTML/PDF/JSON con fuentes, resultados, relaciones y limitaciones; + README y demostración con datos ficticios.*

- **Formato HTML y JSON** (`report/reporter.py`): informe visual autocontenido **y**
  volcado JSON completo. Extra: export **Graphviz DOT**.
- **Fuentes**: cada hallazgo muestra su **módulo/fuente** y el enlace original.
- **Resultados**: pestañas por tipo (perfiles, correos/brechas, teléfono, dominio,
  registros, huella, imagen, dorks, candidatos) + *stat tiles* y nivel de exposición.
- **Relaciones encontradas**: **grafo interactivo** (árbol/red) con inspector, que es
  exactamente "visualizar las conexiones" del enunciado.
- **Limitaciones**: panel explícito (alcance OSINT, falsos positivos, homónimos,
  temporalidad) + **trazabilidad** (módulos y nº de consultas).
- **README**: `README.md` con instalación, uso y arquitectura.
- **Demostración con datos ficticios**: `demo.py` → `reports/demo_report.html`
  (persona inventada "Ada Lovelace King").

---

## Extras opcionales del enunciado — cubiertos
- ✅ **Correlación / perfilado** entre entidades → `correlate.py`.
- ✅ **Grafo de relaciones** (y export a **Graphviz DOT**) → `entity.py`, `report/`.
- ✅ **Interfaz web** → `web/`.
- ✅ **Ejemplo de ejecución con resultados ficticios** → `demo.py`.

## Cómo defenderlo en 30 segundos
> "Es un framework modular: cada fuente OSINT es un plugin que hereda de una clase base,
> así que ampliarlo es añadir un fichero. Acepta cinco tipos de entrada con validación
> que nunca rompe la ejecución, integra herramientas externas (sherlock, holehe,
> theHarvester) y más de 10 fuentes, y combina todo en un grafo correlacionado.
> Todo es human-in-the-loop: el analista confirma qué resultados son del objetivo,
> separando lo confirmado de lo meramente posible. El informe HTML/JSON muestra fuentes,
> resultados, relaciones (grafo árbol/red) y limitaciones. Solo usa fuentes abiertas y
> excluye a propósito reconocimiento facial y volcados de contraseñas."
