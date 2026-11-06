"""
Panel Visual Interactivo (Streamlit) para Vuelos Baratos.
Interfaz gráfica moderna para buscar ofertas en tiempo real con Google Flights (vía SerpApi)
o Amadeus for Developers, explorar calendarios de precios, acceder a webs oficiales de aerolíneas
y gestionar alertas de precio.
"""

from datetime import date, timedelta
import pandas as pd
import streamlit as st

import config
import aeropuertos
import filtros
import enlaces
import demo
import serpapi_client
import calendario as modulo_calendario
import alertas as modulo_alertas
import historial as modulo_historial
from amadeus_api import AmadeusCliente, AmadeusError
from modelos import Busqueda, Oferta

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Vuelos Baratos - Buscador Inteligente",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos visuales personalizados
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #4B5563;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .card-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #0F172A;
    }
    .price-tag {
        font-size: 1.6rem;
        font-weight: 700;
        color: #059669;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: #E0E7FF;
        color: #3730A3;
    }
    .badge-google {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: #D1FAE5;
        color: #065F46;
    }
    .badge-demo {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: #FEF3C7;
        color: #92400E;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Lista de aeropuertos comunes para autocompletado amigable
OPCIONES_AEROPUERTOS = [
    ("BIO - Bilbao", "BIO"),
    ("VLC - Valencia", "VLC"),
    ("MAD - Madrid-Barajas", "MAD"),
    ("BCN - Barcelona-El Prat", "BCN"),
    ("VIT - Vitoria", "VIT"),
    ("SDR - Santander", "SDR"),
    ("BIQ - Biarritz", "BIQ"),
    ("AGP - Málaga", "AGP"),
    ("SVQ - Sevilla", "SVQ"),
    ("ALC - Alicante", "ALC"),
    ("PMI - Palma de Mallorca", "PMI"),
    ("IBZ - Ibiza", "IBZ"),
    ("SCQ - Santiago de Compostela", "SCQ"),
    ("LON - Londres (Todos)", "LON"),
    ("LHR - Londres Heathrow", "LHR"),
    ("LGW - Londres Gatwick", "LGW"),
    ("STN - Londres Stansted", "STN"),
    ("PAR - París (Todos)", "PAR"),
    ("CDG - París Charles de Gaulle", "CDG"),
    ("ORY - París Orly", "ORY"),
    ("BVA - París Beauvais", "BVA"),
    ("ROM - Roma (Todos)", "ROM"),
    ("FCO - Roma Fiumicino", "FCO"),
    ("BER - Berlín", "BER"),
    ("AMS - Ámsterdam", "AMS"),
    ("FRA - Fráncfort", "FRA"),
    ("MUC - Múnich", "MUC"),
    ("BRU - Bruselas", "BRU"),
    ("LIS - Lisboa", "LIS"),
    ("OPO - Oporto", "OPO"),
    ("MXP - Milán Malpensa", "MXP"),
    ("BGY - Milán Bérgamo", "BGY"),
    ("VIE - Viena", "VIE"),
    ("DUB - Dublín", "DUB"),
    ("PRG - Praga", "PRG"),
    ("WAW - Varsovia", "WAW"),
]


def _extraer_codigo_iata(texto_seleccionado: str) -> str:
    """Extrae el código IATA del formato 'XXX - Nombre' o lo devuelve limpio."""
    if " - " in texto_seleccionado:
        return texto_seleccionado.split(" - ")[0].strip().upper()
    return texto_seleccionado.strip().upper()


# -------------------------------------------------------------
# Barra lateral (Sidebar)
# -------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500&auto=format&fit=crop&q=60",
        use_container_width=True,
    )
    st.title("⚙️ Motores y Claves")

    tiene_serpapi = bool(config.SERPAPI_API_KEY)
    tiene_amadeus = config.validar_credenciales(salir_si_invalido=False)

    if tiene_serpapi:
        st.success("🟢 Google Flights (SerpApi): Activo")
    else:
        st.info("⚪ SerpApi: No configurado")

    if tiene_amadeus:
        st.success("🟢 Amadeus API: Conectada")
    else:
        st.caption("⚪ Amadeus API: Sin claves")

    # Selección de motor
    opciones_motor = []
    if tiene_serpapi:
        opciones_motor.append("Google Flights (SerpApi) - En Vivo 🟢")
    if tiene_amadeus:
        opciones_motor.append("Amadeus API")
    opciones_motor.append("Modo Demostración (Simulado)")

    motor_seleccionado = st.radio(
        "Motor de búsqueda preferido:",
        options=opciones_motor,
        index=0,
    )

    # Configuración de claves
    with st.expander("🔑 Gestionar Claves de API"):
        st.markdown("**Google Flights (SerpApi):**")
        s_key = st.text_input("SERPAPI_API_KEY:", value=config.SERPAPI_API_KEY, type="password")
        if st.button("💾 Guardar Clave SerpApi", key="save_serp"):
            if s_key.strip():
                config.guardar_serpapi_key_env(s_key.strip())
                st.success("Clave SerpApi actualizada.")
                st.rerun()

        st.markdown("---")
        st.markdown("**Amadeus for Developers:**")
        c_id = st.text_input("AMADEUS_CLIENT_ID:", value=config.AMADEUS_CLIENT_ID, type="password")
        c_sec = st.text_input("AMADEUS_CLIENT_SECRET:", value=config.AMADEUS_CLIENT_SECRET, type="password")
        c_env = st.selectbox("Entorno Amadeus:", options=["test", "prod"], index=0 if config.AMADEUS_ENV == "test" else 1)

        if st.button("💾 Guardar Claves Amadeus", key="save_amadeus"):
            if c_id.strip() and c_sec.strip():
                config.guardar_credenciales_env(c_id, c_sec, c_env)
                st.success("Claves Amadeus actualizadas.")
                st.rerun()

    st.markdown("---")
    st.subheader("🛡️ Privacidad Garantizada")
    st.caption(
        "• Sesiones efímeras sin cookies persistentes\n"
        "• Almacenamiento 100% en tu máquina local (`datos/`)\n"
        "• Cero rastreadores ni analíticas externas\n"
        "• Sin pasarelas de pago ni cobros"
    )

    if st.button("🗑️ Vaciar Historial Local"):
        modulo_historial.borrar_historial(pedir_confirmacion=False)
        st.success("Historial eliminado.")


