from pathlib import Path
import json
import sys
import tempfile

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.conector_produccion_real_556 import procesar_consulta_produccion_real_556
from SERVICIOS.produccion_automatica_evento_556f import ProduccionAutomaticaEvento556F
from SERVICIOS.planificador_diario_produccion_461 import PlanificadorDiarioProduccion461


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _snapshot_db(db: Path) -> dict[str, str]:
    salida = {}
    for p in sorted(db.rglob("*")):
        if p.is_file():
            salida[str(p.relative_to(db)).replace("\\", "/")] = p.read_text(encoding="utf-8")
    return salida


def preparar_base(stock_suficiente: bool = True, con_ficha: bool = True) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="hostai556f_"))
    db = tmp / "DATOS" / "db"
    db.mkdir(parents=True)

    _write_json(db / "eventos.json", [
        {
            "id": "EVT-BORONATX",
            "nombre": "BoronatX",
            "fecha": "2026-10-22",
            "pax": 80,
            "estado": "pendiente",
            "servicios": [
                {
                    "nombre": "Coctel bienvenida",
                    "hora_inicio": "13:00",
                    "pases": [
                        {
                            "nombre": "Entrante",
                            "recetas": ["REC-CARRILLERA"],
                        }
                    ],
                }
            ],
        }
    ])

    _write_json(db / "escandallos_canonicos.json", {
        "escandallos": [
            {
                "receta": {
                    "codigo": "REC-CARRILLERA",
                    "nombre": "Carrillera braseada",
                    "rendimiento": 10,
                    "unidad_rendimiento": "personas",
                    "ingredientes": [
                        {"nombre": "Carrillera", "articulo_id": "ART-CARRI", "cantidad": 2.0, "unidad": "kg"},
                        {"nombre": "Vino tinto", "articulo_id": "ART-VINO", "cantidad": 1.0, "unidad": "l"},
                    ],
                }
            }
        ]
    })

    _write_json(db / "articulos.json", [
        {"codigo": "ART-CARRI", "nombre": "Carrillera", "unidad": "kg", "proveedor": "Makro"},
        {"codigo": "ART-VINO", "nombre": "Vino tinto", "unidad": "l", "proveedor": "Bodegas"},
    ])

    carri = 25.0 if stock_suficiente else 4.0
    vino = 20.0 if stock_suficiente else 3.0
    _write_json(db / "stock_inicial.json", [
        {"codigo": "ART-CARRI", "articulo": "Carrillera", "unidad": "kg", "stock_actual": carri, "stock_minimo": 2.0, "proveedor": "Makro"},
        {"codigo": "ART-VINO", "articulo": "Vino tinto", "unidad": "l", "stock_actual": vino, "stock_minimo": 1.0, "proveedor": "Bodegas"},
    ])
    _write_json(db / "stock_movimientos.json", [])

    fichas = []
    if con_ficha:
        fichas = [
            {
                "id": "FPROD-0000000001",
                "receta": "Carrillera braseada",
                "rendimiento_base": 10,
                "unidad_rendimiento": "personas",
                "version": 1,
                "estado": "VALIDADA",
                "origen": "USUARIO",
                "validada_por": "jefe_cocina",
                "validada_en": "2026-07-10T10:00:00+00:00",
                "fases": [
                    {
                        "orden": 1,
                        "nombre": "Preparar mise en place",
                        "descripcion": "Pesar y preparar bases",
                        "duracion_base_min": 40,
                        "tipo_tiempo": "activo",
                        "requiere_presencia": True,
                        "escalable_por_volumen": True,
                        "recursos": ["mesa_trabajo"],
                        "puede_paralelizar": True,
                        "punto_control": "Mise en place lista",
                    },
                    {
                        "orden": 2,
                        "nombre": "Brasear",
                        "descripcion": "Coccion lenta",
                        "duracion_base_min": 120,
                        "tipo_tiempo": "pasivo",
                        "requiere_presencia": False,
                        "escalable_por_volumen": False,
                        "recursos": ["horno"],
                        "puede_paralelizar": False,
                        "punto_control": "Textura correcta",
                    },
                ],
                "observaciones": "",
            }
        ]

    _write_json(db / "fichas_produccion_reales.json", {
        "version_modelo": "5.5.6E.3.1",
        "actualizado_en": "2026-07-10T10:00:00+00:00",
        "fichas": fichas,
    })
    return tmp


def main():
    base_ok = preparar_base(stock_suficiente=True, con_ficha=True)
    db_ok = base_ok / "DATOS" / "db"
    snapshot_antes = _snapshot_db(db_ok)
    assert not (base_ok / "DATOS" / "produccion").exists()

    planificador_ro = PlanificadorDiarioProduccion461(base_ok, create_output_dir=False)
    assert not (base_ok / "DATOS" / "produccion").exists()
    plan_ro = planificador_ro.planificar_dia([])
    assert plan_ro["total_elaboraciones"] == 0
    assert not (base_ok / "DATOS" / "produccion").exists()

    motor = ProduccionAutomaticaEvento556F(base_ok)
    r1 = motor.planificar_evento("BoronatX", cocineros=3)
    assert r1["ok"] is True, r1
    assert r1["estado"] == "PLAN_PRELIMINAR_OK", r1
    assert r1["datos_reales_modificados"] is False
    assert r1["compras_propuestas"] == []
    assert r1["plan_diario"]["total_elaboraciones"] >= 1
    assert not (base_ok / "DATOS" / "produccion").exists()
    assert _snapshot_db(db_ok) == snapshot_antes

    r1b = motor.planificar_evento("EVT-BORONATX", cocineros=3)
    assert r1b["id_plan_automatico"] == r1["id_plan_automatico"]
    assert _snapshot_db(db_ok) == snapshot_antes

    base_sin_ficha = preparar_base(stock_suficiente=True, con_ficha=False)
    r2 = ProduccionAutomaticaEvento556F(base_sin_ficha).planificar_evento("BoronatX", cocineros=2)
    assert r2["ok"] is False, r2
    assert any(b.get("tipo") == "FALTA_FICHA_PRODUCCION" for b in r2.get("bloqueos", [])), r2

    base_stock_bajo = preparar_base(stock_suficiente=False, con_ficha=True)
    r3 = ProduccionAutomaticaEvento556F(base_stock_bajo).planificar_evento("BoronatX", cocineros=2)
    assert r3["ok"] is False, r3
    assert len(r3.get("compras_propuestas", [])) >= 1, r3
    assert any(b.get("tipo") == "BLOQUEO_STOCK" for b in r3.get("bloqueos", [])), r3

    rr = procesar_consulta_produccion_real_556(
        "Planifica la produccion automatica del evento BoronatX con 3 cocineros",
        base_ok,
    )
    assert rr["gestionado"] is True, rr
    assert rr["intencion"] == "planificar_produccion_automatica_evento", rr
    assert rr["datos"]["evento"]["nombre"] == "BoronatX", rr
    assert rr["datos"]["datos_reales_modificados"] is False, rr
    assert _snapshot_db(db_ok) == snapshot_antes

    planificador_rw = PlanificadorDiarioProduccion461(base_ok)
    assert (base_ok / "DATOS" / "produccion").exists()
    exportado = planificador_rw.exportar_plan({"version": "test"}, nombre="plan_rw_test.json")
    assert Path(exportado["archivo"]).exists()

    print("TEST OK 5.5.6F Producción Automática por Evento")


if __name__ == "__main__":
    main()