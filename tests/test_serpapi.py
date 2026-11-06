"""
Pruebas unitarias para serpapi_client.py utilizando datos simulados (mocks).
"""

from unittest.mock import patch, MagicMock
import serpapi_client


def test_extraer_codigo_aerolinea():
    assert serpapi_client._extraer_codigo_aerolinea("VY 1717", "Vueling") == "VY"
    assert serpapi_client._extraer_codigo_aerolinea("IB 1078", "Iberia") == "IB"
    assert serpapi_client._extraer_codigo_aerolinea("FR 2108", "Ryanair") == "FR"
    assert serpapi_client._extraer_codigo_aerolinea("", "Air Europa") == "UX"
    assert serpapi_client._extraer_codigo_aerolinea("", "EasyJet") == "U2"


def test_buscar_vuelos_google_parseo():
    mock_response = {
        "best_flights": [
            {
                "flights": [
                    {
                        "departure_airport": {
                            "name": "Aeropuerto de Valencia",
                            "id": "VLC",
                            "time": "2026-11-04 17:00",
                        },
                        "arrival_airport": {
                            "name": "Aeropuerto de Bilbao",
                            "id": "BIO",
                            "time": "2026-11-04 18:15",
                        },
                        "duration": 75,
                        "airline": "Vueling",
                        "flight_number": "VY 1717",
                        "extensions": ["Equipaje de mano incluido"],
                    }
                ],
                "total_duration": 75,
                "price": 179.0,
            }
        ],
        "other_flights": [],
    }

    with patch("serpapi_client.privacidad.sesion_nueva") as mock_sesion:
        mock_get = MagicMock()
        mock_get.status_code = 200
        mock_get.json.return_value = mock_response
        mock_sesion.return_value.get.return_value = mock_get

        ofertas = serpapi_client.buscar_vuelos_google(
            origen="VLC",
            destino="BIO",
            fecha_salida="2026-11-04",
            api_key="test_key",
        )

        assert len(ofertas) == 1
        o = ofertas[0]
        assert o.origen == "VLC"
        assert o.destino == "BIO"
        assert o.fecha_salida == "2026-11-04"
        assert o.hora_salida == "17:00"
        assert o.hora_llegada == "18:15"
        assert o.aerolinea == "Vueling"
        assert o.numero_vuelo == "VY 1717"
        assert o.precio_total == 179.0
        assert o.escalas == 0
        assert "vueling.com" in o.enlace_aerolinea
