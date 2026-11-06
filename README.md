# ✈️ Vuelos Baratos | Cheap Flights Engine

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?logo=python" alt="Python Versions">
  <img src="https://img.shields.io/badge/Framework-Streamlit-FF4B4B?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/APIs-Amadeus%20%7C%20Google%20Flights%20(SerpApi)-green" alt="APIs">
  <img src="https://img.shields.io/badge/Tests-26%20Passed-brightgreen?logo=pytest" alt="Pytest">
  <img src="https://img.shields.io/badge/Privacy-100%25%20Local%20%26%20Stateless-success" alt="Privacy">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

---

## 🌐 Language / Idioma
- [🇪🇸 Español (Castellano)](#-español-castellano)
- [🇬🇧 English](#-english)

---

# 🇪🇸 Español (Castellano)

Buscador inteligente de vuelos económicos que combina la API oficial de **Amadeus for Developers (Self-Service)**, **Google Flights en tiempo real (vía SerpApi)** y acceso directo a los motores de reservas oficiales de las principales aerolíneas. Diseñado bajo el principio estricto de **privacidad por diseño**, almacena todos tus datos localmente, no utiliza cookies persistentes ni telemetría y te devuelve enlaces directos para comparar y reservar manualmente con total seguridad.

---

### 📌 Tabla de Contenidos (Español)
1. [Características Principales](#-características-principales)
2. [Arquitectura del Proyecto](#-arquitectura-del-proyecto)
3. [Requisitos del Sistema](#-requisitos-del-sistema)
4. [Instalación Paso a Paso](#-instalación-paso-a-paso)
5. [Configuración de Claves (.env)](#-configuración-de-claves-env)
6. [Interfaz Web Interactiva (Streamlit)](#️-interfaz-web-interactiva-streamlit)
7. [Guía de Comandos CLI (`main.py`)](#-guía-de-comandos-cli-mainpy)
8. [Integración con Google Chrome DevTools / Brave MCP](#-integración-con-chrome-devtools--brave-mcp)
9. [Automatización y Tareas Programadas](#-automatización-y-tareas-programadas)
10. [Garantías de Privacidad](#-garantías-de-privacidad)
11. [Pruebas Unitarias (`pytest`)](#-pruebas-unitarias-pytest)
12. [Licencia](#-licencia)

---

### 🚀 Características Principales

- **Múltiples Motores de Búsqueda:**
  - **Google Flights en Vivo (SerpApi):** Precios reales y vuelos actualizados de todas las compañías (Iberia, Vueling, Ryanair, Air Europa, etc.).
  - **Amadeus for Developers API:** Conexión con los endpoints oficiales `v2/shopping/flight-offers` y `v1/shopping/flight-dates`.
  - **Modo Demostración Offline:** Permite probar toda la suite y la interfaz sin consumir llamadas de API.
- **Búsqueda Directa en Webs de Aerolíneas:** Generador de enlaces automáticos precargados con tu ruta, fecha y pasajeros para más de 18 aerolíneas (Iberia, Vueling, Ryanair, Volotea, EasyJet, British Airways, Air France, Lufthansa, etc.).
- **Privacidad Radical:** Sesiones HTTP efímeras en cada petición, sin persistencia de cookies, User-Agent neutro, sin telemetría, soporte para proxy HTTP/SOCKS y almacenamiento 100% local en `datos/`.
- **Detección y Desglose de Equipaje:** Inspección de franquicia de equipaje de bodega (`includedCheckedBags`) y suplementos desglosados en Amadeus.
- **Panel Visual Completo:** Aplicación web con Streamlit con filtros interactivos, selector de fechas, gráficos de precios, exportación a CSV y gestión de alertas.
- **Sistema de Alertas y Vigilancia:** Monitorización automática en segundo plano con avisos en consola y notificaciones de escritorio cuando el precio baja del umbral deseado.
- **Integración con Chrome DevTools / Brave MCP:** Permite a agentes de IA navegar, auditar y ejecutar búsquedas en la web mediante el Model Context Protocol.

---

### 📁 Arquitectura del Proyecto

```text
vuelos_baratos/
├── main.py                 # CLI principal con subcomandos (buscar, aerolineas, calendario, etc.)
├── app.py                  # Interfaz gráfica web interactiva con Streamlit
├── iniciar_web.bat         # Lanzador rápido en 1 clic para Windows
├── config.py               # Carga y validación de variables de entorno (.env)
├── amadeus_api.py          # Cliente HTTP para la API de Amadeus (OAuth en memoria, búsqueda)
├── serpapi_client.py       # Cliente para Google Flights Engine vía SerpApi en tiempo real
├── demo.py                 # Generador de datos y ofertas de demostración offline
├── enlaces.py              # Generación de deep-links (Google Flights, Skyscanner, webs oficiales)
├── privacidad.py           # Gestión de sesiones efímeras, User-Agent neutro y rate limiting
├── modelos.py              # Dataclasses tipadas (Oferta, Busqueda, Alerta)
├── filtros.py              # Lógica de filtrado (precio máximo, directos, deduplicación)
├── calendario.py           # Construcción de calendarios de tarifas por fecha
├── aeropuertos.py          # Catálogo IATA y gestión de aeropuertos alternativos
├── equipaje.py             # Parser de equipaje de mano y facturado
├── alertas.py              # Gestión y persistencia de alertas en datos/alertas.json
├── vigilancia.py           # Monitorización periódica o en modo una sola ejecución
├── historial.py            # Historial local sin datos privados en datos/historial.json
├── salida.py               # Tablas en terminal, exportación a CSV y formateo
├── notificaciones.py       # Notificaciones por consola y escritorio del sistema (plyer)
├── tests/                  # Suite completa de 26 pruebas unitarias con mocks
│   ├── test_alertas.py
│   ├── test_calendario.py
│   ├── test_enlaces.py
│   ├── test_equipaje.py
│   ├── test_filtros.py
│   ├── test_precios.py
│   └── test_serpapi.py
├── .env.example            # Plantilla de variables de entorno
├── .gitignore              # Protección estricta de credenciales y datos locales
├── requirements.txt        # Dependencias de producción y pruebas
└── README.md               # Documentación bilingüe detallada
```

---

### 💻 Requisitos del Sistema

- **Python:** Versión 3.10 o superior (compatible con Python 3.10, 3.11, 3.12, 3.13 y 3.14).
- Conexión a Internet para consultas en vivo.
- Sistema Operativo: Windows, macOS o Linux.

---

### 🛠 Instalación Paso a Paso

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/jsoto-06/BuscaVuelos.git
   cd BuscaVuelos
   ```

2. **Crear y activar un entorno virtual:**
   - **En Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **En Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

---

### 🔑 Configuración de Claves (.env)

Copia el archivo `.env.example` a `.env`:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Edita `.env` con tus credenciales:

```ini
# Credenciales de Amadeus (Gratis en https://developers.amadeus.com/)
AMADEUS_CLIENT_ID=tu_client_id_aqui
AMADEUS_CLIENT_SECRET=tu_client_secret_aqui
AMADEUS_ENV=test

# Clave de SerpApi para Google Flights en vivo (Gratis en https://serpapi.com/)
SERPAPI_API_KEY=tu_serpapi_key_aqui

# Parámetros generales
MONEDA=EUR
ORIGEN_POR_DEFECTO=BIO
ALTERNATIVOS_ORIGEN=VIT,SDR,BIQ
MIN_SEGUNDOS_ENTRE_PETICIONES=2
PROXY_URL=
INTERVALO_VIGILANCIA_HORAS=6
NOTIFICAR_SISTEMA=true
```

> [!NOTE]
> Si no configuras las claves, la aplicación web y la CLI activan automáticamente el **Modo Demostración** o el acceso directo a las **Webs de Aerolíneas**, sin lanzar errores ni excepciones.

---

### 🖥️ Interfaz Web Interactiva (Streamlit)

Para abrir el panel visual en tu navegador:

```bash
# Opción 1: Mediante la CLI
python main.py web

# Opción 2: Directamente con Streamlit
streamlit run app.py

# Opción 3 (Windows): Doble clic en iniciar_web.bat
```

La aplicación web estará disponible en: **`http://localhost:8501`**

**Pestañas incluidas:**
1. **🔍 Buscar Vuelos:** Comparativa de tarifas en vivo con métricas, autocompletado y descarga en CSV.
2. **🌐 Webs de Aerolíneas:** Tarjetas directas para reservar en Iberia, Vueling, Ryanair, Volotea, etc.
3. **📅 Calendario de Precios:** Gráficos de barras interactivos con la evolución de precios por día.
4. **🔔 Alertas de Precio:** Alta y gestión de rutas vigiladas con umbral máximo.
5. **📜 Historial:** Registro de búsquedas con opción de vaciado en 1 clic.

---

### 📖 Guía de Comandos CLI (`main.py`)

Todos los comandos cuentan con ayuda detallada en español con `--help`:

```bash
python main.py --help
```

#### 1. Búsqueda de Vuelos (`buscar`)
```bash
# Búsqueda simple
python main.py buscar --destinos LON --desde 2026-12-01

# Búsqueda en ventana de fechas con precio máximo y aeropuertos alternativos
python main.py buscar --destinos LON,PAR --desde 2026-12-01 --hasta 2026-12-05 --alternativos --directos --max-precio 150

# Abrir las mejores ofertas en el navegador
python main.py buscar --destinos LON --desde 2026-12-01 --abrir 2 --abrir-aerolinea 2
```

#### 2. Enlaces Directos a Aerolíneas (`aerolineas`)
```bash
python main.py aerolineas --destinos LON --desde 2026-12-01 --abrir 3
```

#### 3. Calendario de Tarifas (`calendario`)
```bash
python main.py calendario --destinos LON --desde 2026-12-01 --hasta 2026-12-20
```

#### 4. Gestión de Alertas y Vigilancia (`alerta` y `vigilar`)
```bash
# Crear alerta
python main.py alerta añadir --origen BIO --destino LON --desde 2026-12-01 --hasta 2026-12-05 --max-precio 120

# Listar y borrar alertas
python main.py alerta listar
python main.py alerta borrar ID_DE_ALERTA

# Modo vigilancia (en bucle o una sola vez para programadores de tareas)
python main.py vigilar
python main.py vigilar --una-vez
```

#### 5. Historial Local (`historial`)
```bash
python main.py historial ver
python main.py historial borrar
```

---

### 🤖 Integración con Chrome DevTools / Brave MCP

El proyecto está preparado para ser navegado y controlado por agentes de IA usando el protocolo **Model Context Protocol (MCP)** sobre Chrome o Brave:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest",
        "--executablePath=C:\\Users\\Jony\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
      ]
    }
  }
}
```

Permite inspeccionar el DOM, rellenar formularios, comprobar alertas, tomar snapshots y verificar tarifas automáticamente.

---

### ⏰ Automatización y Tareas Programadas

El comando `python main.py vigilar --una-vez` está optimizado para programadores del sistema operativo sin dejar procesos consumiendo memoria.

- **Windows (Programador de Tareas):** Crea una tarea básica diaria que ejecute `python main.py vigilar --una-vez`.
- **Linux / macOS (`cron`):**
  ```cron
  0 */6 * * * cd /ruta/al/proyecto && ./venv/bin/python main.py vigilar --una-vez >> vigilancia.log 2>&1
  ```

---

### 🔒 Garantías de Privacidad

- **Cero Cookies Persistentes:** Cada petición crea una instancia nueva y limpia de `requests.Session`.
- **User-Agent Neutro:** Evita fingerprinting o rastreo de hardware.
- **Sin Telemetría:** Cero llamadas analíticas, sin rastreadores externos ni seguimiento publicitario.
- **Tokens en Memoria:** El token OAuth de Amadeus nunca se persiste en disco.
- **Almacenamiento Local:** Los archivos en `datos/` (`alertas.json`, `historial.json`) y `.env` están rigurosamente excluidos en `.gitignore`.

---

### 🧪 Pruebas Unitarias (`pytest`)

Ejecuta las 26 pruebas automatizadas sin necesidad de conexión a internet ni consumo de saldo de APIs:

```bash
pytest -v
```

---

# 🇬🇧 English

A privacy-focused flight search engine and aggregator powered by **Amadeus for Developers API**, **Google Flights real-time engine (via SerpApi)**, and direct integration with 18+ official airline booking engines. Designed strictly with **Privacy-by-Design**, it runs 100% locally on your machine, stores no persistent tracking cookies, has zero telemetry, and provides direct booking links for safe, manual comparison and reservation.

---

### 📌 Table of Contents (English)
1. [Key Features](#-key-features)
2. [Project Architecture](#-project-architecture)
3. [System Requirements](#-system-requirements)
4. [Step-by-Step Installation](#-step-by-step-installation)
5. [API Keys & Configuration (.env)](#-api-keys--configuration-env)
6. [Interactive Web UI (Streamlit)](#️-interactive-web-ui-streamlit)
7. [CLI Usage Guide (`main.py`)](#-cli-usage-guide-mainpy)
8. [Chrome DevTools / Brave MCP Integration](#-chrome-devtools--brave-mcp-integration)
9. [Automation & Scheduled Tasks](#-automation--scheduled-tasks)
10. [Privacy Guarantees](#-privacy-guarantees)
11. [Unit Testing (`pytest`)](#-unit-testing-pytest)
12. [License](#-license)

---

### 🚀 Key Features

- **Multi-Engine Search:**
  - **Live Google Flights (SerpApi):** Real-time flight search across all worldwide airlines (Iberia, Vueling, Ryanair, Volotea, Air Europa, etc.).
  - **Amadeus for Developers API:** Direct connection to official `v2/shopping/flight-offers` and `v1/shopping/flight-dates` endpoints.
  - **Offline Demo Mode:** Test all features, UI components, and mock results without needing API credentials.
- **Direct Airline Booking Links:** Preloads origin, destination, dates, and passengers directly into 18+ airline websites (Iberia, Vueling, Ryanair, Volotea, EasyJet, British Airways, Air France, Lufthansa, KLM, TAP, Wizz Air, Norwegian, etc.).
- **Privacy by Design:** Ephemeral HTTP sessions per request, neutral User-Agent headers, no tracking cookies, no telemetry, HTTP/SOCKS proxy support, and 100% local JSON storage in `datos/`.
- **Baggage Allowance Parsing:** Automatically parses included checked baggage (`includedCheckedBags`) and baggage pricing add-ons.
- **Full Interactive Web Dashboard:** Built with Streamlit featuring autocomplete airport inputs, interactive date pickers, price charts, CSV exports, and alert management.
- **Automated Price Watcher & Alerts:** Background monitoring that checks prices against thresholds and notifies you via console and native OS desktop alerts without duplicate spam.
- **Chrome DevTools & Brave MCP Ready:** Direct compatibility with Model Context Protocol for automated browser interaction, snapshots, and audits.

---

### 📁 Project Architecture

```text
vuelos_baratos/
├── main.py                 # Main CLI application with subcommands (buscar, aerolineas, calendario, etc.)
├── app.py                  # Streamlit interactive web dashboard
├── iniciar_web.bat         # 1-click launcher for Windows
├── config.py               # Environment configuration (.env loader and defaults)
├── amadeus_api.py          # Amadeus API client (in-memory OAuth token, rate-limited)
├── serpapi_client.py       # Live Google Flights client using SerpApi
├── demo.py                 # Offline mock data generator
├── enlaces.py              # Direct URL generator (Google Flights, Skyscanner, Airlines)
├── privacidad.py           # Ephemeral HTTP sessions, rate limits & proxy handling
├── modelos.py              # Typed dataclasses (Oferta, Busqueda, Alerta)
├── filtros.py              # Price and stop filters, date validation, deduplication
├── calendario.py           # Window price calendar generator
├── aeropuertos.py          # IATA catalog & nearby alternate origins
├── equipaje.py             # Checked baggage parser and fee calculator
├── alertas.py              # Price alerts saved locally to datos/alertas.json
├── vigilancia.py           # Background monitoring service (loop or single-run)
├── historial.py            # Local private search history in datos/historial.json
├── salida.py               # Pretty terminal tables, CSV export and summaries
├── notificaciones.py       # Console & desktop notifications (plyer)
├── tests/                  # 26 automated unit tests with mocks
├── .env.example            # Environment variables template
├── .gitignore              # Ignores credentials, local storage, and caches
├── requirements.txt        # Runtime and testing dependencies
└── README.md               # Bilingual documentation
```

---

### 💻 System Requirements

- **Python:** 3.10 or higher (compatible with Python 3.10, 3.11, 3.12, 3.13, and 3.14).
- Internet connection for live API queries.
- Operating System: Windows, macOS, or Linux.

---

### 🛠 Step-by-Step Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jsoto-06/BuscaVuelos.git
   cd BuscaVuelos
   ```

2. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

### 🔑 API Keys & Configuration (.env)

Copy `.env.example` to `.env`:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Edit `.env` with your API credentials:

```ini
# Amadeus API Credentials (Free at https://developers.amadeus.com/)
AMADEUS_CLIENT_ID=your_client_id_here
AMADEUS_CLIENT_SECRET=your_client_secret_here
AMADEUS_ENV=test

# SerpApi Key for live Google Flights (Free at https://serpapi.com/)
SERPAPI_API_KEY=your_serpapi_key_here

# General Settings
MONEDA=EUR
ORIGEN_POR_DEFECTO=BIO
ALTERNATIVOS_ORIGEN=VIT,SDR,BIQ
MIN_SEGUNDOS_ENTRE_PETICIONES=2
PROXY_URL=
INTERVALO_VIGILANCIA_HORAS=6
NOTIFICAR_SISTEMA=true
```

---

### 🖥️ Interactive Web UI (Streamlit)

Launch the web app directly in your browser:

```bash
# Option 1: Via the CLI
python main.py web

# Option 2: Directly with Streamlit
streamlit run app.py

# Option 3 (Windows): Double-click iniciar_web.bat
```

Access the interface at: **`http://localhost:8501`**

---

### 📖 CLI Usage Guide (`main.py`)

Get instant command help:

```bash
python main.py --help
```

#### 1. Search Flights (`buscar`)
```bash
# Single route search
python main.py buscar --destinos LON --desde 2026-12-01

# Multi-destination date window search with max price and alternate origins
python main.py buscar --destinos LON,PAR --desde 2026-12-01 --hasta 2026-12-05 --alternativos --directos --max-precio 150

# Open top offers in your browser
python main.py buscar --destinos LON --desde 2026-12-01 --abrir 2 --abrir-aerolinea 2
```

#### 2. Direct Airline Links (`aerolineas`)
```bash
python main.py aerolineas --destinos LON --desde 2026-12-01 --abrir 3
```

#### 3. Price Calendar (`calendario`)
```bash
python main.py calendario --destinos LON --desde 2026-12-01 --hasta 2026-12-20
```

#### 4. Alerts & Monitoring (`alerta` & `vigilar`)
```bash
# Add a price alert
python main.py alerta añadir --origen BIO --destino LON --desde 2026-12-01 --hasta 2026-12-05 --max-precio 120

# List and delete alerts
python main.py alerta listar
python main.py alerta borrar ALERT_ID

# Continuous or single-run monitoring
python main.py vigilar
python main.py vigilar --una-vez
```

#### 5. Search History (`historial`)
```bash
python main.py historial ver
python main.py historial borrar
```

---

### 🤖 Chrome DevTools / Brave MCP Integration

Connect directly to Chrome or Brave via the **Model Context Protocol (MCP)**:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest",
        "--executablePath=C:\\Users\\Jony\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
      ]
    }
  }
}
```

---

### ⏰ Automation & Scheduled Tasks

The `--una-vez` flag is designed for native system schedulers without keeping a persistent background process alive:

- **Windows (Task Scheduler):** Run `python main.py vigilar --una-vez` periodically.
- **Linux / macOS (`cron`):**
  ```cron
  0 */6 * * * cd /path/to/project && ./venv/bin/python main.py vigilar --una-vez >> watcher.log 2>&1
  ```

---

### 🔒 Privacy Guarantees

- **No Persistent Cookies:** Every request creates a clean, isolated `requests.Session`.
- **Neutral User-Agent:** Standard browser headers to prevent tracking.
- **Zero Telemetry:** No analytics, crash reporting, or external tracking pings.
- **In-Memory OAuth:** Tokens are never stored on disk.
- **Strict Local Data:** `datos/`, `resultados/`, and `.env` are strictly excluded in `.gitignore`.

---

### 🧪 Unit Testing (`pytest`)

Run all 26 automated unit tests offline without using any API quota:

```bash
pytest -v
```

---

### 📄 Licencia / License

Distributed under the **MIT License**. Feel free to use, modify, and distribute this software while respecting the terms of service of the respective APIs and airlines.
