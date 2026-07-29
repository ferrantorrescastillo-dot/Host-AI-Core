from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class BaseDatosLocal:
    COLECCIONES = [
        "eventos", "stock_lotes", "stock_movimientos",
        "compras_necesidades", "compras_pedidos",
        "compras_proveedores", "compras_propuestas", "compras_registros",
        "compras_producto_proveedor", "compras_recepciones", "compras_incidencias",
        "escandallos", "precios", "planes_produccion",
        "ideas_culinarias", "historial_chat", "historial_escandallos_costes",
        "historial_costes_eventos", "historial_rentabilidad",
    ]

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.db_dir = self.base_dir / "DATOS" / "db"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.db_dir / "_metadata.json"
        self._asegurar_archivos()

    def _asegurar_archivos(self):
        for c in self.COLECCIONES:
            p = self._path(c)
            if not p.exists():
                self._guardar_json(p, [])
        if not self.metadata_path.exists():
            self._guardar_json(self.metadata_path, {
                "version": "3.0.1",
                "creado_en": datetime.now().isoformat(timespec="seconds"),
                "actualizado_en": datetime.now().isoformat(timespec="seconds"),
            })

    def _validar(self, coleccion: str):
        if coleccion not in self.COLECCIONES:
            raise ValueError(f"Colección no soportada: {coleccion}")

    def _path(self, coleccion: str) -> Path:
        self._validar(coleccion)
        return self.db_dir / f"{coleccion}.json"

    def cargar(self, coleccion: str) -> List[Dict[str, Any]]:
        p = self._path(coleccion)
        try:
            datos = json.loads(p.read_text(encoding="utf-8"))
            return datos if isinstance(datos, list) else []
        except Exception:
            return []

    def guardar(self, coleccion: str, datos: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._validar(coleccion)
        if not isinstance(datos, list):
            raise ValueError("Los datos deben ser una lista.")
        self._guardar_json(self._path(coleccion), datos)
        self._actualizar_metadata()
        return {"coleccion": coleccion, "total": len(datos), "path": str(self._path(coleccion))}

    def resumen(self) -> Dict[str, Any]:
        cols = []
        for c in self.COLECCIONES:
            datos = self.cargar(c)
            cols.append({"coleccion": c, "total": len(datos), "archivo": str(self._path(c))})
        return {
            "db_dir": str(self.db_dir),
            "colecciones": cols,
            "total_registros": sum(c["total"] for c in cols),
            "lectura_host_ai": f"Base de datos local activa con {len(cols)} colecciones.",
        }

    def snapshot(self, nombre: str = "") -> Dict[str, Any]:
        d = self.db_dir / "snapshots"
        d.mkdir(exist_ok=True)
        nombre = nombre or datetime.now().strftime("snapshot_%Y%m%d_%H%M%S")
        p = d / f"{nombre}.json"
        datos = {"creado_en": datetime.now().isoformat(timespec="seconds"),
                 "colecciones": {c: self.cargar(c) for c in self.COLECCIONES}}
        self._guardar_json(p, datos)
        return {"snapshot": str(p), "lectura_host_ai": f"Snapshot creado: {p.name}."}

    def borrar_todo(self) -> Dict[str, Any]:
        for c in self.COLECCIONES:
            self.guardar(c, [])
        return {"ok": True, "mensaje": "Base de datos local limpiada."}

    def _guardar_json(self, path: Path, datos: Any):
        path.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    def _actualizar_metadata(self):
        self._guardar_json(self.metadata_path, {
            "version": "3.0.1",
            "actualizado_en": datetime.now().isoformat(timespec="seconds"),
        })
