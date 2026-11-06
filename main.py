#!/usr/bin/env python3
"""
Punto de entrada principal (CLI) para vuelos_baratos.
Búsqueda de vuelos con la API oficial de Amadeus for Developers y webs oficiales
de aerolíneas con prioridad en la privacidad.
"""

import sys

# Configurar codificación UTF-8 en Windows para terminales estándar
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import argparse
import logging
from typing import List

import config
import aeropuertos
import filtros
import enlaces
import salida
import historial
import alertas as modulo_alertas
import calendario as modulo_calendario
import vigilancia as modulo_vigilancia
from amadeus_api import (
    AmadeusCliente,
    AmadeusError,
    AmadeusAuthError,
    AmadeusRateLimitError,
    AmadeusNetworkError,
)
from modelos import Busqueda, Oferta


def configurar_logging(verbose: bool) -> None:
    """Configura el nivel de log. Si verbose es True, muestra logs detallados de depuración."""
    nivel = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def comando_buscar(args: argparse.Namespace) -> int:
    """Ejecuta el subcomando 'buscar'."""
    usar_serpapi = bool(config.SERPAPI_API_KEY) and (
        getattr(args, "motor", None) == "google"
        or not config.validar_credenciales(salir_si_invalido=False)
    )

    if not usar_serpapi:
        config.validar_credenciales(salir_si_invalido=True)

    try:
        origenes = aeropuertos.obtener_origenes(
            origen_usuario=args.origen, incluir_alternativos=args.alternativos
        )
        destinos = aeropuertos.parsear_lista_iata(args.destinos)
        f_desde, f_hasta = filtros.validar_rango_fechas(args.desde, args.hasta)
    except ValueError as ve:
        print(f"\n❌ Error en los parámetros: {ve}\n", file=sys.stderr)
        return 1

    dias: List[str] = (
        filtros.generar_dias_ventana(f_desde, f_hasta)
        if f_hasta
        else [f_desde.isoformat()]
    )

    motor_nombre = "Google Flights (SerpApi en vivo)" if usar_serpapi else "Amadeus API"
    print(f"\n🛫 Buscando vuelos desde {', '.join(origenes)} hacia {', '.join(destinos)}...")
    print(f"🌐 Motor: {motor_nombre}")
    print(f"📅 Fechas: {dias[0]}" + (f" hasta {dias[-1]} ({len(dias)} días)" if len(dias) > 1 else ""))

    todas_ofertas: List[Oferta] = []

    if usar_serpapi:
        import serpapi_client
        for orig in origenes:
            for dest in destinos:
                for dia in dias:
                    if len(origenes) > 1 or len(destinos) > 1 or len(dias) > 1:
                        print(f"  • Consultando {orig} ➔ {dest} para el {dia}...", end=" ", flush=True)
                    try:
                        ofertas = serpapi_client.buscar_vuelos_google(
                            origen=orig,
                            destino=dest,
                            fecha_salida=dia,
                            adultos=args.adultos,
                            moneda=config.MONEDA,
                            directos=args.directos,
                            max_precio=args.max_precio,
                        )
                        todas_ofertas.extend(ofertas)
                        if len(origenes) > 1 or len(destinos) > 1 or len(dias) > 1:
                            print(f"({len(ofertas)} ofertas)")
                    except Exception as e:
                        if len(origenes) > 1 or len(destinos) > 1 or len(dias) > 1:
                            print(f"(Error: {e})")
                        else:
                            raise
    else:
        cliente = AmadeusCliente()
        for orig in origenes:
            for dest in destinos:
                for dia in dias:
                    if len(origenes) > 1 or len(destinos) > 1 or len(dias) > 1:
                        print(f"  • Consultando {orig} ➔ {dest} para el {dia}...", end=" ", flush=True)

                    try:
                        ofertas = cliente.buscar_vuelos(
                            origen=orig,
                            destino=dest,
                            fecha_salida=dia,
                            adultos=args.adultos,
                            moneda=config.MONEDA,
                            directos=args.directos,
                            max_precio=args.max_precio,
                        )
                        todas_ofertas.extend(ofertas)
                        if len(origenes) > 1 or len(destinos) > 1 or len(dias) > 1:
                            print(f"({len(ofertas)} ofertas)")
                    except AmadeusError as ae:
                        if len(origenes) > 1 or len(destinos) > 1 or len(dias) > 1:
                            print(f"(Error: {ae})")
                        else:
                            raise

    # Aplicar filtros, deduplicación y ordenación
    ofertas_finales = filtros.aplicar_filtros(
        todas_ofertas,
        max_precio=args.max_precio,
        solo_directos=args.directos,
        top=args.top,
    )

    # Imprimir tabla y resumen
    salida.imprimir_tabla_ofertas(ofertas_finales)
    salida.imprimir_resumen(ofertas_finales)

    # Registrar en historial local
    origen_principal = args.origen or config.ORIGEN_POR_DEFECTO
    busqueda_reg = Busqueda(
        origen=origen_principal,
        destinos=destinos,
        fecha_desde=args.desde,
        fecha_hasta=args.hasta,
        alternativos=args.alternativos,
        directos=args.directos,
        max_precio=args.max_precio,
        adultos=args.adultos,
        top=args.top,
    )
    historial.registrar_busqueda(busqueda_reg, num_resultados=len(ofertas_finales))

    # Exportar CSV si fue solicitado
    if args.csv and ofertas_finales:
        salida.exportar_csv(ofertas_finales, origen=origen_principal, destinos=destinos)

    # Abrir enlaces de comparadores si fue solicitado
    if getattr(args, "abrir", 0) > 0 and ofertas_finales:
        enlaces_abrir = [o.enlace_google for o in ofertas_finales[: args.abrir]]
        print(f"🌐 Abriendo {len(enlaces_abrir)} enlace(s) en tu navegador predeterminado...")
        enlaces.abrir_enlaces_en_navegador(enlaces_abrir, args.abrir)

    # Abrir webs oficiales de aerolíneas en el navegador si fue solicitado
    if getattr(args, "abrir_aerolinea", 0) > 0 and ofertas_finales:
        enlaces_aero = [o.enlace_aerolinea for o in ofertas_finales[: args.abrir_aerolinea] if o.enlace_aerolinea]
        print(f"✈️ Abriendo {len(enlaces_aero)} web(s) oficial(es) de aerolíneas en tu navegador...")
        enlaces.abrir_enlaces_en_navegador(enlaces_aero, args.abrir_aerolinea)

    return 0


