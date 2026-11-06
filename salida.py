"""
Módulo para la visualización en terminal (tabla enriquecida), exportación a CSV
y resumen de ofertas de vuelos.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import config
from modelos import Oferta


AVISO_DESCARGO = (
    "⚠️  AVISO IMPORTANTE: Los precios de los vuelos y la disponibilidad de plazas varían con "
    "gran rapidez. Esta herramienta busca y compara tarifas públicas, pero NO gestiona reservas ni cobros.\n"
    "    Antes de realizar cualquier pago, verifica siempre en la web oficial de la aerolínea o agencia la tarifa final,\n"
    "    las tasas aeroportuarias y las condiciones de equipaje permitidas."
)


def formatear_escalas(escalas: int) -> str:
    """Retorna una cadena amigable para el número de escalas."""
    if escalas == 0:
        return "Directo"
    if escalas == 1:
        return "1 escala"
    return f"{escalas} escalas"


def imprimir_tabla_ofertas(ofertas: List[Oferta]) -> None:
    """
    Imprime en consola una tabla formateada con las ofertas encontradas.
    Incluye aviso legal y de confirmación de precio al final.
    """
    if not ofertas:
        print("\nNo se encontraron ofertas que coincidan con los criterios de búsqueda.\n")
        return

    # Encabezados de la tabla
    headers = [
        "#",
        "Origen",
        "Destino",
        "Fecha",
        "Salida",
        "Llegada",
        "Escalas",
        "Duración",
        "Aerolínea",
        "Total (sin bodega)",
        "Total (con bodega)",
        "Equipaje",
    ]

    filas = []
    for idx, o in enumerate(ofertas, 1):
        total_sin_bodega = f"{o.precio_total:.2f} {o.moneda}"
        total_con_bodega = o.precio_con_equipaje_texto
        filas.append([
            str(idx),
            o.origen,
            o.destino,
            o.fecha_salida,
            o.hora_salida,
            o.hora_llegada,
            formatear_escalas(o.escalas),
            o.duracion,
            o.aerolinea[:18],
            total_sin_bodega,
            total_con_bodega,
            o.equipaje_incluido,
        ])

    # Calcular anchos de columna
    anchos = [len(h) for h in headers]
    for fila in filas:
        for i, celda in enumerate(fila):
            if len(celda) > anchos[i]:
                anchos[i] = len(celda)

    # Construir líneas
    separador = "+-" + "-+-".join("-" * a for a in anchos) + "-+"
    linea_cabecera = "| " + " | ".join(f"{h:<{anchos[i]}}" for i, h in enumerate(headers)) + " |"

    print("\n" + separador)
    print(linea_cabecera)
    print(separador)

    for fila in filas:
        linea = "| " + " | ".join(f"{c:<{anchos[i]}}" for i, c in enumerate(fila)) + " |"
        print(linea)

    print(separador)

    # Imprimir enlaces directos a las opciones principales
    print("\n🔗 Enlaces directos a las webs oficiales de las aerolíneas y comparadores:")
    top_enlaces = min(5, len(ofertas))
    for idx in range(top_enlaces):
        o = ofertas[idx]
        print(
            f"  [{idx + 1}] {o.origen} ➔ {o.destino} ({o.fecha_salida}) | "
            f"{o.aerolinea} ({o.numero_vuelo}) - {o.precio_total:.2f} {o.moneda}:"
        )
        if o.enlace_aerolinea:
            print(f"      ✈️ Web Oficial ({o.aerolinea}): {o.enlace_aerolinea}")
        print(f"      🔎 Google Flights:           {o.enlace_google}")
        print(f"      🔎 Skyscanner:               {o.enlace_skyscanner}")
    if len(ofertas) > top_enlaces:
        print(f"  ... y {len(ofertas) - top_enlaces} oferta(s) más.")

    # Aviso final
    print("\n" + "-" * 80)
    print(AVISO_DESCARGO)
    print("-" * 80 + "\n")


def imprimir_enlaces_aerolineas_ruta(
    origen: str,
    destino: str,
    fecha_salida: str,
    enlaces_dict: dict,
) -> None:
    """Imprime una tabla de enlaces directos a las webs oficiales de las aerolíneas para una ruta."""
    print(f"\n🌐 Búsqueda directa en las webs oficiales de aerolíneas: {origen} ➔ {destino} ({fecha_salida})")
    print("=" * 80)
    for nombre_aerolinea, url in enlaces_dict.items():
        print(f"  ✈️  {nombre_aerolinea:<24} : {url}")
    print("=" * 80)
    print("💡 Estos enlaces abren el motor de reservas oficial de cada aerolínea con origen, destino y fecha pre-cargados.\n")


def exportar_csv(
    ofertas: List[Oferta],
    origen: str,
    destinos: List[str],
    ruta_dir: Optional[Path] = None,
) -> Path:
    """
    Exporta la lista de ofertas a un archivo CSV en el directorio resultados/.
    """
    carpeta = ruta_dir or config.RESULTADOS_DIR
    carpeta.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_txt = "_".join(destinos)
    nombre_archivo = f"vuelos_{origen}_{dest_txt}_{timestamp}.csv"
    ruta_archivo = carpeta / nombre_archivo

    encabezados = [
        "#",
        "Origen",
        "Destino",
        "Fecha Salida",
        "Hora Salida",
        "Fecha Llegada",
        "Hora Llegada",
        "Escalas",
        "Duracion",
        "Aerolinea",
        "Vuelo",
        "Total Sin Bodega",
        "Total Con Bodega",
        "Moneda",
        "Equipaje Incluido",
        "Enlace Web Oficial Aerolinea",
        "Enlace Google Flights",
        "Enlace Skyscanner",
    ]

    with open(ruta_archivo, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f)
        escritor.writerow(encabezados)
        for idx, o in enumerate(ofertas, 1):
            escritor.writerow([
                idx,
                o.origen,
                o.destino,
                o.fecha_salida,
                o.hora_salida,
                o.fecha_llegada,
                o.hora_llegada,
                o.escalas,
                o.duracion,
                o.aerolinea,
                o.numero_vuelo,
                f"{o.precio_total:.2f}",
                f"{o.precio_con_equipaje:.2f}" if o.precio_con_equipaje is not None else "no disponible",
                o.moneda,
                o.equipaje_incluido,
                o.enlace_aerolinea,
                o.enlace_google,
                o.enlace_skyscanner,
            ])

    print(f"💾 Resultados exportados correctamente a CSV: {ruta_archivo}")
    return ruta_archivo


def imprimir_resumen(ofertas: List[Oferta]) -> None:
    """Imprime un resumen estadístico breve de los resultados encontrados."""
    if not ofertas:
        return

    precio_min = min(o.precio_total for o in ofertas)
    precio_max = max(o.precio_total for o in ofertas)
    media = sum(o.precio_total for o in ofertas) / len(ofertas)
    moneda = ofertas[0].moneda

    mejor = min(ofertas, key=lambda x: x.precio_total)

    print("📊 RESUMEN DE LA BÚSQUEDA:")
    print(f"  • Total ofertas encontradas: {len(ofertas)}")
    print(f"  • Precio más bajo: {precio_min:.2f} {moneda} ({mejor.origen} ➔ {mejor.destino} el {mejor.fecha_salida})")
    print(f"  • Precio más alto: {precio_max:.2f} {moneda}")
    print(f"  • Precio promedio: {media:.2f} {moneda}")
