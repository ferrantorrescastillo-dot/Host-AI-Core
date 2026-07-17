"""Orquestador central de intenciones de Host AI.

Convierte una solicitud de alto nivel en una llamada al pipeline, motor o
servicio adecuado. RC2.2 solo anade documentacion y normalizacion segura de
entrada, manteniendo la compatibilidad con las intenciones actuales.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List

@dataclass
class SolicitudHostAI:
    """Solicitud normalizada que recibe el orquestador."""
    intencion: str
    parametros: Dict[str, Any]
    def to_dict(self): return asdict(self)

@dataclass
class RespuestaHostAI:
    """Respuesta estandar devuelta por el orquestador."""
    ok: bool
    intencion: str
    mensaje: str
    datos: Dict[str, Any]
    acciones_recomendadas: List[str]
    requiere_aprobacion: bool = False
    def to_dict(self): return asdict(self)

class OrquestadorHostAI:
    """Resuelve intenciones y coordina llamadas al nucleo de Host AI."""

    def __init__(self, core):
        self.core = core

    @staticmethod
    def _normalizar_intencion(intencion: str) -> str:
        """Normaliza el nombre de intencion sin alterar su significado."""
        return (intencion or "").strip().lower()

    @staticmethod
    def _normalizar_parametros(parametros):
        """Garantiza que los parametros sean siempre un diccionario usable."""
        return parametros or {}

    def resolver(self, solicitud):
        """Resuelve una solicitud Host AI y devuelve una respuesta estructurada."""
        intencion = self._normalizar_intencion(solicitud.intencion)
        p = self._normalizar_parametros(solicitud.parametros)
        try:
            if intencion == "memoria_limpiar":
                self.core.memoria.limpiar_memoria()
                return RespuestaHostAI(True, intencion, "Memoria operacional limpiada.", {}, [])

            if intencion == "listar_pipelines":
                datos = {"pipelines": self.core.registro_pipelines.listar()}
                return self._responder(RespuestaHostAI(True, intencion, f"Pipelines registrados: {len(datos['pipelines'])}.", datos, ["Elegir pipeline y acción a ejecutar."]))

            if intencion == "ejecutar_pipeline":
                resultado = self.core.director.ejecutar_pipeline(p["pipeline"], p["accion"], p.get("parametros", {}))
                return self._desde_resultado(intencion, resultado)

            mapas = {
                "evento": {
                    "crear_evento": "crear",
                    "listar_eventos": "listar",
                    "buscar_eventos": "buscar",
                    "editar_evento": "editar",
                    "eliminar_evento": "eliminar",
                    "duplicar_evento": "duplicar",
                    "agregar_servicio_evento": "agregar_servicio",
                    "agregar_pase_evento": "agregar_pase",
                    "agregar_plato_evento": "agregar_plato",
                    "linea_temporal_evento": "linea_temporal",
                    "diagnosticar_evento": "diagnosticar",
                    "simular_produccion_evento": "simular_produccion",
                },
                "stock": {
                    "registrar_entrada_stock": "registrar_entrada",
                    "consumir_stock": "consumir",
                    "stock_actual": "stock_actual",
                    "diagnosticar_stock": "diagnosticar",
                    "ajustar_minimo_stock": "ajustar_minimo",
                    "predecir_necesidad_stock": "predecir_necesidad",
                    "movimientos_stock": "movimientos",
                },
                "compras": {
                    "registrar_necesidad_compra": "registrar_necesidad",
                    "listar_necesidades_compra": "listar_necesidades",
                    "buscar_necesidades_compra": "buscar_necesidades",
                    "editar_necesidad_compra": "editar_necesidad",
                    "cambiar_estado_necesidad_compra": "cambiar_estado_necesidad",
                    "eliminar_necesidad_compra": "eliminar_necesidad",
                    "generar_pedidos_sugeridos": "generar_pedidos_sugeridos",
                    "listar_pedidos_compra": "listar_pedidos",
                    "editar_pedido_compra": "editar_pedido",
                    "agregar_linea_pedido_compra": "agregar_linea_pedido",
                    "editar_linea_pedido_compra": "editar_linea_pedido",
                    "eliminar_linea_pedido_compra": "eliminar_linea_pedido",
                    "cambiar_estado_pedido_compra": "cambiar_estado_pedido",
                    "recibir_pedido_compra": "recibir_pedido",
                    "historial_pedido_compra": "historial_pedido",
                    "diagnosticar_compras": "diagnosticar",
                    "generar_propuesta_inteligente_compra": "generar_propuesta_inteligente",
                    "listar_propuestas_compra": "listar_propuestas",
                    "confirmar_propuesta_compra": "confirmar_propuesta",
                    "cancelar_propuesta_compra": "cancelar_propuesta",
                    "registrar_compra_manual": "registrar_compra_manual",
                    "listar_historial_compras": "listar_historial_compras",
                    "listar_proveedores_compra": "listar_proveedores",
                    "crear_proveedor_manual": "crear_proveedor_manual",
                    "editar_proveedor_compra": "editar_proveedor",
                    "desactivar_proveedor_compra": "desactivar_proveedor",
                    "asociar_producto_proveedor_compra": "asociar_producto_proveedor",
                    "preparar_onboarding_proveedor_detectado": "preparar_onboarding_proveedor_detectado",
                },
                "produccion_completa": {
                    "analizar_produccion_completa_evento": "analizar_evento",
                    "generar_pedidos_desde_evento": "generar_pedidos_desde_evento",
                    "listar_informes_produccion_completa": "listar_informes",
                },
                "escandallos": {
                    "registrar_escandallo": "registrar_escandallo",
                    "listar_escandallos": "listar_escandallos",
                    "buscar_escandallos": "buscar_escandallos",
                    "editar_escandallo": "editar_escandallo",
                    "agregar_linea_escandallo": "agregar_linea",
                    "editar_linea_escandallo": "editar_linea",
                    "eliminar_linea_escandallo": "eliminar_linea",
                    "duplicar_escandallo": "duplicar_escandallo",
                    "eliminar_escandallo": "eliminar_escandallo",
                    "calcular_escandallo_receta": "calcular_receta",
                    "calcular_escandallo_evento": "calcular_evento",
                },
                "costes": {
                    "registrar_precio": "registrar_precio",
                    "listar_precios": "listar_precios",
                    "calcular_coste_receta": "calcular_receta",
                    "calcular_coste_evento": "calcular_evento",
                    "simular_variacion_precio_receta": "simular_variacion_precio_receta",
                    "diagnosticar_coste_evento": "diagnosticar_evento",
                },
                "produccion_real": {
                    "planificar_produccion_real_evento": "planificar_evento",
                    "listar_planes_produccion_real": "listar_planes",
                    "diagnosticar_plan_produccion_real": "diagnosticar_plan",
                    "repartir_trabajo_produccion_real": "repartir_trabajo",
                },
                "ia_culinaria": {
                    "proponer_platos_stock": "proponer_platos_stock",
                    "crear_idea_culinaria": "crear_idea",
                    "analizar_idea_culinaria": "analizar_idea",
                    "convertir_idea_escandallo": "convertir_idea_escandallo",
                },
                "asistente": {
                    "chat_host_ai": "responder",
                    "detectar_intencion_chat": "detectar_intencion",
                    "historial_chat": "historial",
                },
                "persistencia": {
                    "guardar_todo_db": "guardar_todo",
                    "resumen_db": "resumen_db",
                    "snapshot_db": "snapshot",
                    "limpiar_db": "limpiar_db",
                },
                "excel": {
                    "analizar_excel": "analizar_excel",
                    "exportar_analisis_excel": "exportar_analisis",
                },
                "detector_excel": {
                    "detectar_documento_excel": "detectar_archivo",
                    "detectar_documento_desde_analisis_excel": "detectar_desde_analisis",
                },
                "mapeador_columnas_excel": {
                    "mapear_columnas_excel": "mapear_archivo",
                    "mapear_columnas_desde_deteccion_excel": "mapear_desde_deteccion",
                    "aprender_columna_excel": "aprender_columna",
                    "listar_diccionario_columnas_excel": "listar_diccionario",
                    "exportar_diccionario_columnas_excel": "exportar_diccionario",
                },
                "importador_escandallos_excel": {
                    "vista_previa_escandallos_excel": "vista_previa",
                    "importar_escandallos_excel": "importar",
                },
                "importador_articulos_excel": {
                    "vista_previa_articulos_excel": "vista_previa",
                    "importar_articulos_excel": "importar",
                    "listar_articulos_importados_excel": "listar_articulos",
                },
                "importador_inventario_excel": {
                    "vista_previa_inventario_excel": "vista_previa",
                    "importar_inventario_excel": "importar",
                    "comparar_inventario_excel": "comparar",
                },
                "conflictos_excel": {
                    "analizar_conflictos_excel": "analizar",
                    "resumen_conflictos_excel": "resumen",
                    "resolver_conflicto_excel": "resolver",
                },
                "asistente_importacion_excel": {
                    "preparar_importacion_excel": "preparar",
                    "ejecutar_importacion_excel": "ejecutar",
                    "listar_sesiones_importacion_excel": "listar_sesiones",
                },
                "pdf_facturas": {
                    "analizar_pdf_factura": "analizar_pdf",
                    "detectar_factura_texto": "detectar_factura_texto",
                    "exportar_analisis_pdf": "exportar_analisis_pdf",
                },
                "proveedores_pdf": {
                    "detectar_proveedor_pdf": "detectar_en_pdf",
                    "detectar_proveedor_texto": "detectar_desde_texto",
                    "aprender_proveedor_pdf": "aprender",
                    "listar_proveedores_pdf": "listar",
                    "exportar_diccionario_proveedores_pdf": "exportar",
                },
                "base_lineas_factura": {
                    "crear_linea_factura_demo": "crear_linea_demo",
                    "crear_bloque_lineas_factura_demo": "crear_bloque_demo",
                    "validar_bloque_lineas_factura": "validar_bloque",
                    "exportar_bloque_lineas_factura": "exportar_bloque",
                },
                "parser_lineas_factura": {
                    "leer_lineas_factura_texto": "leer_texto",
                    "leer_lineas_factura_pdf": "leer_pdf",
                    "exportar_lineas_factura": "exportar_lineas",
                },
                "detector_campos_linea_factura": {
                    "detectar_campos_linea_factura": "detectar_linea",
                    "detectar_campos_lote_factura": "detectar_lote",
                    "exportar_campos_linea_factura": "exportar",
                },
                "lector_completo_lineas_factura": {
                    "leer_factura_pdf_completa": "leer_pdf_completo",
                    "leer_factura_texto_completa": "leer_texto_completo",
                    "exportar_lectura_factura_completa": "exportar",
                },
                "validador_lineas_factura": {
                    "validar_linea_factura": "validar_linea",
                    "validar_factura_completa": "validar_factura",
                    "validar_factura_texto": "validar_texto",
                    "validar_factura_pdf": "validar_pdf",
                    "exportar_validacion_factura": "exportar",
                },
                "base_relacion_articulos_factura": {
                    "crear_relacion_articulo_factura_demo": "crear_relacion_demo",
                    "crear_informe_relacion_articulos_demo": "crear_informe_demo",
                    "validar_informe_relacion_articulos": "validar_informe",
                    "exportar_informe_relacion_articulos": "exportar_informe",
                },
                "buscador_articulos_parecidos": {
                    "buscar_articulo_parecido": "buscar",
                    "buscar_articulos_parecidos_lote": "buscar_lote",
                    "exportar_busqueda_articulos_parecidos": "exportar",
                },
                "relacionador_automatico_articulos_factura": {
                    "relacionar_linea_articulo_factura": "relacionar_linea",
                    "relacionar_bloque_articulos_factura": "relacionar_bloque",
                    "relacionar_factura_texto_articulos": "relacionar_texto",
                    "relacionar_factura_pdf_articulos": "relacionar_pdf",
                    "exportar_relacion_articulos_factura": "exportar",
                },
                "aprendizaje_relacion_proveedor": {
                    "aprender_relacion_proveedor_articulo": "aprender",
                    "buscar_aprendizaje_proveedor_articulo": "buscar",
                    "aplicar_aprendizaje_linea_factura": "aplicar_linea",
                    "aplicar_aprendizaje_bloque_factura": "aplicar_bloque",
                    "listar_aprendizajes_proveedor_articulo": "listar",
                    "exportar_aprendizajes_proveedor_articulo": "exportar",
                },
                "validador_relaciones_articulos_factura": {
                    "validar_relacion_articulo_factura": "validar_relacion",
                    "validar_informe_relaciones_articulos": "validar_informe",
                    "validar_relaciones_factura_texto": "validar_texto",
                    "exportar_validacion_relaciones_articulos": "exportar",
                },
                "base_actualizacion_precios_factura": {
                    "preparar_cambio_precio_factura": "preparar_cambio",
                    "preparar_informe_precios_factura": "preparar_informe",
                    "exportar_informe_precios_factura": "exportar",
                },
                "actualizador_inteligente_precios_factura": {
                    "aplicar_cambio_precio_factura": "aplicar_cambio",
                    "aplicar_informe_precios_factura": "aplicar_informe",
                    "preparar_y_aplicar_precios_factura": "preparar_y_aplicar",
                    "listar_log_actualizacion_precios": "listar_log",
                    "exportar_log_actualizacion_precios": "exportar_log",
                },
                "historico_inteligente_precios": {
                    "registrar_precio_historico": "registrar",
                    "registrar_historico_desde_aplicacion": "registrar_desde_aplicacion",
                    "analizar_historico_articulo": "analizar_articulo",
                    "listar_historico_precios": "listar",
                    "exportar_historico_precios": "exportar",
                },
                "comparador_proveedores_precios": {
                    "comparar_proveedores_articulo": "comparar_articulo",
                    "comparar_proveedores_todos": "comparar_todos",
                    "exportar_comparacion_proveedores": "exportar",
                },
                "alertas_inteligentes_precios": {
                    "generar_alertas_precio_articulo": "generar_articulo",
                    "generar_alertas_precios_todos": "generar_todos",
                    "listar_alertas_precios": "listar",
                    "exportar_alertas_precios": "exportar",
                },
                "base_actualizacion_stock_factura": {
                    "preparar_movimiento_stock_factura": "preparar_movimiento",
                    "preparar_informe_stock_factura": "preparar_informe",
                    "exportar_informe_stock_factura": "exportar",
                },
                "actualizador_inteligente_stock_factura": {
                    "aplicar_movimiento_stock_factura": "aplicar_movimiento",
                    "aplicar_informe_stock_factura": "aplicar_informe",
                    "preparar_y_aplicar_stock_factura": "preparar_y_aplicar",
                    "consultar_stock_articulo_factura": "stock_articulo",
                    "listar_log_actualizacion_stock": "listar_log",
                    "exportar_log_actualizacion_stock": "exportar_log",
                },
                "historico_inteligente_stock": {
                    "registrar_movimiento_stock_historico": "registrar",
                    "registrar_historico_stock_desde_aplicacion": "registrar_desde_aplicacion",
                    "analizar_historico_stock_articulo": "analizar_articulo",
                    "listar_historico_stock": "listar",
                    "exportar_historico_stock": "exportar",
                },
                "alertas_inteligentes_stock": {
                    "generar_alertas_stock_articulo": "generar_articulo",
                    "generar_alertas_stock_todos": "generar_todos",
                    "listar_alertas_stock": "listar",
                    "exportar_alertas_stock": "exportar",
                },
                "reconciliador_stock_factura": {
                    "reconciliar_movimiento_stock_factura": "reconciliar_movimiento",
                    "reconciliar_informe_stock_factura": "reconciliar_informe",
                    "exportar_reconciliacion_stock_factura": "exportar",
                },
                "base_ocr_documentos": {
                    "diagnosticar_ocr_archivo": "diagnosticar_archivo",
                    "diagnosticar_ocr_lote": "diagnosticar_lote",
                    "exportar_diagnostico_ocr": "exportar",
                },
                "motor_ocr_simulado": {
                    "registrar_texto_ocr_manual": "registrar_texto_manual",
                    "extraer_texto_ocr": "extraer_texto",
                    "exportar_resultado_ocr": "exportar",
                },
                "lector_facturas_con_ocr": {
                    "leer_factura_archivo_con_ocr": "leer_archivo",
                    "validar_y_relacionar_factura_ocr": "validar_y_relacionar",
                    "exportar_lectura_factura_ocr": "exportar",
                },
                "validador_corrector_ocr": {
                    "validar_texto_ocr": "validar_texto",
                    "validar_resultado_ocr": "validar_resultado_ocr",
                    "exportar_validacion_ocr": "exportar",
                },
                "base_importador_universal_facturas": {
                    "planificar_importacion_factura": "planificar",
                    "preparar_importacion_factura": "preparar",
                    "exportar_preparacion_importacion_factura": "exportar",
                },
                "ejecutor_importador_universal_facturas": {
                    "ejecutar_importacion_factura_archivo": "ejecutar_archivo",
                    "ejecutar_importacion_factura_preparada": "ejecutar_preparacion",
                    "exportar_resultado_importacion_factura": "exportar",
                },
                "auditoria_importaciones_universales": {
                    "registrar_auditoria_importacion": "registrar",
                    "listar_auditoria_importaciones": "listar",
                    "resumen_auditoria_importaciones": "resumen",
                    "exportar_auditoria_importaciones": "exportar",
                },
                "resumen_ejecutivo_importaciones": {
                    "generar_resumen_importaciones": "generar",
                    "exportar_resumen_importaciones": "exportar",
                },
                "cierre_importador_universal": {
                    "comprobar_cierre_importador_universal": "comprobar",
                    "exportar_cierre_importador_universal": "exportar",
                },
                "analizador_inteligente_compras": {
                    "analizar_compras": "analizar",
                    "exportar_analisis_compras": "exportar",
                },
                "motor_recomendaciones_compras": {
                    "generar_recomendaciones_compras": "generar",
                    "exportar_recomendaciones_compras": "exportar",
                },
                "detector_anomalias_compras": {
                    "detectar_anomalias_compras": "detectar",
                    "exportar_anomalias_compras": "exportar",
                },
                "prediccion_inteligente_precios": {
                    "predecir_precios_compras": "predecir",
                    "predecir_precio_articulo": "predecir_articulo",
                    "exportar_prediccion_precios": "exportar",
                },
                "comparador_inteligente_proveedores": {
                    "comparar_inteligente_proveedores_compras": "comparar",
                    "comparar_inteligente_proveedores_articulo": "comparar_articulo",
                    "exportar_comparador_inteligente_proveedores": "exportar",
                },
                "prediccion_roturas_stock": {
                    "predecir_roturas_stock": "predecir",
                    "predecir_rotura_articulo": "predecir_articulo",
                    "exportar_prediccion_roturas_stock": "exportar",
                },
                "motor_inteligente_pedidos": {
                    "generar_pedidos_inteligentes": "generar",
                    "generar_pedido_inteligente_articulo": "generar_articulo",
                    "exportar_pedidos_inteligentes": "exportar",
                },
                "cierre_inteligencia_compras": {
                    "comprobar_cierre_inteligencia_compras": "comprobar",
                    "exportar_cierre_inteligencia_compras": "exportar",
                },
                "analizador_inteligente_stock": {
                    "analizar_inteligente_stock": "analizar",
                    "exportar_analisis_inteligente_stock": "exportar",
                },
                "motor_alertas_stock": {
                    "generar_alertas_inteligentes_stock": "generar",
                    "exportar_alertas_inteligentes_stock": "exportar",
                },
                "control_inteligente_movimientos_stock": {
                    "controlar_movimientos_stock": "analizar",
                    "exportar_control_movimientos_stock": "exportar",
                },
                "reconciliador_inteligente_stock": {
                    "reconciliar_inteligente_stock": "reconciliar",
                    "exportar_reconciliacion_inteligente_stock": "exportar",
                },
                "prediccion_necesidades_stock": {
                    "predecir_necesidades_stock": "predecir",
                    "exportar_prediccion_necesidades_stock": "exportar",
                },
                "optimizador_stock": {
                    "optimizar_stock": "optimizar",
                    "exportar_optimizacion_stock": "exportar",
                },
                "stock_por_ubicaciones": {
                    "analizar_stock_ubicaciones": "analizar",
                    "mover_stock_ubicacion": "mover",
                    "exportar_stock_ubicaciones": "exportar",
                },
                "cierre_gestion_inteligente_stock": {
                    "cerrar_gestion_inteligente_stock": "cerrar",
                    "exportar_cierre_gestion_inteligente_stock": "exportar",
                },
                "analizador_inteligente_produccion": {
                    "analizar_inteligente_produccion": "analizar",
                    "exportar_analisis_inteligente_produccion": "exportar",
                },
                "motor_alertas_produccion": {
                    "generar_alertas_produccion": "generar",
                    "exportar_alertas_produccion": "exportar",
                },
                "planificador_inteligente_produccion": {
                    "planificar_inteligente_produccion": "planificar",
                    "exportar_planificacion_produccion": "exportar",
                },
                "asignador_recursos_produccion": {
                    "asignar_recursos_produccion": "asignar",
                    "exportar_asignacion_recursos_produccion": "exportar",
                },
                "control_ejecucion_produccion": {
                    "controlar_ejecucion_produccion": "controlar",
                    "exportar_control_ejecucion_produccion": "exportar",
                },
                "replanificador_inteligente_produccion": {
                    "replanificar_inteligente_produccion": "replanificar",
                    "exportar_replanificacion_produccion": "exportar",
                },
                "optimizador_inteligente_produccion": {
                    "optimizar_inteligente_produccion": "optimizar",
                    "exportar_optimizacion_produccion": "exportar",
                },
                "cierre_inteligente_produccion": {
                    "comprobar_cierre_inteligente_produccion": "comprobar",
                    "exportar_cierre_inteligente_produccion": "exportar",
                },
                "analizador_inteligente_escandallos": {
                    "analizar_inteligente_escandallos": "analizar",
                    "exportar_analisis_inteligente_escandallos": "exportar",
                },
                "motor_alertas_escandallos": {
                    "generar_alertas_escandallos": "generar",
                    "exportar_alertas_escandallos": "exportar",
                },
                "optimizador_inteligente_recetas": {
                    "optimizar_inteligente_recetas": "optimizar",
                    "exportar_optimizacion_inteligente_recetas": "exportar",
                },
                "comparador_historico_escandallos": {
                    "comparar_historico_escandallos": "comparar",
                    "exportar_comparador_historico_escandallos": "exportar",
                },
                "simulador_costes_escandallos": {
                    "simular_costes_escandallos": "simular",
                    "exportar_simulacion_costes_escandallos": "exportar",
                },
                "prediccion_inteligente_rentabilidad": {
                    "predecir_inteligente_rentabilidad": "predecir",
                    "exportar_prediccion_inteligente_rentabilidad": "exportar",
                },
                "motor_optimizacion_carta": {
                    "optimizar_carta_inteligente": "optimizar",
                    "exportar_optimizacion_carta": "exportar",
                },
                "cierre_escandallos_inteligentes": {
                    "comprobar_cierre_escandallos_inteligentes": "comprobar",
                    "exportar_cierre_escandallos_inteligentes": "exportar",
                },
                "analizador_lenguaje_natural": {
                    "analizar_lenguaje_natural": "analizar",
                    "exportar_analisis_lenguaje_natural": "exportar",
                },
                "motor_conversacional_308": {
                    "conversar_host_ai_308": "responder",
                    "historial_conversacional_308": "historial",
                    "limpiar_conversacion_308": "limpiar",
                    "exportar_conversacion_308": "exportar",
                },
                "selector_inteligente_motores_308": {
                    "seleccionar_motor_host_ai_308": "seleccionar",
                    "seleccionar_motor_desde_conversacion_308": "seleccionar_desde_conversacion",
                },
                "generador_inteligente_respuestas_308": {
                    "generar_respuesta_host_ai_308": "generar",
                    "generar_respuesta_desde_texto_308": "generar_desde_texto",
                },
                "memoria_conversacional_308": {
                    "recordar_memoria_conversacional_308": "recordar",
                    "consultar_memoria_conversacional_308": "consultar",
                    "resolver_referencias_memoria_308": "resolver_referencias",
                    "aprender_desde_turno_memoria_308": "aprender_desde_turno",
                    "limpiar_memoria_conversacional_308": "limpiar",
                    "exportar_memoria_conversacional_308": "exportar",
                },
                "automatizador_inteligente_308": {
                    "preparar_automatizacion_308": "preparar",
                    "ejecutar_automatizacion_308": "ejecutar",
                    "validar_confirmacion_automatizacion_308": "validar_confirmacion",
                },
                "asistente_inteligente_host_ai_308": {
                    "asistente_host_ai_308": "responder",
                    "diagnosticar_asistente_host_ai_308": "diagnosticar",
                    "exportar_asistente_host_ai_308": "exportar",
                },
                "cierre_ia_conversacional_308": {
                    "comprobar_cierre_ia_conversacional_308": "comprobar",
                    "exportar_cierre_ia_conversacional_308": "exportar",
                },
            }

            for pipeline, mapa in mapas.items():
                if intencion in mapa:
                    resultado = self.core.director.ejecutar_pipeline(pipeline, mapa[intencion], p)
                    return self._desde_resultado(intencion, resultado)

            return self._responder(RespuestaHostAI(False, intencion, f"Intención no soportada todavía: {intencion}", {}, ["Crear handler en OrquestadorHostAI."]))

        except Exception as exc:
            return self._responder(RespuestaHostAI(False, intencion, f"Error resolviendo solicitud: {exc}", {"error": str(exc)}, ["Revisar parámetros de entrada."]))

    def _desde_resultado(self, intencion, resultado):
        return self._responder(RespuestaHostAI(resultado.ok, intencion, resultado.mensaje, {"resultado_pipeline": resultado.to_dict(), **resultado.datos}, resultado.acciones_recomendadas, resultado.requiere_aprobacion))

    def _responder(self, respuesta):
        if hasattr(self.core, "memoria") and respuesta.intencion != "memoria_limpiar":
            try:
                self.core.memoria.registrar_respuesta_orquestador(respuesta.intencion, respuesta.to_dict())
            except Exception:
                pass
        return respuesta
