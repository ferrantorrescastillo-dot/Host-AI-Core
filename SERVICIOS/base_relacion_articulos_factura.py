from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import json

from MODELOS.relacion_articulos_factura import (
    CandidatoArticuloFactura,
    RelacionLineaArticulo,
    InformeRelacionArticulosFactura,
)


class BaseRelacionArticulosFactura:
    """
    Host AI 3.0.3.4.1

    Servicio base para crear, validar y exportar relaciones entre líneas de factura
    y artículos internos. Todavía no busca automáticamente artículos.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def crear_relacion_demo(self) -> Dict[str, Any]:
        candidato = CandidatoArticuloFactura(
            articulo_id="ART-CARRILLERA",
            nombre_articulo="Carrillera de ternera",
            confianza=96,
            metodo="demo",
            motivos=["Coincidencia de ejemplo"],
            proveedor_id="PROV-MAKRO",
            unidad="kg",
            familia="carnes",
        )
        relacion = RelacionLineaArticulo(
            descripcion_factura="CARR TERN",
            cantidad=8,
            unidad="kg",
            precio_unitario=8.45,
            importe=67.60,
            proveedor_id="PROV-MAKRO",
            articulo_id="ART-CARRILLERA",
            nombre_articulo="Carrillera de ternera",
            confianza=96,
            metodo="demo",
            requiere_revision=False,
            candidatos=[candidato],
        )
        return relacion.to_dict()

    def crear_informe_demo(self) -> Dict[str, Any]:
        relacion = RelacionLineaArticulo(
            descripcion_factura="CARR TERN",
            cantidad=8,
            unidad="kg",
            precio_unitario=8.45,
            importe=67.60,
            proveedor_id="PROV-MAKRO",
            articulo_id="ART-CARRILLERA",
            nombre_articulo="Carrillera de ternera",
            confianza=96,
            metodo="demo",
            requiere_revision=False,
        )
        informe = InformeRelacionArticulosFactura(
            proveedor_id="PROV-MAKRO",
            proveedor_nombre="Makro",
            numero_factura="F-2026-001",
            relaciones=[relacion],
        )
        datos = informe.to_dict()
        datos["lectura_host_ai"] = "Informe demo de relaciones creado."
        return datos

    def validar_informe(self, informe: Dict[str, Any]) -> Dict[str, Any]:
        errores = []
        avisos = []
        for idx, rel in enumerate(informe.get("relaciones", []), start=1):
            if not rel.get("descripcion_factura"):
                errores.append(f"Relación {idx}: falta descripción de factura.")
            if not rel.get("articulo_id"):
                avisos.append(f"Relación {idx}: sin artículo relacionado.")
            if float(rel.get("confianza", 0) or 0) < 60:
                avisos.append(f"Relación {idx}: confianza baja.")
        return {
            "ok": len(errores) == 0,
            "errores": errores,
            "avisos": avisos,
            "lectura_host_ai": "Informe de relaciones válido." if not errores else f"Informe con {len(errores)} errores.",
        }

    def exportar_informe(self, informe: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "informe_relacion_articulos_factura.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Informe de relación exportado: {destino.name}.",
        }
