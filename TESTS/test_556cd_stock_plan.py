from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from SERVICIOS.cruce_stock_produccion_556c import CruceStockProduccion556C
from SERVICIOS.planificador_produccion_556d import PlanificadorProduccion556D
from SERVICIOS.conector_produccion_real_556 import procesar_consulta_produccion_real_556

def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp); db = base/"DATOS"/"db"; db.mkdir(parents=True)
        (db/"articulos.json").write_text(json.dumps([
            {"codigo":"A-PAT","nombre":"Patata","precio":2.0}, {"codigo":"A-MAY","nombre":"Mayonesa","precio":4.0}
        ]), encoding="utf-8")
        (db/"escandallos_canonicos.json").write_text(json.dumps({"escandallos":[{"receta":{"codigo":"R-ENS","nombre":"Ensaladilla","rendimiento":4,"unidad_rendimiento":"u","ingredientes":[
            {"nombre":"Patata","articulo_id":"A-PAT","cantidad":1.2,"unidad":"kg"}, {"nombre":"Mayonesa","articulo_id":"A-MAY","cantidad":0.2,"unidad":"kg"}
        ]}}]}), encoding="utf-8")
        (db/"stock_inicial.json").write_text(json.dumps([
            {"codigo":"A-PAT","articulo":"Patata","unidad":"kg","stock_actual":40,"stock_minimo":5},
            {"codigo":"A-MAY","articulo":"Mayonesa","unidad":"kg","stock_actual":2,"stock_minimo":1}
        ]), encoding="utf-8")
        (db/"stock_movimientos.json").write_text("[]", encoding="utf-8")
        c = CruceStockProduccion556C(base).cruzar("ensaladilla", 100, "personas")
        by = {x["nombre"]: x for x in c["lineas"]}
        assert by["Patata"]["requerido"] == 30.0 and by["Patata"]["faltante"] == 0.0
        assert by["Mayonesa"]["requerido"] == 5.0 and by["Mayonesa"]["faltante"] == 3.0
        assert c["produccion_viable"] is False
        d = PlanificadorProduccion556D(base).generar("ensaladilla", 100, "personas")
        assert d["estado"] == "BLOQUEADO_POR_FALTANTES"
        assert len(d["tareas"]) >= 6
        r = procesar_consulta_produccion_real_556("Prepara el plan de producción de ensaladilla para 100 personas", base)
        assert r["gestionado"] and "PLAN PRELIMINAR" in r["mensaje"]
    print("TEST OK 5.5.6CD - Cruce con stock y plan real de producción")
if __name__ == "__main__": main()
