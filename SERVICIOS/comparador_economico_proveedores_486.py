from __future__ import annotations

from typing import Dict, Any, Iterable, List


def calcular_coste_total_proveedor(oferta: Dict[str, Any]) -> Dict[str, Any]:
    precio = float(oferta.get("precio_unitario", 0))
    cantidad = float(oferta.get("cantidad", 1) or 1)
    transporte = float(oferta.get("transporte", 0))
    descuento = float(oferta.get("descuento", 0))
    fiabilidad = float(oferta.get("fiabilidad", 1.0))
    coste_base = max(precio * cantidad - descuento + transporte, 0)
    penalizacion = 0.0 if fiabilidad >= 0.95 else round(coste_base * (0.95 - fiabilidad), 4)
    total = round(coste_base + penalizacion, 4)
    return {**oferta, "coste_base": round(coste_base, 4), "penalizacion_fiabilidad": penalizacion, "coste_total": total}


def comparar_proveedores(ofertas: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    calculadas: List[Dict[str, Any]] = [calcular_coste_total_proveedor(o) for o in ofertas]
    calculadas.sort(key=lambda x: x["coste_total"])
    mejor = calculadas[0] if calculadas else None
    return {"mejor_opcion": mejor, "comparativa": calculadas, "numero_proveedores": len(calculadas)}


def recomendacion_compra_proveedor(ofertas: Iterable[Dict[str, Any]]) -> str:
    resultado = comparar_proveedores(ofertas)
    mejor = resultado.get("mejor_opcion")
    if not mejor:
        return "No hay ofertas para comparar."
    proveedor = mejor.get("proveedor", "Proveedor sin nombre")
    articulo = mejor.get("articulo", "artículo")
    total = mejor.get("coste_total", 0)
    return f"Comprar {articulo} a {proveedor}: mejor coste real estimado {total:.2f} €."
