from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Iterable, List


BLOQUES_4X = {
    "4.1 Catalogo": ["APP/buscar_articulos_415.py", "APP/editar_articulo_417.py"],
    "4.2 Proveedores": ["APP/extraer_proveedores_421.py", "APP/editar_proveedor_422.py"],
    "4.3 Stock": ["APP/movimiento_stock_437.py", "APP/salida_stock_439.py"],
    "4.4 Recepcion": ["APP/interpretar_recepcion_texto_441.py", "APP/aplicar_recepcion_mercancia_443.py"],
    "4.5 Infraestructura": ["APP/configuracion_host_ai_4414.py", "APP/base_datos_definitiva_451.py"],
    "4.6 Produccion": ["APP/planificador_diario_produccion_461.py", "APP/informe_diario_produccion_468.py"],
    "4.7 Eventos": ["APP/gestion_eventos_471.py", "APP/informe_final_evento_478.py"],
    "4.8 Rentabilidad": ["APP/coste_real_receta_481.py", "APP/informe_financiero_inteligente_488.py"],
    "4.9 IA Operativa": ["APP/motor_decisiones_operativas_491.py", "APP/panel_ia_central_497.py"],
}


def _existe(base: Path, relativo: str) -> bool:
    return (base / relativo).exists()


def verificar_bloque(base: str | Path, nombre: str, archivos: Iterable[str]) -> Dict[str, Any]:
    base_path = Path(base)
    estado_archivos = [{"archivo": archivo, "existe": _existe(base_path, archivo)} for archivo in archivos]
    faltantes = [a["archivo"] for a in estado_archivos if not a["existe"]]
    return {
        "bloque": nombre,
        "ok": not faltantes,
        "archivos": estado_archivos,
        "faltantes": faltantes,
    }


def generar_cierre_host_ai_4(base: str | Path = ".") -> Dict[str, Any]:
    base_path = Path(base)
    bloques = [verificar_bloque(base_path, nombre, archivos) for nombre, archivos in BLOQUES_4X.items()]
    total = len(bloques)
    ok = sum(1 for b in bloques if b["ok"])
    faltantes: List[str] = []
    for bloque in bloques:
        faltantes.extend([f"{bloque['bloque']}: {archivo}" for archivo in bloque["faltantes"]])

    estado = "listo_para_auditoria_final" if ok == total else "requiere_revision"
    return {
        "version": "Host AI 4.0",
        "estado": estado,
        "bloques_totales": total,
        "bloques_ok": ok,
        "bloques_pendientes": total - ok,
        "bloques": bloques,
        "faltantes": faltantes,
        "siguiente_paso": "auditoria tecnica completa antes de Host AI 5.0" if estado == "listo_para_auditoria_final" else "revisar archivos faltantes antes de cerrar 4.0",
    }


def formatear_cierre_host_ai_4(informe: Dict[str, Any]) -> str:
    lineas = [
        "=== CIERRE HOST AI 4.0 ===",
        f"Estado: {informe.get('estado')}",
        f"Bloques OK: {informe.get('bloques_ok')}/{informe.get('bloques_totales')}",
        "",
        "Bloques:",
    ]
    for bloque in informe.get("bloques", []):
        marca = "OK" if bloque.get("ok") else "REVISAR"
        lineas.append(f"- {marca}: {bloque.get('bloque')}")
    if informe.get("faltantes"):
        lineas.append("")
        lineas.append("Archivos faltantes:")
        for faltante in informe["faltantes"][:20]:
            lineas.append(f"- {faltante}")
    lineas.append("")
    lineas.append(f"Siguiente paso: {informe.get('siguiente_paso')}")
    return "\n".join(lineas)