def comando_aerolineas(args: argparse.Namespace) -> int:
    """
    Ejecuta el subcomando 'aerolineas' para consultar y abrir webs oficiales
    de aerolíneas directamente, sin requerir claves de Amadeus.
    """
    try:
        origen = aeropuertos.validar_iata(args.origen or config.ORIGEN_POR_DEFECTO)
        destinos = aeropuertos.parsear_lista_iata(args.destinos)
        f_desde = filtros.validar_fecha(args.desde)
    except ValueError as ve:
        print(f"\n❌ Error en los parámetros: {ve}\n", file=sys.stderr)
        return 1

    todos_enlaces = []
    for dest in destinos:
        enlaces_dict = enlaces.obtener_enlaces_principales_aerolineas(
            origen=origen,
            destino=dest,
            fecha_salida=f_desde.isoformat(),
            adultos=args.adultos,
        )
        salida.imprimir_enlaces_aerolineas_ruta(
            origen=origen,
            destino=dest,
            fecha_salida=f_desde.isoformat(),
            enlaces_dict=enlaces_dict,
        )
        todos_enlaces.extend(list(enlaces_dict.values()))

    if getattr(args, "abrir", 0) > 0 and todos_enlaces:
        num_abrir = min(args.abrir, len(todos_enlaces))
        print(f"🌐 Abriendo {num_abrir} web(s) oficial(es) de aerolíneas en tu navegador...")
        enlaces.abrir_enlaces_en_navegador(todos_enlaces, num_abrir)

    return 0


