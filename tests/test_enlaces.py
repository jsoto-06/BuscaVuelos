"""
Pruebas unitarias para enlaces.py: generación de enlaces de Google Flights,
Skyscanner y deep-links oficiales a motores de reserva de aerolíneas.
"""

import enlaces


def test_generar_enlace_google_flights():
    url = enlaces.generar_enlace_google_flights("BIO", "LON", "2026-12-01")
    assert "google.com/travel/flights" in url
    assert "BIO" in url
    assert "LON" in url
    assert "2026-12-01" in url


def test_generar_enlace_skyscanner():
    url = enlaces.generar_enlace_skyscanner("BIO", "LON", "2026-12-01")
    assert "skyscanner.es/transport/vuelos/bio/lon/261201/" in url


def test_generar_enlaces_aerolineas_principales():
    # Iberia
    url_ib = enlaces.generar_enlace_aerolinea("IB", "BIO", "MAD", "2026-12-01")
    assert "iberia.com" in url_ib
    assert "origin=BIO" in url_ib
    assert "destination=MAD" in url_ib
    assert "01/12/2026" in url_ib

    # Vueling
    url_vy = enlaces.generar_enlace_aerolinea("VY", "BIO", "BCN", "2026-12-01")
    assert "vueling.com" in url_vy
    assert "Origin=BIO" in url_vy
    assert "Destination=BCN" in url_vy
    assert "DepartureDate=2026-12-01" in url_vy

    # Ryanair
    url_fr = enlaces.generar_enlace_aerolinea("FR", "SDR", "LON", "2026-12-01")
    assert "ryanair.com" in url_fr
    assert "originIata=SDR" in url_fr
    assert "destinationIata=LON" in url_fr
    assert "dateOut=2026-12-01" in url_fr

    # Air Europa
    url_ux = enlaces.generar_enlace_aerolinea("UX", "MAD", "PMI", "2026-12-01")
    assert "aireuropa.com" in url_ux
    assert "origin=MAD" in url_ux
    assert "destination=PMI" in url_ux

    # EasyJet
    url_u2 = enlaces.generar_enlace_aerolinea("U2", "BIO", "LGW", "2026-12-01")
    assert "easyjet.com" in url_u2
    assert "/BIO/LGW" in url_u2

    # British Airways
    url_ba = enlaces.generar_enlace_aerolinea("BA", "BIO", "LHR", "2026-12-01")
    assert "britishairways.com" in url_ba
    assert "origin=BIO" in url_ba
    assert "destination=LHR" in url_ba


def test_obtener_enlaces_principales_aerolineas():
    enlaces_map = enlaces.obtener_enlaces_principales_aerolineas("BIO", "LON", "2026-12-01")
    assert "Iberia (IB)" in enlaces_map
    assert "Vueling (VY)" in enlaces_map
    assert "Ryanair (FR)" in enlaces_map
    assert "British Airways (BA)" in enlaces_map
    assert len(enlaces_map) >= 8
