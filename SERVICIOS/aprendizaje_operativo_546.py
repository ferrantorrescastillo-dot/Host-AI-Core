"""Host AI 5.4.6 - Aprendizaje Operativo.

Construye memoria operativa utilizable por Host AI: preferencias, tiempos reales,
proveedores habituales, rendimiento de personal y patrones del restaurante.
No escribe en base de datos: genera recomendaciones de aprendizaje en modo seguro.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List

try:
    from SERVICIOS.optimizador_global_545 import optimizar_operacion_545
except ModuleNotFoundError:
    optimizar_operacion_545 = None  # type: ignore


def _num(valor: Any, defecto: float = 0.0) -> float:
    try:
        if valor in (None, ""):
            return defecto
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def _mas_comun(valores: List[str], defecto: str = "sin datos") -> str:
    limpios = [v for v in valores if v]
    if not limpios:
        return defecto
    return Counter(limpios).most_common(1)[0][0]


def aprender_operativa_546(historico: List[Dict[str, Any]] | None = None, contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Extrae aprendizajes operativos del historico del restaurante."""
    historico = historico or _historico_demo()
    contexto = contexto or {}

    proveedores_por_articulo: Dict[str, List[str]] = defaultdict(list)
    tiempos_por_tarea: Dict[str, List[float]] = defaultdict(list)
    personal_por_tarea: Dict[str, List[str]] = defaultdict(list)
    incidencias = Counter()
    dias_fuertes = Counter()

    for registro in historico:
        dia = str(registro.get("dia", "")).lower()
        if dia:
            dias_fuertes[dia] += int(_num(registro.get("personas"), 1))
        for compra in registro.get("compras", []) or []:
            if isinstance(compra, dict):
                articulo = str(compra.get("articulo", "")).lower()
                proveedor = str(compra.get("proveedor", ""))
                if articulo and proveedor:
                    proveedores_por_articulo[articulo].append(proveedor)
        for tarea in registro.get("tareas", []) or []:
            if isinstance(tarea, dict):
                nombre = str(tarea.get("nombre", "")).lower()
                if nombre:
                    tiempos_por_tarea[nombre].append(_num(tarea.get("tiempo_real_h"), _num(tarea.get("tiempo_h"), 0)))
                    responsable = str(tarea.get("responsable", ""))
                    if responsable:
                        personal_por_tarea[nombre].append(responsable)
        for inc in registro.get("incidencias", []) or []:
            if isinstance(inc, dict):
                incidencias[str(inc.get("tipo", "incidencia"))] += 1
            elif inc:
                incidencias[str(inc)] += 1

    aprendizajes = {
        "proveedores_preferidos": {art: _mas_comun(provs) for art, provs in proveedores_por_articulo.items()},
        "tiempos_medios_tarea_h": {t: round(sum(vals) / len(vals), 2) for t, vals in tiempos_por_tarea.items() if vals},
        "responsables_recomendados": {t: _mas_comun(vals) for t, vals in personal_por_tarea.items()},
        "incidencias_frecuentes": dict(incidencias.most_common(8)),
        "dias_mas_fuertes": dict(dias_fuertes.most_common(4)),
    }

    recomendaciones = _recomendaciones(aprendizajes)
    return {
        "ok": True,
        "version": "5.4.6",
        "estado": "aprendizaje_operativo_generado",
        "registros_analizados": len(historico),
        "aprendizajes": aprendizajes,
        "recomendaciones": recomendaciones,
        "requiere_confirmacion": False,
        "aplicado": False,
        "mensaje": "Aprendizaje generado en modo seguro. No se ha escrito memoria permanente.",
        "lectura_jefe_cocina": _lectura_jefe(recomendaciones),
        "contexto_recibido": contexto,
    }


def _recomendaciones(aprendizajes: Dict[str, Any]) -> List[Dict[str, Any]]:
    recs: List[Dict[str, Any]] = []
    if aprendizajes.get("proveedores_preferidos"):
        recs.append({"tipo": "compras", "prioridad": "media", "accion": "Usar proveedores preferidos por articulo antes de buscar alternativas."})
    if aprendizajes.get("tiempos_medios_tarea_h"):
        recs.append({"tipo": "produccion", "prioridad": "alta", "accion": "Usar tiempos reales medios para planificar en vez de tiempos teoricos."})
    if aprendizajes.get("responsables_recomendados"):
        recs.append({"tipo": "personal", "prioridad": "media", "accion": "Asignar tareas al cocinero que historicamente las ejecuta mejor o mas a menudo."})
    if aprendizajes.get("incidencias_frecuentes"):
        tipo = next(iter(aprendizajes["incidencias_frecuentes"].keys()))
        recs.append({"tipo": "riesgo", "prioridad": "alta", "accion": f"Vigilar preventivamente incidencia recurrente: {tipo}."})
    if aprendizajes.get("dias_mas_fuertes"):
        recs.append({"tipo": "planificacion", "prioridad": "media", "accion": "Reforzar compras y personal en los dias historicamente mas fuertes."})
    return recs


def _lectura_jefe(recomendaciones: List[Dict[str, Any]]) -> str:
    if not recomendaciones:
        return "Todavia no hay suficiente historico para aprender con seguridad."
    principal = recomendaciones[0]
    return f"Lo primero que ajustaria con el historico seria: {principal.get('accion')}"


def _historico_demo() -> List[Dict[str, Any]]:
    return [
        {"dia": "sabado", "personas": 180, "compras": [{"articulo": "arroz bomba", "proveedor": "Makro"}], "tareas": [{"nombre": "paella", "tiempo_real_h": 3.5, "responsable": "Juan"}], "incidencias": [{"tipo": "falta_stock"}]},
        {"dia": "sabado", "personas": 120, "compras": [{"articulo": "arroz bomba", "proveedor": "Makro"}], "tareas": [{"nombre": "paella", "tiempo_real_h": 3.0, "responsable": "Juan"}], "incidencias": []},
        {"dia": "viernes", "personas": 80, "compras": [{"articulo": "nata", "proveedor": "Transgourmet"}], "tareas": [{"nombre": "postres", "tiempo_real_h": 2.0, "responsable": "Marta"}], "incidencias": [{"tipo": "proveedor_tarde"}]},
    ]


def formatear_aprendizaje_546(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = ["HOST AI 5.4.6 - APRENDIZAJE OPERATIVO", "-" * 60]
    lineas.append(f"Estado: {resultado.get('estado')}")
    lineas.append(f"Registros analizados: {resultado.get('registros_analizados')}")
    lineas.append(f"Aplicado a memoria real: {resultado.get('aplicado')}")
    lineas.append("")
    aprendizajes = resultado.get("aprendizajes", {}) or {}
    lineas.append("APRENDIZAJES")
    for clave, valor in aprendizajes.items():
        lineas.append(f"- {clave}: {valor}")
    lineas.append("")
    lineas.append("RECOMENDACIONES")
    for rec in resultado.get("recomendaciones", []):
        lineas.append(f"- [{rec.get('prioridad')}] {rec.get('accion')}")
    lineas.append("")
    lineas.append("LECTURA DE SEGUNDO JEFE")
    lineas.append(f"- {resultado.get('lectura_jefe_cocina')}")
    return "\n".join(lineas)


__all__ = ["aprender_operativa_546", "formatear_aprendizaje_546"]