# -------------------------------------------------------------
# Cabecera principal
# -------------------------------------------------------------
st.markdown('<div class="main-title">✈️ Vuelos Baratos</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Compara ofertas reales en Google Flights y Amadeus, explora calendarios de tarifas y reserva en las webs oficiales de las aerolíneas.</div>',
    unsafe_allow_html=True,
)

tab_buscar, tab_aerolineas, tab_calendario, tab_alertas, tab_historial = st.tabs([
    "🔍 Buscar Vuelos",
    "🌐 Webs de Aerolíneas (Directo)",
    "📅 Calendario de Precios",
    "🔔 Alertas de Precio",
    "📜 Historial",
])


# -------------------------------------------------------------
# TAB 1: Buscar Vuelos (Google Flights / Amadeus / Demo)
# -------------------------------------------------------------
with tab_buscar:
    st.subheader("Búsqueda de Vuelos en Tiempo Real")
    st.caption(f"Utilizando motor: **{motor_seleccionado}**")

    hoy = date.today()
    fecha_defecto = hoy + timedelta(days=12)

    col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.2, 1.2])

    with col1:
        origen_input = st.selectbox(
            "Aeropuerto de Salida:",
            options=[opt[0] for opt in OPCIONES_AEROPUERTOS],
            index=1,  # VLC - Valencia
            key="buscar_origen",
        )
        origen_codigo = _extraer_codigo_iata(origen_input)

    with col2:
        destino_input = st.selectbox(
            "Aeropuerto de Destino:",
            options=[opt[0] for opt in OPCIONES_AEROPUERTOS],
            index=0,  # BIO - Bilbao
            key="buscar_destino",
        )
        destino_codigo = _extraer_codigo_iata(destino_input)

    with col3:
        tipo_fecha = st.radio(
            "Modalidad de fecha:",
            options=["Día exacto", "Rango de días"],
            horizontal=True,
        )

    with col4:
        adultos = st.number_input("Adultos:", min_value=1, max_value=9, value=1, step=1, key="buscar_adultos")

    col_f1, col_f2, col_opc = st.columns([1.5, 1.5, 2])
    with col_f1:
        fecha_desde = st.date_input("Fecha de salida:", value=fecha_defecto, min_value=hoy, key="buscar_fecha_desde")

    with col_f2:
        if tipo_fecha == "Rango de días":
            fecha_hasta = st.date_input(
                "Fecha tope (hasta):",
                value=fecha_defecto + timedelta(days=2),
                min_value=fecha_desde,
                key="buscar_fecha_hasta",
            )
        else:
            fecha_hasta = None

    with col_opc:
        c_alt, c_dir, c_prec = st.columns([1, 1, 1.2])
        with c_alt:
            usar_alternativos = st.checkbox("Alternativos cercanos", value=False, key="buscar_alt")
        with c_dir:
            solo_directos = st.checkbox("Solo directos", value=False, key="buscar_dir")
        with c_prec:
            filtro_max = st.number_input("Precio Máx (€):", min_value=0.0, value=0.0, step=10.0, key="buscar_max")

    max_precio_val = filtro_max if filtro_max > 0 else None

    btn_buscar = st.button("🚀 Buscar Ofertas", type="primary", use_container_width=True)

    if btn_buscar:
        f_d, f_h = filtros.validar_rango_fechas(
            fecha_desde.isoformat(),
            fecha_hasta.isoformat() if fecha_hasta else None,
        )
        dias = filtros.generar_dias_ventana(f_d, f_h if f_h else f_d)

        # 1. MOTOR: Google Flights vía SerpApi
        if "Google Flights" in motor_seleccionado:
            with st.spinner("Consultando tarifas en vivo en Google Flights (vía SerpApi)..."):
                try:
                    origenes = aeropuertos.obtener_origenes(
                        origen_usuario=origen_codigo,
                        incluir_alternativos=usar_alternativos,
                    )
                    todas_ofertas = []
                    for orig in origenes:
                        for d in dias:
                            ofertas_dia = serpapi_client.buscar_vuelos_google(
                                origen=orig,
                                destino=destino_codigo,
                                fecha_salida=d,
                                adultos=int(adultos),
                                moneda=config.MONEDA,
                                directos=solo_directos,
                                max_precio=max_precio_val,
                            )
                            todas_ofertas.extend(ofertas_dia)

                    ofertas_filtradas = filtros.aplicar_filtros(
                        todas_ofertas,
                        max_precio=max_precio_val,
                        solo_directos=solo_directos,
                    )

                    busq = Busqueda(
                        origen=origen_codigo,
                        destinos=[destino_codigo],
                        fecha_desde=fecha_desde.isoformat(),
                        fecha_hasta=fecha_hasta.isoformat() if fecha_hasta else None,
                        alternativos=usar_alternativos,
                        directos=solo_directos,
                        max_precio=max_precio_val,
                        adultos=int(adultos),
                    )
                    modulo_historial.registrar_busqueda(busq, len(ofertas_filtradas))
                    st.session_state["ultimas_ofertas"] = ofertas_filtradas
                except Exception as e:
                    st.error(f"Error consultando Google Flights: {e}")

        # 2. MOTOR: Amadeus API
        elif "Amadeus" in motor_seleccionado:
            if not tiene_amadeus:
                st.error("Introduce tus claves de Amadeus en la barra lateral para usar este motor.")
            else:
                with st.spinner("Consultando la API oficial de Amadeus..."):
                    try:
                        origenes = aeropuertos.obtener_origenes(
                            origen_usuario=origen_codigo,
                            incluir_alternativos=usar_alternativos,
                        )
                        cliente = AmadeusCliente()
                        todas_ofertas = []
                        for orig in origenes:
                            for d in dias:
                                ofertas_dia = cliente.buscar_vuelos(
                                    origen=orig,
                                    destino=destino_codigo,
                                    fecha_salida=d,
                                    adultos=int(adultos),
                                    moneda=config.MONEDA,
                                    directos=solo_directos,
                                    max_precio=max_precio_val,
                                )
                                todas_ofertas.extend(ofertas_dia)

                        ofertas_filtradas = filtros.aplicar_filtros(
                            todas_ofertas,
                            max_precio=max_precio_val,
                            solo_directos=solo_directos,
                        )
                        st.session_state["ultimas_ofertas"] = ofertas_filtradas
                    except Exception as e:
                        st.error(f"Error consultando Amadeus: {e}")

        # 3. MOTOR: Demostración
        else:
            with st.spinner("Generando ofertas de muestra..."):
                ofertas_raw = demo.generar_ofertas_demo(
                    origen=origen_codigo,
                    destino=destino_codigo,
                    fechas=dias,
                    adultos=int(adultos),
                )
                ofertas_filtradas = filtros.aplicar_filtros(
                    ofertas_raw,
                    max_precio=max_precio_val,
                    solo_directos=solo_directos,
                )
                st.session_state["ultimas_ofertas"] = ofertas_filtradas

    # Mostrar resultados
    if "ultimas_ofertas" in st.session_state:
        ofertas = st.session_state["ultimas_ofertas"]

        if not ofertas:
            st.warning("No se encontraron vuelos que coincidan con los criterios seleccionados.")
        else:
            precio_min = min(o.precio_total for o in ofertas)
            precio_max = max(o.precio_total for o in ofertas)
            media = sum(o.precio_total for o in ofertas) / len(ofertas)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Vuelos encontrados", len(ofertas))
            m2.metric("Mejor precio", f"{precio_min:.2f} {config.MONEDA}")
            m3.metric("Precio promedio", f"{media:.2f} {config.MONEDA}")
            m4.metric("Precio máximo", f"{precio_max:.2f} {config.MONEDA}")

            st.markdown("### 📋 Ofertas Disponibles en Vivo")

            datos_csv = []
            for idx, o in enumerate(ofertas, 1):
                datos_csv.append({
                    "Ranking": idx,
                    "Origen": o.origen,
                    "Destino": o.destino,
                    "Fecha": o.fecha_salida,
                    "Salida": o.hora_salida,
                    "Llegada": o.hora_llegada,
                    "Escalas": "Directo" if o.escalas == 0 else f"{o.escalas} escala(s)",
                    "Duración": o.duracion,
                    "Aerolínea": o.aerolinea,
                    "Precio (€)": o.precio_total,
                    "Equipaje": o.equipaje_incluido,
                    "Web Aerolínea": o.enlace_aerolinea,
                    "Google Flights": o.enlace_google,
                    "Skyscanner": o.enlace_skyscanner,
                })
            df_ofertas = pd.DataFrame(datos_csv)
            csv_bytes = df_ofertas.to_csv(index=False).encode("utf-8-sig")

            st.download_button(
                label="📥 Descargar Resultados en CSV",
                data=csv_bytes,
                file_name=f"vuelos_{origen_codigo}_{destino_codigo}_{fecha_desde}.csv",
                mime="text/csv",
            )

            for idx, o in enumerate(ofertas, 1):
                escalas_txt = "✈️ Directo" if o.escalas == 0 else f"🔄 {o.escalas} escala(s)"
                eq_color = "🟢" if "Incluido" in o.equipaje_incluido or "incl." in o.equipaje_incluido else "⚪"

                if "[DEMO]" in o.aerolinea:
                    badge_html = '<span class="badge-demo">Demo</span>'
                elif "google" in o.id:
                    badge_html = '<span class="badge-google">En Vivo (Google Flights)</span>'
                else:
                    badge_html = f'<span class="badge">Opción #{idx}</span>'

                with st.container():
                    st.markdown(
                        f"""
                        <div class="card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    {badge_html}
                                    <span class="card-title" style="margin-left: 10px;">
                                        {o.origen} ➔ {o.destino} | {o.aerolinea} ({o.numero_vuelo})
                                    </span>
                                </div>
                                <div class="price-tag">{o.precio_total:.2f} {o.moneda}</div>
                            </div>
                            <div style="margin-top: 8px; color: #475569; font-size: 0.95rem;">
                                📅 <b>Fecha:</b> {o.fecha_salida} &nbsp;|&nbsp; 
                                ⏰ <b>Horario:</b> {o.hora_salida} - {o.hora_llegada} &nbsp;|&nbsp; 
                                ⏳ <b>Duración:</b> {o.duracion} &nbsp;|&nbsp; 
                                {escalas_txt} &nbsp;|&nbsp; 
                                {eq_color} <b>Equipaje:</b> {o.equipaje_incluido}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    b1, b2, b3 = st.columns([1.5, 1, 1])
                    if o.enlace_aerolinea:
                        b1.link_button(
                            f"🌐 Web Oficial {o.aerolinea.replace(' [DEMO]', '')}",
                            o.enlace_aerolinea,
                            use_container_width=True,
                        )
                    b2.link_button(
                        "🔎 Google Flights",
                        o.enlace_google,
                        use_container_width=True,
                    )
                    b3.link_button(
                        "🔎 Skyscanner",
                        o.enlace_skyscanner,
                        use_container_width=True,
                    )
                    st.write("")


# -------------------------------------------------------------
# TAB 2: Webs de Aerolíneas (Directo sin API)
# -------------------------------------------------------------
with tab_aerolineas:
    st.subheader("🌐 Búsqueda Directa en Páginas Oficiales de Aerolíneas")
    st.write(
        "Abre el motor de reservas oficial de cada compañía aérea con tu origen, destino y fecha ya precargados. "
        "Consulta las plazas en vivo directamente en cada aerolínea."
    )

    ca1, ca2, ca3, ca4 = st.columns([1.5, 1.5, 1.2, 1])

    with ca1:
        a_orig_sel = st.selectbox(
            "Origen:",
            options=[opt[0] for opt in OPCIONES_AEROPUERTOS],
            index=1,  # VLC - Valencia
            key="aero_origen",
        )
        a_orig = _extraer_codigo_iata(a_orig_sel)

    with ca2:
        a_dest_sel = st.selectbox(
            "Destino:",
            options=[opt[0] for opt in OPCIONES_AEROPUERTOS],
            index=0,  # BIO - Bilbao
            key="aero_destino",
        )
        a_dest = _extraer_codigo_iata(a_dest_sel)

    with ca3:
        a_fecha = st.date_input(
            "Fecha del vuelo:",
            value=fecha_defecto,
            min_value=hoy,
            key="aero_fecha",
        )

    with ca4:
        a_adultos = st.number_input(
            "Pasajeros:", min_value=1, max_value=9, value=1, step=1, key="aero_adultos"
        )

    enlaces_aerolineas = enlaces.obtener_enlaces_principales_aerolineas(
        origen=a_orig,
        destino=a_dest,
        fecha_salida=a_fecha.isoformat(),
        adultos=int(a_adultos),
    )

    st.markdown("---")
    st.markdown(
        f"#### ✈️ Aerolíneas recomendadas para la ruta **{a_orig} ({aeropuertos.nombre_aeropuerto(a_orig)}) ➔ "
        f"{a_dest} ({aeropuertos.nombre_aeropuerto(a_dest)})** el **{a_fecha.strftime('%d/%m/%Y')}**:"
    )

    col_izq, col_der = st.columns(2)
    items_aero = list(enlaces_aerolineas.items())

    for idx, (nombre, url) in enumerate(items_aero):
        columna = col_izq if idx % 2 == 0 else col_der
        with columna:
            st.markdown(
                f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="card-title">✈️ {nombre}</span>
                    </div>
                    <p style="color: #64748B; font-size: 0.85rem; margin-top: 4px;">
                        Consulta plazas, tarifas de equipaje y asientos oficiales sin intermediarios ni comisiones.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.link_button(
                f"🔗 Buscar directamente en {nombre}",
                url,
                use_container_width=True,
            )
            st.write("")


# -------------------------------------------------------------
# TAB 3: Calendario de Precios
# -------------------------------------------------------------
with tab_calendario:
    st.subheader("📅 Explorador de Precios por Fechas (Gráfico Interactivo)")

    cc1, cc2, cc3, cc4 = st.columns([1.5, 1.5, 1.2, 1.2])

    with cc1:
        c_orig_sel = st.selectbox(
            "Origen:",
            options=[opt[0] for opt in OPCIONES_AEROPUERTOS],
            index=1,  # VLC
            key="cal_origen",
        )
        c_orig = _extraer_codigo_iata(c_orig_sel)

    with cc2:
        c_dest_sel = st.selectbox(
            "Destino:",
            options=[opt[0] for opt in OPCIONES_AEROPUERTOS],
            index=0,  # BIO
            key="cal_destino",
        )
        c_dest = _extraer_codigo_iata(c_dest_sel)

    with cc3:
        c_desde = st.date_input(
            "Desde el día:",
            value=fecha_defecto,
            min_value=hoy,
            key="cal_desde",
        )

    with cc4:
        c_hasta = st.date_input(
            "Hasta el día:",
            value=fecha_defecto + timedelta(days=6),
            min_value=c_desde,
            key="cal_hasta",
        )

    if st.button("📊 Generar Gráfico de Precios", type="primary", use_container_width=True):
        f_d, f_h = filtros.validar_rango_fechas(c_desde.isoformat(), c_hasta.isoformat())
        dias_cal = filtros.generar_dias_ventana(f_d, f_h)

        if "Google Flights" in motor_seleccionado:
            with st.spinner("Analizando tarifas reales en Google Flights día a día..."):
                st.session_state["precios_calendario"] = serpapi_client.consultar_precios_ventana_google(
                    origen=c_orig,
                    destino=c_dest,
                    fechas=dias_cal,
                    moneda=config.MONEDA,
                )
        elif "Amadeus" in motor_seleccionado:
            if not tiene_amadeus:
                st.error("Configura tus claves de Amadeus en la barra lateral para continuar.")
            else:
                with st.spinner("Analizando tarifas en Amadeus día a día..."):
                    try:
                        cliente = AmadeusCliente()
                        st.session_state["precios_calendario"] = modulo_calendario.consultar_precios_ventana(
                            cliente=cliente,
                            origen=c_orig,
                            destino=c_dest,
                            f_desde=c_desde,
                            f_hasta=c_hasta,
                        )
                    except Exception as e:
                        st.error(f"Error consultando calendario: {e}")
        else:
            st.session_state["precios_calendario"] = demo.generar_precios_calendario_demo(
                c_orig, c_dest, dias_cal
            )

    if "precios_calendario" in st.session_state:
        precios_dict = st.session_state["precios_calendario"]
        mejor_fecha, mejor_precio = modulo_calendario.encontrar_fecha_mas_barata(precios_dict)

        if mejor_fecha and mejor_precio:
            st.success(f"🌟 **Fecha más económica:** {mejor_fecha} por **{mejor_precio:.2f} {config.MONEDA}**")

            filas_grafico = []
            for d, p in sorted(precios_dict.items()):
                filas_grafico.append({
                    "Fecha": d,
                    "Precio (€)": p if p is not None else 0,
                })
            df_grafico = pd.DataFrame(filas_grafico)

            st.bar_chart(
                data=df_grafico,
                x="Fecha",
                y="Precio (€)",
                color="#2563EB",
                use_container_width=True,
            )

            enlace_g_opt, enlace_sky_opt = enlaces.generar_enlaces(c_orig, c_dest, mejor_fecha)
            col_b1, col_b2 = st.columns(2)
            col_b1.link_button(
                f"🔎 Ver fecha más barata ({mejor_fecha}) en Google Flights",
                enlace_g_opt,
                use_container_width=True,
            )
            col_b2.link_button(
                f"🔎 Ver fecha más barata ({mejor_fecha}) en Skyscanner",
                enlace_sky_opt,
                use_container_width=True,
            )
        else:
            st.warning("No se encontraron tarifas disponibles en el rango de fechas seleccionado.")


# -------------------------------------------------------------
# TAB 4: Alertas de Precio
# -------------------------------------------------------------
with tab_alertas:
    st.subheader("🔔 Vigilancia Automática y Alertas de Precio")
    st.write(
        "Configura alertas persistentes. Cuando una oferta baje de tu precio máximo, "
        "el sistema emitirá un aviso visual en tu escritorio sin repetir ofertas ya vistas."
    )

    with st.expander("➕ Crear Nueva Alerta de Precio", expanded=True):
        al_c1, al_c2, al_c3, al_c4, al_c5 = st.columns([1.5, 1.5, 1.2, 1.2, 1.2])

        with al_c1:
            al_orig_sel = st.selectbox(
                "Origen:",
                options=[opt[0] for opt in OPCIONES_AEROPUERTOS],
                index=1,
                key="nueva_al_orig",
            )
            al_orig = _extraer_codigo_iata(al_orig_sel)

        with al_c2:
            al_dest_sel = st.selectbox(
                "Destino:",
                options=[opt[0] for opt in OPCIONES_AEROPUERTOS],
                index=0,
                key="nueva_al_dest",
            )
            al_dest = _extraer_codigo_iata(al_dest_sel)

        with al_c3:
            al_desde = st.date_input(
                "Fecha desde:",
                value=fecha_defecto,
                min_value=hoy,
                key="nueva_al_desde",
            )

        with al_c4:
            al_hasta = st.date_input(
                "Fecha hasta:",
                value=fecha_defecto + timedelta(days=5),
                min_value=al_desde,
                key="nueva_al_hasta",
            )

        with al_c5:
            al_max = st.number_input(
                "Precio Máximo (€):",
                min_value=10.0,
                value=80.0,
                step=10.0,
                key="nueva_al_max",
            )

        if st.button("Guardar Alerta", type="primary"):
            try:
                nueva_al = modulo_alertas.crear_alerta(
                    origen=al_orig,
                    destino=al_dest,
                    fecha_desde=al_desde.isoformat(),
                    fecha_hasta=al_hasta.isoformat(),
                    max_precio=float(al_max),
                )
                st.success(f"Alerta creada con éxito [ID: {nueva_al.id}].")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar alerta: {e}")

    alertas_actuales = modulo_alertas.cargar_alertas()
    st.markdown("#### Alertas Registradas Actualmente")

    if not alertas_actuales:
        st.info("No tienes alertas activas en este momento.")
    else:
        for al in alertas_actuales:
            col_info, col_del = st.columns([5, 1])
            with col_info:
                st.markdown(
                    f"""
                    <div style="background-color: #F1F5F9; border-left: 4px solid #3B82F6; padding: 10px 14px; border-radius: 4px; margin-bottom: 8px;">
                        <b>[{al.id}] {al.origen} ➔ {al.destino}</b> &nbsp;|&nbsp; 
                        📅 {al.fecha_desde} hasta {al.fecha_hasta} &nbsp;|&nbsp; 
                        💰 Máx: <b>{al.max_precio:.2f} {config.MONEDA}</b> &nbsp;|&nbsp; 
                        🔔 Avisos enviados: {len(al.ofertas_notificadas)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_del:
                if st.button("🗑️ Borrar", key=f"del_{al.id}", use_container_width=True):
                    modulo_alertas.borrar_alerta(al.id)
                    st.toast(f"Alerta {al.id} eliminada")
                    st.rerun()


# -------------------------------------------------------------
# TAB 5: Historial
# -------------------------------------------------------------
with tab_historial:
    st.subheader("📜 Historial de Búsquedas Recientes")
    st.caption("Guardado 100% en tu máquina local. Ningún dato personal sale de tu equipo.")

    entradas_historial = modulo_historial.cargar_historial()
    if not entradas_historial:
        st.info("El historial de búsquedas está vacío.")
    else:
        filas_h = []
        for h in reversed(entradas_historial):
            filas_h.append({
                "Fecha y Hora": h.get("fecha_hora", "").replace("T", " "),
                "Origen": h.get("origen"),
                "Destino(s)": ", ".join(h.get("destinos", [])),
                "Salida": h.get("fecha_desde"),
                "Hasta": h.get("fecha_hasta") or "-",
                "Resultados": h.get("resultados_encontrados", 0),
            })
        st.dataframe(pd.DataFrame(filas_h), use_container_width=True)
