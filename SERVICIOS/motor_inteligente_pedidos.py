from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json
from MODELOS.motor_pedidos_inteligente import DecisionPedidoInteligente, InformeMotorPedidosInteligente

class MotorInteligentePedidos:
    """Host AI 3.0.4.7 - Motor Inteligente de Pedidos.

    Convierte análisis, recomendaciones, anomalías, comparativa de proveedores, predicciones de precio
    y predicciones de rotura de stock en decisiones accionables de compra.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def generar_pedidos_inteligentes(self, horizonte_dias: int = 14, dias_seguridad: int = 3) -> Dict[str, Any]:
        roturas = self._safe(lambda: self.core.prediccion_roturas_stock.predecir_roturas(horizonte_dias), {})
        comparador = self._safe(lambda: self.core.comparador_inteligente_proveedores.comparar_proveedores(), {})
        precios = self._safe(lambda: self.core.prediccion_inteligente_precios.predecir_precios(), {})
        anomalias = self._safe(lambda: self.core.detector_anomalias_compras.detectar_anomalias(), {})

        proveedores_por_articulo = self._proveedores_por_articulo(comparador)
        pred_precio_por_articulo = {p.get("articulo_id"): p for p in precios.get("predicciones", []) if p.get("articulo_id")}
        anomalias_por_articulo = self._contar_anomalias_por_articulo(anomalias)

        decisiones: List[Dict[str, Any]] = []
        for r in roturas.get("predicciones", []):
            articulo_id = r.get("articulo_id", "SIN-ARTICULO")
            riesgo = r.get("nivel_riesgo", "estable")
            dias_hasta_rotura = float(r.get("dias_hasta_rotura", 999) or 999)
            consumo = float(r.get("consumo_medio", 0) or 0)
            stock = float(r.get("stock_actual", 0) or 0)
            unidad = r.get("unidad", "")
            proveedor = proveedores_por_articulo.get(articulo_id, r.get("proveedor_id", ""))
            pred_precio = pred_precio_por_articulo.get(articulo_id, {})
            tendencia = (pred_precio.get("tendencia") or pred_precio.get("datos", {}).get("tendencia") or "estable").lower()
            confianza_precio = pred_precio.get("confianza", "media")
            incidencias = anomalias_por_articulo.get(articulo_id, 0)

            decision = "no_comprar"
            prioridad = "normal"
            motivo = "Stock suficiente y sin señales urgentes."
            cantidad = 0.0
            confianza = "media"

            if riesgo == "critica" or dias_hasta_rotura <= 3:
                decision = "comprar"
                prioridad = "critica"
                cantidad = max(0.0, round((consumo * (horizonte_dias + dias_seguridad)) - stock, 3))
                motivo = "Riesgo crítico de rotura de stock."
                confianza = r.get("confianza", "media")
            elif riesgo == "aviso" or dias_hasta_rotura <= horizonte_dias:
                decision = "comprar"
                prioridad = "alta"
                cantidad = max(0.0, round((consumo * (horizonte_dias + dias_seguridad)) - stock, 3))
                motivo = "Rotura prevista dentro del horizonte de compra."
                confianza = r.get("confianza", "media")
            elif tendencia in ("subida", "alcista") and confianza_precio in ("alta", "media"):
                decision = "comprar"
                prioridad = "media"
                cantidad = max(0.0, round(consumo * dias_seguridad, 3))
                motivo = "Precio con tendencia de subida: conviene adelantar una compra controlada."
                confianza = confianza_precio
            elif tendencia in ("bajada", "bajista") and dias_hasta_rotura > horizonte_dias:
                decision = "esperar"
                prioridad = "baja"
                motivo = "Stock suficiente y precio con tendencia de bajada."
                confianza = confianza_precio

            if incidencias >= 3 and proveedor:
                decision = "cambiar_proveedor" if decision != "comprar" else "comprar"
                motivo += " El proveedor/artículo acumula incidencias; revisar proveedor antes de comprar."
                prioridad = "alta" if prioridad in ("normal", "media", "baja") else prioridad

            decisiones.append(DecisionPedidoInteligente(
                articulo_id=articulo_id,
                nombre_articulo=r.get("nombre_articulo", articulo_id),
                decision=decision,
                cantidad_recomendada=cantidad,
                unidad=unidad,
                proveedor_recomendado=proveedor,
                prioridad=prioridad,
                motivo=motivo,
                confianza=confianza,
                datos={"rotura": r, "prediccion_precio": pred_precio, "anomalias_articulo": incidencias},
            ).to_dict())

        decisiones.sort(key=lambda x: ({"critica": 0, "alta": 1, "media": 2, "normal": 3, "baja": 4}.get(x["prioridad"], 9), x["decision"]))
        resumen = {
            "horizonte_dias": horizonte_dias,
            "dias_seguridad": dias_seguridad,
            "valor_operativo": "decisiones de compra generadas desde stock, precios, proveedores y anomalías",
        }
        informe = InformeMotorPedidosInteligente(
            total_decisiones=len(decisiones),
            comprar=sum(1 for d in decisiones if d["decision"] == "comprar"),
            esperar=sum(1 for d in decisiones if d["decision"] == "esperar"),
            cambiar_proveedor=sum(1 for d in decisiones if d["decision"] == "cambiar_proveedor"),
            no_comprar=sum(1 for d in decisiones if d["decision"] == "no_comprar"),
            decisiones=decisiones,
            resumen=resumen,
            lectura_host_ai=f"Motor inteligente de pedidos: {len(decisiones)} decisiones generadas.",
        )
        return informe.to_dict()

    def generar_pedido_articulo(self, articulo_id: str, horizonte_dias: int = 14) -> Dict[str, Any]:
        informe = self.generar_pedidos_inteligentes(horizonte_dias)
        for d in informe.get("decisiones", []):
            if d.get("articulo_id") == articulo_id:
                d["encontrado"] = True
                d["lectura_host_ai"] = f"Pedido {d['nombre_articulo']}: {d['decision']} ({d['prioridad']})."
                return d
        return {"encontrado": False, "lectura_host_ai": "No hay datos suficientes para decidir pedido de este artículo."}

    def exportar_pedidos(self, informe: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        destino = self.facturas_dir / (nombre or "motor_inteligente_pedidos.json")
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Motor inteligente de pedidos exportado: {destino.name}."}

    def _safe(self, fn, default):
        try:
            return fn() or default
        except Exception:
            return default

    def _proveedores_por_articulo(self, comparador: Dict[str, Any]) -> Dict[str, str]:
        datos: Dict[str, str] = {}
        for c in comparador.get("comparaciones", []):
            proveedor = c.get("proveedor_id") or c.get("proveedor_nombre") or ""
            for articulo in c.get("articulos", []) or []:
                datos.setdefault(articulo, proveedor)
        return datos

    def _contar_anomalias_por_articulo(self, anomalias: Dict[str, Any]) -> Dict[str, int]:
        datos: Dict[str, int] = {}
        for a in anomalias.get("anomalias", []):
            articulo = a.get("articulo_id") or a.get("nombre_articulo") or a.get("articulo")
            if articulo:
                datos[articulo] = datos.get(articulo, 0) + 1
        return datos
