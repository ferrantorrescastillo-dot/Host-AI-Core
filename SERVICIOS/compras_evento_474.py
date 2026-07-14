# Host AI 4.7.4 - Compras automaticas del evento


def _num(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def calcular_necesidades_evento(evento, menu=None, recetas=None):
    menu = menu or (evento.get("menus") or [{}])[0]
    personas = int(evento.get("personas", 0) or 0)
    recetas = recetas or {}
    necesidades = {}

    for plato in menu.get("platos", []):
        nombre_plato = plato.get("nombre") or plato.get("receta")
        ingredientes = plato.get("ingredientes") or recetas.get(nombre_plato, {}).get("ingredientes", []) if isinstance(recetas, dict) else plato.get("ingredientes", [])
        for ing in ingredientes or []:
            articulo = ing.get("articulo") or ing.get("nombre")
            if not articulo:
                continue
            unidad = ing.get("unidad", "kg")
            cantidad_persona = _num(ing.get("cantidad_persona", ing.get("cantidad", 0)))
            total = cantidad_persona * personas
            clave = (articulo.lower(), unidad)
            if clave not in necesidades:
                necesidades[clave] = {"articulo": articulo, "unidad": unidad, "cantidad_necesaria": 0.0, "proveedor_preferente": ing.get("proveedor", "")}
            necesidades[clave]["cantidad_necesaria"] += total
    return list(necesidades.values())


def comparar_con_stock(necesidades, stock=None):
    stock = stock or {}
    lineas = []
    for nec in necesidades:
        articulo = nec["articulo"]
        disponible = _num(stock.get(articulo, stock.get(articulo.lower(), 0))) if isinstance(stock, dict) else 0
        falta = max(0, _num(nec["cantidad_necesaria"]) - disponible)
        lineas.append({
            **nec,
            "stock_disponible": round(disponible, 3),
            "cantidad_a_comprar": round(falta, 3),
            "estado": "comprar" if falta > 0 else "ok_stock",
        })
    return lineas


def generar_pedido_evento(evento, necesidades_con_stock, proveedor_por_defecto="Proveedor pendiente"):
    lineas = [l for l in necesidades_con_stock if _num(l.get("cantidad_a_comprar")) > 0]
    pedido = {
        "id_evento": evento.get("id_evento"),
        "nombre_evento": evento.get("nombre"),
        "estado": "borrador",
        "total_lineas": len(lineas),
        "lineas": [
            {
                "articulo": l["articulo"],
                "cantidad": l["cantidad_a_comprar"],
                "unidad": l.get("unidad", "kg"),
                "proveedor": l.get("proveedor_preferente") or proveedor_por_defecto,
            }
            for l in lineas
        ],
        "resumen": f"Pedido evento: {len(lineas)} articulos a comprar",
    }
    return pedido


def integrar_compras_evento(evento, pedido):
    copia = dict(evento)
    copia["compras"] = pedido.get("lineas", [])
    copia["pedido_evento"] = pedido
    return copia
