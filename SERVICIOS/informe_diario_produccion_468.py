# Host AI 4.6.8 - Informe diario de producción

from collections import defaultdict

try:
    from SERVICIOS.checklist_final_produccion_467 import generar_checklist_final
except Exception:
    from checklist_final_produccion_467 import generar_checklist_final


def generar_informe_diario_produccion(tareas, fecha=None, stock=None, documentos=None, incidencias=None):
    incidencias = incidencias or []
    total = len(tareas)
    terminadas = sum(1 for t in tareas if t.get("estado") in ("terminada", "completada", "ok"))
    pendientes = total - terminadas

    por_cocinero = defaultdict(lambda: {"tareas": 0, "terminadas": 0, "minutos_activos": 0, "minutos_pasivos": 0})
    por_recurso = defaultdict(int)

    for tarea in tareas:
        cocinero = tarea.get("cocinero", "Sin asignar")
        por_cocinero[cocinero]["tareas"] += 1
        if tarea.get("estado") in ("terminada", "completada", "ok"):
            por_cocinero[cocinero]["terminadas"] += 1
        por_cocinero[cocinero]["minutos_activos"] += int(tarea.get("minutos_activos", tarea.get("tiempo_activo", 0)) or 0)
        por_cocinero[cocinero]["minutos_pasivos"] += int(tarea.get("minutos_pasivos", tarea.get("tiempo_pasivo", 0)) or 0)
        recurso = tarea.get("recurso") or tarea.get("recurso_principal")
        if recurso:
            por_recurso[recurso] += 1

    checklist = generar_checklist_final(tareas, stock=stock, documentos=documentos)
    estado = "OK" if pendientes == 0 and checklist["ok"] and not incidencias else "REVISAR"

    return {
        "fecha": fecha,
        "estado": estado,
        "total_tareas": total,
        "terminadas": terminadas,
        "pendientes": pendientes,
        "por_cocinero": dict(por_cocinero),
        "por_recurso": dict(por_recurso),
        "checklist": checklist,
        "incidencias": incidencias,
        "resumen": f"Producción: {terminadas}/{total} tareas terminadas. Estado: {estado}",
    }


def formatear_informe(informe):
    lineas = [
        "=== INFORME DIARIO DE PRODUCCION ===",
        f"Fecha: {informe.get('fecha') or 'Sin fecha'}",
        informe.get("resumen", ""),
        "",
        "Por cocinero:",
    ]
    for cocinero, datos in informe.get("por_cocinero", {}).items():
        lineas.append(f"- {cocinero}: {datos['terminadas']}/{datos['tareas']} tareas, activo {datos['minutos_activos']} min")
    lineas.append("")
    lineas.append(f"Checklist: {informe.get('checklist', {}).get('resumen', '')}")
    if informe.get("incidencias"):
        lineas.append("Incidencias:")
        for inc in informe["incidencias"]:
            lineas.append(f"- {inc}")
    return "\n".join(lineas)
