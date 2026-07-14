from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json

from MODELOS.resumen_importaciones import ResumenEjecutivoImportaciones


class ResumenEjecutivoImportacionesServicio:
    """
    Host AI 3.0.3.8.4

    Genera un resumen ejecutivo de importaciones universales:
    - cuántas facturas se han aplicado
    - cuántas bloqueadas
    - líneas leídas
    - precios y stock aplicados
    - proveedores principales
    - recomendaciones operativas
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def generar_resumen(self, ultimas: int = 10) -> Dict[str, Any]:
        auditoria = getattr(self.core, "auditoria_importaciones_universales", None)
        if auditoria is None:
            datos = ResumenEjecutivoImportaciones(
                avisos=["No existe módulo de auditoría."],
                recomendaciones=["Activar auditoría de importaciones."]
            ).to_dict()
            datos["lectura_host_ai"] = "No se pudo generar resumen: falta auditoría."
            return datos

        registros = [r.to_dict() for r in auditoria.registros]
        proveedores = {}
        for r in registros:
            prov = r.get("proveedor_nombre") or r.get("proveedor_id") or "SIN-PROVEEDOR"
            proveedores[prov] = proveedores.get(prov, 0) + 1

        total = len(registros)
        aplicadas = sum(1 for r in registros if r.get("estado") == "aplicado")
        bloqueadas = sum(1 for r in registros if r.get("estado") == "bloqueado")
        preparadas = sum(1 for r in registros if r.get("estado") == "preparado")
        errores = sum(1 for r in registros if r.get("estado") == "error")
        total_lineas = sum(int(r.get("total_lineas", 0) or 0) for r in registros)
        precios = sum(int(r.get("precios_aplicados", 0) or 0) for r in registros)
        stock = sum(int(r.get("stock_aplicado", 0) or 0) for r in registros)

        avisos = []
        recomendaciones = []
        if bloqueadas:
            avisos.append(f"Hay {bloqueadas} importaciones bloqueadas.")
            recomendaciones.append("Revisar las facturas bloqueadas antes de cerrar compras.")
        if errores:
            avisos.append(f"Hay {errores} importaciones con error.")
            recomendaciones.append("Revisar OCR, proveedor y líneas de factura.")
        if total and aplicadas == total:
            recomendaciones.append("Todas las importaciones registradas están aplicadas.")
        if not total:
            recomendaciones.append("Importar una factura de prueba para validar el flujo completo.")

        resumen = ResumenEjecutivoImportaciones(
            total_importaciones=total,
            aplicadas=aplicadas,
            bloqueadas=bloqueadas,
            preparadas=preparadas,
            errores=errores,
            total_lineas=total_lineas,
            total_precios_aplicados=precios,
            total_stock_aplicado=stock,
            proveedores=proveedores,
            ultimas_importaciones=registros[-ultimas:],
            avisos=avisos,
            recomendaciones=recomendaciones,
        )
        datos = resumen.to_dict()
        datos["lectura_host_ai"] = f"Resumen importaciones: {aplicadas}/{total} aplicadas."
        return datos

    def exportar_resumen(self, resumen: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "resumen_ejecutivo_importaciones.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Resumen ejecutivo exportado: {destino.name}.",
        }
