"""
Módulo de privacidad para vuelos_baratos.
Garantiza sesiones HTTP efímeras, User-Agent genérico, proxies y control de cadencia.
"""

import time
import requests
import config

# Cabecera User-Agent genérica de navegador moderno para evitar huellas identificativas
USER_AGENT_GENERICO = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Variable interna para rastrear la última petición y controlar el rate limit
_ultima_peticion_tiempo: float = 0.0


def esperar_rate_limit(min_segundos: float | None = None) -> None:
    """
    Aplica una pausa de cortesía entre peticiones sucesivas para respetar
    el límite de frecuencia de la API y evitar bloqueos por sobreuso.
    """
    global _ultima_peticion_tiempo
    if min_segundos is None:
        min_segundos = config.MIN_SEGUNDOS_ENTRE_PETICIONES

    if min_segundos <= 0:
        _ultima_peticion_tiempo = time.time()
        return

    ahora = time.time()
    tiempo_transcurrido = ahora - _ultima_peticion_tiempo
    if _ultima_peticion_tiempo > 0 and tiempo_transcurrido < min_segundos:
        tiempo_espera = min_segundos - tiempo_transcurrido
        time.sleep(tiempo_espera)

    _ultima_peticion_tiempo = time.time()


def sesion_nueva() -> requests.Session:
    """
    Crea una nueva sesión de requests sin estado persistente ni cookies previas.
    Aplica User-Agent genérico y proxy opcional si está configurado.
    """
    sesion = requests.Session()

    # Cabeceras neutras estándar de navegador
    sesion.headers.update({
        "User-Agent": USER_AGENT_GENERICO,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Connection": "close",
    })

    # Proxy opcional
    if config.PROXY_URL:
        sesion.proxies = {
            "http": config.PROXY_URL,
            "https": config.PROXY_URL,
        }

    return sesion
