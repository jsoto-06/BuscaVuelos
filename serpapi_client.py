"""
Cliente para la API de SerpApi (Google Flights Engine).
Permite buscar vuelos reales en tiempo real con datos de Google Flights,
cubriendo todas las aerolíneas del mundo (Iberia, Vueling, Ryanair, etc.).
"""

import logging
from typing import List, Dict, Any, Optional
import requests

import config
import privacidad
import enlaces
from modelos import Oferta

logger = logging.getLogger(__name__)


def _extraer_codigo_aerolinea(numero_vuelo: str, nombre_aerolinea: str) -> str:
    """Extrae el código IATA de la aerolínea desde el número de vuelo o nombre."""
    if numero_vuelo:
        partes = numero_vuelo.strip().split()
        if len(partes) >= 1 and len(partes[0]) in (2, 3):
            return partes[0].upper()

    mapeo = {
        "iberia": "IB",
        "vueling": "VY",
        "ryanair": "FR",
        "air europa": "UX",
        "easyjet": "U2",
        "british airways": "BA",
        "air france": "AF",
        "lufthansa": "LH",
        "klm": "KL",
        "volotea": "V7",
        "binter": "NT",
        "tap": "TP",
        "wizz": "W6",
        "transavia": "HV",
        "norwegian": "DY",
    }
    nombre_limpio = nombre_aerolinea.lower()
    for clave, cod in mapeo.items():
        if clave in nombre_limpio:
            return cod

    return "IB"


def buscar_vuelos_google(
    origen: str,
    destino: str,
    fecha_salida: str,
    adultos: int = 1,
    moneda: str = "EUR",
    directos: bool = False,
    max_precio: Optional[float] = None,
    api_key: Optional[str] = None,
) -> List[Oferta]:
    """
    Consulta las ofertas de vuelos en tiempo real en Google Flights mediante SerpApi.
    Parsea los resultados a la estructura estándar Oferta.
    """
    key = (api_key or config.SERPAPI_API_KEY).strip()
    if not key:
        raise ValueError("No se ha configurado la clave de SerpApi (SERPAPI_API_KEY).")

    privacidad.esperar_rate_limit(0.5)

    params: Dict[str, Any] = {
        "engine": "google_flights",
        "departure_id": origen.strip().upper(),
        "arrival_id": destino.strip().upper(),
        "outbound_date": fecha_salida,
        "currency": moneda,
        "hl": "es",
        "gl": "es",
        "type": "2",  # Solo ida
        "adults": adultos,
        "api_key": key,
    }

    if directos:
        params["stops"] = "1"  # 1 en SerpApi significa vuelos directos / non-stop

    url = "https://serpapi.com/search.json"
    sesion = privacidad.sesion_nueva()

    try:
        resp = sesion.get(url, params=params, timeout=25)
        if resp.status_code == 401 or resp.status_code == 403:
            raise ValueError(
                f"Clave de SerpApi no válida o sin créditos ({resp.status_code}). Verifica tu SERPAPI_API_KEY."
            )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise ConnectionError(f"Error al conectar con SerpApi Google Flights: {e}")
    finally:
        sesion.close()

    todos_los_vuelos_raw = data.get("best_flights", []) + data.get("other_flights", [])
    ofertas: List[Oferta] = []

    for idx, item in enumerate(todos_los_vuelos_raw):
        tramos = item.get("flights", [])
        if not tramos:
            continue

        primer_tramo = tramos[0]
        ultimo_tramo = tramos[-1]

        dep_info = primer_tramo.get("departure_airport", {})
        arr_info = ultimo_tramo.get("arrival_airport", {})

        origen_real = dep_info.get("id", origen).upper()
        destino_real = arr_info.get("id", destino).upper()

        salida_dt = dep_info.get("time", "")
        llegada_dt = arr_info.get("time", "")

        partes_sal = salida_dt.split(" ")
        f_sal = partes_sal[0] if len(partes_sal) > 0 else fecha_salida
        h_sal = partes_sal[1][:5] if len(partes_sal) > 1 else ""

        partes_lleg = llegada_dt.split(" ")
        f_lleg = partes_lleg[0] if len(partes_lleg) > 0 else f_sal
        h_lleg = partes_lleg[1][:5] if len(partes_lleg) > 1 else ""

        escalas = len(tramos) - 1
        duracion_min = int(item.get("total_duration", 0))
        duracion_str = f"{duracion_min // 60}h {duracion_min % 60:02d}m" if duracion_min > 0 else "1h 15m"

        aerolinea_nombre = primer_tramo.get("airline", "Aerolínea")
        numero_vuelo = primer_tramo.get("flight_number", "")
        precio = float(item.get("price", 0.0))

        if max_precio and precio > max_precio:
            continue

        # Equipaje desde extensiones
        exts = primer_tramo.get("extensions", [])
        equipaje_desc = "no indicado"
        for ext in exts:
            ext_l = ext.lower()
            if "equipaje de mano" in ext_l or "carry-on" in ext_l:
                equipaje_desc = "Equipaje de mano incl."
            if "equipaje de bodega" in ext_l or "checked bag" in ext_l:
                equipaje_desc = "Equipaje de bodega incl."

        cod_aero = _extraer_codigo_aerolinea(numero_vuelo, aerolinea_nombre)
        enlace_g = enlaces.generar_enlace_google_flights(origen_real, destino_real, f_sal)
        enlace_sky = enlaces.generar_enlace_skyscanner(origen_real, destino_real, f_sal)
        enlace_aero = enlaces.generar_enlace_aerolinea(cod_aero, origen_real, destino_real, f_sal, adultos=adultos)

        ofertas.append(
            Oferta(
                id=f"google_{idx + 1}",
                origen=origen_real,
                destino=destino_real,
                fecha_salida=f_sal,
                hora_salida=h_sal,
                hora_llegada=h_lleg,
                fecha_llegada=f_lleg,
                escalas=escalas,
                duracion=duracion_str,
                aerolinea=aerolinea_nombre,
                numero_vuelo=numero_vuelo,
                precio_total=precio,
                moneda=moneda,
                equipaje_incluido=equipaje_desc,
                piezas_equipaje=None,
                precio_con_equipaje=None,
                enlace_google=enlace_g,
                enlace_skyscanner=enlace_sky,
                enlace_aerolinea=enlace_aero,
            )
        )

    return ofertas


def consultar_precios_ventana_google(
    origen: str,
    destino: str,
    fechas: List[str],
    adultos: int = 1,
    moneda: str = "EUR",
    api_key: Optional[str] = None,
) -> Dict[str, Optional[float]]:
    """
    Obtiene el precio mínimo para cada día de la ventana consultando Google Flights.
    """
    precios: Dict[str, Optional[float]] = {}
    for d in fechas:
        try:
            ofertas = buscar_vuelos_google(
                origen=origen,
                destino=destino,
                fecha_salida=d,
                adultos=adultos,
                moneda=moneda,
                api_key=api_key,
            )
            if ofertas:
                precios[d] = min(o.precio_total for o in ofertas)
            else:
                precios[d] = None
        except Exception as e:
            logger.warning(f"Error consultando fecha {d} en Google Flights: {e}")
            precios[d] = None
    return precios
