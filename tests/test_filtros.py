"""
Pruebas unitarias para filtros.py: ordenación, filtrado y deduplicación.
"""

from datetime import date, timedelta
import pytest
from modelos import Oferta
import filtros


def _crear_oferta_dummy(
    id_oferta: str,
    precio: float,
    escalas: int = 0,
    aerolinea: str = "IB",
    salida: str = "08:00",
    llegada: str = "10:00",
) -> Oferta:
    return Oferta(
        id=id_oferta,
        origen="BIO",
        destino="LON",
        fecha_salida="2026-12-01",
        hora_salida=salida,
        hora_llegada=llegada,
        fecha_llegada="2026-12-01",
        escalas=escalas,
        duracion="2h 00m",
        aerolinea=aerolinea,
        numero_vuelo=f"{aerolinea}123",
        precio_total=precio,
        moneda="EUR",
        equipaje_incluido="no indicado",
        piezas_equipaje=None,
        precio_con_equipaje=None,
        enlace_google="",
        enlace_skyscanner="",
    )


def test_orden_por_precio():
    o1 = _crear_oferta_dummy("1", 150.0)
    o2 = _crear_oferta_dummy("2", 80.0)
    o3 = _crear_oferta_dummy("3", 120.0)

    ordenadas = filtros.ordenar_por_precio([o1, o2, o3], ascendente=True)
    assert [o.precio_total for o in ordenadas] == [80.0, 120.0, 150.0]


def test_filtro_max_precio():
    o1 = _crear_oferta_dummy("1", 90.0)
    o2 = _crear_oferta_dummy("2", 150.0)
    o3 = _crear_oferta_dummy("3", 120.0)

    filtradas = filtros.filtrar_por_precio([o1, o2, o3], max_precio=120.0)
    precios = [o.precio_total for o in filtradas]
    assert 90.0 in precios
    assert 120.0 in precios
    assert 150.0 not in precios


def test_filtro_directos():
    o_directo = _crear_oferta_dummy("1", 100.0, escalas=0)
    o_escala1 = _crear_oferta_dummy("2", 70.0, escalas=1)
    o_escala2 = _crear_oferta_dummy("3", 60.0, escalas=2)

    solo_directos = filtros.filtrar_directos([o_directo, o_escala1, o_escala2], solo_directos=True)
    assert len(solo_directos) == 1
    assert solo_directos[0].id == "1"

    sin_filtro = filtros.filtrar_directos([o_directo, o_escala1, o_escala2], solo_directos=False)
    assert len(sin_filtro) == 3


def test_eliminacion_duplicados():
    # Misma aerolínea, misma salida, misma llegada, mismo precio
    o1 = _crear_oferta_dummy("1", 100.0, aerolinea="IB", salida="08:00", llegada="10:00")
    o2 = _crear_oferta_dummy("2", 100.0, aerolinea="IB", salida="08:00", llegada="10:00")
    # Diferente hora de salida
    o3 = _crear_oferta_dummy("3", 100.0, aerolinea="IB", salida="12:00", llegada="14:00")
    # Diferente aerolínea
    o4 = _crear_oferta_dummy("4", 100.0, aerolinea="BA", salida="08:00", llegada="10:00")

    unicas = filtros.eliminar_duplicados([o1, o2, o3, o4])
    assert len(unicas) == 3
    assert {o.id for o in unicas} == {"1", "3", "4"}


def test_aplicar_filtros_completo():
    o1 = _crear_oferta_dummy("1", 200.0, escalas=0)
    o2 = _crear_oferta_dummy("2", 50.0, escalas=1)
    o3 = _crear_oferta_dummy("3", 80.0, escalas=0)
    o4 = _crear_oferta_dummy("4", 80.0, escalas=0)  # Duplicado de o3

    resultado = filtros.aplicar_filtros(
        [o1, o2, o3, o4],
        max_precio=100.0,
        solo_directos=True,
        top=10,
    )
    assert len(resultado) == 1
    assert resultado[0].id == "3"
    assert resultado[0].precio_total == 80.0


def test_validacion_fechas():
    manana = (date.today() + timedelta(days=1)).isoformat()
    pasado_manana = (date.today() + timedelta(days=2)).isoformat()
    ayer = (date.today() - timedelta(days=1)).isoformat()

    # Fecha válida
    d = filtros.validar_fecha(manana)
    assert d.isoformat() == manana

    # Fecha pasada lanza error
    with pytest.raises(ValueError, match="ya ha pasado"):
        filtros.validar_fecha(ayer)

    # Rango con fin anterior al inicio
    with pytest.raises(ValueError, match="no puede ser anterior"):
        filtros.validar_rango_fechas(pasado_manana, manana)
