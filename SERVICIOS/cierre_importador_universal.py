from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json

from MODELOS.cierre_importador_universal import InformeCierreImportadorUniversal


class CierreImportadorUniversal:
    """
    Host AI 3.0.3.8.5

    Cierra el bloque del importador universal.
    Comprueba que están montados los módulos clave y genera un informe final.
    """

    MODULOS_CLAVE = [
        "base_ocr_documentos",
        "motor_ocr_simulado",
        "validador_corrector_ocr",
        "lector_facturas_con_ocr",
        "base_importador_universal_facturas",
        "ejecutor_importador_universal_facturas",
        "auditoria_importaciones_universales",
        "resumen_ejecutivo_importaciones",
        "validador_lineas_factura",
        "relacionador_automatico_articulos_factura",
        "actualizador_inteligente_precios_factura",
        "actualizador_inteligente_stock_factura",
        "reconciliador_stock_factura",
    ]

    FLUJO_COMPLETO = [
        "diagnosticar_archivo",
        "leer_pdf_o_ocr",
        "extraer_lineas",
        "validar_lineas",
        "relacionar_articulos",
        "validar_relaciones",
        "preparar_precios",
        "preparar_stock",
        "aplicar_precios",
        "aplicar_stock",
        "reconciliar_stock",
        "registrar_auditoria",
        "generar_resumen",
    ]

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def comprobar_cierre(self) -> Dict[str, Any]:
        comprobados = []
        faltantes = []

        for modulo in self.MODULOS_CLAVE:
            if hasattr(self.core, modulo):
                comprobados.append(modulo)
            else:
                faltantes.append(modulo)

        resumen = {}
        if hasattr(self.core, "resumen_ejecutivo_importaciones"):
            try:
                resumen = self.core.resumen_ejecutivo_importaciones.generar_resumen()
            except Exception as exc:
                resumen = {"error": str(exc)}

        avisos = []
        recomendaciones = []

        if faltantes:
            avisos.append(f"Faltan {len(faltantes)} módulos clave.")
            recomendaciones.append("No pasar a 3.0.4 hasta resolver módulos faltantes.")
        else:
            recomendaciones.append("El importador universal queda preparado para pruebas con facturas reales.")

        recomendaciones.extend([
            "Probar con una factura PDF real con texto.",
            "Probar con una imagen escaneada usando texto OCR manual.",
            "Revisar que precios y stock no se apliquen sin aprobación cuando haya avisos.",
            "Guardar copia de seguridad antes de importar facturas reales.",
        ])

        informe = InformeCierreImportadorUniversal(
            listo_para_uso=len(faltantes) == 0,
            modulos_comprobados=comprobados,
            modulos_faltantes=faltantes,
            pruebas_recomendadas=[
                "python TESTS\\test_base_importador_universal_facturas.py",
                "python TESTS\\test_ejecutor_importador_universal_facturas.py",
                "python TESTS\\test_auditoria_importaciones_universales.py",
                "python TESTS\\test_resumen_ejecutivo_importaciones.py",
            ],
            flujo_completo=self.FLUJO_COMPLETO,
            avisos=avisos,
            recomendaciones=recomendaciones,
            resumen=resumen,
        )
        datos = informe.to_dict()
        datos["lectura_host_ai"] = (
            "Importador universal cerrado y listo para pruebas reales."
            if datos["listo_para_uso"]
            else "Importador universal no está listo: faltan módulos."
        )
        return datos

    def exportar_informe(self, informe: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "cierre_importador_universal.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Cierre importador universal exportado: {destino.name}."}
