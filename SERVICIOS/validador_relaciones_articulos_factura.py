from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json

from MODELOS.validacion_relaciones_articulos import ValidacionRelacionArticulo, InformeValidacionRelaciones


class ValidadorRelacionesArticulosFactura:
    """
    Host AI 3.0.3.4.5

    Valida relaciones entre líneas de factura y artículos internos.
    Reglas:
    - confianza >= 85 automática
    - 60-84 revisión
    - <60 inválida
    - sin articulo_id inválida
    """

    UMBRAL_AUTO = 85.0
    UMBRAL_REVISION = 60.0

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def validar_relacion(self, relacion: Dict[str, Any]) -> Dict[str, Any]:
        descripcion = str(relacion.get("descripcion_factura", "") or "").strip()
        articulo_id = str(relacion.get("articulo_id", "") or "").strip()
        nombre_articulo = str(relacion.get("nombre_articulo", "") or "").strip()
        confianza = float(relacion.get("confianza", 0) or 0)
        metodo = str(relacion.get("metodo", "") or "")

        errores = []
        avisos = []
        requiere_revision = bool(relacion.get("requiere_revision", False))

        if not descripcion:
            errores.append("Falta descripción de factura.")
        if not articulo_id:
            errores.append("No hay artículo relacionado.")
        if not nombre_articulo:
            avisos.append("Falta nombre del artículo relacionado.")
        if confianza < self.UMBRAL_REVISION:
            errores.append("Confianza insuficiente.")
        elif confianza < self.UMBRAL_AUTO:
            avisos.append("Confianza media. Requiere revisión.")
            requiere_revision = True

        if metodo == "sin_relacion":
            errores.append("Método sin relación.")

        valida = len(errores) == 0
        val = ValidacionRelacionArticulo(
            descripcion_factura=descripcion,
            articulo_id=articulo_id,
            nombre_articulo=nombre_articulo,
            valida=valida,
            confianza=confianza,
            requiere_revision=requiere_revision,
            errores=errores,
            avisos=avisos,
            metodo=metodo,
        )
        datos = val.to_dict()
        datos["lectura_host_ai"] = "Relación válida." if valida else f"Relación inválida: {', '.join(errores)}"
        return datos

    def validar_informe(self, informe: Dict[str, Any]) -> Dict[str, Any]:
        validaciones = []
        for rel in informe.get("relaciones", []):
            d = self.validar_relacion(rel)
            validaciones.append(ValidacionRelacionArticulo(
                descripcion_factura=d["descripcion_factura"],
                articulo_id=d["articulo_id"],
                nombre_articulo=d["nombre_articulo"],
                valida=d["valida"],
                confianza=d["confianza"],
                requiere_revision=d["requiere_revision"],
                errores=d["errores"],
                avisos=d["avisos"],
                metodo=d["metodo"],
            ))

        avisos_generales = []
        errores_generales = []
        if not validaciones:
            errores_generales.append("No hay relaciones para validar.")

        out = InformeValidacionRelaciones(
            validaciones=validaciones,
            avisos_generales=avisos_generales,
            errores_generales=errores_generales,
        )
        datos = out.to_dict()
        datos["lectura_host_ai"] = (
            f"Validación relaciones: {datos['validas']} válidas, "
            f"{datos['con_revision']} revisión, {datos['invalidas']} inválidas."
        )
        return datos

    def validar_factura_texto(self, texto: str, **kwargs) -> Dict[str, Any]:
        informe = self.core.relacionador_automatico_articulos_factura.relacionar_factura_texto(
            texto=texto,
            proveedor_sugerido=kwargs.get("proveedor_sugerido", ""),
            cif_sugerido=kwargs.get("cif_sugerido", ""),
            numero_factura=kwargs.get("numero_factura", ""),
            fecha_factura=kwargs.get("fecha_factura", ""),
            total_factura_detectado=kwargs.get("total_factura_detectado", 0.0),
        )
        return self.validar_informe(informe)

    def exportar_validacion(self, informe: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "validacion_relaciones_articulos.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Validación relaciones exportada: {destino.name}."}
