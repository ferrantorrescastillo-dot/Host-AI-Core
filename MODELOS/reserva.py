from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time
import re
from typing import Any
from uuid import uuid4


ESTADOS_RESERVA = frozenset({"PENDIENTE", "CONFIRMADA", "CANCELADA", "NO_SHOW", "COMPLETADA"})
SERVICIOS_RESERVA = frozenset({"COMIDA", "CENA"})
RESERVA_ID_PATTERN = re.compile(r"RES-[A-F0-9]{12}")


def nuevo_reserva_id() -> str:
    return f"RES-{uuid4().hex[:12].upper()}"


@dataclass(frozen=True)
class Reserva:
    reserva_id: str
    nombre_cliente: str
    fecha: str
    hora: str
    pax: int
    estado: str
    servicio: str
    observaciones: str = ""
    evento_id: str | None = None
    origen: str = "MANUAL"
    creado_en: str = ""
    actualizado_en: str = ""
    eliminada: bool = False
    eliminado_en: str = ""

    def __post_init__(self) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        object.__setattr__(self, "reserva_id", str(self.reserva_id or nuevo_reserva_id()).strip().upper())
        object.__setattr__(self, "nombre_cliente", str(self.nombre_cliente or "").strip())
        object.__setattr__(self, "fecha", str(self.fecha or "").strip())
        object.__setattr__(self, "hora", str(self.hora or "").strip())
        object.__setattr__(self, "estado", str(self.estado or "").strip().upper())
        object.__setattr__(self, "servicio", str(self.servicio or "").strip().upper())
        object.__setattr__(self, "observaciones", str(self.observaciones or "").strip())
        object.__setattr__(self, "evento_id", str(self.evento_id).strip() if self.evento_id else None)
        object.__setattr__(self, "origen", str(self.origen or "MANUAL").strip().upper())
        object.__setattr__(self, "creado_en", str(self.creado_en or now))
        object.__setattr__(self, "actualizado_en", str(self.actualizado_en or self.creado_en or now))
        object.__setattr__(self, "eliminada", bool(self.eliminada))
        object.__setattr__(self, "eliminado_en", str(self.eliminado_en or ""))
        try:
            pax = int(self.pax)
        except (TypeError, ValueError) as exc:
            raise ValueError("pax debe ser un entero positivo") from exc
        object.__setattr__(self, "pax", pax)
        self._validar()

    def _validar(self) -> None:
        if RESERVA_ID_PATTERN.fullmatch(self.reserva_id) is None:
            raise ValueError("reserva_id no es canonico")
        if not self.nombre_cliente:
            raise ValueError("nombre_cliente es obligatorio")
        try:
            date.fromisoformat(self.fecha)
        except ValueError as exc:
            raise ValueError("fecha debe usar YYYY-MM-DD") from exc
        try:
            parsed_time = time.fromisoformat(self.hora)
        except ValueError as exc:
            raise ValueError("hora debe usar HH:MM") from exc
        if parsed_time.second or parsed_time.microsecond or len(self.hora) != 5:
            raise ValueError("hora debe usar HH:MM")
        if self.pax <= 0:
            raise ValueError("pax debe ser mayor que cero")
        if self.estado not in ESTADOS_RESERVA:
            raise ValueError("estado de reserva no valido")
        if self.servicio not in SERVICIOS_RESERVA:
            raise ValueError("servicio de reserva no valido")
        for field_name in ("creado_en", "actualizado_en"):
            try:
                datetime.fromisoformat(getattr(self, field_name))
            except ValueError as exc:
                raise ValueError(f"{field_name} no es ISO-8601 valido") from exc

    @classmethod
    def crear(cls, **datos: Any) -> "Reserva":
        return cls(reserva_id=str(datos.pop("reserva_id", "") or nuevo_reserva_id()), **datos)

    @classmethod
    def from_dict(cls, datos: dict[str, Any]) -> "Reserva":
        permitidos = set(cls.__dataclass_fields__)
        return cls(**{key: value for key, value in dict(datos or {}).items() if key in permitidos})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
