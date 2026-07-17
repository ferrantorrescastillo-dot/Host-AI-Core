from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore


def _preparar_config(base: Path, recursos: dict[str, int] | None = None) -> None:
    cfg = base / "DATOS" / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    payload = {"recursos": recursos or {"horno": 1, "fogones": 4, "mesa_trabajo": 2, "abatidor": 1}}
    (cfg / "recursos_cocina_556e2.json").write_text(json.dumps(payload), encoding="utf-8")


def _buscar(lista: list[dict], clave: str, valor: str) -> dict:
    return next(item for item in lista if item.get(clave) == valor)


def test_detecta_recursos_separa_humano_y_conserva_capacidad_desconocida(tmp_path):
    _preparar_config(tmp_path, {"horno": 1, "fogones": 4})
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Inventario")
    tarea = core.produccion_real.anadir_tarea_manual(plan["id"], "Carrillera", prioridad=90)
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Cocción lenta", 180, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Termomixar salsa", 20, recurso="thermomix", responsable="ayudante")

    inventario = core.produccion_real.inventario_recursos(plan["id"])

    horno = _buscar(inventario["recursos_fisicos"], "id_normalizado", "horno")
    thermomix = _buscar(inventario["recursos_fisicos"], "id_normalizado", "thermomix")
    cocinero = _buscar(inventario["recursos_humanos"], "rol", "cocinero")
    ayudante = _buscar(inventario["recursos_humanos"], "rol", "ayudante")

    assert horno["capacidad"] == 1
    assert horno["capacidad_confirmada"] is True
    assert horno["usado_por"] == [{"tarea": "Carrillera", "fase": "Cocción lenta"}]
    assert thermomix["capacidad"] == "desconocida"
    assert thermomix["capacidad_confirmada"] is False
    assert cocinero["cantidad"] == "desconocida"
    assert ayudante["cantidad"] == "desconocida"
    assert all(item["id_normalizado"] != "cocinero" for item in inventario["recursos_fisicos"])
    assert all(item["rol"] != "horno" for item in inventario["recursos_humanos"])
    assert any(item.get("tipo") == "capacidad_desconocida" and item.get("recurso") == "thermomix" for item in inventario["datos_incompletos"])


def test_normaliza_alias_seguro_sin_duplicar_y_preserva_origen(tmp_path):
    _preparar_config(tmp_path, {"fogones": 4, "mesa_trabajo": 2, "horno": 1})
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Alias recursos")
    core.produccion_real.obtener_plan(plan["id"]).configuracion_planificacion = {"cocineros": 2}
    tarea = core.produccion_real.anadir_tarea_manual(plan["id"], "Bases", prioridad=70)
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Reducir", 30, recurso="fuego", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Cocer", 15, recurso="fogón", responsable="Cocinero 1")
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Preparar", 20, recurso="mesa de trabajo", responsable="Cocinero 2")
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Hornear", 25, recurso=" HORNO ", responsable="cocinero")

    inventario = core.produccion_real.inventario_recursos(plan["id"])

    fogones = _buscar(inventario["recursos_fisicos"], "id_normalizado", "fogones")
    mesa = _buscar(inventario["recursos_fisicos"], "id_normalizado", "mesa_trabajo")
    horno = _buscar(inventario["recursos_fisicos"], "id_normalizado", "horno")
    cocinero = _buscar(inventario["recursos_humanos"], "rol", "cocinero")

    assert set(fogones["nombres_origen"]) == {"fuego", "fogón"}
    assert mesa["nombres_origen"] == ["mesa de trabajo"]
    assert horno["nombres_origen"] == ["HORNO"]
    assert len([item for item in inventario["recursos_fisicos"] if item["id_normalizado"] == "horno"]) == 1
    assert cocinero["cantidad"] == 2
    assert cocinero["cantidad_confirmada"] is True
    assert cocinero["cantidad_origen"] == "plan.configuracion_planificacion.cocineros"


