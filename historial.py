"""
Módulo para el registro y consulta del historial local de búsquedas.
Preserva la privacidad: no almacena identificadores ni datos personales.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import config
from modelos import Busqueda


def _obtener_ruta(ruta_personalizada: Optional[Path] = None) -> Path:
    """Retorna la ruta del archivo de historial."""
    if ruta_personalizada:
        return Path(ruta_personalizada)
    return config.HISTORIAL_FILE


def cargar_historial(ruta_archivo: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Carga las entradas de historial desde el archivo JSON."""
    ruta = _obtener_ruta(ruta_archivo)
    if not ruta.exists():
        return []

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
            if isinstance(datos, list):
                return datos
            return []
    except (json.JSONDecodeError, OSError):
        return []


def registrar_busqueda(
    busqueda: Busqueda,
    num_resultados: int,
    ruta_archivo: Optional[Path] = None,
) -> None:
    """
    Registra una búsqueda realizada en el historial local.
    Almacena exclusivamente parámetros técnicos y fecha/hora, sin datos personales.
    """
    ruta = _obtener_ruta(ruta_archivo)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    entradas = cargar_historial(ruta)

    nueva_entrada = {
        "fecha_hora": datetime.now().isoformat(timespec="seconds"),
        "origen": busqueda.origen,
        "destinos": busqueda.destinos,
        "fecha_desde": busqueda.fecha_desde,
        "fecha_hasta": busqueda.fecha_hasta,
        "alternativos": busqueda.alternativos,
        "directos": busqueda.directos,
        "max_precio": busqueda.max_precio,
        "adultos": busqueda.adultos,
        "resultados_encontrados": num_resultados,
    }

    entradas.append(nueva_entrada)

    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(entradas, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def borrar_historial(
    pedir_confirmacion: bool = True,
    ruta_archivo: Optional[Path] = None,
) -> bool:
    """
    Elimina el archivo de historial. Si pedir_confirmacion es True,
    solicita confirmación al usuario antes de proceder.
    """
    ruta = _obtener_ruta(ruta_archivo)
    if not ruta.exists():
        print("El historial ya se encuentra vacío.")
        return True

    if pedir_confirmacion:
        try:
            resp = input("¿Seguro que deseas borrar el historial de búsquedas? (s/N): ").strip().lower()
            if resp not in ("s", "si", "y", "yes"):
                print("Operación cancelada. El historial se conserva.")
                return False
        except (KeyboardInterrupt, EOFError):
            print("\nOperación cancelada.")
            return False

    try:
        ruta.unlink()
        print("Historial borrado con éxito.")
        return True
    except OSError as e:
        print(f"Error al intentar borrar el archivo de historial: {e}")
        return False


def formatear_historial_texto(entradas: List[Dict[str, Any]]) -> str:
    """Formatea la lista de entradas de historial para visualización en terminal."""
    if not entradas:
        return "El historial de búsquedas está vacío."

    lineas = [
        "",
        "📜 Historial de búsquedas recientes (almacenamiento 100% local)",
        "=" * 85,
        f"{'Fecha/Hora':<20} | {'Origen':<6} | {'Destinos':<15} | {'Fechas':<22} | {'Resultados':<10}",
        "-" * 85,
    ]

    for item in entradas:
        fh = item.get("fecha_hora", "").replace("T", " ")
        orig = item.get("origen", "")
        dest = ",".join(item.get("destinos", []))
        f_ini = item.get("fecha_desde", "")
        f_fin = item.get("fecha_hasta", "")
        rango = f"{f_ini} -> {f_fin}" if f_fin else f_ini
        res = str(item.get("resultados_encontrados", 0))

        lineas.append(
            f"{fh:<20} | {orig:<6} | {dest:<15} | {rango:<22} | {res:<10}"
        )

    lineas.append("=" * 85)
    lineas.append(f"Total de búsquedas registradas: {len(entradas)}")
    lineas.append("")
    return "\n".join(lineas)
