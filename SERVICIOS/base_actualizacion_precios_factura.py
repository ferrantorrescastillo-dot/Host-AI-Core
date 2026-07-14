from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json

from MODELOS.actualizacion_precios_factura import CambioPrecioFactura, InformeActualizacionPrecios


class BaseActualizacionPreciosFactura:
    """
    Host AI 3.0.3.5.1

    Base para preparar cambios de precio desde facturas.
    Todavía no escribe en el motor de costes; eso vendrá en 3.0.3.5.2.
    """

    UMBRAL_REVISION_PORCENTAJE = 20.0

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def preparar_cambio(self, relacion: Dict[str, Any], precio_anterior: float = 0.0) -> Dict[str, Any]:
        precio_nuevo = float(relacion.get("precio_unitario", 0) or 0)
        cambio = CambioPrecioFactura(
            articulo_id=relacion.get("articulo_id", ""),
            nombre_articulo=relacion.get("nombre_articulo", ""),
            proveedor_id=relacion.get("proveedor_id", ""),
            precio_anterior=float(precio_anterior or 0),
            precio_nuevo=precio_nuevo,
            unidad=relacion.get("unidad", ""),
            numero_factura=relacion.get("numero_factura", ""),
            fecha_factura=relacion.get("fecha_factura", ""),
            origen_linea=relacion,
        )

        if not cambio.articulo_id:
            cambio.requiere_revision = True
            cambio.accion_sugerida = "revisar"
            cambio.avisos.append("No hay artículo relacionado.")
        if precio_nuevo <= 0:
            cambio.requiere_revision = True
            cambio.accion_sugerida = "revisar"
            cambio.avisos.append("Precio nuevo inválido.")
        if not cambio.precio_anterior:
            cambio.avisos.append("No hay precio anterior.")
        elif abs(cambio.variacion_porcentaje) >= self.UMBRAL_REVISION_PORCENTAJE:
            cambio.requiere_revision = True
            cambio.accion_sugerida = "revisar"
            cambio.avisos.append(f"Variación fuerte: {cambio.variacion_porcentaje}%.")

        datos = cambio.to_dict()
        datos["lectura_host_ai"] = f"Cambio preparado: {cambio.nombre_articulo} {cambio.precio_anterior} -> {cambio.precio_nuevo}."
        return datos

    def preparar_informe(self, informe_relaciones: Dict[str, Any]) -> Dict[str, Any]:
        cambios = []
        for rel in informe_relaciones.get("relaciones", []):
            precio_anterior = self._obtener_precio_anterior(rel)
            d = self.preparar_cambio(rel, precio_anterior=precio_anterior)
            cambios.append(CambioPrecioFactura(
                articulo_id=d["articulo_id"],
                nombre_articulo=d["nombre_articulo"],
                proveedor_id=d["proveedor_id"],
                proveedor_nombre=d.get("proveedor_nombre", ""),
                precio_anterior=d["precio_anterior"],
                precio_nuevo=d["precio_nuevo"],
                unidad=d["unidad"],
                numero_factura=d["numero_factura"],
                fecha_factura=d["fecha_factura"],
                origen_linea=d["origen_linea"],
                accion_sugerida=d["accion_sugerida"],
                requiere_revision=d["requiere_revision"],
                avisos=d["avisos"],
            ))

        informe = InformeActualizacionPrecios(cambios=cambios)
        datos = informe.to_dict()
        datos["lectura_host_ai"] = (
            f"Informe precios: {datos['actualizables']} actualizables, "
            f"{datos['requieren_revision']} para revisar."
        )
        return datos

    def exportar_informe(self, informe: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "informe_actualizacion_precios.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Informe precios exportado: {destino.name}."}

    def _obtener_precio_anterior(self, relacion: Dict[str, Any]) -> float:
        costes = getattr(self.core, "costes_inteligente", None)
        if not costes:
            return 0.0
        try:
            return float(costes.obtener_precio(relacion.get("nombre_articulo", ""), relacion.get("articulo_id", "")) or 0.0)
        except Exception:
            return 0.0
