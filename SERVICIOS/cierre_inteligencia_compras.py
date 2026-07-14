from __future__ import annotations
from typing import Dict, Any, Callable, List
import json
from MODELOS.cierre_inteligencia_compras import ValidacionModuloCompras, InformeCierreInteligenciaCompras

class CierreInteligenciaCompras:
    """Host AI 3.0.4.8 - Cierre Inteligencia de Compras.

    Ejecuta el bloque 3.0.4 como sistema único y genera el informe final.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def comprobar_cierre(self) -> Dict[str, Any]:
        pruebas: List[tuple[str, str, Callable[[], Dict[str, Any]], str]] = [
            ("Analizador Inteligente de Compras", "3.0.4.1", lambda: self.core.analizador_inteligente_compras.analizar_compras(), "analisis"),
            ("Motor Inteligente de Recomendaciones", "3.0.4.2", lambda: self.core.motor_recomendaciones_compras.generar_recomendaciones(), "recomendaciones"),
            ("Detector Inteligente de Anomalías", "3.0.4.3", lambda: self.core.detector_anomalias_compras.detectar_anomalias(), "anomalias"),
            ("Predicción Inteligente de Precios", "3.0.4.4", lambda: self.core.prediccion_inteligente_precios.predecir_precios(), "predicciones"),
            ("Comparador Inteligente de Proveedores", "3.0.4.5", lambda: self.core.comparador_inteligente_proveedores.comparar_proveedores(), "comparaciones"),
            ("Predicción de Roturas de Stock", "3.0.4.6", lambda: self.core.prediccion_roturas_stock.predecir_roturas(), "predicciones"),
            ("Motor Inteligente de Pedidos", "3.0.4.7", lambda: self.core.motor_inteligente_pedidos.generar_pedidos_inteligentes(), "decisiones"),
        ]
        validaciones: List[Dict[str, Any]] = []
        metricas: Dict[str, Any] = {}
        for nombre, version, funcion, clave in pruebas:
            try:
                datos = funcion() or {}
                total = self._contar(datos, clave)
                ok = total >= 0 and bool(datos)
                metricas[version] = total
                validaciones.append(ValidacionModuloCompras(nombre, version, ok, total, f"{nombre}: OK ({total}).", {"clave": clave}).to_dict())
            except Exception as exc:
                metricas[version] = 0
                validaciones.append(ValidacionModuloCompras(nombre, version, False, 0, f"{nombre}: ERROR {exc}", {"error": str(exc)}).to_dict())

        ok_global = all(v.get("ok") for v in validaciones) and len(validaciones) == 7
        modulos_validados = sum(1 for v in validaciones if v.get("ok"))
        acciones = []
        if ok_global:
            acciones.append("Cerrar Host AI 3.0.4 Inteligencia de Compras y continuar con Host AI 3.0.5 Gestión Inteligente del Stock.")
        else:
            acciones.append("Revisar los módulos 3.0.4 que no han validado antes de avanzar al bloque 3.0.5.")
        informe_final = {
            "bloque": "HOST AI 3.0.4 Inteligencia de Compras",
            "estado": "cerrado" if ok_global else "pendiente_revision",
            "siguiente_bloque": "HOST AI 3.0.5 Gestión Inteligente del Stock",
            "metricas": metricas,
        }
        return InformeCierreInteligenciaCompras(
            ok_global=ok_global,
            modulos_validados=modulos_validados,
            total_modulos=7,
            validaciones=validaciones,
            metricas=metricas,
            informe_final=informe_final,
            acciones_recomendadas=acciones,
            lectura_host_ai=f"Cierre Inteligencia Compras: {modulos_validados}/7 módulos validados.",
        ).to_dict()

    def exportar_cierre(self, cierre: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        destino = self.facturas_dir / (nombre or "cierre_inteligencia_compras_304.json")
        destino.write_text(json.dumps(cierre, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Cierre Inteligencia de Compras exportado: {destino.name}."}

    def _contar(self, datos: Dict[str, Any], clave: str) -> int:
        valor = datos.get(clave, [])
        if isinstance(valor, list): return len(valor)
        if isinstance(valor, dict): return len(valor)
        if isinstance(valor, int): return valor
        for alt in ("total", "total_decisiones", "total_articulos", "total_proveedores", "total_anomalias"):
            if isinstance(datos.get(alt), int): return int(datos[alt])
        return 0
