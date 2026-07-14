from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json
from MODELOS.alertas_precios import AlertaPrecio


class AlertasInteligentesPrecios:
    """
    Host AI 3.0.3.5.5

    Genera alertas de precios:
    - subida fuerte
    - bajada fuerte
    - proveedor caro
    - oportunidad de ahorro
    - falta histórico
    """

    UMBRAL_SUBIDA = 10.0
    UMBRAL_BAJADA = -10.0

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.facturas_dir / "alertas_precios.json"
        self.alertas: List[Dict[str, Any]] = self._cargar()

    def generar_alertas_articulo(self, articulo_id: str) -> Dict[str, Any]:
        hist = getattr(self.core, "historico_inteligente_precios", None)
        if not hist:
            return {"alertas": [], "total": 0, "lectura_host_ai": "No existe histórico de precios."}

        analisis = hist.analizar_articulo(articulo_id)
        if not analisis.get("encontrado"):
            alerta = AlertaPrecio(
                articulo_id=articulo_id,
                nombre_articulo="",
                tipo="sin_historico",
                nivel="aviso",
                mensaje="No hay histórico suficiente para analizar precios.",
                accion_sugerida="Registrar más compras.",
            )
            return self._salida([alerta])

        alertas = []
        variacion = float(analisis.get("variacion_total", 0) or 0)
        nombre = analisis.get("nombre_articulo", articulo_id)

        if variacion >= self.UMBRAL_SUBIDA:
            alertas.append(AlertaPrecio(
                articulo_id=articulo_id,
                nombre_articulo=nombre,
                tipo="subida_fuerte",
                nivel="critico" if variacion >= 20 else "aviso",
                mensaje=f"El precio ha subido {variacion}%.",
                precio_referencia=analisis.get("primer_precio", 0),
                precio_actual=analisis.get("ultimo_precio", 0),
                variacion_porcentaje=variacion,
                accion_sugerida="Revisar proveedor o buscar alternativa.",
                datos=analisis,
            ))
        elif variacion <= self.UMBRAL_BAJADA:
            alertas.append(AlertaPrecio(
                articulo_id=articulo_id,
                nombre_articulo=nombre,
                tipo="bajada_fuerte",
                nivel="info",
                mensaje=f"El precio ha bajado {abs(variacion)}%.",
                precio_referencia=analisis.get("primer_precio", 0),
                precio_actual=analisis.get("ultimo_precio", 0),
                variacion_porcentaje=variacion,
                accion_sugerida="Valorar comprar más si el producto rota.",
                datos=analisis,
            ))

        comp = getattr(self.core, "comparador_proveedores_precios", None)
        if comp:
            comparacion = comp.comparar_articulo(articulo_id)
            if comparacion.get("encontrado") and comparacion.get("ahorro_potencial_unitario", 0) > 0:
                ahorro = comparacion["ahorro_potencial_unitario"]
                alertas.append(AlertaPrecio(
                    articulo_id=articulo_id,
                    nombre_articulo=nombre,
                    tipo="oportunidad_ahorro",
                    nivel="info",
                    mensaje=f"Hay ahorro potencial de {ahorro} por unidad cambiando de proveedor.",
                    precio_referencia=comparacion["peor_proveedor"]["precio_medio"],
                    precio_actual=comparacion["mejor_proveedor"]["precio_medio"],
                    proveedor_id=comparacion["mejor_proveedor"]["proveedor_id"],
                    accion_sugerida=f"Comparar con {comparacion['mejor_proveedor']['proveedor_id']}.",
                    datos=comparacion,
                ))

        return self._salida(alertas)

    def generar_alertas_todos(self) -> Dict[str, Any]:
        hist = getattr(self.core, "historico_inteligente_precios", None)
        if not hist:
            return {"alertas": [], "total": 0, "lectura_host_ai": "No existe histórico de precios."}

        articulos = sorted({r.articulo_id for r in hist.registros})
        todas = []
        for aid in articulos:
            r = self.generar_alertas_articulo(aid)
            todas.extend(r.get("alertas", []))

        self.alertas = todas
        self._guardar()
        return {
            "alertas": todas,
            "total": len(todas),
            "lectura_host_ai": f"Alertas generadas: {len(todas)}.",
        }

    def listar_alertas(self) -> Dict[str, Any]:
        return {
            "alertas": self.alertas,
            "total": len(self.alertas),
            "lectura_host_ai": f"Alertas de precios guardadas: {len(self.alertas)}.",
        }

    def exportar_alertas(self) -> Dict[str, Any]:
        self._guardar()
        return {"archivo": str(self.path), "lectura_host_ai": "Alertas de precios exportadas."}

    def _salida(self, alertas: List[AlertaPrecio]) -> Dict[str, Any]:
        data = [a.to_dict() for a in alertas]
        self.alertas.extend(data)
        self._guardar()
        return {
            "alertas": data,
            "total": len(data),
            "lectura_host_ai": f"Alertas generadas: {len(data)}.",
        }

    def _cargar(self) -> List[Dict[str, Any]]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8")).get("alertas", [])
            except Exception:
                return []
        return []

    def _guardar(self):
        self.path.write_text(json.dumps({"version": "3.0.3.5.5", "alertas": self.alertas}, ensure_ascii=False, indent=2), encoding="utf-8")
