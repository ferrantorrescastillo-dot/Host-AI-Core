from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _atomic_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


@dataclass
class ResultadoTransaccion:
    transaccion_id: str
    estado: str
    backup_dir: str
    archivos: list[str]
    escritos: int
    restaurados: int
    integridad_ok: bool
    auditoria: list[dict[str, Any]]
    error: str = ''

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MotorEscrituraSeguraI1342:
    VERSION = 'I1.3.4.2'

    def __init__(self, base_dir: str | Path, rutas_permitidas: list[str] | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.rutas_permitidas = set(rutas_permitidas or ['DATOS/db/menus.json'])
        self.backups_root = self.base_dir / 'DATOS' / 'backups' / 'i1342'
        self.auditoria_path = self.base_dir / 'DATOS' / 'auditoria' / 'i1342_transacciones.jsonl'

    def _validar_ruta(self, relativa: str) -> Path:
        if relativa not in self.rutas_permitidas:
            raise ValueError(f'Ruta no autorizada para I1.3.4.2: {relativa}')
        path = (self.base_dir / relativa).resolve()
        if self.base_dir not in path.parents:
            raise ValueError('Ruta fuera del proyecto')
        return path

    def _auditar(self, eventos: list[dict[str, Any]], evento: str, **datos: Any) -> None:
        reg = {'fecha': _now(), 'evento': evento, **datos}
        eventos.append(reg)

    def _guardar_auditoria(self, eventos: list[dict[str, Any]]) -> None:
        self.auditoria_path.parent.mkdir(parents=True, exist_ok=True)
        with self.auditoria_path.open('a', encoding='utf-8') as fh:
            for e in eventos:
                fh.write(json.dumps(e, ensure_ascii=False) + '\n')

    def ejecutar(self, cambios: dict[str, Any], *, forzar_fallo: bool = False, idempotency_key: str | None = None) -> ResultadoTransaccion:
        tx = f'TX-{uuid.uuid4().hex[:12].upper()}'
        eventos: list[dict[str, Any]] = []
        backup_dir = self.backups_root / tx
        escritos = restaurados = 0
        objetivos: dict[str, Path] = {}
        huellas_antes: dict[str, str | None] = {}

        try:
            if not cambios:
                raise ValueError('No hay cambios para aplicar')
            self._auditar(eventos, 'TRANSACCION_INICIADA', transaccion_id=tx, idempotency_key=idempotency_key)
            for rel in cambios:
                objetivos[rel] = self._validar_ruta(rel)
                huellas_antes[rel] = _sha256(objetivos[rel])

            backup_dir.mkdir(parents=True, exist_ok=False)
            manifest = {'version': self.VERSION, 'transaccion_id': tx, 'creado_en': _now(), 'archivos': {}}
            for rel, path in objetivos.items():
                destino = backup_dir / rel
                destino.parent.mkdir(parents=True, exist_ok=True)
                if path.exists():
                    shutil.copy2(path, destino)
                    manifest['archivos'][rel] = {'existia': True, 'sha256': huellas_antes[rel]}
                else:
                    manifest['archivos'][rel] = {'existia': False, 'sha256': None}
            _atomic_json(backup_dir / 'manifest.json', manifest)
            self._auditar(eventos, 'BACKUP_CREADO', transaccion_id=tx, backup_dir=str(backup_dir))

            for i, (rel, contenido) in enumerate(cambios.items(), 1):
                _atomic_json(objetivos[rel], contenido)
                escritos += 1
                self._auditar(eventos, 'ARCHIVO_ESCRITO', transaccion_id=tx, ruta=rel, sha256=_sha256(objetivos[rel]))
                if forzar_fallo and i == 1:
                    raise RuntimeError('Fallo de diagnóstico forzado')

            for rel, path in objetivos.items():
                if _sha256(path) is None:
                    raise RuntimeError(f'Verificación fallida: {rel}')
                json.loads(path.read_text(encoding='utf-8'))
            self._auditar(eventos, 'VERIFICACION_OK', transaccion_id=tx)
            self._auditar(eventos, 'COMMIT', transaccion_id=tx, archivos=escritos)
            self._guardar_auditoria(eventos)
            return ResultadoTransaccion(tx, 'COMMIT', str(backup_dir), list(cambios), escritos, 0, True, eventos)
        except Exception as exc:
            self._auditar(eventos, 'ERROR', transaccion_id=tx, error=str(exc))
            if backup_dir.exists():
                manifest_path = backup_dir / 'manifest.json'
                manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'archivos': {}}
                for rel, meta in manifest.get('archivos', {}).items():
                    path = self._validar_ruta(rel)
                    copia = backup_dir / rel
                    if meta.get('existia'):
                        path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(copia, path)
                    elif path.exists():
                        path.unlink()
                    restaurados += 1
                self._auditar(eventos, 'ROLLBACK', transaccion_id=tx, restaurados=restaurados)
            integridad = all(_sha256(objetivos[r]) == huellas_antes[r] for r in objetivos) if objetivos else True
            self._auditar(eventos, 'INTEGRIDAD_POST_ROLLBACK', transaccion_id=tx, ok=integridad)
            self._guardar_auditoria(eventos)
            return ResultadoTransaccion(tx, 'ROLLBACK', str(backup_dir), list(cambios), escritos, restaurados, integridad, eventos, str(exc))
