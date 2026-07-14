from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime


class EjecutorImportadorUniversalFacturas:
    """
    Host AI 3.0.3.8.2

    Ejecuta una importación universal preparada:
    - prepara factura si recibe archivo
    - aplica precios
    - aplica stock
    - reconcilia stock
    - devuelve resultado completo

    Por seguridad:
    - si requiere revisión, no aplica salvo forzar=True.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def ejecutar_desde_archivo(self, ruta_archivo: str, texto_manual_ocr: str = "", forzar: bool = False) -> Dict[str, Any]:
        preparacion = self.core.base_importador_universal_facturas.preparar_importacion(
            ruta_archivo,
            texto_manual_ocr=texto_manual_ocr,
        )
        return self.ejecutar_preparacion(preparacion, forzar=forzar)

    def ejecutar_preparacion(self, preparacion: Dict[str, Any], forzar: bool = False) -> Dict[str, Any]:
        errores = []
        avisos = list(preparacion.get("avisos", []))

        if not preparacion.get("ok"):
            return {
                "ok": False,
                "aplicado": False,
                "preparacion": preparacion,
                "errores": ["La preparación no es válida."],
                "avisos": avisos,
                "lectura_host_ai": "No se ejecutó importación: preparación inválida.",
            }

        if preparacion.get("requiere_revision") and not forzar:
            resultado_bloqueado = {
                "ok": True,
                "aplicado": False,
                "preparacion": preparacion,
                "errores": ["La importación requiere revisión. Usa forzar=True para aplicar."],
                "avisos": avisos,
                "lectura_host_ai": "Importación preparada pero no aplicada por requerir revisión.",
            }
            auditoria = getattr(self.core, "auditoria_importaciones_universales", None)
            if auditoria is not None:
                resultado_bloqueado["auditoria"] = auditoria.registrar_resultado(resultado_bloqueado)
            return resultado_bloqueado

        informe_precios = preparacion.get("informe_precios", {})
        informe_stock = preparacion.get("informe_stock", {})

        aplicacion_precios = self.core.actualizador_inteligente_precios_factura.aplicar_informe(
            informe_precios,
            forzar=forzar,
        )
        aplicacion_stock = self.core.actualizador_inteligente_stock_factura.aplicar_informe(
            informe_stock,
            forzar=forzar,
        )
        reconciliacion = self.core.reconciliador_stock_factura.reconciliar_informe(informe_stock)

        aplicado = (
            aplicacion_precios.get("bloqueados", 0) == 0 and
            aplicacion_stock.get("bloqueados", 0) == 0
        )

        datos = {
            "ok": True,
            "aplicado": aplicado,
            "forzado": forzar,
            "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
            "preparacion": preparacion,
            "aplicacion_precios": aplicacion_precios,
            "aplicacion_stock": aplicacion_stock,
            "reconciliacion_stock": reconciliacion,
            "errores": errores,
            "avisos": avisos,
            "lectura_host_ai": (
                f"Importación ejecutada: precios {aplicacion_precios.get('aplicados', 0)} aplicados, "
                f"stock {aplicacion_stock.get('aplicados', 0)} aplicado."
            ),
        }
        auditoria = getattr(self.core, "auditoria_importaciones_universales", None)
        if auditoria is not None:
            datos["auditoria"] = auditoria.registrar_resultado(datos)
        return datos

    def exportar_resultado(self, resultado: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "resultado_ejecucion_importacion_universal.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Resultado ejecución importación exportado: {destino.name}.",
        }
