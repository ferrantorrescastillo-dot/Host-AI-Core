# Host AI 4.8.1 - Coste real por receta
# Calcula costes actualizados usando precios actuales o historicos.

from datetime import datetime


def _num(valor, defecto=0.0):
    try:
        return float(valor if valor is not None else defecto)
    except Exception:
        return float(defecto)


def _normalizar(nombre):
    return str(nombre or "").strip().lower()


def obtener_precio_articulo(articulo, precios_actuales=None, historico_precios=None):
    """Devuelve el mejor precio disponible para un articulo.

    Prioridad:
    1. Precio directo dentro del ingrediente.
    2. Diccionario de precios actuales.
    3. Ultimo precio del historico.
    4. 0.0 si no existe.
    """
    if isinstance(articulo, dict) and articulo.get("precio_unitario") is not None:
        return _num(articulo.get("precio_unitario"))

    nombre = articulo.get("articulo") if isinstance(articulo, dict) else articulo
    clave = _normalizar(nombre)
    precios_actuales = precios_actuales or {}
    historico_precios = historico_precios or {}

    for k, v in precios_actuales.items():
        if _normalizar(k) == clave:
            if isinstance(v, dict):
                return _num(v.get("precio", v.get("precio_unitario", 0)))
            return _num(v)

    historico = None
    for k, v in historico_precios.items():
        if _normalizar(k) == clave:
            historico = v
            break
    if isinstance(historico, list) and historico:
        ultimo = sorted(historico, key=lambda x: str(x.get("fecha", "")))[-1]
        return _num(ultimo.get("precio", ultimo.get("precio_unitario", 0)))
    return 0.0


def calcular_coste_real_receta(receta, precios_actuales=None, historico_precios=None, incluir_merma=True):
    ingredientes = receta.get("ingredientes", []) or []
    lineas = []
    coste_total = 0.0
    avisos = []

    for ing in ingredientes:
        nombre = ing.get("articulo") or ing.get("nombre") or "Articulo sin nombre"
        cantidad = _num(ing.get("cantidad", ing.get("cantidad_total", ing.get("cantidad_receta", 0))))
        merma_pct = _num(ing.get("merma_pct", 0)) if incluir_merma else 0.0
        cantidad_real = cantidad * (1 + merma_pct / 100)
        precio = obtener_precio_articulo(ing, precios_actuales, historico_precios)
        coste = cantidad_real * precio
        if precio <= 0:
            avisos.append(f"Sin precio para {nombre}")
        lineas.append({
            "articulo": nombre,
            "cantidad": round(cantidad, 4),
            "cantidad_real": round(cantidad_real, 4),
            "unidad": ing.get("unidad", "u"),
            "precio_unitario": round(precio, 4),
            "coste": round(coste, 4),
            "merma_pct": round(merma_pct, 2),
        })
        coste_total += coste

    raciones = max(1, int(_num(receta.get("raciones", receta.get("personas", 1)), 1)))
    return {
        "receta": receta.get("nombre", receta.get("receta", "Receta")),
        "raciones": raciones,
        "coste_total": round(coste_total, 2),
        "coste_racion": round(coste_total / raciones, 2),
        "lineas": lineas,
        "avisos": avisos,
        "calculado_en": datetime.now().isoformat(timespec="seconds"),
    }


def calcular_costes_recetas(recetas, precios_actuales=None, historico_precios=None):
    resultados = [calcular_coste_real_receta(r, precios_actuales, historico_precios) for r in recetas]
    return {
        "total_recetas": len(resultados),
        "coste_total": round(sum(r["coste_total"] for r in resultados), 2),
        "recetas": resultados,
    }
