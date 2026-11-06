"""
Módulo para generación de enlaces de comparación y webs oficiales de aerolíneas.
Genera enlaces para Google Flights, Skyscanner y enlaces de búsqueda directa
en los motores de reserva oficiales de las principales aerolíneas.
"""

import urllib.parse
import webbrowser
import logging
from typing import Tuple, List, Dict, Optional

logger = logging.getLogger(__name__)


def generar_enlace_google_flights(origen: str, destino: str, fecha_salida: str) -> str:
    """
    Genera un enlace de búsqueda para Google Flights.
    Ejemplo fecha: '2026-12-01'.
    """
    origen_clean = origen.strip().upper()
    destino_clean = destino.strip().upper()
    query = f"Vuelos de {origen_clean} a {destino_clean} el {fecha_salida}"
    param_q = urllib.parse.quote(query)
    return f"https://www.google.com/travel/flights?q={param_q}&hl=es"


def generar_enlace_skyscanner(origen: str, destino: str, fecha_salida: str) -> str:
    """
    Genera un enlace de búsqueda para Skyscanner en formato español.
    Formato de fecha Skyscanner: YYMMDD (ej. 261201 para 2026-12-01).
    Añade parámetros de sesión (adultsv2, cabinclass, ref) para reducir bloqueos anti-bot.
    """
    origen_clean = origen.strip().lower()
    destino_clean = destino.strip().lower()

    # Convertir 'YYYY-MM-DD' en 'YYMMDD'
    partes = fecha_salida.split("-")
    if len(partes) == 3 and len(partes[0]) == 4:
        yy = partes[0][2:]
        mm = partes[1]
        dd = partes[2]
        fecha_skyscanner = f"{yy}{mm}{dd}"
    else:
        fecha_skyscanner = fecha_salida.replace("-", "")

    return (
        f"https://www.skyscanner.es/transport/vuelos/{origen_clean}/{destino_clean}/{fecha_skyscanner}/"
        f"?adultsv2=1&cabinclass=economy&childrenv2=&inboundaltsenabled=false&outboundaltsenabled=false&preferdirects=false&ref=home&rtn=0"
    )


def _formatear_fecha_ddmmyyyy(fecha_iso: str) -> str:
    """Convierte 'YYYY-MM-DD' a 'DD/MM/YYYY'."""
    partes = fecha_iso.split("-")
    if len(partes) == 3:
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return fecha_iso


