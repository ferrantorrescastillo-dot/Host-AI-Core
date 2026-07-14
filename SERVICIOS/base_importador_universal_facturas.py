from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json

from MODELOS.importacion_universal_facturas import PlanImportacionFactura, ResultadoImportacionUniversalFactura


class BaseImportadorUniversalFacturas:
    """
    Host AI 3.0.3.8.1

    Orquesta el flujo completo en modo preparación:
    - Detecta si es PDF/imagen.
    - Decide si necesita OCR.
    - Lee factura.
    - Valida líneas.
    - Relaciona artículos.
    - Prepara precios.
    - Prepara stock.

    Todavía NO aplica precios ni stock automáticamente.
    Eso se hará en 3.0.3.8.2.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def planificar_importacion(self, ruta_archivo: str) -> Dict[str, Any]:
        ruta = Path(ruta_archivo)
        if not ruta.is_absolute():
            ruta = self.base_dir / ruta
        if not ruta.exists():
            raise FileNotFoundError(f"No existe el archivo: {ruta}")

        ext = ruta.suffix.lower()
        diagnostico = self.core.base_ocr_documentos.diagnosticar_archivo(str(ruta)) if hasattr(self.core, "base_ocr_documentos") else {}
        necesita_ocr = bool(diagnostico.get("necesita_ocr", False))
        pasos = ["diagnosticar_archivo"]

        if necesita_ocr:
            pasos += ["extraer_texto_ocr", "leer_factura_con_ocr"]
        else:
            pasos += ["leer_pdf_factura"]

        pasos += [
            "validar_lineas",
            "relacionar_articulos",
            "validar_relaciones",
            "preparar_precios",
            "preparar_stock",
        ]

        plan = PlanImportacionFactura(
            archivo=str(ruta),
            tipo_archivo=ext.replace(".", ""),
            necesita_ocr=necesita_ocr,
            pasos=pasos,
            puede_importar=True,
            requiere_revision=necesita_ocr,
            avisos=(["El documento necesita OCR."] if necesita_ocr else []),
            datos_previos={"diagnostico_ocr": diagnostico},
        )
        datos = plan.to_dict()
        datos["lectura_host_ai"] = f"Plan de importación creado: {len(pasos)} pasos."
        return datos

    def preparar_importacion(self, ruta_archivo: str, texto_manual_ocr: str = "") -> Dict[str, Any]:
        plan = self.planificar_importacion(ruta_archivo)
        errores = []
        avisos = list(plan.get("avisos", []))

        if plan.get("necesita_ocr"):
            lectura = self.core.lector_facturas_con_ocr.leer_archivo_con_ocr(
                ruta_archivo,
                texto_manual=texto_manual_ocr,
                exportar_json=True,
            )
        else:
            lectura = self.core.lector_completo_lineas_factura.leer_factura_pdf_completa(
                ruta_archivo,
                exportar_json=True,
            )
            lectura["ok"] = True

        if not lectura.get("ok", True):
            errores.append("No se pudo leer la factura.")
            res = ResultadoImportacionUniversalFactura(
                archivo=plan["archivo"],
                ok=False,
                plan=plan,
                lectura=lectura,
                requiere_revision=True,
                errores=errores,
                avisos=avisos,
            )
            datos = res.to_dict()
            datos["lectura_host_ai"] = "Importación preparada con errores."
            return datos

        validacion_lineas = self.core.validador_lineas_factura.validar_factura_completa(lectura)
        relaciones = self.core.relacionador_automatico_articulos_factura.relacionar_bloque(lectura)
        validacion_relaciones = self.core.validador_relaciones_articulos_factura.validar_informe(relaciones)
        informe_precios = self.core.base_actualizacion_precios_factura.preparar_informe(relaciones)
        informe_stock = self.core.base_actualizacion_stock_factura.preparar_informe(relaciones)

        requiere_revision = (
            bool(plan.get("requiere_revision")) or
            not validacion_lineas.get("puede_importar", True) or
            not validacion_relaciones.get("puede_continuar", False) or
            informe_precios.get("requieren_revision", 0) > 0 or
            informe_stock.get("requieren_revision", 0) > 0
        )

        res = ResultadoImportacionUniversalFactura(
            archivo=plan["archivo"],
            ok=True,
            plan=plan,
            lectura=lectura,
            validacion_lineas=validacion_lineas,
            relaciones=relaciones,
            validacion_relaciones=validacion_relaciones,
            informe_precios=informe_precios,
            informe_stock=informe_stock,
            requiere_revision=requiere_revision,
            errores=errores,
            avisos=avisos,
        )
        datos = res.to_dict()
        datos["lectura_host_ai"] = (
            f"Importación preparada: {lectura.get('total_lineas', 0)} líneas, "
            f"{relaciones.get('relacionadas_auto', 0)} relaciones automáticas."
        )
        return datos

    def exportar_preparacion(self, resultado: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "preparacion_importacion_universal_factura.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Preparación importación exportada: {destino.name}."}
