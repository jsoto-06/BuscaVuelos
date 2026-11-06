"""
Módulo para la vigilancia periódica de alertas de precio.
Permite comprobación puntual (--una-vez) o bucle continuo en segundo plano.
"""

import time
import logging
from datetime import datetime
from typing import Optional

import config
import alertas as modulo_alertas
import filtros
import historial
import notificaciones
from amadeus_api import AmadeusCliente, AmadeusError
from modelos import Busqueda

logger = logging.getLogger(__name__)


def comprobar_alertas_una_vez(cliente: Optional[AmadeusCliente] = None) -> int:
    """
    Ejecuta una ronda de comprobación de todas las alertas activas.
    Si una alerta falla por error en la API, registra el error y continúa con las demás.
    Retorna el número de nuevas ofertas notificadas.
    """
    if cliente is None:
        cliente = AmadeusCliente()

    lista_alertas = modulo_alertas.cargar_alertas()
    if not lista_alertas:
        print("No hay alertas registradas para vigilar. Añade una con 'python main.py alerta añadir'.")
        return 0

    print(f"\n🔍 Comprobando {len(lista_alertas)} alerta(s) de precio activas...")
    total_notificadas = 0

    for alerta in lista_alertas:
        print(
            f"  -> Verificando alerta [{alerta.id}]: {alerta.origen} ➔ {alerta.destino} "
            f"({alerta.fecha_desde} a {alerta.fecha_hasta}) - Máx: {alerta.max_precio:.2f} {config.MONEDA}"
        )
        try:
            f_desde, f_hasta = filtros.validar_rango_fechas(alerta.fecha_desde, alerta.fecha_hasta)
            dias = filtros.generar_dias_ventana(f_desde, f_hasta if f_hasta else f_desde)

            for dia in dias:
                ofertas = cliente.buscar_vuelos(
                    origen=alerta.origen,
                    destino=alerta.destino,
                    fecha_salida=dia,
                    adultos=1,
                    moneda=config.MONEDA,
                    max_precio=alerta.max_precio,
                    limite_resultados=20,
                )

                for oferta in ofertas:
                    if oferta.precio_total <= alerta.max_precio:
                        hash_oferta = oferta.hash_alerta
                        if hash_oferta in alerta.ofertas_notificadas:
                            # Ya fue notificada anteriormente; evitar spam
                            continue

                        # Nueva oferta encontrada que cumple los criterios
                        titulo = (
                            f"¡Vuelo barato encontrado! {oferta.origen} ➔ {oferta.destino} por "
                            f"{oferta.precio_total:.2f} {oferta.moneda}"
                        )
                        mensaje = (
                            f"Fecha: {oferta.fecha_salida} ({oferta.hora_salida}) | "
                            f"Aerolínea: {oferta.aerolinea} ({oferta.numero_vuelo}) | "
                            f"Escalas: {oferta.escalas}\n"
                            f"Comparar en Google Flights: {oferta.enlace_google}"
                        )

                        notificaciones.notificar_oferta(titulo, mensaje)

                        # Actualizar alerta persistida
                        modulo_alertas.registrar_aviso_oferta(
                            alerta=alerta,
                            hash_oferta=hash_oferta,
                            precio=oferta.precio_total,
                        )

                        # Registrar en historial local
                        busq = Busqueda(
                            origen=oferta.origen,
                            destinos=[oferta.destino],
                            fecha_desde=oferta.fecha_salida,
                            fecha_hasta=oferta.fecha_salida,
                            max_precio=alerta.max_precio,
                        )
                        historial.registrar_busqueda(busq, num_resultados=1)
                        total_notificadas += 1

        except AmadeusError as ae:
            logger.error(
                f"Error de Amadeus al comprobar alerta [{alerta.id}] ({alerta.origen}->{alerta.destino}): {ae}"
            )
            print(f"     ⚠️ Error al consultar la ruta {alerta.origen}->{alerta.destino}: {ae}")
        except Exception as e:
            logger.error(
                f"Error inesperado comprobando alerta [{alerta.id}]: {e}", exc_info=True
            )
            print(f"     ⚠️ Error en la alerta [{alerta.id}]: {e}")

    print(f"✓ Comprobación finalizada. Nuevas ofertas notificadas: {total_notificadas}\n")
    return total_notificadas


def ejecutar_vigilancia(
    una_vez: bool = False,
    intervalo_horas: Optional[float] = None,
    cliente: Optional[AmadeusCliente] = None,
) -> None:
    """
    Controla el flujo de vigilancia. Si una_vez es True, ejecuta una única ronda.
    En caso contrario, se ejecuta en un bucle temporal indefinido.
    """
    if cliente is None:
        cliente = AmadeusCliente()

    if una_vez:
        comprobar_alertas_una_vez(cliente)
        return

    intervalo = intervalo_horas if intervalo_horas is not None else config.INTERVALO_VIGILANCIA_HORAS
    segundos_espera = max(60.0, intervalo * 3600.0)

    print(
        f"Iniciando servicio de vigilancia continua.\n"
        f"Frecuencia de comprobación: cada {intervalo} hora(s).\n"
        f"Presiona Ctrl+C en cualquier momento para detener el servicio.\n"
    )

    try:
        while True:
            comprobar_alertas_una_vez(cliente)
            proxima = datetime.fromtimestamp(time.time() + segundos_espera).strftime("%H:%M:%S")
            print(f"Pausa activa hasta la próxima ronda ({proxima})...")
            time.sleep(segundos_espera)
    except KeyboardInterrupt:
        print("\n\nServicio de vigilancia detenido por el usuario.")