def generar_enlace_aerolinea(
    codigo_aerolinea: str,
    origen: str,
    destino: str,
    fecha_salida: str,
    adultos: int = 1,
) -> str:
    """
    Genera un deep-link directo de búsqueda en la web oficial de la aerolínea
    con origen, destino y fecha pre-cargados. Si la aerolínea no tiene un patrón
    de búsqueda directa conocido, genera una búsqueda específica dirigida a su dominio oficial.
    """
    cod = codigo_aerolinea.strip().upper()
    orig = origen.strip().upper()
    dest = destino.strip().upper()
    dd_mm_yyyy = _formatear_fecha_ddmmyyyy(fecha_salida)

    # 1. Iberia (IB / I2)
    if cod in ("IB", "I2"):
        return (
            f"https://www.iberia.com/es/vuelos/?origin={orig}&destination={dest}"
            f"&departure={dd_mm_yyyy}&adt={adultos}&cabin=T"
        )

    # 2. Vueling (VY)
    if cod == "VY":
        return (
            f"https://tickets.vueling.com/ScheduleSelectNew.aspx"
            f"?DepartureDate={fecha_salida}&Origin={orig}&Destination={dest}&Adults={adultos}&IsReturn=false"
        )

    # 3. Ryanair (FR)
    if cod == "FR":
        return (
            f"https://www.ryanair.com/es/es/trip/flights/select"
            f"?originIata={orig}&destinationIata={dest}&dateOut={fecha_salida}&isReturn=false&adults={adultos}"
        )

    # 4. Air Europa (UX)
    if cod == "UX":
        return (
            f"https://www.aireuropa.com/es/es/flights"
            f"?origin={orig}&destination={dest}&departureDate={fecha_salida}&adults={adultos}"
        )

    # 5. EasyJet (U2 / EZY / EC / DS)
    if cod in ("U2", "EZY", "EC", "DS"):
        return (
            f"https://www.easyjet.com/es/reserva-de-vuelos/{orig}/{dest}"
            f"?origin={orig}&destination={dest}&departureDate={fecha_salida}"
        )

    # 6. British Airways (BA)
    if cod == "BA":
        return (
            f"https://www.britishairways.com/travel/fx/public/es_es"
            f"?eId=111011&origin={orig}&destination={dest}&depDate={fecha_salida}&ad={adultos}"
        )

    # 7. Air France (AF)
    if cod == "AF":
        return (
            f"https://wwws.airfrance.es/search/advanced"
            f"?origin={orig}&destination={dest}&departureDate={fecha_salida}&adults={adultos}"
        )

    # 8. KLM (KL)
    if cod == "KL":
        return (
            f"https://www.klm.es/search/advanced"
            f"?origin={orig}&destination={dest}&departureDate={fecha_salida}&adults={adultos}"
        )

    # 9. Lufthansa (LH)
    if cod == "LH":
        return (
            f"https://www.lufthansa.com/es/es/flight-search"
            f"?origin={orig}&destination={dest}&startDate={fecha_salida}&adults={adultos}"
        )

    # 10. TAP Air Portugal (TP)
    if cod == "TP":
        return (
            f"https://www.flytap.com/es-es/reserva"
            f"?origin={orig}&destination={dest}&departureDate={fecha_salida}&adults={adultos}"
        )

    # 11. Volotea (V7)
    if cod == "V7":
        return (
            f"https://www.volotea.com/es/reserva/"
            f"?origin={orig}&destination={dest}&departure_date={fecha_salida}&adults={adultos}"
        )

    # 12. Binter Canarias (NT)
    if cod == "NT":
        return (
            f"https://www.bintercanarias.com/es/reserva"
            f"?origen={orig}&destino={dest}&fechaSalida={fecha_salida}"
        )

    # 13. Wizz Air (W6 / WZZ)
    if cod in ("W6", "WZZ"):
        return f"https://wizzair.com/es-es/vuelos/{orig.lower()}-a-{dest.lower()}"

    # 14. Transavia (HV / TO)
    if cod in ("HV", "TO"):
        return (
            f"https://www.transavia.com/es-ES/reserva-un-vuelo/vuelos/buscar/"
            f"?origin={orig}&destination={dest}&outboundDate={fecha_salida}"
        )

    # 15. Norwegian (DY / D8)
    if cod in ("DY", "D8"):
        partes = fecha_salida.split("-")
        if len(partes) == 3:
            return (
                f"https://www.norwegian.com/es/booking/flight-tickets/farecalendar/"
                f"?D_City={orig}&A_City={dest}&D_Day={partes[2]}&D_Month={partes[1]}&D_Year={partes[0]}"
            )
        return f"https://www.norwegian.com/es/booking/flight-tickets/?D_City={orig}&A_City={dest}"

    # 16. Eurowings (EW)
    if cod == "EW":
        return (
            f"https://www.eurowings.com/es/reservar/vuelos.html"
            f"?origin={orig}&destination={dest}&date={fecha_salida}"
        )

    # 17. Swiss (LX)
    if cod == "LX":
        return (
            f"https://www.swiss.com/es/es/flight-search"
            f"?origin={orig}&destination={dest}&startDate={fecha_salida}&adults={adultos}"
        )

    # 18. Turkish Airlines (TK)
    if cod == "TK":
        return (
            f"https://www.turkishairlines.com/es-es/vuelos/reserva/"
            f"?origin={orig}&destination={dest}"
        )

    # Fallback genérico: búsqueda oficial dirigida a la aerolínea
    consulta = f"vuelo {orig} a {dest} {fecha_salida} aerolinea {cod} reserva oficial"
    return f"https://www.google.com/search?q={urllib.parse.quote(consulta)}"


def obtener_enlaces_principales_aerolineas(
    origen: str,
    destino: str,
    fecha_salida: str,
    adultos: int = 1,
) -> Dict[str, str]:
    """
    Retorna un diccionario de nombres de aerolíneas principales con sus enlaces
    directos de búsqueda para la ruta y fecha dadas.
    """
    principales = [
        ("Iberia", "IB"),
        ("Vueling", "VY"),
        ("Ryanair", "FR"),
        ("Air Europa", "UX"),
        ("EasyJet", "U2"),
        ("British Airways", "BA"),
        ("Air France", "AF"),
        ("Lufthansa", "LH"),
        ("Volotea", "V7"),
        ("TAP Air Portugal", "TP"),
    ]

    enlaces = {}
    for nombre, cod in principales:
        enlaces[f"{nombre} ({cod})"] = generar_enlace_aerolinea(
            codigo_aerolinea=cod,
            origen=origen,
            destino=destino,
            fecha_salida=fecha_salida,
            adultos=adultos,
        )
    return enlaces


def generar_enlaces(origen: str, destino: str, fecha_salida: str) -> Tuple[str, str]:
    """Genera ambos enlaces: (Google Flights, Skyscanner)."""
    return (
        generar_enlace_google_flights(origen, destino, fecha_salida),
        generar_enlace_skyscanner(origen, destino, fecha_salida),
    )


def abrir_enlaces_en_navegador(enlaces: List[str], max_abrir: int) -> int:
    """
    Abre en el navegador predeterminado hasta max_abrir enlaces.
    Retorna el número de enlaces abiertos con éxito.
    """
    if max_abrir <= 0 or not enlaces:
        return 0

    abiertos = 0
    for url in enlaces[:max_abrir]:
        if not url:
            continue
        try:
            webbrowser.open(url, new=2)
            abiertos += 1
        except Exception as e:
            logger.warning(f"No se pudo abrir el enlace en el navegador: {e}")

    return abiertos
