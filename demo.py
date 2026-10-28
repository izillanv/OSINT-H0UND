#!/usr/bin/env python3
"""
demo.py
=======
Genera un informe de EJEMPLO con datos 100% FICTICIOS (persona inventada),
sin tocar la red. Sirve para las capturas del README y para ver el aspecto del
informe sin necesidad de ejecutar una investigacion real.

    python demo.py            # crea reports/demo_report.html (+ .json + .dot)

Personaje ficticio: "Ada Lovelace King" (@adaloveking).
"""

from __future__ import annotations

from osinthound.config import CONF_CONFIRMED, CONF_POSSIBLE
from osinthound.correlate import build_graph
from osinthound.finding import Finding
from osinthound.report import Reporter
from osinthound.validators import build_target


def _f(kind, label, value="", url="", category="General",
       confidence=CONF_CONFIRMED, **meta) -> Finding:
    f = Finding(kind=kind, label=label, value=value, url=url, source="demo",
                category=category, confidence=confidence, meta=meta)
    f.accepted = True
    return f


def build_demo():
    # --- Objetivo ficticio ---
    target, _ = build_target({
        "name": "Ada Lovelace King",
        "aka": "Ada Byron",
        "username": "adaloveking, lovelace_a",
        "email": "ada.king@proton.me, a.king@novatech.io",
        "phone": "+44 20 7946 0958",
        "domain": "novatech.io",
        "location": "Londres",
    }, country="GB")

    findings = [
        # -------- Perfiles sociales (confirmados + posibles) --------
        _f("profile", "GitHub (@adaloveking)", url="https://github.com/adaloveking",
           category="Perfiles sociales", username="adaloveking", site="GitHub", grupo="Desarrollo"),
        _f("profile", "GitLab (@adaloveking)", url="https://gitlab.com/adaloveking",
           category="Perfiles sociales", username="adaloveking", site="GitLab", grupo="Desarrollo"),
        _f("profile", "Reddit (@adaloveking)", url="https://www.reddit.com/user/adaloveking",
           category="Perfiles sociales", username="adaloveking", site="Reddit", grupo="Social"),
        _f("profile", "Keybase (@adaloveking)", url="https://keybase.io/adaloveking",
           category="Perfiles sociales", username="adaloveking", site="Keybase", grupo="Seguridad"),
        _f("profile", "Twitch (@lovelace_a)", url="https://www.twitch.tv/lovelace_a",
           category="Perfiles sociales", username="lovelace_a", site="Twitch", grupo="Gaming"),
        _f("profile", "Mastodon (Gravatar)", url="https://mastodon.social/@adaking",
           category="Perfiles sociales", confidence=CONF_POSSIBLE, via="Gravatar", username="adaking",
           nota="cuenta vinculada en el perfil de Gravatar"),
        _f("profile", "Spotify (@adaloveking)", url="https://open.spotify.com/user/adaloveking",
           category="Perfiles sociales", confidence=CONF_POSSIBLE, username="adaloveking", site="Spotify"),

        # -------- Correos + brechas --------
        _f("email", "ada.king@proton.me", value="ada.king@proton.me", category="Correos",
           gravatar=True, nombre_gravatar="Ada K.", proveedor="gratuito",
           acepta_correo=True, foto="https://www.gravatar.com/avatar/00000000000000000000000000000000?d=identicon&s=80",
           perfil_gravatar="https://gravatar.com/adaloveking"),
        _f("email", "a.king@novatech.io", value="a.king@novatech.io", category="Correos",
           proveedor="corporativo/propio", acepta_correo=True, mx=["mail.novatech.io"], dominio="novatech.io"),
        _f("breach", "Brecha: LinkedIn (2021)", value="ada.king@proton.me", category="Brechas",
           email="ada.king@proton.me", fecha="2021-06", datos_filtrados="Correos, nombres, cargos",
           cuentas_afectadas=700000000, fuente="HIBP"),
        _f("breach", "Brecha: Collection #1", value="ada.king@proton.me", category="Brechas",
           email="ada.king@proton.me", fecha="2019-01", datos_filtrados="Correos, contrasenas (hash)",
           fuente="HIBP"),
        _f("breach", "Brecha: Dropbox", value="a.king@novatech.io", category="Brechas",
           email="a.king@novatech.io", fecha="2012-07", datos_filtrados="Correos, contrasenas", fuente="XposedOrNot"),

        # -------- Telefono --------
        _f("phone", "+44 20 7946 0958", value="+442079460958", category="Telefono",
           pais="Londres, Reino Unido", prefijo_pais="+44", operador="BT",
           tipo_linea="Fijo", internacional="+44 20 7946 0958",
           zonas_horarias=["Europe/London"],
           pivotes={"WhatsApp": "https://wa.me/442079460958",
                    "Buscar en Google": "https://www.google.com/search?q=%22+442079460958%22"}),

        # -------- Dominio --------
        _f("domain", "novatech.io", value="novatech.io", url="https://novatech.io", category="Dominio",
           a=["185.199.108.153"], mx=["mail.novatech.io"], ns=["ns1.cloudns.net", "ns2.cloudns.net"],
           spf="v=spf1 include:_spf.google.com ~all", dmarc="—", riesgo_spoofing="sin DMARC",
           registrador="Namecheap, Inc.", creado="2019-03-12", caduca="2027-03-12",
           servidores_nombres=["ns1.cloudns.net", "ns2.cloudns.net"], contacto_whois="redacted for privacy",
           subdominios=["www.novatech.io", "mail.novatech.io", "vpn.novatech.io",
                        "dev.novatech.io", "staging.novatech.io", "git.novatech.io"]),
        _f("pivot", "Subdominio: vpn.novatech.io", value="vpn.novatech.io", url="https://vpn.novatech.io",
           category="Dominio", confidence=CONF_POSSIBLE, dominio_padre="novatech.io"),
        _f("pivot", "Subdominio: staging.novatech.io", value="staging.novatech.io",
           url="https://staging.novatech.io", category="Dominio", confidence=CONF_POSSIBLE,
           dominio_padre="novatech.io"),

        # -------- Registros publicos --------
        _f("record", "Companies House", url="https://find-and-update.company-information.service.gov.uk/search?q=Ada%20Lovelace%20King",
           category="Registros publicos", confidence=CONF_POSSIBLE, grupo="Reino Unido",
           instruccion="Abrir y confirmar coincidencias reales"),
        _f("record", "The Gazette (UK)", url="https://www.thegazette.co.uk/all-notices/notice?text=%22Ada%20Lovelace%20King%22",
           category="Registros publicos", confidence=CONF_POSSIBLE, grupo="Reino Unido"),
        _f("record", "OpenCorporates (cargos)", url="https://opencorporates.com/officers?q=Ada%20Lovelace%20King",
           category="Registros publicos", confidence=CONF_POSSIBLE, grupo="Global"),
        _f("pivot", "EUR-Lex (DO de la UE)", url="https://eur-lex.europa.eu/search.html?type=quick&text=%22Ada%20Lovelace%20King%22",
           category="Registros publicos", confidence=CONF_POSSIBLE, grupo="Global"),

        # -------- Huella publica --------
        _f("pivot", "Ada Lovelace King - NovaTech (CTO)", url="https://www.linkedin.com/in/adaloveking",
           category="Huella publica", confidence=CONF_POSSIBLE, fuente="linkedin.com", tipo="Profesional"),
        _f("pivot", "Charla en DEF CON - OSINT moderno", url="https://media.defcon.org/talk-ada-king",
           category="Huella publica", confidence=CONF_POSSIBLE, fuente="media.defcon.org", tipo="Medios"),
        _f("pivot", "Paper: grafos de correlacion (ORCID)", url="https://orcid.org/0000-0002-ada-king",
           category="Huella publica", confidence=CONF_POSSIBLE, fuente="orcid.org", tipo="Academico"),

        # -------- Dorks / pivotes --------
        _f("pivot", "Nombre exacto", url="https://www.google.com/search?q=%22Ada%20Lovelace%20King%22",
           category="Dorks y pivotes", confidence=CONF_POSSIBLE, grupo="Nombre"),
        _f("pivot", "Documentos con el nombre", url="https://www.google.com/search?q=%22Ada%20Lovelace%20King%22%20filetype:pdf",
           category="Dorks y pivotes", confidence=CONF_POSSIBLE, grupo="Nombre"),
        _f("pivot", "Correo en pastes", url="https://www.google.com/search?q=%22ada.king@proton.me%22%20site:pastebin.com",
           category="Dorks y pivotes", confidence=CONF_POSSIBLE, grupo="Correo ada.king@proton.me"),
        _f("pivot", "Tecnica IntelX -> Yandex", url="https://intelx.io/",
           category="Dorks y pivotes", confidence=CONF_POSSIBLE, grupo="Correo ada.king@proton.me"),

        # -------- Imagen --------
        _f("image", "Imagen: perfil.jpg", value="perfil.jpg", category="Imagen",
           fichero="perfil.jpg", camara="Apple iPhone 14 Pro", fecha_captura="2024:05:18 14:32:07",
           software="iOS 17.4", gps=[51.5079, -0.0877], mapa="https://www.google.com/maps?q=51.5079,-0.0877",
           nota="Para metadatos completos usar ExifTool"),
        _f("pivot", "Imagen: Yandex (inversa)", url="https://yandex.com/images/",
           category="Imagen", confidence=CONF_POSSIBLE,
           instruccion="Suele dar los mejores resultados de reutilizacion de foto"),
        _f("pivot", "Imagen: FotoForensics (ELA)", url="https://fotoforensics.com/",
           category="Imagen", confidence=CONF_POSSIBLE,
           instruccion="Analisis forense: detecta posible manipulacion/edicion"),

        # -------- Candidatos derivados --------
        _f("username", "Alias candidato: adalovelaceking", value="adalovelaceking",
           category="Candidatos (revisar)", confidence=CONF_POSSIBLE, derived_from="nombre", username="adalovelaceking"),
        _f("email", "Correo candidato: adaloveking@gmail.com", value="adaloveking@gmail.com",
           category="Candidatos (revisar)", confidence=CONF_POSSIBLE, derived_from="alias:adaloveking"),
    ]

    graph = build_graph(target, findings)
    meta = {
        "objetivo": target.summary(),
        "pais": "Reino Unido",
        "fecha": "2026-10-28 17:05:00",
        "modulos": ["Huella publica", "Enumeracion de usuarios", "Analisis de correo",
                    "Brechas de datos", "Analisis telefonico", "Auditoria de dominio",
                    "Registros y boletines oficiales", "Metadatos de imagen",
                    "Google Dorks y pivotes", "Herramientas externas"],
        "herramientas_externas": "instaladas: sherlock, holehe",
        "advertencias": [],
        "duracion_s": 24.7,
        "consultas_realizadas": 71,
        "total_hallazgos": len(findings),
        "confirmados": sum(1 for f in findings if f.accepted and not f.is_possible),
    }
    return target, graph, findings, meta


def main():
    target, graph, findings, meta = build_demo()
    rep = Reporter(target, graph, findings, meta)
    paths = rep.save_all(outdir="reports", slug="demo_report")
    print("Informe de demostracion generado:")
    for k, v in paths.items():
        print(f"  {k.upper():5} -> {v}")
    print("\nAbre reports/demo_report.html en el navegador.")


if __name__ == "__main__":
    main()
