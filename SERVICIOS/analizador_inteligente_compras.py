from __future__ import annotations

"""
Servicio Host AI 3.0.4.1 - Analizador Inteligente de Compras.

Responsabilidad:
- Leer información ya generada por auditorías, histórico de precios e histórico de stock.
- Construir un informe estructurado de compras.
- Exportar el informe cuando el pipeline lo solicite.

Nota RC2.3:
Este servicio no debe conocer pipelines ni lógica de interfaz. Solo analiza datos disponibles
expuestos por el Core y devuelve un diccionario serializable.
"""

import json
from typing import Any, Dict

from MODELOS.analisis_compras import AnalisisInteligenteCompras


class AnalizadorInteligenteCompras:
    """Analiza compras históricas y resume proveedores, artículos, gasto y avisos."""

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def analizar_compras(self) -> Dict[str, Any]:
        """Genera el informe inteligente de compras a partir de datos ya cargados."""
        registros = self._obtener_registros_auditoria()

        proveedores: Dict[str, int] = {}
        total_lineas = 0
        precios_aplicados = 0
        stock_aplicado = 0

        for registro in registros:
            proveedor = self._resolver_proveedor(registro)
            proveedores[proveedor] = proveedores.get(proveedor, 0) + 1
            total_lineas += int(registro.get("total_lineas", 0) or 0)
            precios_aplicados += int(registro.get("precios_aplicados", 0) or 0)
            stock_aplicado += int(registro.get("stock_aplicado", 0) or 0)

        articulos = self._analizar_articulos_stock()
        gasto_total, compras_por_proveedor = self._analizar_gasto_precios()
        mas_comprados = sorted(
            articulos.values(),
            key=lambda item: item["cantidad_total"],
            reverse=True,
        )[:10]

        avisos = self._generar_avisos(registros, articulos)

        analisis = AnalisisInteligenteCompras(
            total_importaciones=len(registros),
            total_lineas=total_lineas,
            total_stock_aplicado=stock_aplicado,
            total_precios_aplicados=precios_aplicados,
            proveedores=proveedores,
            articulos=articulos,
            gasto_estimado_total=round(gasto_total, 4),
            compras_por_proveedor={k: round(v, 4) for k, v in compras_por_proveedor.items()},
            articulos_mas_comprados=mas_comprados,
            avisos=avisos,
        )

        datos = analisis.to_dict()
        datos["lectura_host_ai"] = (
            f"Análisis compras: {len(registros)} importaciones, {len(articulos)} artículos."
        )
        return datos

    def exportar_analisis(self, analisis: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        """Exporta el informe de análisis de compras a JSON."""
        nombre = nombre or "analisis_inteligente_compras.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(analisis, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Análisis compras exportado: {destino.name}.",
        }

    def _obtener_registros_auditoria(self) -> list[Dict[str, Any]]:
        auditoria = getattr(self.core, "auditoria_importaciones_universales", None)
        return [registro.to_dict() for registro in getattr(auditoria, "registros", [])] if auditoria else []

    def _resolver_proveedor(self, registro: Dict[str, Any]) -> str:
        return registro.get("proveedor_nombre") or registro.get("proveedor_id") or "SIN-PROVEEDOR"

    def _analizar_articulos_stock(self) -> Dict[str, Dict[str, Any]]:
        articulos: Dict[str, Dict[str, Any]] = {}
        historico_stock = getattr(self.core, "historico_inteligente_stock", None)
        if not historico_stock:
            return articulos

        for registro in historico_stock.registros:
            articulo_id = registro.articulo_id
            articulos.setdefault(
                articulo_id,
                {
                    "articulo_id": articulo_id,
                    "nombre_articulo": registro.nombre_articulo,
                    "cantidad_total": 0.0,
                    "unidad": registro.unidad,
                    "movimientos": 0,
                },
            )
            if registro.tipo == "entrada":
                articulos[articulo_id]["cantidad_total"] += float(registro.cantidad or 0)
            articulos[articulo_id]["movimientos"] += 1

        return articulos

    def _analizar_gasto_precios(self) -> tuple[float, Dict[str, float]]:
        gasto_total = 0.0
        compras_por_proveedor: Dict[str, float] = {}
        historico_precios = getattr(self.core, "historico_inteligente_precios", None)
        if not historico_precios:
            return gasto_total, compras_por_proveedor

        for registro in historico_precios.registros:
            precio = float(registro.precio or 0)
            gasto_total += precio
            proveedor = registro.proveedor_id or "SIN-PROVEEDOR"
            compras_por_proveedor[proveedor] = compras_por_proveedor.get(proveedor, 0.0) + precio

        return gasto_total, compras_por_proveedor

    def _generar_avisos(
        self,
        registros: list[Dict[str, Any]],
        articulos: Dict[str, Dict[str, Any]],
    ) -> list[str]:
        avisos: list[str] = []
        if not registros:
            avisos.append("No hay importaciones auditadas todavía.")
        if not articulos:
            avisos.append("No hay histórico de stock suficiente para ranking de artículos.")
        return avisos
