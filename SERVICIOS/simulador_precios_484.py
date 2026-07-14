# Host AI 4.8.4 - Simulador inteligente de precios

try:
    from SERVICIOS.margen_plato_menu_482 import calcular_margen_plato
    from SERVICIOS.coste_real_receta_481 import _num
except Exception:
    from margen_plato_menu_482 import calcular_margen_plato
    from coste_real_receta_481 import _num


def simular_precio_plato(receta, precios_simulados, precios_actuales=None, historico_precios=None, ventas_estimadas=0, iva_pct=0):
    resultados = []
    ventas_estimadas = int(_num(ventas_estimadas))
    for precio in precios_simulados:
        margen = calcular_margen_plato(receta, precio_venta=precio, precios_actuales=precios_actuales, historico_precios=historico_precios, iva_pct=iva_pct)
        resultados.append({
            "precio_venta": round(_num(precio), 2),
            "coste_racion": margen["coste_racion"],
            "margen": margen["margen"],
            "margen_pct": margen["margen_pct"],
            "beneficio_estimado": round(margen["margen"] * ventas_estimadas, 2),
            "estado": margen["estado"],
        })
    mejor = sorted(resultados, key=lambda x: (x["beneficio_estimado"], x["margen_pct"]), reverse=True)[0] if resultados else None
    return {
        "plato": receta.get("nombre", receta.get("receta", "Plato")),
        "ventas_estimadas": ventas_estimadas,
        "simulaciones": resultados,
        "mejor_opcion": mejor,
    }


def simular_subida_porcentual(receta, porcentaje_subida, precios_actuales=None, historico_precios=None, ventas_estimadas=0):
    precio_actual = _num(receta.get("precio_venta", receta.get("pvp", 0)))
    nuevo_precio = round(precio_actual * (1 + _num(porcentaje_subida) / 100), 2)
    base = calcular_margen_plato(receta, precio_actual, precios_actuales, historico_precios)
    nuevo = calcular_margen_plato(receta, nuevo_precio, precios_actuales, historico_precios)
    ventas = int(_num(ventas_estimadas))
    return {
        "plato": receta.get("nombre", receta.get("receta", "Plato")),
        "precio_actual": round(precio_actual, 2),
        "precio_nuevo": nuevo_precio,
        "margen_actual": base["margen"],
        "margen_nuevo": nuevo["margen"],
        "diferencia_margen_unitario": round(nuevo["margen"] - base["margen"], 2),
        "impacto_estimado": round((nuevo["margen"] - base["margen"]) * ventas, 2),
        "ventas_estimadas": ventas,
    }


def precio_objetivo_por_margen(receta, margen_objetivo_pct, precios_actuales=None, historico_precios=None):
    coste = calcular_margen_plato(receta, precio_venta=receta.get("precio_venta", 1), precios_actuales=precios_actuales, historico_precios=historico_precios)["coste_racion"]
    objetivo = _num(margen_objetivo_pct)
    if objetivo > 1:
        objetivo = objetivo / 100
    precio = coste / max(1 - objetivo, 0.01)
    return {
        "plato": receta.get("nombre", receta.get("receta", "Plato")),
        "coste_racion": round(coste, 2),
        "margen_objetivo_pct": round(objetivo, 4),
        "precio_recomendado": round(precio, 2),
    }
