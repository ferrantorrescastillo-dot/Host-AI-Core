from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Iterable

from MODELOS.reserva import Reserva


class RepositorioReservas:
    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.path = self.base_dir / "DATOS" / "db" / "reservas.json"

    def listar(self) -> list[Reserva]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("persistencia de reservas no legible") from exc
        if not isinstance(raw, list):
            raise ValueError("persistencia de reservas invalida")
        reservas = [Reserva.from_dict(item) for item in raw]
        self._validar_ids_unicos(reservas)
        return reservas

    def obtener(self, reserva_id: str) -> Reserva | None:
        objetivo = str(reserva_id or "").strip().upper()
        return next((item for item in self.listar() if item.reserva_id == objetivo), None)

    def guardar_todos(self, reservas: Iterable[Reserva]) -> None:
        """Escritura interna para bootstrap/fixtures; no es una capability publica."""
        items = list(reservas)
        self._validar_ids_unicos(items)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.to_dict() for item in sorted(items, key=lambda r: (r.fecha, r.hora, r.reserva_id))]
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.path.parent, suffix=".tmp") as tmp:
            json.dump(payload, tmp, ensure_ascii=False, indent=2, sort_keys=True)
            tmp.write("\n")
            temp_path = Path(tmp.name)
        temp_path.replace(self.path)

    @staticmethod
    def _validar_ids_unicos(reservas: Iterable[Reserva]) -> None:
        ids = [item.reserva_id for item in reservas]
        if len(ids) != len(set(ids)):
            raise ValueError("reserva_id duplicado")
