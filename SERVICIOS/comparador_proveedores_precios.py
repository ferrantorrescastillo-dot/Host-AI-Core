from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json


class ComparadorProveedoresPrecios:
    """
    Host AI 3.0.3.5.4

    Compara precios por proveedor usando el histórico.
    Permite saber:
    - mejor proveedor para un artículo
    - peor proveedor
    - ahorro potencial
    - ranking de proveedores
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def comparar_articulo(self, articulo_id: str) -> Dict[str, Any]:
        hist = getattr(self.core, "historico_inteligente_precios", None)
        if not hist:
            return {"encontrado": False, "lectura_host_ai": "No existe histórico de precios."}

        registros = [r.to_dict() for r in hist.registros if r.articulo_id == articulo_id]
        if not registros:
            return {"encontrado": False, "lectura_host_ai": "No hay registros para este artículo."}

        proveedores = {}
        for r in registros:
            proveedor = r.get("proveedor_id") or "SIN-PROVEEDOR"
            proveedores.setdefault(proveedor, []).append(float(r.get("precio", 0) or 0))

        ranking = []
        for proveedor, precios in proveedores.items():
            ranking.append({
                "proveedor_id": proveedor,
                "precio_minimo": round(min(precios), 4),
                "precio_maximo": round(max(precios), 4),
                "precio_medio": round(sum(precios) / len(precios), 4),
                "total_registros": len(precios),
            })

        ranking.sort(key=lambda x: x["precio_medio"])
        mejor = ranking[0]
        peor = ranking[-1]
        ahorro = round(peor["precio_medio"] - mejor["precio_medio"], 4)

        datos = {
            "encontrado": True,
            "articulo_id": articulo_id,
            "nombre_articulo": registros[-1].get("nombre_articulo", ""),
            "ranking": ranking,
            "mejor_proveedor": mejor,
            "peor_proveedor": peor,
            "ahorro_potencial_unitario": ahorro,
            "lectura_host_ai": f"Mejor proveedor para {registros[-1].get('nombre_articulo', articulo_id)}: {mejor['proveedor_id']}."
        }
        return datos

    def comparar_todos(self) -> Dict[str, Any]:
        hist = getattr(self.core, "historico_inteligente_precios", None)
        if not hist:
            return {"comparaciones": [], "total": 0, "lectura_host_ai": "No existe histórico de precios."}

        articulos = sorted({r.articulo_id for r in hist.registros})
        comparaciones = []
        for aid in articulos:
            c = self.comparar_articulo(aid)
            if c.get("encontrado"):
                comparaciones.append(c)

        return {
            "comparaciones": comparaciones,
            "total": len(comparaciones),
            "lectura_host_ai": f"Comparación proveedores completada: {len(comparaciones)} artículos.",
        }

    def exportar_comparacion(self, comparacion: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "comparacion_proveedores_precios.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(comparacion, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Comparación proveedores exportada: {destino.name}."}
