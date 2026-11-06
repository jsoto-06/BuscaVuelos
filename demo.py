"""
Módulo de simulación y datos de demostración (Modo Demo).
Permite explorar y probar toda la interfaz visual y la lógica de negocio
sin necesidad de disponer de claves activas de la API de Amadeus.
"""

from typing import List, Dict, Optional
import random
import enlaces
from modelos import Oferta


def generar_ofertas_demo(
    origen: str,
    destino: str,
    fechas: List[str],
    adultos: int = 1,
) -> List[Oferta]:
    """
    Genera un listado de ofertas realistas simuladas para probar la interfaz visual.
    Incluye aerolíneas habituales, horarios variados y desgloses de equipaje.
    """
    aerolineas_muestra = [
        ("Iberia", "IB", "IB8452", 0, "1h 15m", 54.0, "Incluido (1 pieza)", 1, 54.0),
        ("Vueling", "VY", "VY1540", 0, "1h 10m", 38.5, "No incluido", 0, 68.5),
        ("Ryanair", "FR", "FR2108", 0, "1h 20m", 29.9, "No incluido", 0, 59.9),
        ("Air Europa", "UX", "UX4012", 1, "3h 10m", 68.0, "Incluido (1 pieza)", 1, 68.0),
        ("Volotea", "V7", "V73105", 0, "1h 15m", 42.0, "No incluido", 0, 67.0),
    ]

    ofertas = []
    id_counter = 1

    for f in fechas:
        # Generar 3-5 vuelos por día
        for aero_info in aerolineas_muestra:
            nombre, cod, num, escalas, dur, precio_base, eq_desc, eq_piezas, precio_eq = aero_info

            # Pequeña variación de precio según el día
            variacion = (hash(f"{cod}_{f}") % 25) - 10
            precio_final = round(max(24.0, (precio_base + variacion) * adultos), 2)
            precio_eq_final = round((precio_eq + variacion) * adultos, 2) if precio_eq else None

            # Horarios simulados
            h_sal = f"{7 + (id_counter % 14):02d}:{(id_counter * 15) % 60:02d}"
            h_lleg = f"{9 + (id_counter % 14):02d}:{(id_counter * 15 + 20) % 60:02d}"

            enlace_g, enlace_sky = enlaces.generar_enlaces(origen, destino, f)
            enlace_aero = enlaces.generar_enlace_aerolinea(cod, origen, destino, f, adultos=adultos)

            ofertas.append(
                Oferta(
                    id=f"demo_{id_counter}",
                    origen=origen.upper(),
                    destino=destino.upper(),
                    fecha_salida=f,
                    hora_salida=h_sal,
                    hora_llegada=h_lleg,
                    fecha_llegada=f,
                    escalas=escalas,
                    duracion=dur,
                    aerolinea=f"{nombre} [DEMO]",
                    numero_vuelo=num,
                    precio_total=precio_final,
                    moneda="EUR",
                    equipaje_incluido=eq_desc,
                    piezas_equipaje=eq_piezas,
                    precio_con_equipaje=precio_eq_final,
                    enlace_google=enlace_g,
                    enlace_skyscanner=enlace_sky,
                    enlace_aerolinea=enlace_aero,
                )
            )
            id_counter += 1

    return ofertas


def generar_precios_calendario_demo(
    origen: str,
    destino: str,
    fechas: List[str],
) -> Dict[str, Optional[float]]:
    """Genera precios mínimos simulados para cada día de una ventana temporal."""
    precios = {}
    random.seed(42)  # Precios consistentes durante la sesión

    for idx, f in enumerate(fechas):
        # Crear un patrón realista con días valle y días pico
        base = 35.0 + (hash(f) % 45)
        if idx == len(fechas) // 2:
            base = 29.50  # Día más barato destacado
        precios[f] = round(base, 2)

    return precios
