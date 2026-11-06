"""
Módulo para la persistencia y gestión de alertas de precio locales en JSON.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import config
import aeropuertos
import filtros
from modelos import Alerta


def _obtener_ruta(ruta_personalizada: Optional[Path] = None) -> Path:
    """Retorna la ruta del archivo de alertas a utilizar."""
    if ruta_personalizada:
        return Path(ruta_personalizada)
    return config.ALERTAS_FILE


def cargar_alertas(ruta_archivo: Optional[Path] = None) -> List[Alerta]:
    """Carga todas las alertas guardadas en el archivo JSON."""
    ruta = _obtener_ruta(ruta_archivo)
    if not ruta.exists():
        return []

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
            if not isinstance(datos, list):
                return []
            return [Alerta.from_dict(item) for item in datos if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError):
        return []


def guardar_alertas(alertas: List[Alerta], ruta_archivo: Optional[Path] = None) -> None:
    """Guarda la lista completa de alertas en el archivo JSON."""
    ruta = _obtener_ruta(ruta_archivo)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    datos = [alerta.to_dict() for alerta in alertas]
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def crear_alerta(
    origen: str,
    destino: str,
    fecha_desde: str,
    fecha_hasta: str,
    max_precio: float,
    ruta_archivo: Optional[Path] = None,
) -> Alerta:
    """
    Crea una nueva alerta de precio, validando aeropuertos y fechas, y la persiste.
    """
    origen_val = aeropuertos.validar_iata(origen)
    destino_val = aeropuertos.validar_iata(destino)
    filtros.validar_rango_fechas(fecha_desde, fecha_hasta)

    if max_precio <= 0:
        raise ValueError("El precio máximo debe ser un número positivo.")

    nueva_alerta = Alerta(
        id=uuid.uuid4().hex[:8],
        origen=origen_val,
        destino=destino_val,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        max_precio=round(float(max_precio), 2),
        creada_en=datetime.now().isoformat(timespec="seconds"),
        ultimo_precio_visto=None,
        ultimo_aviso=None,
        ofertas_notificadas=[],
    )

    alertas = cargar_alertas(ruta_archivo)
    alertas.append(nueva_alerta)
    guardar_alertas(alertas, ruta_archivo)

    return nueva_alerta


def borrar_alerta(alerta_id: str, ruta_archivo: Optional[Path] = None) -> bool:
    """
    Elimina una alerta por su ID. Retorna True si existía y fue borrada, False si no existía.
    """
    alerta_id_limpio = alerta_id.strip()
    alertas = cargar_alertas(ruta_archivo)
    alertas_filtradas = [a for a in alertas if a.id != alerta_id_limpio]

    if len(alertas_filtradas) == len(alertas):
        return False

    guardar_alertas(alertas_filtradas, ruta_archivo)
    return True


def registrar_aviso_oferta(
    alerta: Alerta,
    hash_oferta: str,
    precio: float,
    ruta_archivo: Optional[Path] = None,
) -> None:
    """
    Actualiza la alerta indicando que se ha notificado una oferta concreta.
    Añade el hash a ofertas_notificadas para evitar duplicar avisos.
    """
    if hash_oferta not in alerta.ofertas_notificadas:
        alerta.ofertas_notificadas.append(hash_oferta)
    alerta.ultimo_precio_visto = round(precio, 2)
    alerta.ultimo_aviso = datetime.now().isoformat(timespec="seconds")

    # Guardar cambios
    alertas = cargar_alertas(ruta_archivo)
    for i, a in enumerate(alertas):
        if a.id == alerta.id:
            alertas[i] = alerta
            break
    guardar_alertas(alertas, ruta_archivo)
