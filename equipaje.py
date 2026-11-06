"""
Módulo para el análisis y extracción de información sobre equipaje en ofertas de Amadeus.
Gestiona el equipaje de bodega incluido y calcula el coste estimado si está disponible.
"""

from typing import Dict, Any, Tuple, Optional


def extraer_info_equipaje(
    oferta_raw: Dict[str, Any], precio_total: float
) -> Tuple[str, Optional[int], Optional[float]]:
    """
    Analiza la oferta de Amadeus para determinar:
      1. Descripción del equipaje de bodega incluido (ej. 'Incluido (1 pieza)', 'No incluido', 'no indicado')
      2. Número de piezas incluidas (si procede)
      3. Precio total estimado con equipaje (float o None si 'no disponible')

    Reglas:
      - Si la oferta no indica equipaje, devuelve 'no indicado' (nunca suponer que no incluye).
      - Si incluye equipaje de bodega, precio_con_equipaje = precio_total.
      - Si no incluye y existe coste adicional especificado por Amadeus, suma el suplemento.
      - Si no incluye o no está indicado y no hay coste desglosado, devuelve None ('no disponible').
    """
    if not isinstance(oferta_raw, dict):
        return ("no indicado", None, None)

    traveler_pricings = oferta_raw.get("travelerPricings")
    if not isinstance(traveler_pricings, list) or not traveler_pricings:
        return ("no indicado", None, None)

    # Examinamos el primer viajero (habitualmente adulto principal)
    primer_viajero = traveler_pricings[0]
    if not isinstance(primer_viajero, dict):
        return ("no indicado", None, None)

    fare_details = primer_viajero.get("fareDetailsBySegment")
    if not isinstance(fare_details, list) or not fare_details:
        return ("no indicado", None, None)

    # Recorrer segmentos buscando información de equipaje incluido
    cantidades = []
    pesos = []
    info_encontrada = False

    for seg in fare_details:
        if not isinstance(seg, dict):
            continue
        bags = seg.get("includedCheckedBags")
        if isinstance(bags, dict):
            info_encontrada = True
            if "quantity" in bags:
                try:
                    cantidades.append(int(bags["quantity"]))
                except (ValueError, TypeError):
                    pass
            elif "weight" in bags:
                try:
                    peso_val = float(bags["weight"])
                    unidad = str(bags.get("weightUnit", "KG")).strip().upper()
                    pesos.append((peso_val, unidad))
                except (ValueError, TypeError):
                    pass

    # Determinar estado del equipaje incluido
    descripcion_equipaje = "no indicado"
    piezas_incluidas: Optional[int] = None
    equipaje_esta_incluido = False

    if cantidades:
        # Tomamos el mínimo de los segmentos para no prometer equipaje que falte en escalas
        min_cant = min(cantidades)
        piezas_incluidas = min_cant
        if min_cant > 0:
            equipaje_esta_incluido = True
            descripcion_equipaje = (
                f"Incluido ({min_cant} pieza)" if min_cant == 1 else f"Incluido ({min_cant} piezas)"
            )
        else:
            descripcion_equipaje = "No incluido"
    elif pesos:
        min_peso, unidad = pesos[0]
        if min_peso > 0:
            equipaje_esta_incluido = True
            descripcion_equipaje = f"Incluido ({int(min_peso) if min_peso.is_integer() else min_peso} {unidad})"
        else:
            descripcion_equipaje = "No incluido"
    elif info_encontrada:
        # Se encontró el campo pero sin quantity ni weight válidos
        descripcion_equipaje = "no indicado"

    # Buscar suplemento de equipaje adicional si no está incluido
    precio_con_equipaje: Optional[float] = None

    if equipaje_esta_incluido:
        # Ya está incluido en la tarifa base
        precio_con_equipaje = round(precio_total, 2)
    else:
        # Intentar extraer coste adicional desde price.additionalServices
        coste_adicional = _extraer_coste_adicional_equipaje(oferta_raw)
        if coste_adicional is not None and coste_adicional > 0:
            precio_con_equipaje = round(precio_total + coste_adicional, 2)
        else:
            # Si no está disponible, no inventar el dato
            precio_con_equipaje = None

    return (descripcion_equipaje, piezas_incluidas, precio_con_equipaje)


def _extraer_coste_adicional_equipaje(oferta_raw: Dict[str, Any]) -> Optional[float]:
    """
    Busca si la oferta indica el coste de facturar una maleta en additionalServices.
    """
    price_info = oferta_raw.get("price")
    if isinstance(price_info, dict):
        additional_services = price_info.get("additionalServices")
        if isinstance(additional_services, list):
            for serv in additional_services:
                if isinstance(serv, dict):
                    serv_type = str(serv.get("type", "")).upper()
                    if serv_type in ("CHECKED_BAGS", "BAGGAGE"):
                        try:
                            return float(serv.get("amount", 0.0))
                        except (ValueError, TypeError):
                            pass

    return None
