"""
Pruebas unitarias para equipaje.py: lectura de equipaje incluido, sin dato y datos mal formados.
"""

import equipaje


def test_equipaje_incluido_por_cantidad():
    oferta_raw = {
        "price": {"total": "120.00", "currency": "EUR"},
        "travelerPricings": [
            {
                "fareDetailsBySegment": [
                    {
                        "segmentId": "1",
                        "includedCheckedBags": {"quantity": 1},
                    }
                ]
            }
        ],
    }

    desc, piezas, precio_con_eq = equipaje.extraer_info_equipaje(oferta_raw, 120.00)
    assert desc == "Incluido (1 pieza)"
    assert piezas == 1
    assert precio_con_eq == 120.00


def test_equipaje_incluido_por_peso():
    oferta_raw = {
        "price": {"total": "150.00", "currency": "EUR"},
        "travelerPricings": [
            {
                "fareDetailsBySegment": [
                    {
                        "segmentId": "1",
                        "includedCheckedBags": {"weight": 23, "weightUnit": "KG"},
                    }
                ]
            }
        ],
    }

    desc, piezas, precio_con_eq = equipaje.extraer_info_equipaje(oferta_raw, 150.00)
    assert desc == "Incluido (23 KG)"
    assert precio_con_eq == 150.00


def test_equipaje_no_incluido():
    oferta_raw = {
        "price": {"total": "80.00", "currency": "EUR"},
        "travelerPricings": [
            {
                "fareDetailsBySegment": [
                    {
                        "segmentId": "1",
                        "includedCheckedBags": {"quantity": 0},
                    }
                ]
            }
        ],
    }

    desc, piezas, precio_con_eq = equipaje.extraer_info_equipaje(oferta_raw, 80.00)
    assert desc == "No incluido"
    assert piezas == 0
    # Como no hay precio desglosado de suplemento en additionalServices, debe ser None (no disponible)
    assert precio_con_eq is None


def test_equipaje_sin_dato_no_indicado():
    oferta_raw = {
        "price": {"total": "95.00", "currency": "EUR"},
        "travelerPricings": [
            {
                "fareDetailsBySegment": [
                    {
                        "segmentId": "1",
                        # Sin includedCheckedBags
                    }
                ]
            }
        ],
    }

    desc, piezas, precio_con_eq = equipaje.extraer_info_equipaje(oferta_raw, 95.00)
    assert desc == "no indicado"
    assert piezas is None
    assert precio_con_eq is None


def test_equipaje_datos_mal_formados():
    # Casos extremos: None, tipos erróneos, estructuras vacías
    casos = [
        {},
        {"travelerPricings": None},
        {"travelerPricings": []},
        {"travelerPricings": [{"fareDetailsBySegment": "no-es-lista"}]},
        {"travelerPricings": [{"fareDetailsBySegment": [{"includedCheckedBags": "invalido"}]}]},
    ]

    for caso in casos:
        desc, piezas, precio_con_eq = equipaje.extraer_info_equipaje(caso, 50.00)
        assert desc == "no indicado"
        assert piezas is None
        assert precio_con_eq is None
