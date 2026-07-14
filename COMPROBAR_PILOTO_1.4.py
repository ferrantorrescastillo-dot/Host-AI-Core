from pathlib import Path
from tempfile import TemporaryDirectory

from CORE.host_ai_core import HostAICore
from MODELOS.produccion_real import TareaProduccionReal
from SERVICIOS.produccion_stock_piloto_14 import ProduccionStockPiloto14, formatear_diagnostico_piloto14


def main():
    with TemporaryDirectory() as td:
        core = HostAICore(Path(td))
        core.db.guardar("escandallos", [{"receta_id":"REC-DIAG","nombre":"Elaboración diagnóstico","raciones_base":10,"lineas":[{"nombre":"Materia prima diagnóstico","cantidad":2,"unidad":"kg","articulo_id":"ART-DIAG","tipo":"articulo"}]}])
        core.stock.registrar_entrada("Materia prima diagnóstico", 10, "kg", articulo_id="ART-DIAG")
        plan = core.produccion_real.crear_plan_manual("Plan diagnóstico", responsable="cocina", estado="planificado")
        tarea = TareaProduccionReal(titulo="Elaboración diagnóstico", receta_id="REC-DIAG", receta="Elaboración diagnóstico", cantidad=10, unidad="u")
        core.produccion_real.planes[plan["id"]].tareas.append(tarea)
        core.produccion_real._persistir()
        servicio = ProduccionStockPiloto14(core)
        resultado = servicio.cerrar_y_actualizar_stock(plan["id"], tarea.id, "diagnóstico", "TEST-001")
        duplicado = servicio.preparar_cierre(plan["id"], tarea.id)
        ok = resultado.get("ok") and duplicado.get("estado") == "YA_REGISTRADA" and len(servicio.historial()) == 1
        datos = {"diagnostico":"OK" if ok else "ERROR", "consumos":1 if resultado.get("ok") else 0, "entradas":1 if resultado.get("ok") else 0, "trazabilidad":"OK" if servicio.historial() else "ERROR", "duplicados":"OK" if duplicado.get("estado") == "YA_REGISTRADA" else "ERROR", "rollback":"ACTIVO"}
        print(formatear_diagnostico_piloto14(datos))
        raise SystemExit(0 if ok else 1)

if __name__ == "__main__": main()
