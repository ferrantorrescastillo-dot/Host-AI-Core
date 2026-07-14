# Host AI 4.7.2 - Menus del evento


def _numero(valor, defecto=0.0):
    try:
        return float(valor or defecto)
    except Exception:
        return float(defecto)


def crear_menu_evento(nombre, platos=None, precio_venta_persona=None, margen_objetivo=0.30, bebida_incluida=False, observaciones=None):
    platos = platos or []
    coste_total_persona = sum(_numero(p.get("coste_persona", p.get("coste", 0))) for p in platos)
    precio_venta_persona = _numero(precio_venta_persona) if precio_venta_persona is not None else round(coste_total_persona / max(1 - margen_objetivo, 0.01), 2)
    margen_persona = round(precio_venta_persona - coste_total_persona, 2)
    margen_pct = round(margen_persona / precio_venta_persona, 4) if precio_venta_persona else 0
    return {
        "nombre": nombre,
        "platos": platos,
        "bebida_incluida": bool(bebida_incluida),
        "coste_persona": round(coste_total_persona, 2),
        "precio_venta_persona": round(precio_venta_persona, 2),
        "margen_persona": margen_persona,
        "margen_pct": margen_pct,
        "observaciones": observaciones or "",
    }


def calcular_menu_para_evento(menu, personas):
    personas = int(personas or 0)
    return {
        "menu": menu.get("nombre"),
        "personas": personas,
        "coste_total": round(menu.get("coste_persona", 0) * personas, 2),
        "venta_total": round(menu.get("precio_venta_persona", 0) * personas, 2),
        "margen_total": round(menu.get("margen_persona", 0) * personas, 2),
        "platos": [
            {
                **plato,
                "cantidad_total": round(_numero(plato.get("cantidad_persona", 1)) * personas, 3),
            }
            for plato in menu.get("platos", [])
        ],
    }


def asignar_menu_evento(evento, menu):
    copia = dict(evento)
    menus = list(copia.get("menus", []))
    menus.append(menu)
    copia["menus"] = menus
    resumen = calcular_menu_para_evento(menu, copia.get("personas", 0))
    copia["resumen_menu"] = resumen
    return copia


def comparar_menus_evento(menus):
    ordenados = sorted(menus, key=lambda m: (m.get("margen_pct", 0), m.get("margen_persona", 0)), reverse=True)
    return {
        "total_menus": len(menus),
        "mejor_margen": ordenados[0] if ordenados else None,
        "menus": ordenados,
    }
