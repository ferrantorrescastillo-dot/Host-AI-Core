from pathlib import Path
import json
import sys
import tempfile

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.conector_produccion_real_556 import procesar_consulta_produccion_real_556
from SERVICIOS.produccion_automatica_evento_556f import ProduccionAutomaticaEvento556F


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path):
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def preparar_base(stock_suficiente: bool = False) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="hostai556f_comp_"))
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
                    "pases": [{"nombre": "Entrante", "recetas": ["REC-CARRILLERA"]}],
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

    _write_json(db / "fichas_produccion_reales.json", {
        "version_modelo": "5.5.6E.3.1",
        "actualizado_en": "2026-07-10T10:00:00+00:00",
        "fichas": [
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
                    }
                ],
                "observaciones": "",
            }
        ],
    })
    return tmp


def main():
    base = preparar_base(stock_suficiente=False)
    db = base / "DATOS" / "db"

    motor = ProduccionAutomaticaEvento556F(base)
    r1 = motor.planificar_evento(
        "BoronatX",
        cocineros=2,
        integrar_con_compras=True,
        generar_pedidos_sugeridos=False,
    )
    assert r1["ok"] is False, r1
    assert r1["integracion_compras"]["activada"] is True, r1
    assert r1["integracion_compras"]["necesidades_creadas"] >= 1, r1
    assert r1["integracion_compras"]["pedidos_sugeridos"]["total_pedidos_nuevos"] == 0, r1
    assert r1["datos_reales_modificados"] is True, r1

    necesidades_1 = _read_json(db / "compras_necesidades.json")
    assert len(necesidades_1) >= 1

    r2 = motor.planificar_evento(
        "BoronatX",
        cocineros=2,
        integrar_con_compras=True,
        generar_pedidos_sugeridos=False,
    )
    necesidades_2 = _read_json(db / "compras_necesidades.json")
    assert len(necesidades_2) == len(necesidades_1), r2
    assert r2["integracion_compras"]["necesidades_creadas"] == 0, r2
    assert r2["integracion_compras"]["necesidades_actualizadas"] >= 1, r2

    r3 = procesar_consulta_produccion_real_556(
        "Planifica la produccion automatica del evento BoronatX con 2 cocineros e integrar compras y generar pedidos sugeridos",
        base,
    )
    assert r3["gestionado"] is True, r3
    assert r3["datos"]["integracion_compras"]["activada"] is True, r3
    assert r3["datos"]["integracion_compras"]["pedidos_sugeridos"]["total_pedidos_nuevos"] >= 1, r3

    pedidos = _read_json(db / "compras_pedidos.json")
    assert len(pedidos) >= 1
    assert all((p.get("estado") or "").lower() == "borrador" for p in pedidos), pedidos

    print("TEST OK 5.5.6F Integracion Produccion-Compras")


if __name__ == "__main__":
    main()
