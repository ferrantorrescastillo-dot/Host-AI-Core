from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from SERVICIOS.bandeja_trabajo_piloto_11 import BandejaTrabajoPiloto11
from SERVICIOS.jornada_piloto_12 import JornadaPiloto12


def _write(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _preparar_entorno(tmp_path: Path):
    db = tmp_path / "DATOS" / "db"
    _write(
        db / "eventos.json",
        [
            {
                "id": "EVT-HOY-1",
                "nombre": "Boda RP1",
                "fecha": "2026-07-15",
                "hora_inicio": "13:00",
                "pax": 120,
                "estado": "confirmado",
                "observaciones": "Revisar alérgenos frutos secos",
            }
        ],
    )
    _write(
        db / "planes_produccion.json",
        [
            {
                "id": "PLAN-1",
                "evento_id": "EVT-HOY-1",
                "evento": "Boda RP1",
                "tareas": [
                    {
                        "id": "TAREA-PROD-1",
                        "titulo": "Preparar carrillera",
                        "prioridad": 90,
                        "estado_ejecucion": "pendiente",
                        "bloqueo": "",
                        "fases": [
                            {"nombre": "Mise en place", "duracion_min": 30, "tipo": "preparacion", "dependencia": ""},
                            {"nombre": "Descongelar", "duracion_min": 120, "tipo": "descongelacion", "dependencia": ""},
                            {"nombre": "Reposo", "duracion_min": 45, "tipo": "reposo", "dependencia": "FASE-ANT"},
                            {"nombre": "Abatir", "duracion_min": 35, "tipo": "abatido", "dependencia": ""},
                        ],
                    },
                    {
                        "id": "TAREA-PROD-2",
                        "titulo": "Preparar demi-glace",
                        "prioridad": 80,
                        "estado_ejecucion": "pendiente",
                        "bloqueo": "Stock insuficiente",
                        "fases": [
                            {"nombre": "Base", "duracion_min": 30, "tipo": "preparacion", "dependencia": ""}
                        ],
                    },
                ],
            }
        ],
    )
    _write(
        db / "compras_pedidos.json",
        [
            {
                "id": "PED-1",
                "proveedor": "Makro",
                "estado": "preparado",
                "lineas": [{"nombre": "Arroz bomba", "cantidad": 15, "unidad": "kg"}],
                "total_lineas": 1,
                "creado_en": "2026-07-15T07:00:00",
                "enviado_en": "2026-07-15T07:15:00",
            }
        ],
    )
    _write(
        db / "menus.json",
        [
            {
                "menu_id": "MENU-1",
                "nombre": "Menú RP1",
                "estado": "ACTIVO",
                "platos": [{"plato_id": "PL-1", "nombre": "Carrillera", "componentes": []}],
                "economico": {"precio_venta": 48.0, "coste_total": 21.5, "food_cost_pct": 44.8},
            }
        ],
    )
    _write(
        db / "stock_inicial.json",
        [
            {"articulo": "Arroz bomba", "stock_actual": 3.0, "stock_minimo": 10.0, "unidad": "kg"},
            {"articulo": "Fondo oscuro", "stock_actual": 0.0, "stock_minimo": 2.0, "unidad": "L"},
        ],
    )
    _write(
        db / "articulos.json",
        [
            {"codigo": "ART-1", "nombre": "Harina", "alergenos": "gluten"},
            {"codigo": "ART-2", "nombre": "Almendra", "alergenos": "frutos secos"},
        ],
    )



def test_rp1_briefing_contiene_todas_las_secciones(tmp_path: Path):
    _preparar_entorno(tmp_path)
    bandeja = BandejaTrabajoPiloto11(tmp_path)
    resultado = JornadaPiloto12(tmp_path, bandeja=bandeja).construir(datetime(2026, 7, 15, 8, 0))
    briefing = resultado["briefing_apertura"]

    assert resultado["solo_lectura"] is True
    assert briefing["solo_lectura"] is True
    assert briefing["pregunta"].startswith("¿Qué tiene que hacer")
    assert briefing["mensaje_operativo"]
    assert isinstance(briefing["eventos_hoy"], list)
    assert isinstance(briefing["cronologia"], list)
    assert isinstance(briefing["produccion_priorizada"], list)
    assert isinstance(briefing["compras_criticas"], list)
    assert isinstance(briefing["recepciones_previstas"], list)
    assert isinstance(briefing["productos_descongelar"], list)
    assert isinstance(briefing["alertas"], list)
    assert isinstance(briefing["personal"], list)
    assert isinstance(briefing["alergenos"], dict)
    assert isinstance(briefing["incidencias"], list)
    assert isinstance(briefing["prioridades"], list)



def test_rp1_prioridades_ordenadas_por_score_operativo(tmp_path: Path):
    _preparar_entorno(tmp_path)
    resultado = JornadaPiloto12(tmp_path).construir(datetime(2026, 7, 15, 8, 0))
    prioridades = resultado["briefing_apertura"]["prioridades"]
    assert len(prioridades) >= 2
    assert all(
        prioridades[i]["orden_score"] >= prioridades[i + 1]["orden_score"]
        for i in range(len(prioridades) - 1)
    )



def test_rp1_detecta_descongelacion_y_alertas_alergenos(tmp_path: Path):
    _preparar_entorno(tmp_path)
    resultado = JornadaPiloto12(tmp_path).construir(datetime(2026, 7, 15, 8, 0))
    briefing = resultado["briefing_apertura"]

    assert briefing["productos_descongelar"]
    assert briefing["productos_descongelar"][0]["minutos_descongelacion"] >= 120
    assert briefing["alergenos"]["estado"] == "revisar"
    assert briefing["alergenos"]["pendientes_revision_evento"]



def test_rp1_compra_critica_y_recepcion_prevista_generan_incidencias(tmp_path: Path):
    _preparar_entorno(tmp_path)
    resultado = JornadaPiloto12(tmp_path).construir(datetime(2026, 7, 15, 8, 0))
    briefing = resultado["briefing_apertura"]

    assert briefing["compras_criticas"]
    assert briefing["recepciones_previstas"]
    assert briefing["incidencias"]