def comando_calendario(args: argparse.Namespace) -> int:
    """Ejecuta el subcomando 'calendario'."""
    config.validar_credenciales(salir_si_invalido=True)

    try:
        origen = aeropuertos.validar_iata(args.origen or config.ORIGEN_POR_DEFECTO)
        destinos = aeropuertos.parsear_lista_iata(args.destinos)
        f_desde, f_hasta = filtros.validar_rango_fechas(args.desde, args.hasta)
        if not f_hasta:
            raise ValueError("Debes especificar la fecha final con --hasta para ver la ventana de precios.")
    except ValueError as ve:
        print(f"\n❌ Error en los parámetros: {ve}\n", file=sys.stderr)
        return 1

    cliente = AmadeusCliente()
    for dest in destinos:
        print(f"\nBuscando ventana de precios para {origen} ➔ {dest} entre {f_desde} y {f_hasta}...")
        precios = modulo_calendario.consultar_precios_ventana(
            cliente=cliente,
            origen=origen,
            destino=dest,
            f_desde=f_desde,
            f_hasta=f_hasta,
            moneda=config.MONEDA,
        )
        print(modulo_calendario.formatear_calendario_texto(origen, dest, precios, config.MONEDA))

    return 0


def comando_alerta(args: argparse.Namespace) -> int:
    """Gestiona el subcomando 'alerta' (añadir, listar, borrar)."""
    sub = args.accion_alerta

    if sub in ("añadir", "anadir", "agregar"):
        try:
            origen = aeropuertos.validar_iata(args.origen or config.ORIGEN_POR_DEFECTO)
            destino = aeropuertos.validar_iata(args.destino)
            filtros.validar_rango_fechas(args.desde, args.hasta)
            if args.max_precio <= 0:
                raise ValueError("El precio máximo debe ser un valor positivo.")

            nueva = modulo_alertas.crear_alerta(
                origen=origen,
                destino=destino,
                fecha_desde=args.desde,
                fecha_hasta=args.hasta,
                max_precio=args.max_precio,
            )
            print(
                f"\n✓ Alerta de precio creada con éxito [ID: {nueva.id}]\n"
                f"  Ruta: {nueva.origen} ➔ {nueva.destino}\n"
                f"  Fechas: {nueva.fecha_desde} hasta {nueva.fecha_hasta}\n"
                f"  Umbral máximo: {nueva.max_precio:.2f} {config.MONEDA}\n"
            )
            return 0
        except ValueError as ve:
            print(f"\n❌ Error al crear la alerta: {ve}\n", file=sys.stderr)
            return 1

    elif sub in ("listar", "ver"):
        alertas = modulo_alertas.cargar_alertas()
        if not alertas:
            print("\nNo tienes ninguna alerta de precio configurada.\n")
            return 0

        print("\n📋 ALERTAS DE PRECIO ACTIVAS:")
        print("=" * 75)
        print(f"{'ID':<10} | {'Ruta':<12} | {'Fechas':<24} | {'Máx Precio':<12} | {'Avisos'}")
        print("-" * 75)
        for a in alertas:
            ruta = f"{a.origen} ➔ {a.destino}"
            rango = f"{a.fecha_desde} -> {a.fecha_hasta}"
            precio = f"{a.max_precio:.2f} {config.MONEDA}"
            avisos = f"{len(a.ofertas_notificadas)} oferta(s)"
            print(f"{a.id:<10} | {ruta:<12} | {rango:<24} | {precio:<12} | {avisos}")
        print("=" * 75 + "\n")
        return 0

    elif sub in ("borrar", "eliminar"):
        id_alerta = getattr(args, "id", None)
        if not id_alerta:
            print("\n❌ Debes indicar el ID de la alerta a borrar. Ej: python main.py alerta borrar a1b2c3d4\n")
            return 1

        borrado = modulo_alertas.borrar_alerta(id_alerta)
        if borrado:
            print(f"\n✓ Alerta con ID '{id_alerta}' eliminada con éxito.\n")
            return 0
        else:
            print(f"\n⚠️ No se encontró ninguna alerta con el ID '{id_alerta}'.\n")
            return 1

    else:
        print("\nSubcomando de alerta no reconocido. Usa 'python main.py alerta --help'.\n")
        return 1


