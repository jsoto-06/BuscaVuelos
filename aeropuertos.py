"""
Módulo para validación y gestión de aeropuertos y códigos IATA.
"""

import re
from typing import List, Union, Optional
import config

# Diccionario con nombres de aeropuertos y ciudades frecuentes para mejorar la presentación
NOMBRES_AEROPUERTOS = {
    "BIO": "Bilbao",
    "VIT": "Vitoria",
    "SDR": "Santander",
    "BIQ": "Biarritz",
    "MAD": "Madrid-Barajas",
    "BCN": "Barcelona-El Prat",
    "VLC": "Valencia",
    "AGP": "Málaga",
    "SVQ": "Sevilla",
    "ALC": "Alicante",
    "PMI": "Palma de Mallorca",
    "IBZ": "Ibiza",
    "TFN": "Tenerife Norte",
    "TFS": "Tenerife Sur",
    "LPA": "Gran Canaria",
    "SCQ": "Santiago de Compostela",
    "LON": "Londres (Todos)",
    "LHR": "Londres-Heathrow",
    "LGW": "Londres-Gatwick",
    "STN": "Londres-Stansted",
    "LTN": "Londres-Luton",
    "PAR": "París (Todos)",
    "CDG": "París-Charles de Gaulle",
    "ORY": "París-Orly",
    "BVA": "París-Beauvais",
    "ROM": "Roma (Todos)",
    "FCO": "Roma-Fiumicino",
    "CIA": "Roma-Ciampino",
    "BER": "Berlín",
    "AMS": "Ámsterdam",
    "FRA": "Fráncfort",
    "MUC": "Múnich",
    "BRU": "Bruselas",
    "CRL": "Bruselas-Charleroi",
    "LIS": "Lisboa",
    "OPO": "Oporto",
    "MXP": "Milán-Malpensa",
    "BGY": "Milán-Bérgamo",
    "LIN": "Milán-Linate",
    "VIE": "Viena",
    "DUB": "Dublín",
    "PRG": "Praga",
    "WAW": "Varsovia",
    "CPH": "Copenhague",
}


def validar_iata(codigo: str) -> str:
    """
    Valida que un código IATA tenga exactamente 3 letras alfabéticas.
    Retorna el código en mayúsculas. Lanza ValueError si no es válido.
    """
    if not codigo or not isinstance(codigo, str):
        raise ValueError("El código IATA no puede estar vacío.")

    codigo_limpio = codigo.strip().upper()
    if not re.match(r"^[A-Z]{3}$", codigo_limpio):
        raise ValueError(
            f"Código IATA no válido: '{codigo}'. Debe constar de exactamente 3 letras (ej. BIO, MAD, LON)."
        )
    return codigo_limpio


def parsear_lista_iata(entrada: Union[str, List[str]]) -> List[str]:
    """
    Convierte una cadena separada por comas (ej. 'LON,PAR') o una lista
    en una lista validada de códigos IATA en mayúsculas, sin duplicados.
    """
    if isinstance(entrada, str):
        codigos_raw = [c.strip() for c in entrada.split(",") if c.strip()]
    elif isinstance(entrada, (list, tuple)):
        codigos_raw = [str(c).strip() for c in entrada if str(c).strip()]
    else:
        raise ValueError("Formato de destinos no reconocido.")

    if not codigos_raw:
        raise ValueError("Debes especificar al menos un código de aeropuerto.")

    resultado = []
    for c in codigos_raw:
        valido = validar_iata(c)
        if valido not in resultado:
            resultado.append(valido)

    return resultado


def obtener_origenes(
    origen_usuario: Optional[str] = None,
    incluir_alternativos: bool = False
) -> List[str]:
    """
    Determina la lista de aeropuertos de origen a consultar.
    Si incluir_alternativos es True, añade los configurados en ALTERNATIVOS_ORIGEN.
    """
    origen_ppal = validar_iata(origen_usuario or config.ORIGEN_POR_DEFECTO)
    origenes = [origen_ppal]

    if incluir_alternativos:
        for alt in config.ALTERNATIVOS_ORIGEN:
            try:
                alt_validado = validar_iata(alt)
                if alt_validado not in origenes:
                    origenes.append(alt_validado)
            except ValueError:
                continue

    return origenes


def nombre_aeropuerto(codigo: str) -> str:
    """Retorna una descripción legible del aeropuerto si se conoce."""
    cod = codigo.strip().upper()
    ciudad = NOMBRES_AEROPUERTOS.get(cod)
    if ciudad:
        return f"{ciudad} ({cod})"
    return cod
