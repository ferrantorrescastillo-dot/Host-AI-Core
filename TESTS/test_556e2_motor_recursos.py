from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from SERVICIOS.motor_recursos_produccion_556e2 import MotorRecursosProduccion556E2

def preparar(base:Path)->None:
    db=base/'DATOS'/'db'; cfg=base/'DATOS'/'config'; db.mkdir(parents=True); cfg.mkdir(parents=True)
    (db/'articulos.json').write_text(json.dumps([{"codigo":"A1","nombre":"Patata","precio":2}]),encoding='utf-8')
    (db/'escandallos_canonicos.json').write_text(json.dumps({"escandallos":[{"receta":{"codigo":"R1","nombre":"Ensaladilla","rendimiento":4,"unidad_rendimiento":"u","ingredientes":[{"nombre":"Patata","articulo_id":"A1","cantidad":1.2,"unidad":"kg"}]}}]}),encoding='utf-8')
    (db/'stock_inicial.json').write_text(json.dumps([{"codigo":"A1","articulo":"Patata","unidad":"kg","stock_actual":100}]),encoding='utf-8')
    (db/'stock_movimientos.json').write_text('[]',encoding='utf-8')
    (cfg/'tiempos_produccion_556e1.json').write_text(json.dumps({"redondeo_min":5,"perfiles":{}}),encoding='utf-8')
    (cfg/'recursos_cocina_556e2.json').write_text(json.dumps({"recursos":{"mesa_trabajo":1,"bascula":1,"fogones":1,"abatidor":1,"camara_fria":1,"envasadora":1,"impresora_etiquetas":1}}),encoding='utf-8')

def main()->None:
    with tempfile.TemporaryDirectory() as tmp:
        base=Path(tmp); preparar(base)
        m=MotorRecursosProduccion556E2(base); r=m.analizar('ensaladilla',100,'personas')
        assert r['fases'] and r['datos_reales_modificados'] is False
        c=m.detectar_conflictos([{"receta":"ensaladilla","objetivo":100,"inicio_min":0},{"receta":"ensaladilla","objetivo":100,"inicio_min":0}])
        assert c['conflictos'] and c['estado']=='CONFLICTOS_DETECTADOS'
    print('TEST OK 5.5.6E.2 - Recursos y conflictos de producción')
if __name__=='__main__': main()