def comando_vigilar(args: argparse.Namespace) -> int:
    """Ejecuta el subcomando 'vigilar'."""
    config.validar_credenciales(salir_si_invalido=True)
    modulo_vigilancia.ejecutar_vigilancia(una_vez=args.una_vez)
    return 0


def comando_web(args: argparse.Namespace) -> int:
    """Inicia la interfaz gráfica visual basada en Streamlit."""
    import subprocess
    from pathlib import Path

    app_path = Path(__file__).resolve().parent / "app.py"
    print("\n🚀 Iniciando el panel visual interactivo de Vuelos Baratos...")
    print("Se abrirá en tu navegador web predeterminado (o en http://localhost:8501).\n")
    try:
        resultado = subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
        return resultado.returncode
    except KeyboardInterrupt:
        print("\nPanel visual cerrado.")
        return 0
    except Exception as e:
        print(f"\n❌ Error al iniciar la interfaz gráfica: {e}\n", file=sys.stderr)
        return 1


def comando_historial(args: argparse.Namespace) -> int:
    """Gestiona el subcomando 'historial' (ver, borrar)."""
    sub = args.accion_historial

    if sub in ("ver", "listar"):
        entradas = historial.cargar_historial()
        print(historial.formatear_historial_texto(entradas))
        return 0
    elif sub in ("borrar", "limpiar"):
        historial.borrar_historial(pedir_confirmacion=True)
        return 0
    else:
        print("\nSubcomando de historial no reconocido. Usa 'python main.py historial --help'.\n")
        return 1


