"""
modules/domain_recon.py
=======================
Auditoria de un DOMINIO asociado a la persona/empresa:
  - **DNS**: registros A, MX, NS y TXT.
  - **SPF / DMARC**: politica antispoofing (y aviso si falta).
  - **WHOIS**: registrador, fechas de alta/caducidad y servidores de nombres.
  - **Subdominios**: enumeracion via Certificate Transparency (crt.sh).

Todo son fuentes abiertas de infraestructura (OSINT limpio de manual).
"""

from __future__ import annotations

from typing import Dict, List

from ..config import CONF_POSSIBLE
from ..finding import Finding
from ..validators import Target
from .base import BaseModule, Context, register

try:
    import dns.resolver  # type: ignore
    _HAS_DNS = True
except Exception:
    _HAS_DNS = False

try:
    import whois  # type: ignore
    _HAS_WHOIS = True
except Exception:
    _HAS_WHOIS = False


@register
class DomainRecon(BaseModule):
    name = "domain_recon"
    title = "Auditoria de dominio"
    description = "DNS, WHOIS, SPF/DMARC y subdominios (crt.sh)"
    category = "Dominio"
    accepts = {"domain"}

    # ------------------------------------------------------------------ #
    def _dns(self, domain: str) -> Dict:
        out: Dict = {}
        if not _HAS_DNS:
            return out
        for rtype in ("A", "MX", "NS", "TXT"):
            try:
                ans = dns.resolver.resolve(domain, rtype, lifetime=6)
                if rtype == "MX":
                    out["mx"] = sorted(str(r.exchange).rstrip(".") for r in ans)
                elif rtype == "TXT":
                    out["txt"] = ["".join(
                        s.decode() if isinstance(s, bytes) else s
                        for s in r.strings) for r in ans]
                else:
                    out[rtype.lower()] = sorted(str(r) for r in ans)
            except Exception:
                out[rtype.lower()] = []
        return out

    @staticmethod
    def _spf_dmarc(domain: str, txt: List[str]) -> Dict:
        spf = next((t for t in txt if t.lower().startswith("v=spf1")), "")
        dmarc = ""
        if _HAS_DNS:
            try:
                ans = dns.resolver.resolve(f"_dmarc.{domain}", "TXT", lifetime=6)
                for r in ans:
                    val = "".join(s.decode() if isinstance(s, bytes) else s
                                  for s in r.strings)
                    if val.lower().startswith("v=dmarc1"):
                        dmarc = val
            except Exception:
                pass
        riesgo = []
        if not spf:
            riesgo.append("sin SPF")
        if not dmarc:
            riesgo.append("sin DMARC")
        return {"spf": spf or "—", "dmarc": dmarc or "—",
                "riesgo_spoofing": ", ".join(riesgo) or "bajo"}

    def _whois(self, domain: str) -> Dict:
        if not _HAS_WHOIS:
            return {}
        try:
            w = whois.whois(domain)
        except Exception:
            return {}

        def _first(v):
            return v[0] if isinstance(v, (list, tuple)) and v else v

        return {
            "registrador": str(_first(w.registrar) or "—"),
            "creado": str(_first(w.creation_date) or "—"),
            "caduca": str(_first(w.expiration_date) or "—"),
            "servidores_nombres": [str(n).lower() for n in (w.name_servers or [])][:4],
            "contacto_whois": str(_first(w.emails) or "—"),
        }

    def _subdomains(self, domain: str, ctx: Context) -> List[str]:
        r = ctx.get(f"https://crt.sh/?q=%25.{domain}&output=json", timeout=20)
        if not r or r.status_code != 200:
            return []
        try:
            data = r.json()
        except Exception:
            return []
        subs = set()
        for row in data:
            for name in str(row.get("name_value", "")).splitlines():
                name = name.strip().lstrip("*.").lower()
                if name.endswith(domain) and name != domain:
                    subs.add(name)
        return sorted(subs)[:40]

    def audit(self, domain: str, ctx: Context) -> Dict:
        """Ejecuta todas las comprobaciones y devuelve el dict de resultados."""
        dns_info = self._dns(domain)
        result = {"dominio": domain}
        result.update({k: v for k, v in dns_info.items() if k != "txt"})
        result.update(self._spf_dmarc(domain, dns_info.get("txt", [])))
        result.update(self._whois(domain))
        result["subdominios"] = self._subdomains(domain, ctx)
        return result

    def run(self, target: Target, ctx: Context) -> List[Finding]:
        out: List[Finding] = []
        for domain in target.domains:
            info = self.audit(domain, ctx)
            out.append(Finding(
                kind="domain", label=domain, value=domain, url=f"https://{domain}",
                source=self.name, category=self.category, meta=info,
            ))
            # Un par de subdominios destacados como pivotes (no saturan el grafo).
            for sub in info.get("subdominios", [])[:6]:
                out.append(Finding(
                    kind="pivot", label=f"Subdominio: {sub}", value=sub,
                    url=f"https://{sub}", source=self.name,
                    category="Dominio", confidence=CONF_POSSIBLE,
                    meta={"dominio_padre": domain},
                ))
        return out
