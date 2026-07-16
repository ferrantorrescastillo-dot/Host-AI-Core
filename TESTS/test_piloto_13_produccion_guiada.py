from __future__ import annotations

from types import SimpleNamespace

from SERVICIOS.produccion_guiada_piloto_13 import ProduccionGuiadaPiloto13


class PlanFake:
    def __init__(self, data): self.data = data
    def to_dict(self): return self.data


class MotorFake:
    def __init__(self):
        self.calls = []
        self.recomendacion = None
        self.plan = {
            "id": "P1", "nombre": "Boda sábado", "fecha": "2026-07-18", "estado": "en_produccion",
            "asignacion_recursos": {"asignaciones": [
                {"clave": "T1", "cocinero": "Cocinero 1", "recurso": "horno"},
                {"clave": "T2", "cocinero": "Cocinero 2", "recurso": "mesa_trabajo"},
            ]},
            "tareas": [{"id": "T1"}, {"id": "T2"}],
        }
        self.tareas = [
            {
                "id":"T1",
                "titulo":"Carrillera",
                "estado_ejecucion":"en_curso",
                "prioridad":90,
                "tiempo_real_min":35,
                "tiempo_restante_estimado_min":85,
                "fase_activa_id":"F1",
                "fases":[
                    {
                        "id":"F1",
                        "nombre":"Horno inicial",
                        "estado":"EN_ESPERA",
                        "tipo":"coccion",
                        "duracion_min":60,
                        "duracion_activa_min":10,
                        "duracion_pasiva_min":50,
                        "recurso":"horno",
                        "responsable":"cocinero_1",
                        "dependencia":"",
                    },
                    {
                        "id":"F2",
                        "nombre":"Salseado final",
                        "estado":"PENDIENTE",
                        "tipo":"produccion",
                        "duracion_min":20,
                        "duracion_activa_min":20,
                        "duracion_pasiva_min":0,
                        "recurso":"fuego",
                        "responsable":"cocinero_1",
                        "dependencia":"",
                    },
                ],
                "bloqueo":"",
                "checklist_pendiente":0,
            },
            {"id":"T2","titulo":"Cortar verduras","estado_ejecucion":"pendiente","prioridad":70,"tiempo_real_min":0,"tiempo_restante_estimado_min":45,"fases":[],"bloqueo":"","checklist_pendiente":0},
        ]

    def listar_planes(self): return [self.plan]
    def obtener_plan(self, plan_id): return PlanFake(self.plan)
    def resumen_ejecucion(self, plan_id):
        return {"plan":"Boda sábado","estado_plan":"en_produccion","porcentaje_completado":25,"total_tareas":2,"tareas":self.tareas,"alertas":[],"tareas_pendientes":self.tareas}
    def iniciar_tarea(self,*a): self.calls.append(("iniciar",a)); return {"titulo":"x"}
    def pausar_tarea(self,*a): self.calls.append(("pausar",a)); return {"titulo":"x"}
    def reanudar_tarea(self,*a): self.calls.append(("reanudar",a)); return {"titulo":"x"}
    def finalizar_tarea(self,*a): self.calls.append(("finalizar",a)); return {"titulo":"x"}
    def actualizar_progreso_tarea(self,*a): self.calls.append(("avance",a)); return {"porcentaje_avance":a[-1]}
    def registrar_incidencia_tarea(self,*a): self.calls.append(("incidencia",a)); return {"tipo":a[2]}
    def resolver_bloqueo_tarea(self,*a): self.calls.append(("resolver",a)); return {"ok":True}
    def siguiente_tarea_recomendada(self, plan_id):
        if self.recomendacion is not None:
            return self.recomendacion
        return {
            "codigo": "SUGERIDA",
            "tarea_id": "T2",
            "texto": "Empieza ahora: Cortar verduras",
            "criterios": ["puede arrancarse ya sin esperar otras tareas"],
        }


def servicio():
    motor = MotorFake()
    return ProduccionGuiadaPiloto13(SimpleNamespace(produccion_real=motor)), motor


