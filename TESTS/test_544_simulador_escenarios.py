from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.simulador_escenarios_544 import simular_escenario_544, simular_varios_escenarios_544


def _evento():
    return {"tipo":"boda","personas":180,"fecha":"sabado","hora_servicio":"15:00","menu":"paella","lugar":"Restaurante","restricciones":"sin restricciones","objetivo":"todo el flujo completo"}


def _contexto():
    return {
        "stock": [{"nombre":"arroz bomba","disponible":18,"necesario":18}],
        "personal": {"disponibles":3,"necesarios":3},
        "proveedores": [{"nombre":"Makro","disponible":True}],
    }


def test_simula_incremento_personas_sin_aplicar():
    r = simular_escenario_544(_evento(), _contexto(), {"tipo":"cambio_pax", "delta_personas":40, "descripcion":"vienen 40 personas mas"})
    assert r["ok"] is True
    assert r["version"] == "5.4.4"
    assert r["aplicado"] is False
    assert r["evento_original"]["personas"] == 180
    assert r["evento_simulado"]["personas"] == 220
    assert r["impacto"]["variacion_pax_pct"] > 0


def test_simula_fallo_proveedor():
    r = simular_escenario_544(_evento(), _contexto(), "que pasa si el proveedor falla")
    assert r["ok"] is True
    assert r["impacto"]["alternativas_generadas"] > 0
    assert r["evaluacion_alternativas"]["ok"] is True


def test_compara_varios_escenarios():
    r = simular_varios_escenarios_544(_evento(), _contexto(), ["que pasa si vienen +40 personas", "que pasa si falta un cocinero"])
    assert r["ok"] is True
    assert len(r["resultados"]) == 2
    assert r["aplicado"] is False


if __name__ == "__main__":
    test_simula_incremento_personas_sin_aplicar()
    test_simula_fallo_proveedor()
    test_compara_varios_escenarios()
    print("TEST OK 5.4.4 Simulador Inteligente de Escenarios")
