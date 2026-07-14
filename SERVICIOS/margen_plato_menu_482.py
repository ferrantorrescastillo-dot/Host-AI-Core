# Host AI 4.8.2 - Margen por plato, menu o evento

try:
    from SERVICIOS.coste_real_receta_481 import calcular_coste_real_receta, _num
except Exception:
    from coste_real_receta_481 import calcular_coste_real_receta, _num


def calcular_margen_plato(receta, precio_venta=None, precios_actuales=None, historico_precios=None, iva_pct=0):
    coste = calcular_coste_real_receta(receta, precios_actuales, historico_precios)
    precio = _num(precio_venta if precio_venta is not None else receta.get("precio_venta", receta.get("pvp", 0)))
    iva = _num(iva_pct)
    venta_sin_iva = precio / (1 + iva / 100) if iva > 0 else precio
    margen = venta_sin_iva - coste["coste_racion"]
    margen_pct = margen / venta_sin_iva if venta_sin_iva else 0
    return {
        "plato": coste["receta"],
        "precio_venta": round(precio, 2),
        "venta_sin_iva": round(venta_sin_iva, 2),
        "coste_racion": coste["coste_racion"],
        "margen": round(margen, 2),
        "margen_pct": round(margen_pct, 4),
        "estado": clasificar_margen(margen_pct),
        "detalle_coste": coste,
    }


def clasificar_margen(margen_pct):
    margen_pct = _num(margen_pct)
    if margen_pct >= 0.65:
        return "excelente"
    if margen_pct >= 0.55:
        return "correcto"
    if margen_pct >= 0.45:
        return "ajustado"
    if margen_pct > 0:
        return "bajo"
    return "perdida"


def calcular_margen_menu(nombre_menu, platos, precios_actuales=None, historico_precios=None, precio_venta_menu=None, iva_pct=0):
    detalles = []
    coste_total = 0.0
    venta_componentes = 0.0
    for plato in platos:
        receta = plato.get("receta", plato)
        precio_linea = plato.get("precio_venta", receta.get("precio_venta", 0))
        margen = calcular_margen_plato(receta, precio_linea, precios_actuales, historico_precios, iva_pct=iva_pct)
        cantidad = _num(plato.get("cantidad", 1), 1)
        detalles.append({**margen, "cantidad": cantidad})
        coste_total += margen["coste_racion"] * cantidad
        venta_componentes += margen["venta_sin_iva"] * cantidad

    venta_menu = _num(precio_venta_menu, venta_componentes) if precio_venta_menu is not None else venta_componentes
    if iva_pct:
        venta_menu = venta_menu / (1 + _num(iva_pct) / 100)
    margen_total = venta_menu - coste_total
    margen_pct = margen_total / venta_menu if venta_menu else 0
    return {
        "menu": nombre_menu,
        "platos": detalles,
        "coste_total": round(coste_total, 2),
        "venta_total_sin_iva": round(venta_menu, 2),
        "margen_total": round(margen_total, 2),
        "margen_pct": round(margen_pct, 4),
        "estado": clasificar_margen(margen_pct),
    }


def calcular_margen_evento(evento, menus=None):
    personas = int(_num(evento.get("personas", 0)))
    menus = menus or evento.get("menus", []) or []
    coste = sum(_num(m.get("coste_total", m.get("coste_persona", 0) * personas)) for m in menus)
    venta = _num(evento.get("presupuesto", 0)) or sum(_num(m.get("venta_total_sin_iva", m.get("precio_venta_persona", 0) * personas)) for m in menus)
    margen = venta - coste
    return {
        "evento": evento.get("nombre", "Evento"),
        "personas": personas,
        "coste_total": round(coste, 2),
        "venta_total": round(venta, 2),
        "margen_total": round(margen, 2),
        "margen_pct": round(margen / venta, 4) if venta else 0,
    }
