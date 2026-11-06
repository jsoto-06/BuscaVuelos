"""
Módulo para la consulta y presentación de precios por fecha dentro de una ventana temporal.
"""

from datetime import date
from typing import Dict, Optional, List, Tuple
import logging

from amadeus_api import AmadeusCliente
import filtros
import config

logger = logging.getLogger(__name__)


def consultar_precios_ventana(
    cliente: AmadeusCliente,
    origen: str,
    destino: str,
    f_desde: date,
    f_hasta: date,
    adultos: int = 1,
    moneda: str = config.MONEDA,
) -> Dict[str, Optional[float]]:
    """
    Obtiene el precio mínimo para cada fecha dentro de la ventana [f_desde, f_hasta].
    Intenta primero flight-dates de Amadeus; si no está disponible, recorre los días
    realizando búsquedas individuales con respeto del rate limit.
    """
    precios_por_fecha: Dict[str, Optional[float]] = {}
    dias = filtros.generar_dias_ventana(f_desde, f_hasta)

    # 1. Intentar endpoint flight-dates
    datos_flight_dates = cliente.buscar_fechas_mas_baratas(origen, destino, f_desde.isoformat())
    if datos_flight_dates and isinstance(datos_flight_dates, list):
        logger.info("Utilizando datos del endpoint de fechas de Amadeus (flight-dates).")
        for item in datos_flight_dates:
            fecha_dep = item.get("departureDate")
            precio_str = item.get("price", {}).get("total")
            if fecha_dep and precio_str and fecha_dep in dias:
                try:
                    precios_por_fecha[fecha_dep] = float(precio_str)
                except (ValueError, TypeError):
                    pass

        # Completar los días que no vinieron en la respuesta
        for d in dias:
            if d not in precios_por_fecha:
                precios_por_fecha[d] = None
        return precios_por_fecha

    # 2. Si flight-dates no está disponible, consultar día a día
    logger.info(
        f"Consultando precios día a día para {origen} -> {destino} ({len(dias)} fechas)..."
    )
    for dia in dias:
        try:
            ofertas = cliente.buscar_vuelos(
                origen=origen,
                destino=destino,
                fecha_salida=dia,
                adultos=adultos,
                moneda=moneda,
                limite_resultados=10,
            )
            if ofertas:
                precio_min = min(o.precio_total for o in ofertas)
                precios_por_fecha[dia] = round(precio_min, 2)
            else:
                precios_por_fecha[dia] = None
        except Exception as e:
            logger.warning(f"Error consultando fecha {dia}: {e}")
            precios_por_fecha[dia] = None

    return precios_por_fecha


def encontrar_fecha_mas_barata(
    precios_por_fecha: Dict[str, Optional[float]]
) -> Tuple[Optional[str], Optional[float]]:
    """
    Identifica la fecha con el precio mínimo entre los días con precios válidos.
    Retorna (fecha_mas_barata, precio_minimo) o (None, None).
    """
    validos = {k: v for k, v in precios_por_fecha.items() if v is not None}
    if not validos:
        return None, None

    fecha_min = min(validos, key=validos.get)
    return fecha_min, validos[fecha_min]


def formatear_calendario_texto(
    origen: str,
    destino: str,
    precios_por_fecha: Dict[str, Optional[float]],
    moneda: str = "EUR",
) -> str:
    """
    Genera una representación en texto del calendario de precios,
    marcando con un asterisco (*) la fecha o fechas más baratas.
    """
    if not precios_por_fecha:
        return "No hay fechas para mostrar en el calendario."

    fecha_min, precio_min = encontrar_fecha_mas_barata(precios_por_fecha)

    lineas = [
        "",
        f"📅 Calendario de precios: {origen} ➔ {destino}",
        "=" * 50,
        f"{'':2} {'Fecha':<12} | {'Precio Mínimo':<16} | {'Nota'}",
        "-" * 50,
    ]

    for dia in sorted(precios_por_fecha.keys()):
        precio = precios_por_fecha[dia]
        if precio is None:
            marca = "  "
            precio_txt = "Sin vuelos"
            nota = "-"
        elif precio_min is not None and precio == precio_min:
            marca = "* "
            precio_txt = f"{precio:.2f} {moneda}"
            nota = "★ MÁS BARATO"
        else:
            marca = "  "
            precio_txt = f"{precio:.2f} {moneda}"
            diferencia = precio - precio_min if precio_min else 0
            nota = f"+{diferencia:.2f} {moneda}"

        lineas.append(f"{marca}{dia:<12} | {precio_txt:<16} | {nota}")

    lineas.append("-" * 50)
    if fecha_min and precio_min is not None:
        lineas.append(
            f"(*) Mejor opción: {fecha_min} por {precio_min:.2f} {moneda}"
        )
    else:
        lineas.append("No se encontraron vuelos disponibles en las fechas seleccionadas.")
    lineas.append("=" * 50)
    lineas.append("")

    return "\n".join(lineas)
