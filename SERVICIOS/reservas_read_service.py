from __future__ import annotations

from datetime import date
from pathlib import Path
import unicodedata
from typing import Callable

from MODELOS.reserva import ESTADOS_RESERVA, SERVICIOS_RESERVA, Reserva
from SERVICIOS.repositorio_reservas import RepositorioReservas


class ReservasReadService:
    def __init__(
        self,
        base_dir: Path | str,
        *,
        today_provider: Callable[[], date] = date.today,
        evento_existe: Callable[[str], bool] | None = None,
    ) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.repo = RepositorioReservas(self.base_dir)
        self.today_provider = today_provider
        self.evento_existe = evento_existe or self._evento_existe_en_fuente_actual

    def validar_evento(self, reserva: Reserva) -> None:
        if reserva.evento_id and not self.evento_existe(reserva.evento_id):
            raise ValueError("evento_id no existe")

    def listar(
        self,
        *,
        fecha: str = "",
        estado: str = "",
        servicio: str = "",
        nombre: str = "",
        limite: int = 50,
        desde: str = "",
    ) -> list[dict]:
        fecha = str(fecha or "").strip()
        estado = str(estado or "").strip().upper()
        servicio = str(servicio or "").strip().upper()
        if estado and estado not in ESTADOS_RESERVA:
            raise ValueError("estado de reserva no valido")
        if servicio and servicio not in SERVICIOS_RESERVA:
            raise ValueError("servicio de reserva no valido")
        limite = max(1, min(int(limite), 100))
        termino = self._normalizar(nombre)
        items = []
        for reserva in self.repo.listar():
            if fecha and reserva.fecha != fecha:
                continue
            if desde and reserva.fecha < desde:
                continue
            if estado and reserva.estado != estado:
                continue
            if servicio and reserva.servicio != servicio:
                continue
            if termino and termino not in self._normalizar(reserva.nombre_cliente):
                continue
            items.append(reserva)
        items.sort(key=lambda item: (item.fecha, item.hora, item.reserva_id))
        return [self._dto_listado(item) for item in items[:limite]]

    def hoy(self, **filtros) -> list[dict]:
        return self.listar(fecha=self.today_provider().isoformat(), **filtros)

    def proximas(self, **filtros) -> list[dict]:
        return self.listar(desde=self.today_provider().isoformat(), **filtros)

    def buscar_por_id(self, reserva_id: str) -> dict | None:
        reserva = self.repo.obtener(reserva_id)
        return self._dto_listado(reserva) if reserva else None

    def buscar_por_nombre(self, nombre: str, *, limite: int = 50) -> list[dict]:
        return self.listar(nombre=nombre, limite=limite)

    def detalle(self, reserva_id: str) -> dict | None:
        reserva = self.repo.obtener(reserva_id)
        if reserva is None:
            return None
        return {**self._dto_listado(reserva), "observaciones": reserva.observaciones}

    def _evento_existe_en_fuente_actual(self, evento_id: str) -> bool:
        path = self.base_dir / "DATOS" / "db" / "eventos.json"
        if not path.exists():
            return False
        import json
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        objetivo = str(evento_id or "").strip()
        return any(str(item.get("id") or item.get("id_evento") or "") == objetivo for item in items if isinstance(item, dict))

    @staticmethod
    def _dto_listado(reserva: Reserva) -> dict:
        return {
            "reserva_id": reserva.reserva_id,
            "nombre_cliente": reserva.nombre_cliente,
            "fecha": reserva.fecha,
            "hora": reserva.hora,
            "pax": reserva.pax,
            "estado": reserva.estado,
            "servicio": reserva.servicio,
            "evento_id": reserva.evento_id,
        }

    @staticmethod
    def _normalizar(value: str) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(char for char in text if not unicodedata.combining(char)).strip().casefold()
