from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
from statistics import mean, pstdev
import json
from MODELOS.comparador_proveedores_inteligente import ComparacionProveedor, InformeComparadorProveedores

class ComparadorInteligenteProveedores:
    """Host AI 3.0.4.5 - Comparador Inteligente de Proveedores."""
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def comparar_proveedores(self) -> Dict[str, Any]:
        historico = getattr(self.core, "historico_inteligente_precios", None)
        registros = list(getattr(historico, "registros", []) or []) if historico else []
        anomalias = []
        try:
            anomalias = self.core.detector_anomalias_compras.detectar_anomalias().get("anomalias", [])
        except Exception:
            anomalias = []
        incidencias_por_prov: Dict[str, int] = {}
        for a in anomalias:
            prov = a.get("proveedor_id") or a.get("proveedor_nombre") or "SIN-PROVEEDOR"
            incidencias_por_prov[prov] = incidencias_por_prov.get(prov, 0) + 1
        agrupados: Dict[str, List[Any]] = {}
        for r in registros:
            prov = getattr(r, "proveedor_id", "") or getattr(r, "proveedor_nombre", "") or "SIN-PROVEEDOR"
            agrupados.setdefault(prov, []).append(r)
        comparaciones = []
        for prov, regs in agrupados.items():
            precios = [float(getattr(r, "precio", 0) or 0) for r in regs if float(getattr(r, "precio", 0) or 0) > 0]
            if not precios: continue
            precio_medio = mean(precios)
            dispersion = (pstdev(precios) / precio_medio) if len(precios) > 1 and precio_medio else 0
            estabilidad = "alta" if dispersion <= 0.10 else "media" if dispersion <= 0.30 else "baja"
            frecuencia = "alta" if len(regs) >= 8 else "media" if len(regs) >= 4 else "baja"
            incidencias = incidencias_por_prov.get(prov, 0)
            calidad = "alta" if incidencias == 0 and estabilidad in ("alta", "media") else "media" if incidencias <= 2 else "baja"
            puntos = 100 - min(40, dispersion*100) - min(30, incidencias*6) + min(10, len(regs))
            puntos = max(0, min(100, round(puntos, 2)))
            articulos = sorted({getattr(r, "nombre_articulo", "") or getattr(r, "articulo_id", "") for r in regs})
            comparaciones.append(ComparacionProveedor(
                proveedor_id=prov,
                proveedor_nombre=getattr(regs[-1], "proveedor_nombre", "") or prov,
                total_registros=len(regs), precio_medio=round(precio_medio,4), estabilidad=estabilidad,
                frecuencia=frecuencia, incidencias=incidencias, calidad_historica=calidad,
                puntuacion=puntos, articulos=articulos,
                datos={"dispersion": round(dispersion, 4)}).to_dict())
        comparaciones.sort(key=lambda x: x["puntuacion"], reverse=True)
        mejor = comparaciones[0] if comparaciones else {}
        resumen = {"alta_calidad": sum(1 for c in comparaciones if c["calidad_historica"] == "alta"), "con_incidencias": sum(1 for c in comparaciones if c["incidencias"] > 0)}
        return InformeComparadorProveedores(len(comparaciones), comparaciones, mejor, resumen, f"Comparador proveedores: {len(comparaciones)} proveedores analizados.").to_dict()

    def comparar_articulo(self, articulo_id: str) -> Dict[str, Any]:
        historico = getattr(self.core, "historico_inteligente_precios", None)
        regs = [r for r in list(getattr(historico, "registros", []) or []) if getattr(r, "articulo_id", "") == articulo_id] if historico else []
        if not regs:
            return {"encontrado": False, "lectura_host_ai": "No hay histórico para comparar proveedores de este artículo."}
        original = getattr(self.core.historico_inteligente_precios, "registros", [])
        # cálculo local por proveedor para el artículo
        agrupados: Dict[str, List[Any]] = {}
        for r in regs:
            agrupados.setdefault(getattr(r, "proveedor_id", "") or "SIN-PROVEEDOR", []).append(r)
        datos=[]
        for prov, lista in agrupados.items():
            precios=[float(getattr(r,"precio",0) or 0) for r in lista]
            datos.append({"proveedor_id": prov, "proveedor_nombre": getattr(lista[-1],"proveedor_nombre",prov) or prov, "precio_medio": round(mean(precios),4), "total_registros": len(lista)})
        datos.sort(key=lambda x: x["precio_medio"])
        return {"encontrado": True, "articulo_id": articulo_id, "comparaciones": datos, "mejor_proveedor": datos[0], "lectura_host_ai": f"Comparación artículo {articulo_id}: {len(datos)} proveedores."}

    def exportar_comparacion(self, comparacion: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        destino = self.facturas_dir / (nombre or "comparador_inteligente_proveedores.json")
        destino.write_text(json.dumps(comparacion, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Comparación proveedores exportada: {destino.name}."}