def construir_parser() -> argparse.ArgumentParser:
    """Crea la estructura de argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(
        prog="vuelos_baratos",
        description="Buscador de vuelos baratos con la API oficial de Amadeus for Developers y webs oficiales de aerolíneas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Muestra información detallada de depuración (logs internos).",
    )

    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponibles")

    # -------------------------------------------------------------
    # 1. Subcomando: buscar
    # -------------------------------------------------------------
    p_buscar = subparsers.add_parser(
        "buscar",
        help="Busca ofertas de vuelos para rutas y fechas especificadas.",
        description="Busca vuelos económicos utilizando la API de Amadeus y genera enlaces a comparadores y aerolíneas.",
    )
    p_buscar.add_argument(
        "--destinos",
        required=True,
        help="Códigos IATA de destino separados por comas (ej. LON,PAR,BER).",
    )
    p_buscar.add_argument(
        "--desde",
        required=True,
        help="Fecha de salida (formato YYYY-MM-DD).",
    )
    p_buscar.add_argument(
        "--hasta",
        default=None,
        help="Fecha final de la ventana de salida (opcional, formato YYYY-MM-DD).",
    )
    p_buscar.add_argument(
        "--origen",
        default=None,
        help=f"Código IATA de origen (por defecto: {config.ORIGEN_POR_DEFECTO}).",
    )
    p_buscar.add_argument(
        "--alternativos",
        action="store_true",
        help=f"Incluye aeropuertos alternativos ({','.join(config.ALTERNATIVOS_ORIGEN)}).",
    )
    p_buscar.add_argument(
        "--directos",
        action="store_true",
        help="Filtra únicamente vuelos directos sin escalas.",
    )
    p_buscar.add_argument(
        "--max-precio",
        type=float,
        default=None,
        help="Precio máximo total por pasajero en la moneda configurada.",
    )
    p_buscar.add_argument(
        "--adultos",
        type=int,
        default=1,
        help="Número de pasajeros adultos (por defecto: 1).",
    )
    p_buscar.add_argument(
        "--top",
        type=int,
        default=None,
        help="Muestra únicamente las N opciones más económicas.",
    )
    p_buscar.add_argument(
        "--csv",
        action="store_true",
        help="Exporta las ofertas encontradas a un archivo CSV en resultados/.",
    )
    p_buscar.add_argument(
        "--abrir",
        type=int,
        default=0,
        metavar="N",
        help="Abre automáticamente en el navegador web los enlaces de comparación de las N mejores ofertas.",
    )
    p_buscar.add_argument(
        "--abrir-aerolinea",
        type=int,
        default=0,
        metavar="N",
        help="Abre directamente en el navegador las webs oficiales de las aerolíneas de las N mejores ofertas.",
    )
    p_buscar.add_argument(
        "--motor",
        choices=["google", "amadeus"],
        default="google" if config.SERPAPI_API_KEY else "amadeus",
        help="Motor de búsqueda a utilizar: 'google' (SerpApi en vivo) o 'amadeus' (API Amadeus).",
    )

    # -------------------------------------------------------------
    # 2. Subcomando: aerolineas (búsqueda directa en webs oficiales)
    # -------------------------------------------------------------
    p_aerolineas = subparsers.add_parser(
        "aerolineas",
        help="Genera enlaces directos a las webs oficiales de las aerolíneas para una ruta y fecha.",
        description="Genera y abre los motores de reserva oficiales de las principales aerolíneas con origen, destino y fecha pre-cargados.",
    )
    p_aerolineas.add_argument(
        "--destinos",
        required=True,
        help="Códigos IATA de destino (ej. LON o LON,PAR).",
    )
    p_aerolineas.add_argument(
        "--desde",
        required=True,
        help="Fecha de salida (formato YYYY-MM-DD).",
    )
    p_aerolineas.add_argument(
        "--origen",
        default=None,
        help=f"Código IATA de origen (por defecto: {config.ORIGEN_POR_DEFECTO}).",
    )
    p_aerolineas.add_argument(
        "--adultos",
        type=int,
        default=1,
        help="Número de pasajeros adultos (por defecto: 1).",
    )
    p_aerolineas.add_argument(
        "--abrir",
        type=int,
        default=0,
        metavar="N",
        help="Abre automáticamente en el navegador web las webs de las N primeras aerolíneas.",
    )

    # -------------------------------------------------------------
    # 3. Subcomando: calendario
    # -------------------------------------------------------------
    p_calendario = subparsers.add_parser(
        "calendario",
        help="Muestra una vista de precios por fecha dentro de una ventana temporal.",
        description="Consulta las fechas más baratas para una ruta y resalta el día óptimo.",
    )
    p_calendario.add_argument(
        "--destinos",
        required=True,
        help="Código(s) IATA de destino (ej. LON o LON,PAR).",
    )
    p_calendario.add_argument(
        "--desde",
        required=True,
        help="Fecha inicial de la ventana (YYYY-MM-DD).",
    )
    p_calendario.add_argument(
        "--hasta",
        required=True,
        help="Fecha final de la ventana (YYYY-MM-DD).",
    )
    p_calendario.add_argument(
        "--origen",
        default=None,
        help=f"Código IATA de origen (por defecto: {config.ORIGEN_POR_DEFECTO}).",
    )

    # -------------------------------------------------------------
    # 4. Subcomando: alerta
    # -------------------------------------------------------------
    p_alerta = subparsers.add_parser(
        "alerta",
        help="Gestiona alertas de precio persistidas localmente en JSON.",
        description="Crea, lista o elimina alertas de precio para vigilancia automática.",
    )
    sub_alerta = p_alerta.add_subparsers(dest="accion_alerta", help="Acción de alerta")

    # alerta añadir
    p_alerta_add = sub_alerta.add_parser("añadir", aliases=["anadir", "agregar"], help="Crea una nueva alerta.")
    p_alerta_add.add_argument(
        "--origen",
        default=None,
        help=f"Aeropuerto de origen (por defecto: {config.ORIGEN_POR_DEFECTO}).",
    )
    p_alerta_add.add_argument("--destino", required=True, help="Aeropuerto de destino (ej. LON).")
    p_alerta_add.add_argument("--desde", required=True, help="Fecha inicial de viaje (YYYY-MM-DD).")
    p_alerta_add.add_argument("--hasta", required=True, help="Fecha final de viaje (YYYY-MM-DD).")
    p_alerta_add.add_argument("--max-precio", type=float, required=True, help="Precio umbral máximo deseado.")

    # alerta listar
    sub_alerta.add_parser("listar", aliases=["ver"], help="Lista todas las alertas configuradas.")

    # alerta borrar
    p_alerta_del = sub_alerta.add_parser("borrar", aliases=["eliminar"], help="Borra una alerta por su ID.")
    p_alerta_del.add_argument("id", help="Identificador único de la alerta a eliminar.")

    # -------------------------------------------------------------
    # 5. Subcomando: vigilar
    # -------------------------------------------------------------
    p_vigilar = subparsers.add_parser(
        "vigilar",
        help="Comprueba periódicamente las alertas de precio configuradas.",
        description="Ejecuta la vigilancia de precios. Puede correr en bucle o una sola vez.",
    )
    p_vigilar.add_argument(
        "--una-vez",
        action="store_true",
        help="Ejecuta una única verificación y finaliza (ideal para cron o Programador de tareas).",
    )

    # -------------------------------------------------------------
    # 6. Subcomando: historial
    # -------------------------------------------------------------
    p_historial = subparsers.add_parser(
        "historial",
        help="Gestiona el historial local de búsquedas realizadas.",
        description="Permite ver las búsquedas previas o eliminarlas garantizando la privacidad.",
    )
    sub_historial = p_historial.add_subparsers(dest="accion_historial", help="Acción de historial")
    sub_historial.add_parser("ver", aliases=["listar"], help="Muestra el historial local de búsquedas.")
    sub_historial.add_parser("borrar", aliases=["limpiar"], help="Borra el archivo de historial tras confirmación.")

    # -------------------------------------------------------------
    # 7. Subcomando: web (interfaz visual)
    # -------------------------------------------------------------
    subparsers.add_parser(
        "web",
        aliases=["ui", "interfaz"],
        help="Inicia la interfaz gráfica visual interactiva en el navegador.",
        description="Lanza el panel visual interactivo de Vuelos Baratos con Streamlit.",
    )

    return parser


def main() -> None:
    """Función principal de ejecución."""
    parser = construir_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    configurar_logging(args.verbose)

    try:
        if args.comando == "buscar":
            codigo = comando_buscar(args)
        elif args.comando == "aerolineas":
            codigo = comando_aerolineas(args)
        elif args.comando == "calendario":
            codigo = comando_calendario(args)
        elif args.comando == "alerta":
            codigo = comando_alerta(args)
        elif args.comando == "vigilar":
            codigo = comando_vigilar(args)
        elif args.comando == "historial":
            codigo = comando_historial(args)
        elif args.comando in ("web", "ui", "interfaz"):
            codigo = comando_web(args)
        else:
            parser.print_help()
            codigo = 0
        sys.exit(codigo)

    except KeyboardInterrupt:
        print("\n\nOperación interrumpida por el usuario.")
        sys.exit(0)
    except AmadeusAuthError as aae:
        print(f"\n🔑 [ERROR DE AUTENTICACIÓN] {aae}\n", file=sys.stderr)
        sys.exit(1)
    except AmadeusRateLimitError as arle:
        print(f"\n⏳ [LÍMITE DE FRECUENCIA] {arle}\n", file=sys.stderr)
        sys.exit(1)
    except AmadeusNetworkError as ane:
        print(f"\n🌐 [ERROR DE RED] {ane}\n", file=sys.stderr)
        sys.exit(1)
    except AmadeusError as ae:
        print(f"\n✈️ [ERROR DE AMADEUS] {ae}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.verbose:
            logging.exception("Excepción no controlada:")
        else:
            print(f"\n❌ [ERROR INESPERADO] {e}\n(Usa --verbose para ver el registro detallado.)\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