def test_panel_humano_y_siguiente_accion():
    s, _ = servicio()
    p = s.construir_panel("P1")
    assert p["siguiente_accion"]["codigo"] == "CONTINUAR"
    assert "Carrillera" in p["siguiente_accion"]["texto"]
    assert p["tareas"][0]["estado_texto"] == "🟠 En marcha"
    assert p["tareas"][0]["tiempo_restante_texto"] == "1 h 25 min"
    assert p["tareas"][0]["responsable_texto"] == "Cocinero 1"


def test_bloqueo_es_lo_primero():
    s, m = servicio()
    m.tareas[1]["bloqueo"] = "Falta producto"
    p = s.construir_panel("P1")
    assert p["siguiente_accion"]["codigo"] == "RESOLVER_BLOQUEO"
    assert p["bloqueadas"] == 1


def test_plan_finalizado_no_aparece():
    s, m = servicio()
    m.plan["estado"] = "finalizado"
    assert s.listar_planes_operativos() == []


def test_acciones_delegadas_sin_duplicar_motor():
    s, m = servicio()
    s.iniciar("P1","T2")
    s.pausar("P1","T1")
    s.reanudar("P1","T1")
    s.finalizar("P1","T1")
    s.actualizar_avance("P1","T2",50)
    s.registrar_incidencia("P1","T2","Falta cebolla",True,15)
    s.resolver_bloqueo("P1","T2","Llegó almacén")
    assert [x[0] for x in m.calls] == ["iniciar","pausar","reanudar","finalizar","avance","incidencia","resolver"]
    assert m.calls[5][1][2] == "bloqueo"


def test_terminado_propone_cierre():
    s, m = servicio()
    for t in m.tareas: t["estado_ejecucion"] = "finalizada"
    p = s.construir_panel("P1")
    assert p["siguiente_accion"]["codigo"] == "FINALIZADO"
    assert p["pendientes"] == 0


def test_inicio_con_razonamiento_culinario_desde_motor():
    s, m = servicio()
    m.tareas[0]["estado_ejecucion"] = "pendiente"
    m.tareas[0]["prioridad"] = 40
    m.recomendacion = {
        "codigo": "SUGERIDA",
        "tarea_id": "T2",
        "criterios": [
            "desbloquea elaboraciones dependientes",
            "genera tiempo pasivo para avanzar otras elaboraciones",
        ],
        "mientras_tanto": {"texto": "Preparar Demi-glace"},
        "atencion_intervalo": "Vigilar la reducción y cambiar de fase al finalizar la espera.",
        "siguiente_movimiento": {"texto": "Comenzar Puré de patata"},
    }
    p = s.construir_panel("P1")
    assert p["siguiente_accion"]["codigo"] == "INICIAR"
    assert "Se recomienda" in p["siguiente_accion"]["explicacion"]
    assert "desbloquea elaboraciones dependientes" in p["siguiente_accion"]["explicacion"]
    assert "genera tiempo pasivo" in p["siguiente_accion"]["explicacion"]
    assert p["recomendacion_motor"]["mientras_tanto"] == "Preparar Demi-glace"
    assert "Vigilar la reducción" in p["recomendacion_motor"]["atencion_intervalo"]
    assert p["recomendacion_motor"]["siguiente_movimiento"] == "Comenzar Puré de patata"


def test_atencion_intervalo_no_se_muestra_en_fase_activa():
    s, m = servicio()
    m.tareas[0]["fases"][0]["duracion_pasiva_min"] = 0
    m.tareas[0]["fases"][0]["duracion_activa_min"] = 30
    m.tareas[0]["fases"][0]["estado"] = "EN_CURSO"
    m.tareas[1]["prioridad"] = 60
    m.recomendacion = {
        "codigo": "SUGERIDA",
        "tarea_id": "T1",
        "criterios": ["mantiene el flujo de trabajo"],
        "atencion_intervalo": "Vigilar la fase 'Preparar base' y confirmar el cambio cuando termine la espera.",
        "siguiente_movimiento": {"texto": "Comenzar Carga, transporte y montaje"},
    }
    p = s.construir_panel("P1")
    assert p["recomendacion_motor"]["tarea_id"] == "T1"
    assert "atencion_intervalo" not in p["recomendacion_motor"]


