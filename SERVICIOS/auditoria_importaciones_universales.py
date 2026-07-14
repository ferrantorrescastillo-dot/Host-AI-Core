from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json

from MODELOS.auditoria_importaciones import RegistroAuditoriaImportacion


class AuditoriaImportacionesUniversales:
    """
    Host AI 3.0.3.8.3

    Guarda auditoría de importaciones universales:
    - preparadas
    - aplicadas
    - bloqueadas
    - con errores

    Permite revisar qué facturas se importaron y qué hicieron.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.facturas_dir / "auditoria_importaciones_universales.json"
        self.registros: List[RegistroAuditoriaImportacion] = self._cargar()

    def registrar_resultado(self, resultado: Dict[str, Any]) -> Dict[str, Any]:
        preparacion = resultado.get("preparacion", resultado)
        lectura = preparacion.get("lectura", {})
        relaciones = preparacion.get("relaciones", {})
        aplicacion_precios = resultado.get("aplicacion_precios", {})
        aplicacion_stock = resultado.get("aplicacion_stock", {})

        if resultado.get("aplicado"):
            estado = "aplicado"
        elif resultado.get("errores"):
            estado = "bloqueado"
        elif preparacion.get("ok"):
            estado = "preparado"
        else:
            estado = "error"

        registro = RegistroAuditoriaImportacion(
            archivo=resultado.get("archivo", "") or preparacion.get("archivo", ""),
            estado=estado,
            proveedor_id=lectura.get("proveedor_id", ""),
            proveedor_nombre=lectura.get("proveedor_nombre", ""),
            total_lineas=int(lectura.get("total_lineas", 0) or 0),
            relaciones_auto=int(relaciones.get("relacionadas_auto", 0) or 0),
            precios_aplicados=int(aplicacion_precios.get("aplicados", 0) or 0),
            stock_aplicado=int(aplicacion_stock.get("aplicados", 0) or 0),
            requiere_revision=bool(resultado.get("requiere_revision", False) or preparacion.get("requiere_revision", False)),
            errores=resultado.get("errores", []),
            avisos=resultado.get("avisos", []),
            resumen=resultado.get("lectura_host_ai", ""),
            datos=resultado,
        )
        self.registros.append(registro)
        self._guardar()
        return {
            "registrado": True,
            "registro": registro.to_dict(),
            "lectura_host_ai": f"Auditoría registrada: {estado}.",
        }

    def listar(self, estado: str = "") -> Dict[str, Any]:
        regs = self.registros
        if estado:
            regs = [r for r in regs if r.estado == estado]
        data = [r.to_dict() for r in regs]
        return {
            "registros": data,
            "total": len(data),
            "lectura_host_ai": f"Auditoría importaciones: {len(data)} registros.",
        }

    def resumen(self) -> Dict[str, Any]:
        total = len(self.registros)
        por_estado = {}
        for r in self.registros:
            por_estado[r.estado] = por_estado.get(r.estado, 0) + 1
        datos = {
            "total": total,
            "por_estado": por_estado,
            "aplicadas": por_estado.get("aplicado", 0),
            "bloqueadas": por_estado.get("bloqueado", 0),
            "preparadas": por_estado.get("preparado", 0),
            "errores": por_estado.get("error", 0),
            "lectura_host_ai": f"Resumen auditoría: {total} importaciones registradas.",
        }
        return datos

    def exportar(self) -> Dict[str, Any]:
        self._guardar()
        return {"archivo": str(self.path), "lectura_host_ai": "Auditoría de importaciones exportada."}

    def _cargar(self) -> List[RegistroAuditoriaImportacion]:
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                return [RegistroAuditoriaImportacion(**r) for r in raw.get("registros", [])]
            except Exception:
                return []
        return []

    def _guardar(self):
        self.path.write_text(
            json.dumps({"version": "3.0.3.8.3", "registros": [r.to_dict() for r in self.registros]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
