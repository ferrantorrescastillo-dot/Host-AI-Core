# Host AI 4.6.7 - Checklist final de producción


def generar_checklist_final(tareas, stock=None, documentos=None):
    stock = stock or {}
    documentos = documentos or []
    items = []

    for tarea in tareas:
        nombre = tarea.get("nombre", "Tarea")
        estado = tarea.get("estado", "pendiente")
        items.append({
            "tipo": "produccion",
            "texto": f"Verificar elaboración: {nombre}",
            "ok": estado in ("terminada", "completada", "ok"),
            "referencia": tarea.get("id"),
        })
        if tarea.get("requiere_etiqueta", True):
            items.append({
                "tipo": "etiquetado",
                "texto": f"Etiquetar y fechar: {nombre}",
                "ok": bool(tarea.get("etiquetada")),
                "referencia": tarea.get("id"),
            })
        if tarea.get("ubicacion_destino"):
            items.append({
                "tipo": "ubicacion",
                "texto": f"Guardar {nombre} en {tarea.get('ubicacion_destino')}",
                "ok": bool(tarea.get("guardada")),
                "referencia": tarea.get("id"),
            })

    for articulo, cantidad in stock.items():
        if cantidad < 0:
            items.append({
                "tipo": "stock",
                "texto": f"Revisar stock negativo: {articulo} ({cantidad})",
                "ok": False,
                "referencia": articulo,
            })

    items.append({
        "tipo": "documentacion",
        "texto": "Guardar parte diario de producción",
        "ok": any("produccion" in str(d).lower() for d in documentos),
        "referencia": "parte_diario",
    })

    pendientes = [i for i in items if not i["ok"]]
    return {
        "ok": len(pendientes) == 0,
        "total": len(items),
        "pendientes": len(pendientes),
        "items": items,
        "resumen": f"{len(items) - len(pendientes)}/{len(items)} comprobaciones OK",
    }


def imprimir_checklist(checklist):
    lineas = ["=== CHECKLIST FINAL PRODUCCION ===", checklist.get("resumen", "")]
    for item in checklist.get("items", []):
        marca = "OK" if item.get("ok") else "PENDIENTE"
        lineas.append(f"[{marca}] {item.get('texto')}")
    return "\n".join(lineas)