def test_siguiente_movimiento_se_oculta_si_hay_produccion_critica_pendiente():
    s, m = servicio()
    m.tareas[0]["bloqueo"] = "Stock insuficiente"
    m.tareas[1]["estado_ejecucion"] = "pendiente"
    m.recomendacion = {
        "codigo": "SUGERIDA",
        "tarea_id": "T2",
        "criterios": ["desbloquea elaboraciones dependientes"],
        "mientras_tanto": {},
        "atencion_intervalo": "",
        "siguiente_movimiento": {"texto": "Comenzar Carga, transporte y montaje"},
    }
    p = s.construir_panel("P1")
    assert p["recomendacion_motor"]["tarea_id"] == "T2"
    assert "siguiente_movimiento" not in p["recomendacion_motor"]


def test_mientras_tanto_no_aparece_si_no_hay_compatibilidad():
    s, m = servicio()
    m.tareas[0]["estado_ejecucion"] = "pendiente"
    m.recomendacion = {
        "codigo": "SUGERIDA",
        "tarea_id": "T2",
        "criterios": ["el servicio depende de tenerla lista a tiempo"],
        "mientras_tanto": {},
        "atencion_intervalo": "",
        "siguiente_movimiento": {"texto": "Comenzar Puré de patata"},
    }
    p = s.construir_panel("P1")
    assert "mientras_tanto" not in p["recomendacion_motor"]
    assert "atencion_intervalo" not in p["recomendacion_motor"]
    assert p["recomendacion_motor"]["siguiente_movimiento"] == "Comenzar Puré de patata"


def test_fase_actual_muestra_solo_propiedades_operativas_disponibles():
    s, _ = servicio()
    p = s.construir_panel("P1")
    fase = p.get("fase_actual") or {}
    assert fase.get("nombre") == "Horno inicial"
    props = fase.get("propiedades") or []
    assert props
    texto = "\n".join(props).lower()
    assert "atención" in texto
    assert "tiempo pasivo estimado" in texto
    assert "recurso principal: horno" in texto
    assert "responsable operativo: cocinero 1" in texto
    assert "Siguiente cambio de fase: Salseado final" in "\n".join(props)
    assert "desconocido" not in texto


def test_fase_actual_no_aparece_si_no_hay_fase_operativa():
    s, m = servicio()
    m.tareas[0]["fase_activa_id"] = ""
    for fase in m.tareas[0]["fases"]:
        fase["estado"] = "PENDIENTE"
    p = s.construir_panel("P1")
    assert p.get("fase_actual") == {}


def test_iniciar_tarea_con_fases_activa_primera_fase_y_muestra_fase_actual(tmp_path):
    from CORE.host_ai_core import HostAICore

    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Plan inicio fases")
    tarea = core.produccion_real.anadir_tarea_manual(plan["id"], "Demi-glace", prioridad=90)
    core.produccion_real.anadir_fase_manual(
        plan["id"],
        tarea["id"],
        "Preparar base",
        30,
        tipo="preparacion",
        recurso="mesa_trabajo",
        responsable="cocinero",
    )
    core.produccion_real.anadir_fase_manual(
        plan["id"],
        tarea["id"],
        "Cocinar / reducir",
        120,
        tipo="coccion",
        recurso="fuego",
        responsable="cocinero",
    )

    guiada = ProduccionGuiadaPiloto13(core)
    guiada.iniciar(plan["id"], tarea["id"])
    panel = guiada.construir_panel(plan["id"])

    estado = core.produccion_real.estado_tarea(plan["id"], tarea["id"])
    assert estado.get("fase_activa_id")
    assert panel.get("fase_actual", {}).get("nombre") == "Preparar base"
    assert panel.get("fase_actual", {}).get("propiedades")