def test_compatibilidad_plan_antiguo_y_caso_vacio(tmp_path):
    _preparar_config(tmp_path, {"horno": 1})
    core = HostAICore(tmp_path)
    plan_id = "PLAN-LEGACY-1"
    core.db.guardar("planes_produccion", [{
        "id": plan_id,
        "nombre": "Legacy",
        "fecha": "2026-07-17",
        "responsable": "Ferran",
        "tareas": [{
            "id": "T1",
            "titulo": "Carrillera",
            "prioridad": 80,
            "estado_ejecucion": "pendiente",
            "fases": [{"id": "F1", "nombre": "Hornear", "duracion_min": 120, "tipo": "produccion", "recurso": "horno", "responsable": "cocinero"}],
        }],
        "cronograma": [],
        "avisos": [],
        "estado": "borrador",
    }])

    recargado = HostAICore(tmp_path)
    inventario = recargado.produccion_real.inventario_recursos(plan_id)
    horno = _buscar(inventario["recursos_fisicos"], "id_normalizado", "horno")
    assert horno["capacidad"] == 1

    plan_vacio = recargado.produccion_real.crear_plan_manual("Vacío")
    vacio = recargado.produccion_real.inventario_recursos(plan_vacio["id"])
    assert vacio["recursos_fisicos"] == []
    assert vacio["recursos_humanos"] == []


def test_panel_conserva_clasificacion_cronologia_cuellos_y_recomendacion(tmp_path):
    _preparar_config(tmp_path, {"horno": 1, "mesa_trabajo": 2, "fuego": 1})
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Panel")
    plan_id = plan["id"]
    carrillera = core.produccion_real.anadir_tarea_manual(plan_id, "Carrillera", prioridad=90, origen="escandallo_evento")
    costillar = core.produccion_real.anadir_tarea_manual(plan_id, "Costillar", prioridad=80, origen="escandallo_evento")
    core.produccion_real.anadir_fase_manual(plan_id, carrillera["id"], "Hornear", 120, tipo="produccion", recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, costillar["id"], "Preparar", 60, tipo="produccion", recurso="mesa_trabajo", responsable="cocinero")

    plan_obj = core.produccion_real.obtener_plan(plan_id)
    plan_obj.configuracion_planificacion = {"jornada_horas": 7.5, "cocineros": 1, "hora_inicio": "08:00"}
    plan_obj.planificacion_inteligente = {
        "bloques": [
            {"clave": carrillera["id"], "nombre": "Carrillera", "dia": 1, "inicio_min": 0, "fin_min": 120, "duracion_min": 120, "tipo_tiempo": "activo", "recurso": "horno", "dependencias": [], "datos": {"prioridad_num": 90}},
            {"clave": costillar["id"], "nombre": "Costillar", "dia": 1, "inicio_min": 45, "fin_min": 105, "duracion_min": 60, "tipo_tiempo": "activo", "recurso": "horno", "dependencias": [], "datos": {"prioridad_num": 80}},
        ]
    }
    plan_obj.asignacion_recursos = {
        "carga_por_cocinero": {"Cocinero 1": 180},
        "resumen": {"capacidad_por_cocinero_min": 450},
        "asignaciones": [
            {"cocinero": "Cocinero 1", "dia": 1, "inicio_min": 0, "fin_min": 120, "duracion_min": 120, "elaboracion": "Carrillera", "recurso": "horno", "datos": {"tarea_id": carrillera["id"]}},
            {"cocinero": "Cocinero 1", "dia": 1, "inicio_min": 45, "fin_min": 105, "duracion_min": 60, "elaboracion": "Costillar", "recurso": "horno", "datos": {"tarea_id": costillar["id"]}},
        ],
    }
    core.produccion_real._persistir()

    panel = core.produccion_real.panel_produccion(plan_id)
    recomendacion = core.produccion_real.siguiente_tarea_recomendada(plan_id)

    assert panel["clasificacion_jornada"]["total_elaboraciones"] >= 2
    assert panel["cronologia_operativa_prevista"]["base_horaria"]["texto"].startswith("08:00")
    assert panel["cuellos_botella_previstos"]["resumen"]["recursos"] == 1
    assert panel["inventario_recursos"]["recursos_fisicos"]
    assert recomendacion["codigo"] == "SUGERIDA"