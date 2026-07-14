from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import json

from CORE.MUR.modelos import CheckpointMUR, ConflictoMUR, EventoAuditoriaMUR, SesionResolucionMUR


class RepositorioMURMemoria:
    def __init__(self) -> None:
        self.conflictos: dict[str, dict[str, Any]] = {}
        self.checkpoints: dict[str, dict[str, Any]] = {}
        self.sesiones: dict[str, dict[str, Any]] = {}
        self.auditoria: list[dict[str, Any]] = []

    def guardar_conflicto(self, conflicto: ConflictoMUR) -> None:
        self.conflictos[conflicto.conflicto_id] = deepcopy(conflicto.to_dict())

    def obtener_conflicto(self, conflicto_id: str) -> ConflictoMUR:
        if conflicto_id not in self.conflictos:
            raise KeyError(f'Conflicto no encontrado: {conflicto_id}')
        return ConflictoMUR.from_dict(deepcopy(self.conflictos[conflicto_id]))

    def listar_conflictos(self) -> list[ConflictoMUR]:
        return [ConflictoMUR.from_dict(deepcopy(x)) for x in self.conflictos.values()]

    def guardar_checkpoint(self, checkpoint: CheckpointMUR) -> None:
        self.checkpoints[checkpoint.checkpoint_id] = deepcopy(checkpoint.to_dict())

    def obtener_checkpoint(self, checkpoint_id: str) -> CheckpointMUR:
        if checkpoint_id not in self.checkpoints:
            raise KeyError(f'Checkpoint no encontrado: {checkpoint_id}')
        return CheckpointMUR.from_dict(deepcopy(self.checkpoints[checkpoint_id]))

    def guardar_sesion(self, sesion: SesionResolucionMUR) -> None:
        self.sesiones[sesion.sesion_id] = deepcopy(sesion.to_dict())

    def obtener_sesion(self, sesion_id: str) -> SesionResolucionMUR:
        if sesion_id not in self.sesiones:
            raise KeyError(f'Sesión no encontrada: {sesion_id}')
        return SesionResolucionMUR.from_dict(deepcopy(self.sesiones[sesion_id]))

    def registrar_evento(self, evento: EventoAuditoriaMUR) -> None:
        self.auditoria.append(deepcopy(evento.to_dict()))

    def listar_auditoria(self, conflicto_id: str | None = None) -> list[EventoAuditoriaMUR]:
        rows = self.auditoria if conflicto_id is None else [x for x in self.auditoria if x.get('conflicto_id') == conflicto_id]
        return [EventoAuditoriaMUR.from_dict(deepcopy(x)) for x in rows]


class RepositorioMURJson(RepositorioMURMemoria):
    """Persistencia inicial intercambiable y atómica para M1.1.

    No contiene datos de recetas, artículos ni otros dominios.
    """

    ESQUEMA = 1

    def __init__(self, ruta: str | Path):
        super().__init__()
        self.ruta = Path(ruta)
        self._cargar()

    def _cargar(self) -> None:
        if not self.ruta.exists():
            return
        data = json.loads(self.ruta.read_text(encoding='utf-8'))
        self.conflictos = dict(data.get('conflictos') or {})
        self.checkpoints = dict(data.get('checkpoints') or {})
        self.sesiones = dict(data.get('sesiones') or {})
        self.auditoria = list(data.get('auditoria') or [])

    def _persistir(self) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'version': 'M1.1', 'esquema': self.ESQUEMA,
            'conflictos': self.conflictos, 'checkpoints': self.checkpoints,
            'sesiones': self.sesiones, 'auditoria': self.auditoria,
        }
        tmp = self.ruta.with_suffix(self.ruta.suffix + '.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(self.ruta)

    def guardar_conflicto(self, conflicto: ConflictoMUR) -> None:
        super().guardar_conflicto(conflicto); self._persistir()

    def guardar_checkpoint(self, checkpoint: CheckpointMUR) -> None:
        super().guardar_checkpoint(checkpoint); self._persistir()

    def guardar_sesion(self, sesion: SesionResolucionMUR) -> None:
        super().guardar_sesion(sesion); self._persistir()

    def registrar_evento(self, evento: EventoAuditoriaMUR) -> None:
        super().registrar_evento(evento); self._persistir()
