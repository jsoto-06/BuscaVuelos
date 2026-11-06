"""
Pruebas unitarias para cálculo y formateo de precios y suplementos de equipaje.
"""

import equipaje
from amadeus_api import AmadeusCliente
from modelos import Oferta


def test_precio_con_suplemento_equipaje_disponible():
    oferta_raw = {
        "id": "1",
        "price": {
            "total": "90.00",
            "currency": "EUR",
            "additionalServices": [
                {
                    "amount": "30.00",
                    "type": "CHECKED_BAGS",
                }
            ],
        },
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

    desc, piezas, precio_con_eq = equipaje.extraer_info_equipaje(oferta_raw, 90.00)
    assert desc == "No incluido"
    assert precio_con_eq == 120.00  # 90.00 base + 30.00 de maleta facturada


def test_precio_con_equipaje_no_disponible():
    oferta_raw = {
        "id": "2",
        "price": {
            "total": "75.00",
            "currency": "EUR",
            # Sin additionalServices
        },
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

    desc, piezas, precio_con_eq = equipaje.extraer_info_equipaje(oferta_raw, 75.00)
    assert desc == "No incluido"
    assert precio_con_eq is None

    # En el modelo Oferta, si es None se formatea como 'no disponible'
    oferta = Oferta(
        id="2",
        origen="BIO",
        destino="LON",
        fecha_salida="2026-12-01",
        hora_salida="08:00",
        hora_llegada="10:00",
        fecha_llegada="2026-12-01",
        escalas=0,
        duracion="2h 00m",
        aerolinea="Vueling",
        numero_vuelo="VY1234",
        precio_total=75.00,
        moneda="EUR",
        equipaje_incluido=desc,
        piezas_equipaje=piezas,
        precio_con_equipaje=precio_con_eq,
    )
    assert oferta.precio_con_equipaje_texto == "no disponible"


def test_parseo_oferta_completo_con_precios():
    cliente = AmadeusCliente()
    oferta_raw = {
        "id": "offer_42",
        "itineraries": [
            {
                "duration": "PT1H45M",
                "segments": [
                    {
                        "departure": {"iataCode": "BIO", "at": "2026-12-01T10:30:00"},
                        "arrival": {"iataCode": "LGW", "at": "2026-12-01T11:15:00"},
                        "carrierCode": "BA",
                        "number": "2671",
                    }
                ],
            }
        ],
        "price": {
            "currency": "EUR",
            "total": "115.40",
            "base": "85.00",
        },
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

    oferta = cliente._parsear_oferta(
        raw=oferta_raw,
        carriers_dict={"BA": "British Airways"},
        origen_solicitado="BIO",
        destino_solicitado="LON",
    )

    assert oferta is not None
    assert oferta.id == "offer_42"
    assert oferta.origen == "BIO"
    assert oferta.destino == "LGW"
    assert oferta.duracion == "1h 45m"
    assert oferta.aerolinea == "British Airways"
    assert oferta.numero_vuelo == "BA2671"
    assert oferta.precio_total == 115.40
    assert oferta.moneda == "EUR"
    assert oferta.equipaje_incluido == "Incluido (1 pieza)"
    assert oferta.precio_con_equipaje == 115.40
    assert oferta.precio_con_equipaje_texto == "115.40 EUR"
    assert "google.com/travel/flights" in oferta.enlace_google
    assert "skyscanner.es" in oferta.enlace_skyscanner
