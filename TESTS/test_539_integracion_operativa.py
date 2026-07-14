from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.integracion_operativa_539 import cerrar_inteligencia_operativa_539, formatear_cierre_operativo_539


def escenario_base():
    return {
        "tipo": "boda",
        "personas": 180,
        "fecha": "sabado",
        "hora_servicio": "15:00",
        "menu": "menu boda",
        "lugar": "Mas Boronat",
        "restricciones": "sin restricciones",
        "objetivo": "flujo completo",
    }


def contexto_con_incidencias():
    return {
        "stock": [
            {"nombre": "arroz bomba", "disponible": 8, "necesario": 18, "unidad": "kg", "imprescindible": True},
            {"nombre": "vino blanco cocina", "disponible": 1, "necesario": 6, "unidad": "l"},
        ],
        "recursos": [
            {"nombre": "horno 1", "estado": "ocupado", "detalle": "Ocupado por otro evento"},
        ],
        "proveedores": [
            {"nombre": "Proveedor habitual", "disponible": False, "detalle": "No reparte mañana"},
        ],
        "personal": {"disponibles": 2, "necesarios": 3},
        "conflictos": [
            {"titulo": "Conflicto produccion/evento", "nivel": "alto", "detalle": "Mismo recurso para dos servicios."}
        ],
    }


def test_cierre_539_con_incidencias():
    resultado = cerrar_inteligencia_operativa_539(escenario_base(), contexto_con_incidencias())
    assert resultado["ok"] is True
    assert resultado["version"] == "5.3.9"
    assert resultado["aplica_cambios_reales"] is False
    assert len(resultado["validacion_bloques"]) == 8
    assert all(bloque["ok"] for bloque in resultado["validacion_bloques"])
    assert resultado["resumen_incidencias"]["alto"] >= 1 or resultado["resumen_incidencias"]["critico"] >= 1
    assert resultado["replanificacion"]["requiere_confirmacion"] is True
    assert resultado["replanificacion"]["nuevo_planning"]
    assert "confirmacion" in resultado["recomendacion_final"].lower() or "criticas" in resultado["recomendacion_final"].lower()


def test_cierre_539_sin_incidencias_es_rc():
    resultado = cerrar_inteligencia_operativa_539(escenario_base(), contexto={})
    assert resultado["ok"] is True
    assert resultado["estado"] in {"release_candidate_5_3", "operativo_con_confirmacion"}
    assert resultado["resumen_incidencias"] == {"critico": 0, "alto": 0, "medio": 0, "bajo": 0}
    texto = formatear_cierre_operativo_539(resultado)
    assert "HOST AI 5.3.9" in texto
    assert "VALIDACION DE BLOQUES" in texto


def test_cierre_539_faltan_datos_bloquea():
    resultado = cerrar_inteligencia_operativa_539({"tipo": "boda"}, contexto={})
    assert resultado["ok"] is False
    assert resultado["estado"] == "bloqueado"
    assert any(not bloque["ok"] for bloque in resultado["validacion_bloques"])


if __name__ == "__main__":
    test_cierre_539_con_incidencias()
    test_cierre_539_sin_incidencias_es_rc()
    test_cierre_539_faltan_datos_bloquea()
    print("TEST OK 5.3.9 Integracion Operativa y Release Candidate 5.3")
