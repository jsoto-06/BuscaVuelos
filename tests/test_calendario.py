"""
Pruebas unitarias para calendario.py: construcción de ventanas y marcado de fecha óptima.
"""

from datetime import date
import filtros
import calendario


def test_construccion_ventana_dias():
    f_desde = date(2026, 12, 1)
    f_hasta = date(2026, 12, 5)

    dias = filtros.generar_dias_ventana(f_desde, f_hasta)
    assert dias == [
        "2026-12-01",
        "2026-12-02",
        "2026-12-03",
        "2026-12-04",
        "2026-12-05",
    ]
    assert len(dias) == 5


def test_encontrar_fecha_mas_barata():
    precios = {
        "2026-12-01": 120.0,
        "2026-12-02": 45.5,
        "2026-12-03": 89.0,
        "2026-12-04": None,  # Sin vuelos
        "2026-12-05": 60.0,
    }

    mejor_fecha, mejor_precio = calendario.encontrar_fecha_mas_barata(precios)
    assert mejor_fecha == "2026-12-02"
    assert mejor_precio == 45.5


def test_encontrar_fecha_mas_barata_sin_vuelos():
    precios = {
        "2026-12-01": None,
        "2026-12-02": None,
    }
    mejor_fecha, mejor_precio = calendario.encontrar_fecha_mas_barata(precios)
    assert mejor_fecha is None
    assert mejor_precio is None


def test_marcado_asterisco_fecha_mas_barata():
    precios = {
        "2026-12-01": 150.0,
        "2026-12-02": 49.0,
        "2026-12-03": 99.0,
    }

    texto_calendario = calendario.formatear_calendario_texto(
        origen="BIO",
        destino="LON",
        precios_por_fecha=precios,
        moneda="EUR",
    )

    # Debe contener el asterisco en la línea de la fecha más barata (2026-12-02)
    assert "* 2026-12-02" in texto_calendario
    assert "MÁS BARATO" in texto_calendario
    # Las otras fechas no deben llevar asterisco inicial
    assert "* 2026-12-01" not in texto_calendario
    assert "* 2026-12-03" not in texto_calendario
