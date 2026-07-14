"""Nucleo principal de Host AI.

Este módulo actúa como `composition root` y sigue el flujo de arranque
documentado para facilitar la mantenibilidad. Etapas principales:

1) Entrada al sistema (módulo `main.py`).
2) Creación de `HostAICore` (esta clase).
3) Registro/creación de servicios auxiliares (importadores, OCR, analizadores).
4) Registro/creación de motores de dominio (memoria, compras, stock, producción).
5) Registro de pipelines disponibles (`RegistroPipelines`).
6) Exposición de `DirectorHostAI` y `OrquestadorHostAI` para ejecutar pipelines.
7) El lanzador/console inicia la interacción con el usuario.

Se preserva el orden de inicialización y la API pública; los cambios son
meramente organizativos y documentales.
"""

import json
from pathlib import Path

from CORE.orquestador import OrquestadorHostAI
from CORE.registro_pipelines import RegistroPipelines
from CORE.director_host_ai import DirectorHostAI
from MOTORES.motor_memoria_operacional import MotorMemoriaOperacional
from MOTORES.motor_compras import MotorCompras
from MOTORES.motor_stock import MotorStock
from MOTORES.motor_eventos import MotorEventos
from MOTORES.motor_simulador_produccion_evento import MotorSimuladorProduccionEvento
from MOTORES.motor_produccion_completa import MotorProduccionCompleta
from MOTORES.motor_escandallos_inteligente import MotorEscandallosInteligente
from MOTORES.motor_costes_inteligente import MotorCostesInteligente
from MOTORES.motor_produccion_real import MotorProduccionReal
from MOTORES.motor_ia_culinaria import MotorIACulinaria
from MOTORES.motor_asistente_conversacional import MotorAsistenteConversacional
from SERVICIOS.base_datos_local import BaseDatosLocal
from MOTORES.motor_persistencia import MotorPersistencia
from SERVICIOS.lector_excel import LectorUniversalExcel
from SERVICIOS.detector_documentos_excel import DetectorDocumentosExcel
from SERVICIOS.mapeador_columnas_excel import MapeadorColumnasExcel
from SERVICIOS.importador_escandallos_excel import ImportadorEscandallosExcel
from SERVICIOS.importador_articulos_excel import ImportadorArticulosExcel
from SERVICIOS.importador_inventario_excel import ImportadorInventarioExcel
from SERVICIOS.resolutor_conflictos_excel import ResolutorConflictosExcel
from SERVICIOS.asistente_importacion_excel import AsistenteImportacionExcel
from SERVICIOS.lector_pdf_facturas import LectorPDFFacturas
from SERVICIOS.detector_proveedores_pdf import DetectorProveedoresPDF
from SERVICIOS.base_lineas_factura import BaseLineasFactura
from SERVICIOS.parser_lineas_factura import ParserLineasFactura
from SERVICIOS.detector_campos_linea_factura import DetectorCamposLineaFactura
from SERVICIOS.lector_completo_lineas_factura import LectorCompletoLineasFactura
from SERVICIOS.validador_lineas_factura import ValidadorLineasFactura
from SERVICIOS.base_relacion_articulos_factura import BaseRelacionArticulosFactura
from SERVICIOS.buscador_articulos_parecidos import BuscadorArticulosParecidos
from SERVICIOS.relacionador_automatico_articulos_factura import RelacionadorAutomaticoArticulosFactura
from SERVICIOS.aprendizaje_relacion_proveedor import AprendizajeRelacionProveedorArticulos
from SERVICIOS.validador_relaciones_articulos_factura import ValidadorRelacionesArticulosFactura
from SERVICIOS.base_actualizacion_precios_factura import BaseActualizacionPreciosFactura
from SERVICIOS.actualizador_inteligente_precios_factura import ActualizadorInteligentePreciosFactura
from SERVICIOS.historico_inteligente_precios import HistoricoInteligentePrecios
from SERVICIOS.comparador_proveedores_precios import ComparadorProveedoresPrecios
from SERVICIOS.alertas_inteligentes_precios import AlertasInteligentesPrecios
from SERVICIOS.base_actualizacion_stock_factura import BaseActualizacionStockFactura
from SERVICIOS.actualizador_inteligente_stock_factura import ActualizadorInteligenteStockFactura
from SERVICIOS.historico_inteligente_stock import HistoricoInteligenteStock
from SERVICIOS.alertas_inteligentes_stock import AlertasInteligentesStock
from SERVICIOS.reconciliador_stock_factura import ReconciliadorStockFactura
from SERVICIOS.base_ocr_documentos import BaseOCRDocumentos
from SERVICIOS.motor_ocr_simulado import MotorOCRSimulado
from SERVICIOS.lector_facturas_con_ocr import LectorFacturasConOCR
from SERVICIOS.validador_corrector_ocr import ValidadorCorrectorOCR
from SERVICIOS.base_importador_universal_facturas import BaseImportadorUniversalFacturas
from SERVICIOS.ejecutor_importador_universal_facturas import EjecutorImportadorUniversalFacturas
from SERVICIOS.auditoria_importaciones_universales import AuditoriaImportacionesUniversales
from SERVICIOS.resumen_ejecutivo_importaciones import ResumenEjecutivoImportacionesServicio
from SERVICIOS.cierre_importador_universal import CierreImportadorUniversal
from SERVICIOS.analizador_inteligente_compras import AnalizadorInteligenteCompras
from SERVICIOS.motor_recomendaciones_compras import MotorRecomendacionesCompras
from SERVICIOS.detector_anomalias_compras import DetectorAnomaliasCompras
from SERVICIOS.prediccion_inteligente_precios import PrediccionInteligentePrecios
from SERVICIOS.comparador_inteligente_proveedores import ComparadorInteligenteProveedores
from SERVICIOS.prediccion_roturas_stock import PrediccionRoturasStock
from SERVICIOS.motor_inteligente_pedidos import MotorInteligentePedidos
from SERVICIOS.cierre_inteligencia_compras import CierreInteligenciaCompras
from SERVICIOS.analizador_inteligente_stock import AnalizadorInteligenteStock
from SERVICIOS.motor_alertas_stock import MotorAlertasStock
from SERVICIOS.control_inteligente_movimientos_stock import ControlInteligenteMovimientosStock
from SERVICIOS.reconciliador_inteligente_stock import ReconciliadorInteligenteStock
from SERVICIOS.prediccion_necesidades_stock import PrediccionNecesidadesStock
from SERVICIOS.optimizador_stock import OptimizadorStock
from SERVICIOS.stock_por_ubicaciones import StockPorUbicaciones
from SERVICIOS.cierre_gestion_inteligente_stock import CierreGestionInteligenteStock
from SERVICIOS.analizador_inteligente_produccion import AnalizadorInteligenteProduccion
from SERVICIOS.motor_alertas_produccion import MotorAlertasProduccion
from SERVICIOS.planificador_inteligente_produccion import PlanificadorInteligenteProduccion
from SERVICIOS.asignador_recursos_produccion import AsignadorRecursosProduccion
from SERVICIOS.control_ejecucion_produccion import ControlEjecucionProduccion
from SERVICIOS.replanificador_inteligente_produccion import ReplanificadorInteligenteProduccion
from SERVICIOS.optimizador_inteligente_produccion import OptimizadorInteligenteProduccion
from SERVICIOS.cierre_inteligente_produccion import CierreInteligenteProduccion
from SERVICIOS.analizador_inteligente_escandallos import AnalizadorInteligenteEscandallos
from SERVICIOS.motor_alertas_escandallos import MotorAlertasEscandallos
from SERVICIOS.optimizador_inteligente_recetas import OptimizadorInteligenteRecetas
from SERVICIOS.comparador_historico_escandallos import ComparadorHistoricoEscandallos
from SERVICIOS.simulador_costes_escandallos import SimuladorCostesEscandallos
from SERVICIOS.prediccion_inteligente_rentabilidad import PrediccionInteligenteRentabilidad
from SERVICIOS.motor_optimizacion_carta import MotorOptimizacionCarta
from SERVICIOS.cierre_escandallos_inteligentes import CierreEscandallosInteligentes
from SERVICIOS.analizador_lenguaje_natural import AnalizadorLenguajeNatural
from SERVICIOS.motor_intenciones_ia11 import MotorIntencionesIA11
from SERVICIOS.comprension_conversacional_ia13 import ComprensionConversacionalIA13
from SERVICIOS.integracion_motores_ia14 import IntegracionMotoresIA14
from SERVICIOS.pulido_ia_rr15 import PulidoIARR15
from SERVICIOS.extractor_datos_ia12 import ExtractorDatosIA12
from SERVICIOS.motor_conversacional_308 import MotorConversacional308
from SERVICIOS.selector_inteligente_motores import SelectorInteligenteMotores308
from SERVICIOS.generador_inteligente_respuestas import GeneradorInteligenteRespuestas308
from SERVICIOS.memoria_conversacional_308 import MemoriaConversacional308Servicio
from SERVICIOS.automatizador_inteligente_308 import AutomatizadorInteligente308
from SERVICIOS.asistente_inteligente_host_ai_308 import AsistenteInteligenteHostAI308
from SERVICIOS.cierre_ia_conversacional_308 import CierreIAConversacional308Servicio
from PIPELINES.pipeline_compras import PipelineCompras
from PIPELINES.pipeline_stock import PipelineStock
from PIPELINES.pipeline_evento import PipelineEvento
from PIPELINES.pipeline_produccion_completa import PipelineProduccionCompleta
from PIPELINES.pipeline_escandallos import PipelineEscandallos
from PIPELINES.pipeline_costes import PipelineCostes
from PIPELINES.pipeline_produccion_real import PipelineProduccionReal
from PIPELINES.pipeline_ia_culinaria import PipelineIACulinaria
from PIPELINES.pipeline_asistente_conversacional import PipelineAsistenteConversacional
from PIPELINES.pipeline_persistencia import PipelinePersistencia
from PIPELINES.pipeline_excel import PipelineExcel
from PIPELINES.pipeline_detector_excel import PipelineDetectorExcel
from PIPELINES.pipeline_mapeador_columnas_excel import PipelineMapeadorColumnasExcel
from PIPELINES.pipeline_importador_escandallos_excel import PipelineImportadorEscandallosExcel
from PIPELINES.pipeline_importador_articulos_excel import PipelineImportadorArticulosExcel
from PIPELINES.pipeline_importador_inventario_excel import PipelineImportadorInventarioExcel
from PIPELINES.pipeline_conflictos_excel import PipelineConflictosExcel
from PIPELINES.pipeline_asistente_importacion_excel import PipelineAsistenteImportacionExcel
from PIPELINES.pipeline_pdf_facturas import PipelinePDFFacturas
from PIPELINES.pipeline_proveedores_pdf import PipelineProveedoresPDF
from PIPELINES.pipeline_base_lineas_factura import PipelineBaseLineasFactura
from PIPELINES.pipeline_parser_lineas_factura import PipelineParserLineasFactura
from PIPELINES.pipeline_detector_campos_linea_factura import PipelineDetectorCamposLineaFactura
from PIPELINES.pipeline_lector_completo_lineas_factura import PipelineLectorCompletoLineasFactura
from PIPELINES.pipeline_validador_lineas_factura import PipelineValidadorLineasFactura
from PIPELINES.pipeline_base_relacion_articulos_factura import PipelineBaseRelacionArticulosFactura
from PIPELINES.pipeline_buscador_articulos_parecidos import PipelineBuscadorArticulosParecidos
from PIPELINES.pipeline_relacionador_automatico_articulos_factura import PipelineRelacionadorAutomaticoArticulosFactura
from PIPELINES.pipeline_aprendizaje_relacion_proveedor import PipelineAprendizajeRelacionProveedor
from PIPELINES.pipeline_validador_relaciones_articulos_factura import PipelineValidadorRelacionesArticulosFactura
from PIPELINES.pipeline_base_actualizacion_precios_factura import PipelineBaseActualizacionPreciosFactura
from PIPELINES.pipeline_actualizador_inteligente_precios_factura import PipelineActualizadorInteligentePreciosFactura
from PIPELINES.pipeline_historico_inteligente_precios import PipelineHistoricoInteligentePrecios
from PIPELINES.pipeline_comparador_proveedores_precios import PipelineComparadorProveedoresPrecios
from PIPELINES.pipeline_alertas_inteligentes_precios import PipelineAlertasInteligentesPrecios
from PIPELINES.pipeline_base_actualizacion_stock_factura import PipelineBaseActualizacionStockFactura
from PIPELINES.pipeline_actualizador_inteligente_stock_factura import PipelineActualizadorInteligenteStockFactura
from PIPELINES.pipeline_historico_inteligente_stock import PipelineHistoricoInteligenteStock
from PIPELINES.pipeline_alertas_inteligentes_stock import PipelineAlertasInteligentesStock
from PIPELINES.pipeline_reconciliador_stock_factura import PipelineReconciliadorStockFactura
from PIPELINES.pipeline_base_ocr_documentos import PipelineBaseOCRDocumentos
from PIPELINES.pipeline_motor_ocr_simulado import PipelineMotorOCRSimulado
from PIPELINES.pipeline_lector_facturas_con_ocr import PipelineLectorFacturasConOCR
from PIPELINES.pipeline_validador_corrector_ocr import PipelineValidadorCorrectorOCR
from PIPELINES.pipeline_base_importador_universal_facturas import PipelineBaseImportadorUniversalFacturas
from PIPELINES.pipeline_ejecutor_importador_universal_facturas import PipelineEjecutorImportadorUniversalFacturas
from PIPELINES.pipeline_auditoria_importaciones_universales import PipelineAuditoriaImportacionesUniversales
from PIPELINES.pipeline_resumen_ejecutivo_importaciones import PipelineResumenEjecutivoImportaciones
from PIPELINES.pipeline_cierre_importador_universal import PipelineCierreImportadorUniversal
from PIPELINES.pipeline_analizador_inteligente_compras import PipelineAnalizadorInteligenteCompras
from PIPELINES.pipeline_motor_recomendaciones_compras import PipelineMotorRecomendacionesCompras
from PIPELINES.pipeline_detector_anomalias_compras import PipelineDetectorAnomaliasCompras
from PIPELINES.pipeline_prediccion_inteligente_precios import PipelinePrediccionInteligentePrecios
from PIPELINES.pipeline_comparador_inteligente_proveedores import PipelineComparadorInteligenteProveedores
from PIPELINES.pipeline_prediccion_roturas_stock import PipelinePrediccionRoturasStock
from PIPELINES.pipeline_motor_inteligente_pedidos import PipelineMotorInteligentePedidos
from PIPELINES.pipeline_cierre_inteligencia_compras import PipelineCierreInteligenciaCompras
from PIPELINES.pipeline_analizador_inteligente_stock import PipelineAnalizadorInteligenteStock
from PIPELINES.pipeline_motor_alertas_stock import PipelineMotorAlertasStock
from PIPELINES.pipeline_control_inteligente_movimientos_stock import PipelineControlInteligenteMovimientosStock
from PIPELINES.pipeline_reconciliador_inteligente_stock import PipelineReconciliadorInteligenteStock
from PIPELINES.pipeline_prediccion_necesidades_stock import PipelinePrediccionNecesidadesStock
from PIPELINES.pipeline_optimizador_stock import PipelineOptimizadorStock
from PIPELINES.pipeline_stock_por_ubicaciones import PipelineStockPorUbicaciones
from PIPELINES.pipeline_cierre_gestion_inteligente_stock import PipelineCierreGestionInteligenteStock
from PIPELINES.pipeline_analizador_inteligente_produccion import PipelineAnalizadorInteligenteProduccion
from PIPELINES.pipeline_motor_alertas_produccion import PipelineMotorAlertasProduccion
from PIPELINES.pipeline_planificador_inteligente_produccion import PipelinePlanificadorInteligenteProduccion
from PIPELINES.pipeline_asignador_recursos_produccion import PipelineAsignadorRecursosProduccion
from PIPELINES.pipeline_control_ejecucion_produccion import PipelineControlEjecucionProduccion
from PIPELINES.pipeline_replanificador_inteligente_produccion import PipelineReplanificadorInteligenteProduccion
from PIPELINES.pipeline_optimizador_inteligente_produccion import PipelineOptimizadorInteligenteProduccion
from PIPELINES.pipeline_cierre_inteligente_produccion import PipelineCierreInteligenteProduccion
from PIPELINES.pipeline_analizador_inteligente_escandallos import PipelineAnalizadorInteligenteEscandallos
from PIPELINES.pipeline_motor_alertas_escandallos import PipelineMotorAlertasEscandallos
from PIPELINES.pipeline_optimizador_inteligente_recetas import PipelineOptimizadorInteligenteRecetas
from PIPELINES.pipeline_comparador_historico_escandallos import PipelineComparadorHistoricoEscandallos
from PIPELINES.pipeline_simulador_costes_escandallos import PipelineSimuladorCostesEscandallos
from PIPELINES.pipeline_prediccion_inteligente_rentabilidad import PipelinePrediccionInteligenteRentabilidad
from PIPELINES.pipeline_motor_optimizacion_carta import PipelineMotorOptimizacionCarta
from PIPELINES.pipeline_cierre_escandallos_inteligentes import PipelineCierreEscandallosInteligentes
from PIPELINES.pipeline_analizador_lenguaje_natural import PipelineAnalizadorLenguajeNatural
from PIPELINES.pipeline_motor_conversacional_308 import PipelineMotorConversacional308
from PIPELINES.pipeline_selector_inteligente_motores import PipelineSelectorInteligenteMotores308
from PIPELINES.pipeline_generador_inteligente_respuestas import PipelineGeneradorInteligenteRespuestas308
from PIPELINES.pipeline_memoria_conversacional_308 import PipelineMemoriaConversacional308
from PIPELINES.pipeline_automatizador_inteligente_308 import PipelineAutomatizadorInteligente308
from PIPELINES.pipeline_asistente_inteligente_host_ai_308 import PipelineAsistenteInteligenteHostAI308
from PIPELINES.pipeline_cierre_ia_conversacional_308 import PipelineCierreIAConversacional308

