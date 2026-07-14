# Host AI 4.8.3 - Rentabilidad de carta

try:
    from SERVICIOS.margen_plato_menu_482 import calcular_margen_plato
    from SERVICIOS.coste_real_receta_481 import _num
except Exception:
    from margen_plato_menu_482 import calcular_margen_plato
    from coste_real_receta_481 import _num


def analizar_rentabilidad_carta(platos, precios_actuales=None, historico_precios=None, ventas=None, margen_minimo=0.55):
    ventas = ventas or {}
    resultados = []
    for plato in platos:
        margen = calcular_margen_plato(plato, precios_actuales=precios_actuales, historico_precios=historico_precios)
        unidades = int(_num(ventas.get(plato.get("nombre"), ventas.get(plato.get("receta", ""), plato.get("ventas", 0)))))
        contribucion = margen["margen"] * unidades
        margen_pct = margen["margen_pct"]
        if margen_pct < margen_minimo and unidades >= 20:
            accion = "subir_precio_o_reformular"
        elif margen_pct < margen_minimo:
            accion = "revisar"
        elif unidades < 5 and margen_pct >= margen_minimo:
            accion = "dar_visibilidad"
        else:
            accion = "mantener"
        resultados.append({
            "plato": margen["plato"],
            "precio_venta": margen["precio_venta"],
            "coste_racion": margen["coste_racion"],
            "margen": margen["margen"],
            "margen_pct": margen_pct,
            "estado": margen["estado"],
            "ventas": unidades,
            "contribucion": round(contribucion, 2),
            "accion_recomendada": accion,
        })
    resultados.sort(key=lambda x: (x["contribucion"], x["margen_pct"]), reverse=True)
    return {
        "total_platos": len(resultados),
        "margen_medio": round(sum(r["margen_pct"] for r in resultados) / len(resultados), 4) if resultados else 0,
        "contribucion_total": round(sum(r["contribucion"] for r in resultados), 2),
        "platos": resultados,
        "criticos": [r for r in resultados if r["accion_recomendada"] in ("subir_precio_o_reformular", "revisar")],
    }


def ranking_rentabilidad(analisis, top=10):
    platos = analisis.get("platos", [])
    return {
        "mejores": platos[:top],
        "peores_margen": sorted(platos, key=lambda x: x.get("margen_pct", 0))[:top],
        "mayor_contribucion": sorted(platos, key=lambda x: x.get("contribucion", 0), reverse=True)[:top],
    }


def recomendaciones_carta(analisis):
    recomendaciones = []
    for plato in analisis.get("platos", []):
        if plato["accion_recomendada"] == "subir_precio_o_reformular":
            recomendaciones.append(f"{plato['plato']}: plato vendido con margen bajo. Subir precio o reformular receta.")
        elif plato["accion_recomendada"] == "dar_visibilidad":
            recomendaciones.append(f"{plato['plato']}: buen margen pero pocas ventas. Dar mas visibilidad en carta.")
        elif plato["accion_recomendada"] == "revisar":
            recomendaciones.append(f"{plato['plato']}: margen bajo. Revisar coste y precio.")
    return recomendaciones
