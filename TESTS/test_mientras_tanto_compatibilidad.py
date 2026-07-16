from __future__ import annotations

from MOTORES.motor_produccion_real import MotorProduccionReal


class _DummyMotor:
    def __init__(self, tareas):
        self._tareas = tareas

    def panel_produccion(self, plan_id: str):
        return {"tareas_pendientes": self._tareas}

    @staticmethod
    def _normalizar_estado_ejecucion(estado: str) -> str:
        return str(estado or "pendiente").strip().lower()


def _tarea(
    tarea_id: str,
    titulo: str,
    prioridad: int,
    estado: str = "pendiente",
    origen: str = "escandallo_evento",
    pasiva: int = 0,
    restante: int = 30,
):
    fase = {
        "id": f"F-{tarea_id}",
        "nombre": "Fase",
        "tipo": "coccion" if pasiva else "preparacion",
        "recurso": "horno" if pasiva else "mesa_trabajo",
        "duracion_pasiva_min": pasiva,
        "dependencia": "",
    }
    return {
        "id": tarea_id,
        "titulo": titulo,
        "prioridad": prioridad,
        "estado_ejecucion": estado,
        "origen": origen,
        "bloqueo": "",
        "fases": [fase],
        "fase_activa_id": fase["id"] if pasiva else "",
        "tiempo_restante_estimado_min": restante,
    }


def test_mientras_tanto_descarta_logistica_si_hay_produccion_critica():
    principal = _tarea("T1", "Demi-glace", prioridad=95, pasiva=90, restante=90)
    logistica = _tarea("T2", "Carga, transporte y montaje", prioridad=80, origen="logistica", restante=30)
    critica = _tarea("T3", "Preparar Puré de patata", prioridad=85, origen="escandallo_evento", restante=40)

    dummy = _DummyMotor([principal, logistica, critica])
    rec = MotorProduccionReal.siguiente_tarea_recomendada(dummy, "P1")

    assert rec["codigo"] == "SUGERIDA"
    assert rec["tarea_id"] == "T1"
    assert rec.get("mientras_tanto", {}).get("tarea_id") == "T3"


def test_mientras_tanto_no_aparece_si_no_hay_compatible_real():
    principal = _tarea("T1", "Demi-glace", prioridad=95, pasiva=40, restante=40)
    # Solo existe una tarea final de logística.
    logistica = _tarea("T2", "Carga, transporte y montaje", prioridad=80, origen="logistica", restante=20)

    dummy = _DummyMotor([principal, logistica])
    rec = MotorProduccionReal.siguiente_tarea_recomendada(dummy, "P1")

    assert rec["codigo"] == "SUGERIDA"
    assert rec["tarea_id"] == "T1"
    assert rec.get("mientras_tanto", {}) == {}
