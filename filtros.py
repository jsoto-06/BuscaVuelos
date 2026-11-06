"""
Módulo para validación de fechas, filtrado, ordenación y deduplicación de ofertas.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Set
from modelos import Oferta


def validar_fecha(fecha_str: str) -> date:
    """
    Valida que una fecha tenga formato YYYY-MM-DD y que no sea anterior a hoy.
    Retorna el objeto date. Lanza ValueError si es inválida.
    """
    if not fecha_str or not isinstance(fecha_str, str):
        raise ValueError("La fecha no puede estar vacía.")

    try:
        fecha_obj = datetime.strptime(fecha_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(
            f"Formato de fecha no válido: '{fecha_str}'. Debe ser YYYY-MM-DD (ej. 2026-12-01)."
        )

    hoy = date.today()
    if fecha_obj < hoy:
        raise ValueError(
            f"La fecha {fecha_str} ya ha pasado. Debe ser hoy ({hoy.isoformat()}) o una fecha futura."
        )

    return fecha_obj


def validar_rango_fechas(
    desde_str: str, hasta_str: Optional[str] = None
) -> Tuple[date, Optional[date]]:
    """
    Valida un rango de fechas. Comprueba que ambas sean válidas y que hasta >= desde.
    """
    f_desde = validar_fecha(desde_str)
    f_hasta = None

    if hasta_str:
        f_hasta = validar_fecha(hasta_str)
        if f_hasta < f_desde:
            raise ValueError(
                f"La fecha de fin ({hasta_str}) no puede ser anterior a la fecha de inicio ({desde_str})."
            )

    return f_desde, f_hasta


def generar_dias_ventana(f_desde: date, f_hasta: date) -> List[str]:
    """Genera la lista de fechas en formato ISO YYYY-MM-DD entre desde y hasta inclusivo."""
    dias = []
    actual = f_desde
    while actual <= f_hasta:
        dias.append(actual.isoformat())
        actual += timedelta(days=1)
    return dias


def eliminar_duplicados(ofertas: List[Oferta]) -> List[Oferta]:
    """
    Elimina ofertas duplicadas según la clave (aerolínea, salida, llegada, precio).
    Conserva la primera aparición manteniendo el orden.
    """
    vistas: Set[tuple] = set()
    unicas: List[Oferta] = []

    for oferta in ofertas:
        clave = oferta.clave_deduplicacion
        if clave not in vistas:
            vistas.add(clave)
            unicas.append(oferta)

    return unicas


def filtrar_por_precio(ofertas: List[Oferta], max_precio: Optional[float]) -> List[Oferta]:
    """Filtra ofertas cuyo precio total sea menor o igual a max_precio."""
    if max_precio is None or max_precio <= 0:
        return ofertas
    return [o for o in ofertas if o.precio_total <= max_precio]


def filtrar_directos(ofertas: List[Oferta], solo_directos: bool) -> List[Oferta]:
    """Filtra únicamente vuelos sin escalas si solo_directos es True."""
    if not solo_directos:
        return ofertas
    return [o for o in ofertas if o.escalas == 0]


def ordenar_por_precio(ofertas: List[Oferta], ascendente: bool = True) -> List[Oferta]:
    """Ordena las ofertas según su precio total."""
    return sorted(ofertas, key=lambda o: o.precio_total, reverse=not ascendente)


def aplicar_filtros(
    ofertas: List[Oferta],
    max_precio: Optional[float] = None,
    solo_directos: bool = False,
    top: Optional[int] = None,
) -> List[Oferta]:
    """
    Aplica secuencialmente:
      1. Deduplicación por (aerolínea, salida, llegada, precio)
      2. Filtro por precio máximo
      3. Filtro por vuelos directos
      4. Ordenación por precio ascendente
      5. Límite de resultados (top) si se especifica
    """
    resultado = eliminar_duplicados(ofertas)
    resultado = filtrar_por_precio(resultado, max_precio)
    resultado = filtrar_directos(resultado, solo_directos)
    resultado = ordenar_por_precio(resultado, ascendente=True)

    if top is not None and top > 0:
        resultado = resultado[:top]

    return resultado
