from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from SERVICIOS.motor_tiempos_produccion_556e1 import MotorTiemposProduccion556E1

def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base=Path(tmp); db=base/'DATOS'/'db'; cfg=base/'DATOS'/'config'; db.mkdir(parents=True); cfg.mkdir(parents=True)
        (db/'articulos.json').write_text(json.dumps([{"codigo":"A1","nombre":"Patata","precio":2}]),encoding='utf-8')
        (db/'escandallos_canonicos.json').write_text(json.dumps({"escandallos":[{"receta":{"codigo":"R1","nombre":"Ensaladilla","rendimiento":4,"unidad_rendimiento":"u","ingredientes":[{"nombre":"Patata","articulo_id":"A1","cantidad":1.2,"unidad":"kg"}]}}]}),encoding='utf-8')
        (db/'stock_inicial.json').write_text(json.dumps([{"codigo":"A1","articulo":"Patata","unidad":"kg","stock_actual":100}]),encoding='utf-8')
        (db/'stock_movimientos.json').write_text('[]',encoding='utf-8')
        (cfg/'tiempos_produccion_556e1.json').write_text(json.dumps({"redondeo_min":5,"perfiles":{}}),encoding='utf-8')
        r=MotorTiemposProduccion556E1(base).estimar('ensaladilla',100,'personas')
        assert r['minutos_activos'] > 0 and r['minutos_pasivos'] > 0
        assert r['datos_reales_modificados'] is False and len(r['fases']) >= 6
    print('TEST OK 5.5.6E.1 - Motor de tiempos de producción')
if __name__=='__main__': main()
