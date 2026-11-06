"""
Pruebas unitarias para alertas.py: alta, listado, borrado, persistencia y deduplicación de avisos.
"""

from datetime import date, timedelta
import alertas


def test_alta_listado_borrado_alertas(tmp_path):
    archivo_json = tmp_path / "alertas_test.json"
    manana = (date.today() + timedelta(days=1)).isoformat()
    pasado = (date.today() + timedelta(days=5)).isoformat()

    # 1. Crear alerta
    alerta1 = alertas.crear_alerta(
        origen="BIO",
        destino="LON",
        fecha_desde=manana,
        fecha_hasta=pasado,
        max_precio=120.0,
        ruta_archivo=archivo_json,
    )
    assert alerta1.id is not None
    assert alerta1.origen == "BIO"
    assert alerta1.destino == "LON"
    assert alerta1.max_precio == 120.0

    # 2. Listar alertas
    lista = alertas.cargar_alertas(archivo_json)
    assert len(lista) == 1
    assert lista[0].id == alerta1.id

    # Añadir segunda alerta
    alerta2 = alertas.crear_alerta(
        origen="MAD",
        destino="PAR",
        fecha_desde=manana,
        fecha_hasta=pasado,
        max_precio=80.0,
        ruta_archivo=archivo_json,
    )
    lista2 = alertas.cargar_alertas(archivo_json)
    assert len(lista2) == 2

    # 3. Borrar alerta
    borrado = alertas.borrar_alerta(alerta1.id, ruta_archivo=archivo_json)
    assert borrado is True

    lista3 = alertas.cargar_alertas(archivo_json)
    assert len(lista3) == 1
    assert lista3[0].id == alerta2.id

    # Intentar borrar ID inexistente
    assert alertas.borrar_alerta("no_existe", ruta_archivo=archivo_json) is False


def test_no_repetir_avisos_misma_oferta(tmp_path):
    archivo_json = tmp_path / "alertas_test.json"
    manana = (date.today() + timedelta(days=1)).isoformat()
    pasado = (date.today() + timedelta(days=5)).isoformat()

    alerta = alertas.crear_alerta(
        origen="BIO",
        destino="LON",
        fecha_desde=manana,
        fecha_hasta=pasado,
        max_precio=100.0,
        ruta_archivo=archivo_json,
    )

    hash_oferta = "IB_2026-12-01T08:00_85.0"

    # Registrar primer aviso
    alertas.registrar_aviso_oferta(
        alerta=alerta,
        hash_oferta=hash_oferta,
        precio=85.0,
        ruta_archivo=archivo_json,
    )

    # Verificar que el hash se almacenó
    cargada = alertas.cargar_alertas(archivo_json)[0]
    assert hash_oferta in cargada.ofertas_notificadas
    assert cargada.ultimo_precio_visto == 85.0
    assert cargada.ultimo_aviso is not None

    # Si se intenta registrar el mismo hash de nuevo, no se duplica en la lista
    alertas.registrar_aviso_oferta(
        alerta=cargada,
        hash_oferta=hash_oferta,
        precio=85.0,
        ruta_archivo=archivo_json,
    )
    cargada_nueva = alertas.cargar_alertas(archivo_json)[0]
    assert cargada_nueva.ofertas_notificadas.count(hash_oferta) == 1