class HostAICore:
    """Contenedor principal de dependencias de Host AI.

    Responsabilidades actuales:
    - Resolver rutas base y diccionarios.
    - Inicializar servicios y motores compartidos.
    - Registrar pipelines disponibles.
    - Exponer Director y Orquestador.

    Esta clase sigue actuando como composition root del proyecto.
    """

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(__file__).resolve().parents[1]
        self.diccionario_path = self.base_dir / "DATOS" / "diccionarios" / "diccionario_gastronomico_universal.json"
        self.diccionario = self._cargar_diccionario()
        # Crear DB local y continuar con inicializaciones en métodos privados.
        self.db = BaseDatosLocal(self.base_dir)
        self._inicializar_servicios()
        self._inicializar_motores()

        # Registro de pipelines y exposición de director/orquestador.
        self.registro_pipelines = RegistroPipelines()
        self._registrar_pipelines()
        self.motor_recomendaciones_compras = MotorRecomendacionesCompras(self)
        self.director = DirectorHostAI(self)
        self.orquestador = OrquestadorHostAI(self)

    def _registrar_pipelines(self):
        """Registrar pipelines disponibles; conserva el orden original."""
        self.registro_pipelines.registrar(PipelineEvento(self))
        self.registro_pipelines.registrar(PipelineCompras(self))
        self.registro_pipelines.registrar(PipelineStock(self))
        self.registro_pipelines.registrar(PipelineProduccionCompleta(self))
        self.registro_pipelines.registrar(PipelineEscandallos(self))
        self.registro_pipelines.registrar(PipelineCostes(self))
        self.registro_pipelines.registrar(PipelineProduccionReal(self))
        self.registro_pipelines.registrar(PipelineIACulinaria(self))
        self.registro_pipelines.registrar(PipelineAsistenteConversacional(self))
        self.registro_pipelines.registrar(PipelinePersistencia(self))
        self.registro_pipelines.registrar(PipelineExcel(self))
        self.registro_pipelines.registrar(PipelineDetectorExcel(self))
        self.registro_pipelines.registrar(PipelineMapeadorColumnasExcel(self))
        self.registro_pipelines.registrar(PipelineImportadorEscandallosExcel(self))
        self.registro_pipelines.registrar(PipelineImportadorArticulosExcel(self))
        self.registro_pipelines.registrar(PipelineImportadorInventarioExcel(self))
        self.registro_pipelines.registrar(PipelineConflictosExcel(self))
        self.registro_pipelines.registrar(PipelineAsistenteImportacionExcel(self))
        self.registro_pipelines.registrar(PipelinePDFFacturas(self))
        self.registro_pipelines.registrar(PipelineProveedoresPDF(self))
        self.registro_pipelines.registrar(PipelineBaseLineasFactura(self))
        self.registro_pipelines.registrar(PipelineParserLineasFactura(self))
        self.registro_pipelines.registrar(PipelineDetectorCamposLineaFactura(self))
        self.registro_pipelines.registrar(PipelineLectorCompletoLineasFactura(self))
        self.registro_pipelines.registrar(PipelineValidadorLineasFactura(self))
        self.registro_pipelines.registrar(PipelineBaseRelacionArticulosFactura(self))
        self.registro_pipelines.registrar(PipelineBuscadorArticulosParecidos(self))
        self.registro_pipelines.registrar(PipelineRelacionadorAutomaticoArticulosFactura(self))
        self.registro_pipelines.registrar(PipelineAprendizajeRelacionProveedor(self))
        self.registro_pipelines.registrar(PipelineValidadorRelacionesArticulosFactura(self))
        self.registro_pipelines.registrar(PipelineBaseActualizacionPreciosFactura(self))
        self.registro_pipelines.registrar(PipelineActualizadorInteligentePreciosFactura(self))
        self.registro_pipelines.registrar(PipelineHistoricoInteligentePrecios(self))
        self.registro_pipelines.registrar(PipelineComparadorProveedoresPrecios(self))
        self.registro_pipelines.registrar(PipelineAlertasInteligentesPrecios(self))
        self.registro_pipelines.registrar(PipelineBaseActualizacionStockFactura(self))
        self.registro_pipelines.registrar(PipelineActualizadorInteligenteStockFactura(self))
        self.registro_pipelines.registrar(PipelineHistoricoInteligenteStock(self))
        self.registro_pipelines.registrar(PipelineAlertasInteligentesStock(self))
        self.registro_pipelines.registrar(PipelineReconciliadorStockFactura(self))
        self.registro_pipelines.registrar(PipelineBaseOCRDocumentos(self))
        self.registro_pipelines.registrar(PipelineMotorOCRSimulado(self))
        self.registro_pipelines.registrar(PipelineLectorFacturasConOCR(self))
        self.registro_pipelines.registrar(PipelineValidadorCorrectorOCR(self))
        self.registro_pipelines.registrar(PipelineBaseImportadorUniversalFacturas(self))
        self.registro_pipelines.registrar(PipelineEjecutorImportadorUniversalFacturas(self))
        self.registro_pipelines.registrar(PipelineAuditoriaImportacionesUniversales(self))
        self.registro_pipelines.registrar(PipelineResumenEjecutivoImportaciones(self))
        self.registro_pipelines.registrar(PipelineCierreImportadorUniversal(self))
        self.registro_pipelines.registrar(PipelineAnalizadorInteligenteCompras(self))
        self.registro_pipelines.registrar(PipelineMotorRecomendacionesCompras(self))
        self.registro_pipelines.registrar(PipelineDetectorAnomaliasCompras(self))
        self.registro_pipelines.registrar(PipelinePrediccionInteligentePrecios(self))
        self.registro_pipelines.registrar(PipelineComparadorInteligenteProveedores(self))
        self.registro_pipelines.registrar(PipelinePrediccionRoturasStock(self))
        self.registro_pipelines.registrar(PipelineMotorInteligentePedidos(self))
        self.registro_pipelines.registrar(PipelineCierreInteligenciaCompras(self))
        self.registro_pipelines.registrar(PipelineAnalizadorInteligenteStock(self))
        self.registro_pipelines.registrar(PipelineMotorAlertasStock(self))
        self.registro_pipelines.registrar(PipelineControlInteligenteMovimientosStock(self))
        self.registro_pipelines.registrar(PipelineReconciliadorInteligenteStock(self))
        self.registro_pipelines.registrar(PipelinePrediccionNecesidadesStock(self))
        self.registro_pipelines.registrar(PipelineOptimizadorStock(self))
        self.registro_pipelines.registrar(PipelineStockPorUbicaciones(self))
        self.registro_pipelines.registrar(PipelineCierreGestionInteligenteStock(self))
        self.registro_pipelines.registrar(PipelineAnalizadorInteligenteProduccion(self))
        self.registro_pipelines.registrar(PipelineMotorAlertasProduccion(self))
        self.registro_pipelines.registrar(PipelinePlanificadorInteligenteProduccion(self))
        self.registro_pipelines.registrar(PipelineAsignadorRecursosProduccion(self))
        self.registro_pipelines.registrar(PipelineControlEjecucionProduccion(self))
        self.registro_pipelines.registrar(PipelineReplanificadorInteligenteProduccion(self))
        self.registro_pipelines.registrar(PipelineOptimizadorInteligenteProduccion(self))
        self.registro_pipelines.registrar(PipelineCierreInteligenteProduccion(self))
        self.registro_pipelines.registrar(PipelineAnalizadorInteligenteEscandallos(self))
        self.registro_pipelines.registrar(PipelineMotorAlertasEscandallos(self))
        self.registro_pipelines.registrar(PipelineOptimizadorInteligenteRecetas(self))
        self.registro_pipelines.registrar(PipelineComparadorHistoricoEscandallos(self))
        self.registro_pipelines.registrar(PipelineSimuladorCostesEscandallos(self))
        self.registro_pipelines.registrar(PipelinePrediccionInteligenteRentabilidad(self))
        self.registro_pipelines.registrar(PipelineMotorOptimizacionCarta(self))
        self.registro_pipelines.registrar(PipelineCierreEscandallosInteligentes(self))
        self.registro_pipelines.registrar(PipelineAnalizadorLenguajeNatural(self))
        self.registro_pipelines.registrar(PipelineMotorConversacional308(self))
        self.registro_pipelines.registrar(PipelineSelectorInteligenteMotores308(self))
        self.registro_pipelines.registrar(PipelineGeneradorInteligenteRespuestas308(self))
        self.registro_pipelines.registrar(PipelineMemoriaConversacional308(self))
        self.registro_pipelines.registrar(PipelineAutomatizadorInteligente308(self))
        self.registro_pipelines.registrar(PipelineAsistenteInteligenteHostAI308(self))
        self.registro_pipelines.registrar(PipelineCierreIAConversacional308(self))

    def _inicializar_servicios(self) -> None:
        """Inicializa servicios auxiliares (importadores, OCR, analizadores).

        Mantiene el mismo orden y las mismas instancias.
        """
        self.lector_excel = LectorUniversalExcel(self.base_dir)
        self.detector_excel = DetectorDocumentosExcel(self.lector_excel)
        self.mapeador_columnas_excel = MapeadorColumnasExcel(self.base_dir, self.detector_excel)
        self.importador_escandallos_excel = ImportadorEscandallosExcel(self)
        self.importador_articulos_excel = ImportadorArticulosExcel(self)
        self.importador_inventario_excel = ImportadorInventarioExcel(self)
        self.resolutor_conflictos_excel = ResolutorConflictosExcel(self)
        self.asistente_importacion_excel = AsistenteImportacionExcel(self)
        self.lector_pdf_facturas = LectorPDFFacturas(self.base_dir)
        self.detector_proveedores_pdf = DetectorProveedoresPDF(self.base_dir, self.lector_pdf_facturas)
        self.base_lineas_factura = BaseLineasFactura(self.base_dir)
        self.detector_campos_linea_factura = DetectorCamposLineaFactura(self.base_dir)
        self.parser_lineas_factura = ParserLineasFactura(self.base_dir, self.detector_campos_linea_factura)
        self.lector_completo_lineas_factura = LectorCompletoLineasFactura(self)
        self.validador_lineas_factura = ValidadorLineasFactura(self)
        self.base_relacion_articulos_factura = BaseRelacionArticulosFactura(self.base_dir)
        self.buscador_articulos_parecidos = BuscadorArticulosParecidos(self)
        self.aprendizaje_relacion_proveedor = AprendizajeRelacionProveedorArticulos(self)
        self.relacionador_automatico_articulos_factura = RelacionadorAutomaticoArticulosFactura(self)
        self.validador_relaciones_articulos_factura = ValidadorRelacionesArticulosFactura(self)
        self.base_actualizacion_precios_factura = BaseActualizacionPreciosFactura(self)
        self.historico_inteligente_precios = HistoricoInteligentePrecios(self)
        self.actualizador_inteligente_precios_factura = ActualizadorInteligentePreciosFactura(self)
        self.comparador_proveedores_precios = ComparadorProveedoresPrecios(self)
        self.alertas_inteligentes_precios = AlertasInteligentesPrecios(self)
        self.base_actualizacion_stock_factura = BaseActualizacionStockFactura(self)
        self.historico_inteligente_stock = HistoricoInteligenteStock(self)
        self.actualizador_inteligente_stock_factura = ActualizadorInteligenteStockFactura(self)
        self.alertas_inteligentes_stock = AlertasInteligentesStock(self)
        self.reconciliador_stock_factura = ReconciliadorStockFactura(self)
        self.base_ocr_documentos = BaseOCRDocumentos(self)
        self.motor_ocr_simulado = MotorOCRSimulado(self)
        self.lector_facturas_con_ocr = LectorFacturasConOCR(self)
        self.validador_corrector_ocr = ValidadorCorrectorOCR(self)
        self.base_importador_universal_facturas = BaseImportadorUniversalFacturas(self)
        self.auditoria_importaciones_universales = AuditoriaImportacionesUniversales(self)
        self.ejecutor_importador_universal_facturas = EjecutorImportadorUniversalFacturas(self)
        self.resumen_ejecutivo_importaciones = ResumenEjecutivoImportacionesServicio(self)
        self.cierre_importador_universal = CierreImportadorUniversal(self)
        self.analizador_inteligente_compras = AnalizadorInteligenteCompras(self)
        self.detector_anomalias_compras = DetectorAnomaliasCompras(self)
        self.prediccion_inteligente_precios = PrediccionInteligentePrecios(self)
        self.comparador_inteligente_proveedores = ComparadorInteligenteProveedores(self)
        self.prediccion_roturas_stock = PrediccionRoturasStock(self)
        self.motor_inteligente_pedidos = MotorInteligentePedidos(self)
        self.cierre_inteligencia_compras = CierreInteligenciaCompras(self)
        self.analizador_inteligente_stock = AnalizadorInteligenteStock(self)
        self.motor_alertas_stock = MotorAlertasStock(self)
        self.control_inteligente_movimientos_stock = ControlInteligenteMovimientosStock(self)
        self.reconciliador_inteligente_stock = ReconciliadorInteligenteStock(self)
        self.prediccion_necesidades_stock = PrediccionNecesidadesStock(self)
        self.optimizador_stock = OptimizadorStock(self)
        self.stock_por_ubicaciones = StockPorUbicaciones(self)
        self.cierre_gestion_inteligente_stock = CierreGestionInteligenteStock(self)
        self.analizador_inteligente_produccion = AnalizadorInteligenteProduccion(self)
        self.motor_alertas_produccion = MotorAlertasProduccion(self)
        self.planificador_inteligente_produccion = PlanificadorInteligenteProduccion(self)
        self.asignador_recursos_produccion = AsignadorRecursosProduccion(self)
        self.control_ejecucion_produccion = ControlEjecucionProduccion(self)
        self.replanificador_inteligente_produccion = ReplanificadorInteligenteProduccion(self)
        self.optimizador_inteligente_produccion = OptimizadorInteligenteProduccion(self)
        self.cierre_inteligente_produccion = CierreInteligenteProduccion(self)
        self.analizador_inteligente_escandallos = AnalizadorInteligenteEscandallos(self)
        self.motor_alertas_escandallos = MotorAlertasEscandallos(self)
        self.optimizador_inteligente_recetas = OptimizadorInteligenteRecetas(self)
        self.comparador_historico_escandallos = ComparadorHistoricoEscandallos(self)
        self.simulador_costes_escandallos = SimuladorCostesEscandallos(self)
        self.prediccion_inteligente_rentabilidad = PrediccionInteligenteRentabilidad(self)
        self.motor_optimizacion_carta = MotorOptimizacionCarta(self)
        self.cierre_escandallos_inteligentes = CierreEscandallosInteligentes(self)
        self.analizador_lenguaje_natural = AnalizadorLenguajeNatural(self)
        self.motor_intenciones_ia11 = MotorIntencionesIA11()
        self.extractor_datos_ia12 = self.motor_intenciones_ia11.extractor_datos_ia12
        self.comprension_conversacional_ia13 = ComprensionConversacionalIA13(self.motor_intenciones_ia11)
        self.integracion_motores_ia14 = IntegracionMotoresIA14(self, self.comprension_conversacional_ia13)
        self.pulido_ia_rr15 = PulidoIARR15(self)
        self.motor_conversacional_308 = MotorConversacional308(self)
        self.selector_inteligente_motores_308 = SelectorInteligenteMotores308(self)
        self.generador_inteligente_respuestas_308 = GeneradorInteligenteRespuestas308(self)
        self.memoria_conversacional_308 = MemoriaConversacional308Servicio(self)
        self.automatizador_inteligente_308 = AutomatizadorInteligente308(self)
        self.asistente_inteligente_host_ai_308 = AsistenteInteligenteHostAI308(self)
        self.cierre_ia_conversacional_308 = CierreIAConversacional308Servicio(self)

    def _inicializar_motores(self) -> None:
        """Inicializa motores de dominio en el orden original."""
        self.memoria = MotorMemoriaOperacional(self.base_dir)
        self.compras = MotorCompras(self.db)
        self.stock = MotorStock(self.db)
        self.eventos = MotorEventos(self.db)
        self.simulador_produccion_evento = MotorSimuladorProduccionEvento()
        self.escandallos_inteligente = MotorEscandallosInteligente(self.db)
        self.costes_inteligente = MotorCostesInteligente(self)
        self.produccion_real = MotorProduccionReal(self)
        self.ia_culinaria = MotorIACulinaria(self)
        self.asistente_conversacional = MotorAsistenteConversacional(self)
        self.persistencia = MotorPersistencia(self, self.db)
        self.produccion_completa = MotorProduccionCompleta(self)

    def _cargar_diccionario(self):
        if not self.diccionario_path.exists():
            return {}
        return json.loads(self.diccionario_path.read_text(encoding="utf-8"))
