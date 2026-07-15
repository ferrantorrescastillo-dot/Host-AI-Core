from pathlib import Path

from CORE.host_ai_core import HostAICore
from MODELOS.produccion_real import TareaProduccionReal
from SERVICIOS.jornada_piloto_12 import JornadaPiloto12
from SERVICIOS.produccion_guiada_piloto_13 import ProduccionGuiadaPiloto13


def crear_escenario(tmp_path: Path):
    core = HostAICore(tmp_path)
    core.db.guardar("escandallos", [{
        "receta_id": "REC-CALDO",
        "nombre": "Caldo base",
        "raciones_base": 10,
        "lineas": [{
            "nombre": "Huesos",
            "cantidad": 2.0,
            "cantidad_bruta": 2.0,
            "unidad": "kg",
            "tipo": "articulo",
            "articulo_id": "ART-HUESOS",
        }],
    }])
    core.stock.registrar_entrada("Huesos", 10.0, "kg", articulo_id="ART-HUESOS")

    plan = core.produccion_real.crear_plan_manual("Turno RP2", "2026-07-16", "Chef", estado="planificado")
    tarea = TareaProduccionReal(
        titulo="Caldo base",
        receta_id="REC-CALDO",
        receta="Caldo base",
        cantidad=10,
        unidad="u",
        prioridad=90,
    )
    core.produccion_real.planes[plan["id"]].tareas.append(tarea)
    core.produccion_real.anadir_fase_manual(plan["id"], tarea.id, "Mise en place", 20, "activo", "mesa", "cocinero")
    core.produccion_real.anadir_fase_manual(plan["id"], tarea.id, "Reposo", 60, "reposo", "abatidor", "cocinero")
    core.produccion_real._persistir()
    return core, plan["id"], tarea.id


def test_rp2_ciclo_operativo_completo(tmp_path: Path):
    core, plan_id, tarea_id = crear_escenario(tmp_path)
    servicio = ProduccionGuiadaPiloto13(core)

    inicio = servicio.iniciar(plan_id, tarea_id)
    assert inicio["estado_ejecucion"] in {"en_preparacion", "en_proceso"}

    cambio = servicio.cambiar_fase(plan_id, tarea_id)
    assert cambio["estado_ejecucion"] in {"en_espera", "en_proceso"}

    pausa = servicio.pausar(plan_id, tarea_id)
    assert pausa["estado_ejecucion"] == "pausada"

    reanudar = servicio.reanudar(plan_id, tarea_id)
    assert reanudar["estado_ejecucion"] in {"en_espera", "en_proceso"}

    incidencia = servicio.registrar_incidencia(plan_id, tarea_id, "Demora por horno", bloqueo=False, retraso_min=10)
    assert incidencia["tipo"] == "incidencia"

    merma = servicio.registrar_merma(plan_id, tarea_id, 0.5, "u", motivo="Ajuste por evaporacion")
    assert merma["cantidad"] == 0.5

    cierre = servicio.finalizar_con_stock(plan_id, tarea_id, operario="Chef", lote="RP2-LOTE-1")
    assert cierre["ok"] is True
    assert core.produccion_real.estado_tarea(plan_id, tarea_id)["estado_ejecucion"] == "finalizada"



def test_rp2_briefing_incluye_produccion_viva(tmp_path: Path):
    core, plan_id, tarea_id = crear_escenario(tmp_path)
    servicio = ProduccionGuiadaPiloto13(core)
    servicio.iniciar(plan_id, tarea_id)
    servicio.registrar_incidencia(plan_id, tarea_id, "Falta tapa GN", bloqueo=True, retraso_min=15)

    jornada = JornadaPiloto12(tmp_path).construir()
    briefing = jornada["briefing_apertura"]
    viva = briefing.get("produccion_viva") or {}

    assert viva.get("planes_activos", 0) >= 1
    assert viva.get("tareas_total", 0) >= 1
    assert viva.get("tareas_bloqueadas", 0) >= 1
    assert isinstance(viva.get("siguiente_accion", ""), str)
