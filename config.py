"""
Módulo de configuración para vuelos_baratos.
Carga variables de entorno desde .env y define valores predeterminados.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Cargar variables desde archivo .env si existe
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Rutas de datos y resultados locales
DATOS_DIR = BASE_DIR / "datos"
RESULTADOS_DIR = BASE_DIR / "resultados"
ALERTAS_FILE = DATOS_DIR / "alertas.json"
HISTORIAL_FILE = DATOS_DIR / "historial.json"

# Asegurar directorios locales
DATOS_DIR.mkdir(parents=True, exist_ok=True)
RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

# Credenciales de Amadeus y SerpApi
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID", "").strip()
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET", "").strip()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "").strip()

# Entorno: 'test' o 'prod'
AMADEUS_ENV = os.getenv("AMADEUS_ENV", "test").strip().lower()
if AMADEUS_ENV not in ("test", "prod"):
    AMADEUS_ENV = "test"

# URLs base de Amadeus
AMADEUS_HOSTS = {
    "test": "https://test.api.amadeus.com",
    "prod": "https://api.amadeus.com",
}
AMADEUS_BASE_URL = AMADEUS_HOSTS[AMADEUS_ENV]

# Moneda y orígenes
MONEDA = os.getenv("MONEDA", "EUR").strip().upper()
ORIGEN_POR_DEFECTO = os.getenv("ORIGEN_POR_DEFECTO", "BIO").strip().upper()

# Aeropuertos alternativos por defecto (lista)
_alternativos_raw = os.getenv("ALTERNATIVOS_ORIGEN", "VIT,SDR,BIQ").strip()
ALTERNATIVOS_ORIGEN = [
    iata.strip().upper() for iata in _alternativos_raw.split(",") if iata.strip()
]

# Control de peticiones y privacidad
try:
    MIN_SEGUNDOS_ENTRE_PETICIONES = float(
        os.getenv("MIN_SEGUNDOS_ENTRE_PETICIONES", "2")
    )
except ValueError:
    MIN_SEGUNDOS_ENTRE_PETICIONES = 2.0

PROXY_URL = os.getenv("PROXY_URL", "").strip()

# Vigilancia
try:
    INTERVALO_VIGILANCIA_HORAS = float(
        os.getenv("INTERVALO_VIGILANCIA_HORAS", "6")
    )
except ValueError:
    INTERVALO_VIGILANCIA_HORAS = 6.0

# Notificaciones
_notificar_raw = os.getenv("NOTIFICAR_SISTEMA", "true").strip().lower()
NOTIFICAR_SISTEMA = _notificar_raw in ("true", "1", "yes", "si", "s")


def validar_credenciales(salir_si_invalido: bool = True) -> bool:
    """
    Valida que las credenciales de Amadeus estén configuradas.
    Si faltan o contienen valores de plantilla, muestra un mensaje claro y,
    opcionalmente, finaliza la ejecución sin trazas de error.
    """
    placeholders = {"tu_client_id_aqui", "tu_client_secret_aqui", "your_client_id", "your_client_secret"}
    es_valido = bool(
        AMADEUS_CLIENT_ID
        and AMADEUS_CLIENT_SECRET
        and AMADEUS_CLIENT_ID.lower() not in placeholders
        and AMADEUS_CLIENT_SECRET.lower() not in placeholders
    )

    if not es_valido:
        msg = (
            "\n[AVISO DE CONFIGURACIÓN]\n"
            "No se han configurado credenciales válidas para la API de Amadeus.\n"
            "Para utilizar las funciones de búsqueda o vigilancia:\n"
            "  1. Copia el archivo .env.example a .env\n"
            "  2. Registra una cuenta gratuita en https://developers.amadeus.com/\n"
            "  3. Crea una app en 'My Self-Service Workspace' para obtener tu API Key y API Secret\n"
            "  4. Asigna AMADEUS_CLIENT_ID y AMADEUS_CLIENT_SECRET en tu archivo .env\n"
        )
        if salir_si_invalido:
            print(msg, file=sys.stderr)
            sys.exit(1)
        return False

    return True


def guardar_credenciales_env(client_id: str, client_secret: str, env_type: str = "test") -> None:
    """
    Guarda o actualiza las credenciales de Amadeus en el archivo .env
    y actualiza las variables en memoria en tiempo de ejecución.
    """
    global AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET, AMADEUS_ENV, AMADEUS_BASE_URL
    lineas = []
    claves_actualizadas = {
        "AMADEUS_CLIENT_ID": False,
        "AMADEUS_CLIENT_SECRET": False,
        "AMADEUS_ENV": False,
    }

    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for linea in f:
                linea_strip = linea.strip()
                if linea_strip.startswith("AMADEUS_CLIENT_ID="):
                    lineas.append(f"AMADEUS_CLIENT_ID={client_id.strip()}\n")
                    claves_actualizadas["AMADEUS_CLIENT_ID"] = True
                elif linea_strip.startswith("AMADEUS_CLIENT_SECRET="):
                    lineas.append(f"AMADEUS_CLIENT_SECRET={client_secret.strip()}\n")
                    claves_actualizadas["AMADEUS_CLIENT_SECRET"] = True
                elif linea_strip.startswith("AMADEUS_ENV="):
                    lineas.append(f"AMADEUS_ENV={env_type.strip().lower()}\n")
                    claves_actualizadas["AMADEUS_ENV"] = True
                else:
                    lineas.append(linea)
    else:
        plantilla = BASE_DIR / ".env.example"
        if plantilla.exists():
            with open(plantilla, "r", encoding="utf-8") as f:
                for linea in f:
                    linea_strip = linea.strip()
                    if linea_strip.startswith("AMADEUS_CLIENT_ID="):
                        lineas.append(f"AMADEUS_CLIENT_ID={client_id.strip()}\n")
                        claves_actualizadas["AMADEUS_CLIENT_ID"] = True
                    elif linea_strip.startswith("AMADEUS_CLIENT_SECRET="):
                        lineas.append(f"AMADEUS_CLIENT_SECRET={client_secret.strip()}\n")
                        claves_actualizadas["AMADEUS_CLIENT_SECRET"] = True
                    elif linea_strip.startswith("AMADEUS_ENV="):
                        lineas.append(f"AMADEUS_ENV={env_type.strip().lower()}\n")
                        claves_actualizadas["AMADEUS_ENV"] = True
                    else:
                        lineas.append(linea)

    for k, actualizada in claves_actualizadas.items():
        if not actualizada:
            if k == "AMADEUS_CLIENT_ID":
                lineas.append(f"AMADEUS_CLIENT_ID={client_id.strip()}\n")
            elif k == "AMADEUS_CLIENT_SECRET":
                lineas.append(f"AMADEUS_CLIENT_SECRET={client_secret.strip()}\n")
            elif k == "AMADEUS_ENV":
                lineas.append(f"AMADEUS_ENV={env_type.strip().lower()}\n")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lineas)

    # Actualizar estado en memoria
    AMADEUS_CLIENT_ID = client_id.strip()
    AMADEUS_CLIENT_SECRET = client_secret.strip()
    AMADEUS_ENV = env_type.strip().lower()
    AMADEUS_BASE_URL = AMADEUS_HOSTS.get(AMADEUS_ENV, AMADEUS_HOSTS["test"])
    os.environ["AMADEUS_CLIENT_ID"] = AMADEUS_CLIENT_ID
    os.environ["AMADEUS_CLIENT_SECRET"] = AMADEUS_CLIENT_SECRET
    os.environ["AMADEUS_ENV"] = AMADEUS_ENV


def guardar_serpapi_key_env(serpapi_key: str) -> None:
    """Guarda o actualiza la clave de SerpApi en el archivo .env."""
    global SERPAPI_API_KEY
    lineas = []
    actualizada = False

    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for linea in f:
                if linea.strip().startswith("SERPAPI_API_KEY="):
                    lineas.append(f"SERPAPI_API_KEY={serpapi_key.strip()}\n")
                    actualizada = True
                else:
                    lineas.append(linea)

    if not actualizada:
        lineas.append(f"SERPAPI_API_KEY={serpapi_key.strip()}\n")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lineas)

    SERPAPI_API_KEY = serpapi_key.strip()
    os.environ["SERPAPI_API_KEY"] = SERPAPI_API_KEY
