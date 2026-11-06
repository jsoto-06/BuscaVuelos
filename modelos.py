"""
Modelos de datos para vuelos_baratos (Dataclasses).
Define las estructuras para Oferta, Busqueda y Alerta.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import hashlib


@dataclass
class Oferta:
    """Representa una oferta de vuelo encontrada en la API."""
    id: str
    origen: str
    destino: str
    fecha_salida: str
    hora_salida: str
    hora_llegada: str
    fecha_llegada: str
    escalas: int
    duracion: str
    aerolinea: str
    numero_vuelo: str
    precio_total: float
    moneda: str
    equipaje_incluido: str
    piezas_equipaje: Optional[int] = None
    precio_con_equipaje: Optional[float] = None
    enlace_google: str = ""
    enlace_skyscanner: str = ""
    enlace_aerolinea: str = ""

    @property
    def clave_deduplicacion(self) -> tuple:
        """Clave de unicidad: (aerolinea, salida, llegada, precio)."""
        return (
            self.aerolinea.upper(),
            self.hora_salida,
            self.hora_llegada,
            round(self.precio_total, 2),
        )

    @property
    def hash_alerta(self) -> str:
        """Hash identificador para no repetir avisos de la misma oferta."""
        cadena = f"{self.aerolinea.upper()}_{self.hora_salida}_{round(self.precio_total, 2)}"
        return hashlib.sha256(cadena.encode("utf-8")).hexdigest()[:16]

    @property
    def precio_con_equipaje_texto(self) -> str:
        """Texto formateado para la columna de precio con equipaje."""
        if self.precio_con_equipaje is not None:
            return f"{self.precio_con_equipaje:.2f} {self.moneda}"
        return "no disponible"


@dataclass
class Busqueda:
    """Parámetros de una búsqueda de vuelos."""
    origen: str
    destinos: List[str]
    fecha_desde: str
    fecha_hasta: Optional[str] = None
    alternativos: bool = False
    directos: bool = False
    max_precio: Optional[float] = None
    adultos: int = 1
    moneda: str = "EUR"
    top: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Alerta:
    """Alerta de precio persistida para vigilancia periódica."""
    id: str
    origen: str
    destino: str
    fecha_desde: str
    fecha_hasta: str
    max_precio: float
    creada_en: str
    ultimo_precio_visto: Optional[float] = None
    ultimo_aviso: Optional[str] = None
    ofertas_notificadas: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Alerta":
        return cls(
            id=str(data.get("id", "")),
            origen=str(data.get("origen", "")).upper(),
            destino=str(data.get("destino", "")).upper(),
            fecha_desde=str(data.get("fecha_desde", "")),
            fecha_hasta=str(data.get("fecha_hasta", "")),
            max_precio=float(data.get("max_precio", 0.0)),
            creada_en=str(data.get("creada_en", "")),
            ultimo_precio_visto=(
                float(data["ultimo_precio_visto"])
                if data.get("ultimo_precio_visto") is not None
                else None
            ),
            ultimo_aviso=data.get("ultimo_aviso"),
            ofertas_notificadas=list(data.get("ofertas_notificadas", [])),
        )
