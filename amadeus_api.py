"""
Cliente de la API oficial de Amadeus for Developers (Self-Service).
Gestiona token OAuth en memoria, búsqueda de ofertas, fechas más baratas y reintentos con cortesía.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple

import requests
import config
import privacidad
import equipaje
import enlaces
from modelos import Oferta

logger = logging.getLogger(__name__)


class AmadeusError(Exception):
    """Excepción base para errores de la API de Amadeus."""
    pass


class AmadeusAuthError(AmadeusError):
    """Credenciales inválidas o sin autorización (401/403)."""
    pass


class AmadeusRateLimitError(AmadeusError):
    """Límite de peticiones alcanzado tras reintento (429)."""
    pass


class AmadeusNetworkError(AmadeusError):
    """Error de conexión o timeout tras varios reintentos."""
    pass


def parsear_duracion_iso(duracion_iso: str) -> str:
    """
    Convierte duraciones en formato ISO 8601 (ej. 'PT2H15M', 'PT45M', 'PT1H')
    en una cadena legible (ej. '2h 15m', '45m', '1h 00m').
    """
    if not duracion_iso or not isinstance(duracion_iso, str):
        return ""

    texto = duracion_iso.upper().replace("PT", "")
    horas = 0
    minutos = 0

    if "H" in texto:
        partes = texto.split("H")
        try:
            horas = int(partes[0])
        except ValueError:
            horas = 0
        resto = partes[1] if len(partes) > 1 else ""
    else:
        resto = texto

    if "M" in resto:
        min_str = resto.replace("M", "")
        try:
            minutos = int(min_str)
        except ValueError:
            minutos = 0

    if horas > 0 and minutos > 0:
        return f"{horas}h {minutos:02d}m"
    elif horas > 0:
        return f"{horas}h 00m"
    elif minutos > 0:
        return f"{minutos}m"

    return duracion_iso


class AmadeusCliente:
    """
    Cliente para la API de Amadeus. Mantiene el token OAuth exclusivamente en memoria,
    respeta rate limits y aplica reintentos ante fallos transitorios.
    """

    def __init__(self):
        self._token: Optional[str] = None
        self._token_expira_en: float = 0.0

    def _obtener_token(self) -> str:
        """
        Obtiene un token de acceso OAuth2 válido. Si ya existe en memoria y no ha expirado,
        lo reutiliza; si no, solicita uno nuevo.
        """
        # Reutilizar token en memoria con 60 segundos de margen
        ahora = time.time()
        if self._token and ahora < (self._token_expira_en - 60):
            return self._token

        if not config.AMADEUS_CLIENT_ID or not config.AMADEUS_CLIENT_SECRET:
            raise AmadeusAuthError(
                "Faltan las credenciales AMADEUS_CLIENT_ID o AMADEUS_CLIENT_SECRET en .env."
            )

        url = f"{config.AMADEUS_BASE_URL}/v1/security/oauth2/token"
        datos = {
            "grant_type": "client_credentials",
            "client_id": config.AMADEUS_CLIENT_ID,
            "client_secret": config.AMADEUS_CLIENT_SECRET,
        }

        logger.debug("Solicitando nuevo token OAuth a Amadeus...")
        respuesta_json = self._realizar_peticion(
            metodo="POST",
            url=url,
            data=datos,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            requiere_auth=False,
        )

        token = respuesta_json.get("access_token")
        if not token:
            raise AmadeusAuthError("La respuesta de autenticación no incluyó 'access_token'.")

        expires_in = int(respuesta_json.get("expires_in", 1799))
        self._token = token
        self._token_expira_en = time.time() + expires_in
        logger.debug(f"Token OAuth obtenido con éxito (válido por {expires_in} segundos).")
        return self._token

    def _realizar_peticion(
        self,
        metodo: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        requiere_auth: bool = True,
    ) -> Dict[str, Any]:
        """
        Ejecuta una petición HTTP a través de una sesión efímera, aplicando rate limiting
        y reintentos con backoff exponencial.
        """
        max_intentos_red = 3
        headers = dict(headers or {})

        for intento in range(1, max_intentos_red + 1):
            privacidad.esperar_rate_limit()

            if requiere_auth:
                token = self._obtener_token()
                headers["Authorization"] = f"Bearer {token}"

            sesion = privacidad.sesion_nueva()
            try:
                if metodo.upper() == "GET":
                    resp = sesion.get(url, params=params, headers=headers, timeout=20)
                else:
                    resp = sesion.post(url, data=data, headers=headers, timeout=20)

                # 401 / 403: Error de autenticación
                if resp.status_code in (401, 403):
                    # Si el token caducó anticipadamente, limpiar memoria e intentar una vez
                    if requiere_auth and self._token:
                        self._token = None
                        self._token_expira_en = 0.0
                    raise AmadeusAuthError(
                        f"Error de autenticación ({resp.status_code}): "
                        "Tus credenciales de Amadeus son inválidas, expiraron o no tienen permiso. "
                        "Verifica AMADEUS_CLIENT_ID y AMADEUS_CLIENT_SECRET en .env."
                    )

                # 429: Rate limit excedido -> esperar y reintentar 1 vez
                if resp.status_code == 429:
                    logger.warning("Límite de peticiones alcanzado (429). Esperando 4 segundos...")
                    time.sleep(4.0)
                    privacidad.esperar_rate_limit()
                    # Reintento directo
                    if metodo.upper() == "GET":
                        resp = sesion.get(url, params=params, headers=headers, timeout=20)
                    else:
                        resp = sesion.post(url, data=data, headers=headers, timeout=20)

                    if resp.status_code == 429:
                        raise AmadeusRateLimitError(
                            "Se ha superado el límite de peticiones de la API de Amadeus (429). "
                            "Espera unos instantes antes de volver a intentarlo."
                        )

                # Errores 4xx o 5xx
                if resp.status_code >= 400:
                    detalle = ""
                    try:
                        err_json = resp.json()
                        errores = err_json.get("errors", [])
                        if errores and isinstance(errores, list):
                            detalle = " - " + "; ".join(
                                e.get("detail", str(e)) for e in errores if isinstance(e, dict)
                            )
                    except Exception:
                        detalle = f" - {resp.text[:200]}"

                    raise AmadeusError(
                        f"Error de la API de Amadeus ({resp.status_code}){detalle}"
                    )

                return resp.json()

            except (requests.ConnectionError, requests.Timeout) as e:
                logger.warning(
                    f"Error de red ({e.__class__.__name__}) en intento {intento}/{max_intentos_red}."
                )
                if intento == max_intentos_red:
                    raise AmadeusNetworkError(
                        f"No se pudo conectar con Amadeus tras {max_intentos_red} intentos: {e}"
                    )
                time.sleep(2**intento)
            finally:
                sesion.close()

        raise AmadeusNetworkError("Error de red inesperado.")

    def buscar_vuelos(
        self,
        origen: str,
        destino: str,
        fecha_salida: str,
        adultos: int = 1,
        moneda: str = config.MONEDA,
        directos: bool = False,
        max_precio: Optional[float] = None,
        limite_resultados: int = 50,
    ) -> List[Oferta]:
        """
        Consulta las ofertas de vuelos en Amadeus Flight Offers Search v2.
        Parsea los resultados a objetos Oferta.
        """
        url = f"{config.AMADEUS_BASE_URL}/v2/shopping/flight-offers"
        params: Dict[str, Any] = {
            "originLocationCode": origen.strip().upper(),
            "destinationLocationCode": destino.strip().upper(),
            "departureDate": fecha_salida,
            "adults": adultos,
            "currencyCode": moneda,
            "max": limite_resultados,
        }
        if directos:
            params["nonStop"] = "true"
        if max_precio and max_precio > 0:
            params["maxPrice"] = int(max_precio)

        logger.debug(
            f"Buscando vuelos {origen} -> {destino} para fecha {fecha_salida}..."
        )
        try:
            respuesta = self._realizar_peticion("GET", url, params=params)
        except AmadeusError:
            raise

        ofertas_raw = respuesta.get("data", [])
        diccionarios = respuesta.get("dictionaries", {})
        carriers_dict = diccionarios.get("carriers", {})

        ofertas: List[Oferta] = []
        for raw in ofertas_raw:
            oferta_parseada = self._parsear_oferta(
                raw, carriers_dict, origen_solicitado=origen, destino_solicitado=destino
            )
            if oferta_parseada:
                ofertas.append(oferta_parseada)

        return ofertas

    def _parsear_oferta(
        self,
        raw: Dict[str, Any],
        carriers_dict: Dict[str, str],
        origen_solicitado: str,
        destino_solicitado: str,
    ) -> Optional[Oferta]:
        """Extrae los datos de una oferta individual y construye el objeto Oferta."""
        itinerarios = raw.get("itineraries", [])
        if not itinerarios:
            return None

        primer_itinerario = itinerarios[0]
        segmentos = primer_itinerario.get("segments", [])
        if not segmentos:
            return None

        primer_seg = segmentos[0]
        ultimo_seg = segmentos[-1]

        # Origen y destino
        dep_info = primer_seg.get("departure", {})
        arr_info = ultimo_seg.get("arrival", {})

        origen_real = dep_info.get("iataCode", origen_solicitado)
        destino_real = arr_info.get("iataCode", destino_solicitado)

        # Fechas y horas
        salida_at = dep_info.get("at", "")
        llegada_at = arr_info.get("at", "")

        fecha_salida = salida_at.split("T")[0] if "T" in salida_at else salida_at
        hora_salida = salida_at.split("T")[1][:5] if "T" in salida_at else ""
        fecha_llegada = llegada_at.split("T")[0] if "T" in llegada_at else llegada_at
        hora_llegada = llegada_at.split("T")[1][:5] if "T" in llegada_at else ""

        # Escalas y duración
        escalas = len(segmentos) - 1
        duracion_iso = primer_itinerario.get("duration", "")
        duracion = parsear_duracion_iso(duracion_iso)

        # Aerolínea
        carrier_code = primer_seg.get("carrierCode", "")
        aerolinea_nombre = carriers_dict.get(carrier_code, carrier_code)
        numero_vuelo = f"{carrier_code}{primer_seg.get('number', '')}"

        # Precios
        precio_dict = raw.get("price", {})
        try:
            precio_total = float(precio_dict.get("total", 0.0))
        except (ValueError, TypeError):
            precio_total = 0.0
        moneda = precio_dict.get("currency", config.MONEDA)

        # Equipaje
        desc_eq, piezas_eq, precio_con_eq = equipaje.extraer_info_equipaje(raw, precio_total)

        # Enlaces
        enlace_g, enlace_sky = enlaces.generar_enlaces(origen_real, destino_real, fecha_salida)
        enlace_aero = enlaces.generar_enlace_aerolinea(
            codigo_aerolinea=carrier_code,
            origen=origen_real,
            destino=destino_real,
            fecha_salida=fecha_salida,
        )

        return Oferta(
            id=str(raw.get("id", "")),
            origen=origen_real,
            destino=destino_real,
            fecha_salida=fecha_salida,
            hora_salida=hora_salida,
            hora_llegada=hora_llegada,
            fecha_llegada=fecha_llegada,
            escalas=escalas,
            duracion=duracion,
            aerolinea=aerolinea_nombre,
            numero_vuelo=numero_vuelo,
            precio_total=precio_total,
            moneda=moneda,
            equipaje_incluido=desc_eq,
            piezas_equipaje=piezas_eq,
            precio_con_equipaje=precio_con_eq,
            enlace_google=enlace_g,
            enlace_skyscanner=enlace_sky,
            enlace_aerolinea=enlace_aero,
        )

    def buscar_fechas_mas_baratas(
        self, origen: str, destino: str, fecha_desde: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Intenta consultar el endpoint flight-dates de Amadeus.
        Retorna la lista de resultados si está disponible, o None si no está soportado o falla.
        """
        url = f"{config.AMADEUS_BASE_URL}/v1/shopping/flight-dates"
        params = {
            "origin": origen.strip().upper(),
            "destination": destino.strip().upper(),
            "departureDate": fecha_desde,
        }
        try:
            resp = self._realizar_peticion("GET", url, params=params)
            return resp.get("data")
        except AmadeusError as e:
            logger.debug(f"flight-dates no disponible o devolvió error ({e}). Se usará búsqueda estándar.")
            return None
