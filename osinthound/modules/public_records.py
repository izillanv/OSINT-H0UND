"""
modules/public_records.py
=========================
Genera accesos directos a REGISTROS Y BOLETINES OFICIALES publicos para buscar
a la persona/empresa por nombre, segun su pais. Es OSINT "de manual": fuentes
abiertas y oficiales (BOE, BORME, subvenciones, boletines autonomicos, y sus
equivalentes internacionales).

En lugar de scrapear cada registro (fragil y, en algunos casos, contra sus
condiciones), el modulo entrega el enlace de busqueda ya montado y deja que el
**analista** abra y confirme los resultados reales (human-in-the-loop). Los
hallazgos se marcan como POSIBLE hasta esa confirmacion.
"""

from __future__ import annotations

from typing import Dict, List
from urllib.parse import quote

from ..config import CONF_POSSIBLE
from ..finding import Finding
from ..validators import Target
from .base import BaseModule, Context, register

# Paises de la UE para anadir EUR-Lex.
_EU = {"ES", "PT", "FR", "IT", "DE", "NL", "BE", "AT", "SE", "DK", "FI", "PL",
       "CZ", "GR", "RO", "HU", "IE"}

_GLOBAL = [
    {"name": "OpenCorporates (cargos de empresa)", "kind": "record",
     "url": "https://opencorporates.com/officers?q={q}"},
    {"name": "Wikidata", "kind": "pivot",
     "url": "https://www.wikidata.org/w/index.php?search={q}"},
    {"name": "LinkedIn (via Google)", "kind": "pivot",
     "url": "https://www.google.com/search?q=site:linkedin.com/in+%22{q}%22"},
    {"name": "Documentos PDF con el nombre", "kind": "pivot",
     "url": "https://www.google.com/search?q=%22{q}%22+filetype:pdf"},
]

_EURLEX = {"name": "EUR-Lex (Diario Oficial de la UE)", "kind": "pivot",
           "url": "https://eur-lex.europa.eu/search.html?type=quick&text=%22{q}%22"}

_BY_COUNTRY: Dict[str, List[dict]] = {
    "ES": [
        {"name": "BOE — Boletin Oficial del Estado", "kind": "record",
         "url": "https://www.google.com/search?q=site:boe.es+%22{q}%22"},
        {"name": "BORME — Registro Mercantil", "kind": "record",
         "url": "https://www.google.com/search?q=site:boe.es/borme+%22{q}%22"},
        {"name": "BDNS — Subvenciones concedidas", "kind": "record",
         "url": "https://www.google.com/search?q=site:infosubvenciones.es+%22{q}%22"},
        {"name": "Boletines autonomicos (BOCM/DOGC/BOJA/DOG/BOPV)", "kind": "pivot",
         "url": "https://www.google.com/search?q=%22{q}%22+(boletin+oficial+comunidad)"},
    ],
    "US": [
        {"name": "SEC EDGAR", "kind": "record",
         "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={q}&type=&count=40"},
        {"name": "CourtListener (resoluciones judiciales)", "kind": "record",
         "url": "https://www.courtlistener.com/?q=%22{q}%22"},
    ],
    "GB": [
        {"name": "Companies House", "kind": "record",
         "url": "https://find-and-update.company-information.service.gov.uk/search?q={q}"},
        {"name": "The Gazette (UK)", "kind": "record",
         "url": "https://www.thegazette.co.uk/all-notices/notice?text=%22{q}%22"},
    ],
    "FR": [
        {"name": "Societe.com", "kind": "record",
         "url": "https://www.societe.com/cgi-bin/search?champs={q}"},
        {"name": "Legifrance / Journal Officiel", "kind": "pivot",
         "url": "https://www.google.com/search?q=site:legifrance.gouv.fr+%22{q}%22"},
    ],
    "DE": [
        {"name": "Handelsregister", "kind": "record",
         "url": "https://www.handelsregister.de/"},
        {"name": "Bundesanzeiger", "kind": "pivot",
         "url": "https://www.google.com/search?q=site:bundesanzeiger.de+%22{q}%22"},
    ],
    "IT": [{"name": "Gazzetta Ufficiale", "kind": "pivot",
            "url": "https://www.google.com/search?q=site:gazzettaufficiale.it+%22{q}%22"}],
    "PT": [{"name": "Diario da Republica", "kind": "pivot",
            "url": "https://www.google.com/search?q=site:diariodarepublica.pt+%22{q}%22"}],
    "MX": [{"name": "DOF — Diario Oficial de la Federacion", "kind": "pivot",
            "url": "https://www.google.com/search?q=site:dof.gob.mx+%22{q}%22"}],
    "AR": [{"name": "Boletin Oficial (Argentina)", "kind": "pivot",
            "url": "https://www.google.com/search?q=site:boletinoficial.gob.ar+%22{q}%22"}],
    "CO": [{"name": "Diario Oficial (Colombia)", "kind": "pivot",
            "url": "https://www.google.com/search?q=site:diario-oficial.gov.co+%22{q}%22"}],
}


@register
class PublicRecords(BaseModule):
    name = "public_records"
    title = "Registros y boletines oficiales"
    description = "Accesos a BOE/BORME y registros publicos equivalentes por pais"
    category = "Registros publicos"
    accepts = {"name"}
    needs_network = False  # solo genera enlaces; no consulta nada por si mismo

    def run(self, target: Target, ctx: Context) -> List[Finding]:
        if not target.name:
            return []
        q = quote(target.name)
        country = (target.country or "ES").upper()

        catalog = list(_GLOBAL)
        catalog += _BY_COUNTRY.get(country, [])
        if country in _EU:
            catalog.append(_EURLEX)

        out: List[Finding] = []
        for src in catalog:
            out.append(Finding(
                kind=src["kind"],
                label=src["name"],
                value=target.name,
                url=src["url"].format(q=q),
                source=self.name,
                category=self.category,
                confidence=CONF_POSSIBLE,
                meta={"pais": country, "instruccion": "Abrir y confirmar coincidencias reales"},
            ))
        return out
