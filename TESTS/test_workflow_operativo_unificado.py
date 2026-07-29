from __future__ import annotations

import json
import inspect
from pathlib import Path

from SERVICIOS.confirmaciones_inteligentes_5412 import aplicar_confirmacion_en_flujo_5412
from SERVICIOS.consultas_datos_conversacionales_552 import procesar_consulta_datos_552
from SERVICIOS.continuador_flujo_5411 import seleccionar_accion_en_flujo_5411
from SERVICIOS.ejecutor_flujo_operativo_532 import ejecutar_flujo_operativo
from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.host_ai_executive import HostAIExecutive
from SERVICIOS.modelo_flujo_operativo import (
    cancelar_flujo,
    cargar_flujo_json,
    crear_flujo,
    crear_paso,
    guardar_flujo_json,
    registrar_confirmacion,
    registrar_resultado,
    seleccionar_paso,
)
from SERVICIOS.orquestador_flujo_operativo import OrquestadorFlujoOperativo
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52


DATOS_EVENTO = {
    "tipo": "boda",
    "personas": 180,
    "fecha": "sabado",
    "hora_servicio": "15:00",
    "menu": "menu boda",
    "lugar": "Mas Boronat",
    "restricciones": "sin restricciones",
    "objetivo": "flujo completo",
}


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _crear_flujo_base() -> dict:
    pasos = [
        crear_paso(1, "EVENTO_CREAR", "Crear o localizar evento", "4.7.1", "crear_evento", True, True),
        crear_paso(2, "STOCK_REVISAR", "Consultar stock disponible", "4.3", "consultar_stock", False, False),
    ]
    return crear_flujo("evento", pasos, datos=DATOS_EVENTO, origen="test")


def _id_paso_por_codigo(flujo: dict, codigo: str) -> str:
    for paso in flujo.get("pasos", []):
        if paso.get("codigo") == codigo:
            return str(paso.get("id_paso"))
    raise AssertionError(f"No existe paso para {codigo}")


def _seed_produccion_inteligente_base(
    tmp_path: Path,
    *,
    incluir_fantasma: bool = False,
    stock_bajo: bool = False,
    postre_sin_tiempos: bool = False,
    plan_parcial: bool = False,
) -> Path:
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True, exist_ok=True)

    evento = {
        "id": "EVT-BORONATX",
        "nombre": "BoronatX",
        "fecha": "2026-10-22",
        "pax": 80,
        "estado": "pendiente",
        "servicios": [
            {
                "nombre": "Comida",
                "hora_inicio": "12:30",
                "pases": [
                    {"nombre": "Entrante", "recetas": ["REC-CARRI", "REC-SALSA"]},
                ],
            },
            {
                "nombre": "Cena",
                "hora_inicio": "18:00",
                "pases": [
                    {"nombre": "Postre", "recetas": (["REC-POSTRE", "REC-FANTASMA"] if incluir_fantasma else ["REC-POSTRE"])},
                ],
            },
        ],
    }

    _write_json(db / "eventos.json", [evento])
    _write_json(
        db / "escandallos_canonicos.json",
        {
            "escandallos": [
                {
                    "receta": {
                        "codigo": "REC-CARRI",
                        "nombre": "Carrillera braseada",
                        "rendimiento": 10,
                        "unidad_rendimiento": "personas",
                        "ingredientes": [
                            {"nombre": "Carrillera", "articulo_id": "ART-CARRI", "cantidad": 2.0, "unidad": "kg"},
                        ],
                    }
                },
                {
                    "receta": {
                        "codigo": "REC-SALSA",
                        "nombre": "Salsa reducción",
                        "rendimiento": 10,
                        "unidad_rendimiento": "personas",
                        "ingredientes": [
                            {"nombre": "Vino tinto", "articulo_id": "ART-VINO", "cantidad": 1.0, "unidad": "l"},
                        ],
                    }
                },
                {
                    "receta": {
                        "codigo": "REC-POSTRE",
                        "nombre": "Postre crema",
                        "rendimiento": 10,
                        "unidad_rendimiento": "personas",
                        "ingredientes": [
                            {"nombre": "Nata", "articulo_id": "ART-NATA", "cantidad": 0.5, "unidad": "l"},
                        ],
                    }
                },
            ]
        },
    )
    _write_json(
        db / "fichas_produccion_reales.json",
        {
            "version_modelo": "5.5.6E.3.1",
            "actualizado_en": "2026-07-10T10:00:00+00:00",
            "fichas": [
                {
                    "id": "FPROD-CARRI",
                    "receta": "Carrillera braseada",
                    "rendimiento_base": 10,
                    "unidad_rendimiento": "personas",
                    "version": 1,
                    "estado": "VALIDADA",
                    "fases": [
                        {"orden": 1, "nombre": "Preparar mise en place", "duracion_base_min": 45, "tipo_tiempo": "activo", "requiere_presencia": True, "escalable_por_volumen": True, "recursos": ["mesa_trabajo"], "puede_paralelizar": True},
                        {"orden": 2, "nombre": "Brasear", "duracion_base_min": 120, "tipo_tiempo": "pasivo", "requiere_presencia": False, "escalable_por_volumen": False, "recursos": ["horno"], "puede_paralelizar": False},
                    ],
                },
                {
                    "id": "FPROD-SALSA",
                    "receta": "Salsa reducción",
                    "rendimiento_base": 10,
                    "unidad_rendimiento": "personas",
                    "version": 1,
                    "estado": "VALIDADA",
                    "fases": [
                        {"orden": 1, "nombre": "Reducir", "duracion_base_min": 30, "tipo_tiempo": "activo", "requiere_presencia": True, "escalable_por_volumen": True, "recursos": ["fuego"], "puede_paralelizar": False, "dependencia": "Carrillera braseada"},
                    ],
                },
                {
                    "id": "FPROD-POSTRE",
                    "receta": "Postre crema",
                    "rendimiento_base": 10,
                    "unidad_rendimiento": "personas",
                    "version": 1,
                    "estado": "VALIDADA",
                    "fases": ([] if postre_sin_tiempos else [
                        {"orden": 1, "nombre": "Montar", "duracion_base_min": 20, "tipo_tiempo": "activo", "requiere_presencia": True, "escalable_por_volumen": True, "recursos": ["mesa_trabajo"], "puede_paralelizar": True},
                    ]),
                },
            ],
        },
    )
    articulos = [
        {"codigo": "ART-CARRI", "nombre": "Carrillera", "unidad": "kg", "proveedor": "Makro"},
        {"codigo": "ART-VINO", "nombre": "Vino tinto", "unidad": "l", "proveedor": "Bodegas"},
        {"codigo": "ART-NATA", "nombre": "Nata", "unidad": "l", "proveedor": "Dairy"},
    ]
    _write_json(db / "articulos.json", articulos)
    _write_json(
        db / "stock_inicial.json",
        [
            {"codigo": "ART-CARRI", "articulo": "Carrillera", "unidad": "kg", "stock_actual": 4.0 if stock_bajo else 25.0, "stock_minimo": 2.0, "proveedor": "Makro"},
            {"codigo": "ART-VINO", "articulo": "Vino tinto", "unidad": "l", "stock_actual": 3.0 if stock_bajo else 15.0, "stock_minimo": 1.0, "proveedor": "Bodegas"},
            {"codigo": "ART-NATA", "articulo": "Nata", "unidad": "l", "stock_actual": 0.5 if stock_bajo else 8.0, "stock_minimo": 1.0, "proveedor": "Dairy"},
        ],
    )
    _write_json(db / "stock_movimientos.json", [])

    if plan_parcial:
        _write_json(
            db / "planes_produccion.json",
            [
                {
                    "id": "PLAN-LEGACY-PARCIAL",
                    "evento_id": "EVT-BORONATX",
                    "evento": "BoronatX",
                    "fecha": "2026-10-22",
                    "estado": "en_produccion",
                    "tareas": [
                        {
                            "id": "T1",
                            "titulo": "Carrillera braseada",
                            "receta": "Carrillera braseada",
                            "estado_ejecucion": "en_proceso",
                            "fases": [
                                {"id": "F1", "nombre": "Preparar mise en place", "duracion_min": 45, "tipo": "activo", "recurso": "mesa_trabajo", "responsable": "cocina"}
                            ],
                        }
                    ],
                    "cronograma": [],
                    "avisos": [],
                }
            ],
        )

    return tmp_path


def test_crear_flujo() -> None:
    flujo = _crear_flujo_base()
    assert str(flujo.get("id_flujo", "")).startswith("flujo-")
    assert flujo.get("estado") == "creado"
    assert all(p.get("estado") == "pendiente" for p in flujo.get("pasos", []))
    historial = list(flujo.get("historial") or [])
    assert historial
    assert historial[0].get("evento") == "flujo_creado"


def test_seleccionar_paso_con_confirmacion() -> None:
    flujo = _crear_flujo_base()
    r = seleccionar_paso(flujo, "EVENTO_CREAR", origen="test")
    assert r.get("ok") is True
    paso = r.get("paso") or {}
    assert paso.get("estado") == "esperando_confirmacion"
    assert (r.get("flujo") or {}).get("estado") == "esperando_confirmacion"


def test_confirmar_paso() -> None:
    flujo = _crear_flujo_base()
    flujo = (seleccionar_paso(flujo, "EVENTO_CREAR").get("flujo") or flujo)
    r = registrar_confirmacion(flujo, "EVENTO_CREAR", True, origen="test", valor="si")
    assert r.get("ok") is True
    paso = r.get("paso") or {}
    assert paso.get("estado") == "confirmado"
    assert (paso.get("confirmacion") or {}).get("estado") == "confirmada"
    eventos = [h.get("evento") for h in (r.get("flujo") or {}).get("historial", [])]
    assert "paso_confirmacion_registrada" in eventos


def test_rechazar_paso() -> None:
    flujo = _crear_flujo_base()
    flujo = (seleccionar_paso(flujo, "EVENTO_CREAR").get("flujo") or flujo)
    r = registrar_confirmacion(flujo, "EVENTO_CREAR", False, origen="test", valor="no")
    assert r.get("ok") is True
    paso = r.get("paso") or {}
    assert paso.get("estado") == "rechazado"
    assert (paso.get("confirmacion") or {}).get("estado") == "rechazada"
    assert (r.get("flujo") or {}).get("estado") == "esperando_seleccion"


def test_impedir_ejecucion_sin_confirmacion() -> None:
    flujo = _crear_flujo_base()
    flujo = (seleccionar_paso(flujo, "EVENTO_CREAR").get("flujo") or flujo)
    r = ejecutar_flujo_operativo(flujo, confirmar=False, codigo_paso="EVENTO_CREAR")
    assert r.get("ok") is False
    assert r.get("estado") == "confirmacion_requerida"
    assert r.get("modifico_datos_reales") is False


def test_ejecucion_segura() -> None:
    flujo = _crear_flujo_base()
    flujo = (seleccionar_paso(flujo, "EVENTO_CREAR").get("flujo") or flujo)
    flujo = (registrar_confirmacion(flujo, "EVENTO_CREAR", True).get("flujo") or flujo)
    r = ejecutar_flujo_operativo(flujo, confirmar=True, codigo_paso="EVENTO_CREAR")
    assert r.get("ok") is True
    paso = r.get("paso") or {}
    assert paso.get("estado") == "preparado_modo_seguro"
    assert (paso.get("resultado") or {}).get("datos_reales_modificados") is False
    assert r.get("modifico_datos_reales") is False


def test_completar_flujo() -> None:
    flujo = _crear_flujo_base()
    id1 = _id_paso_por_codigo(flujo, "EVENTO_CREAR")
    id2 = _id_paso_por_codigo(flujo, "STOCK_REVISAR")
    flujo = (registrar_resultado(flujo, id1, {"modo": "seguro", "datos_reales_modificados": False}).get("flujo") or flujo)
    flujo = (registrar_resultado(flujo, id2, {"modo": "seguro", "datos_reales_modificados": False}).get("flujo") or flujo)
    assert flujo.get("estado") == "completado"
    assert flujo.get("fecha_finalizacion")


def test_cancelar_flujo() -> None:
    flujo = _crear_flujo_base()
    r = cancelar_flujo(flujo, motivo="test", origen="pytest")
    assert r.get("ok") is True
    flujo_c = r.get("flujo") or {}
    assert flujo_c.get("estado") == "cancelado"
    assert all(p.get("estado") in {"cancelado", "completado", "preparado_modo_seguro", "rechazado"} for p in flujo_c.get("pasos", []))


def test_persistir_y_reanudar(tmp_path: Path) -> None:
    flujo = _crear_flujo_base()
    guardado = guardar_flujo_json(flujo, base_dir=tmp_path)
    assert guardado.get("ok") is True
    ruta = Path(str(guardado.get("ruta")))
    cargado = cargar_flujo_json(ruta)
    assert cargado.get("ok") is True
    flujo_c = cargado.get("flujo") or {}
    assert flujo_c.get("id_flujo") == flujo.get("id_flujo")
    assert flujo_c.get("estado") == flujo.get("estado")
    assert flujo_c.get("historial") == flujo.get("historial")


def test_integracion_531_5411_5412_532() -> None:
    generado = generar_flujo_operativo_evento(DATOS_EVENTO)
    assert generado.get("ok") is True
    flujo = generado.get("flujo") or {}

    seleccion = seleccionar_accion_en_flujo_5411("1", flujo)
    assert seleccion.get("ok") is True
    flujo = seleccion.get("flujo") or flujo

    confirmacion = aplicar_confirmacion_en_flujo_5412("sí, adelante", flujo)
    assert confirmacion.get("ok") is True
    flujo = confirmacion.get("flujo") or flujo

    paso = confirmacion.get("paso") or {}
    codigo = str(paso.get("codigo") or "")
    if not codigo:
        codigo = str(((flujo.get("accion_seleccionada") or {}).get("codigo") or ""))
    ejecucion = ejecutar_flujo_operativo(flujo, confirmar=True, codigo_paso=codigo)
    assert ejecucion.get("ok") is True
    assert ejecucion.get("modifico_datos_reales") is False
    paso_e = ejecucion.get("paso") or {}
    assert (paso_e.get("resultado") or {}).get("datos_reales_modificados") is False

    eventos = [h.get("evento") for h in (ejecucion.get("flujo") or {}).get("historial", [])]
    assert "paso_seleccionado" in eventos
    assert "paso_confirmacion_registrada" in eventos
    assert "paso_resultado_registrado" in eventos


def test_compatibilidad_respuesta_531() -> None:
    r = generar_flujo_operativo_evento(DATOS_EVENTO)
    assert "ok" in r
    assert "estado" in r
    assert "datos" in r
    assert "pasos" in r


def test_consulta_datos_no_crea_flujo(tmp_path: Path) -> None:
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True, exist_ok=True)
    (db / "escandallos.json").write_text(json.dumps([{"nombre": "Paella"}]), encoding="utf-8")
    (db / "articulos.json").write_text("[]", encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")

    r = procesar_consulta_datos_552("¿Qué recetas tienes registradas?", tmp_path)
    assert r.get("gestionado") is True
    assert r.get("pasos") == []
    assert "flujo" not in r


def test_orquestador_flujo_reanuda_y_ejecuta(tmp_path: Path) -> None:
    orch = OrquestadorFlujoOperativo(tmp_path)
    inicio = orch.iniciar_flujo_operativo(DATOS_EVENTO)
    assert inicio.get("ok") is True
    flujo = inicio.get("flujo") or {}

    saved = orch.repo.guardar(flujo)
    assert saved.get("ok") is True
    reanudado = orch.reanudar_flujo_desde_archivo(ruta=Path(str(saved.get("ruta"))))
    assert reanudado.get("ok") is True

    flujo_r = reanudado.get("flujo") or {}
    sel = orch.seleccionar_accion_en_flujo("1", flujo_r)
    assert sel.get("ok") is True


def test_compras_preparar_genera_propuesta_integrada_en_modo_seguro(tmp_path: Path) -> None:
    db = tmp_path / "DATOS" / "db"
    _write_json(
        db / "eventos.json",
        [
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
        ],
    )
    _write_json(
        db / "escandallos_canonicos.json",
        {
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
        },
    )
    _write_json(
        db / "fichas_produccion_reales.json",
        {
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
        },
    )
    _write_json(db / "articulos.json", [{"codigo": "ART-CARRI", "nombre": "Carrillera", "unidad": "kg"}, {"codigo": "ART-VINO", "nombre": "Vino tinto", "unidad": "l"}])
    _write_json(
        db / "menus.json",
        [
            {
                "nombre": "menu boda",
                "platos": [
                    {
                        "nombre": "Carrillera",
                        "ingredientes": [
                            {"articulo": "Carrillera", "unidad": "kg", "cantidad_persona": 0.25, "proveedor": "Makro"},
                            {"articulo": "Vino tinto", "unidad": "l", "cantidad_persona": 0.08, "proveedor": "Bodegas"},
                        ],
                    }
                ],
            }
        ],
    )
    _write_json(
        db / "stock_inicial.json",
        [
            {"codigo": "ART-CARRI", "articulo": "Carrillera", "unidad": "kg", "stock_actual": 4.0, "stock_minimo": 2.0, "proveedor": "Makro"},
            {"codigo": "ART-VINO", "articulo": "Vino tinto", "unidad": "l", "stock_actual": 3.0, "stock_minimo": 1.0, "proveedor": "Bodegas"},
        ],
    )
    _write_json(db / "stock_movimientos.json", [])

    before_stock = (db / "stock_inicial.json").read_text(encoding="utf-8")
    before_mov = (db / "stock_movimientos.json").read_text(encoding="utf-8")

    generado = generar_flujo_operativo_evento(
        {
            "tipo": "boda",
            "personas": 80,
            "fecha": "2026-10-22",
            "hora_servicio": "15:00",
            "menu": "menu boda",
            "lugar": "Mas Boronat",
            "restricciones": "sin restricciones",
            "objetivo": "flujo completo",
        }
    )
    flujo = generado.get("flujo") or {}
    flujo = (seleccionar_paso(flujo, "COMPRAS_PREPARAR").get("flujo") or flujo)
    flujo = (registrar_confirmacion(flujo, "COMPRAS_PREPARAR", True).get("flujo") or flujo)

    ejecucion = ejecutar_flujo_operativo(
        flujo,
        confirmar=True,
        codigo_paso="COMPRAS_PREPARAR",
        contexto={"base_dir": str(tmp_path)},
    )

    assert ejecucion.get("ok") is True
    assert ejecucion.get("modifico_datos_reales") is False
    detalle = (((ejecucion.get("paso") or {}).get("resultado") or {}).get("detalle") or {})
    propuesta = detalle.get("propuesta_compra_integrada") or {}
    assert propuesta.get("modo_seguro") is True
    assert propuesta.get("datos_reales_modificados") is False
    assert propuesta.get("no_crear_pedidos_reales") is True
    assert propuesta.get("no_modificar_stock") is True
    assert propuesta.get("no_modificar_proveedores") is True
    assert propuesta.get("no_modificar_produccion") is True
    assert propuesta.get("no_escribir_movimientos_reales") is True
    assert propuesta.get("total_lineas_propuesta", 0) >= 1

    assert (db / "stock_inicial.json").read_text(encoding="utf-8") == before_stock
    assert (db / "stock_movimientos.json").read_text(encoding="utf-8") == before_mov
    assert not (db / "compras_pedidos.json").exists()


def test_equivalencia_ruta_directa_vs_orquestador_52_en_confirmar_todo(tmp_path: Path) -> None:
    evento_52 = {
        "evento": {
            "tipo": DATOS_EVENTO["tipo"],
            "personas": DATOS_EVENTO["personas"],
            "fecha": DATOS_EVENTO["fecha"],
            "hora_servicio": DATOS_EVENTO["hora_servicio"],
            "menu": DATOS_EVENTO["menu"],
            "lugar": DATOS_EVENTO["lugar"],
            "restricciones": DATOS_EVENTO["restricciones"],
            "objetivo": DATOS_EVENTO["objetivo"],
        }
    }

    orch_directo = OrquestadorFlujoOperativo(tmp_path)
    inicio_directo = orch_directo.iniciar_flujo_operativo(DATOS_EVENTO)
    assert inicio_directo.get("ok") is True
    flujo_directo = inicio_directo.get("flujo") or {}

    orch_52 = OrquestadorInteligente52(tmp_path)
    preparado_52 = orch_52._procesar_evento_completo(evento_52)
    assert preparado_52.get("ok") is True
    flujo_52 = (preparado_52.get("datos") or {}).get("flujo") or {}

    codigos_directo = [str(p.get("codigo") or "") for p in (flujo_directo.get("pasos") or [])]
    codigos_52 = [str(p.get("codigo") or "") for p in (flujo_52.get("pasos") or [])]
    assert codigos_directo == codigos_52

    ejec_directa = orch_directo.ejecutar_flujo_seguro(flujo_directo, confirmar=True)
    assert ejec_directa.get("ok") is True
    assert ejec_directa.get("modifico_datos_reales") is False

    confirmado_52 = orch_52._continuar_flujo_confirmado({"tipo": "confirmar_todo"})
    assert confirmado_52.get("ok") is True
    datos_52 = confirmado_52.get("datos") or {}
    ejec_52 = datos_52.get("ejecucion") or {}

    assert ejec_52.get("estado") == ejec_directa.get("estado")
    assert len(ejec_52.get("resultados") or []) == len(ejec_directa.get("resultados") or [])
    assert len(ejec_52.get("pendientes_confirmacion") or []) == len(ejec_directa.get("pendientes_confirmacion") or [])
    assert bool(datos_52.get("modifico_datos_reales")) is False


def test_ruta_52_preparacion_mantiene_modo_seguro_sin_pedidos_ni_stock(tmp_path: Path) -> None:
    evento_52 = {
        "evento": {
            "tipo": DATOS_EVENTO["tipo"],
            "personas": DATOS_EVENTO["personas"],
            "fecha": DATOS_EVENTO["fecha"],
            "hora_servicio": DATOS_EVENTO["hora_servicio"],
            "menu": DATOS_EVENTO["menu"],
            "lugar": DATOS_EVENTO["lugar"],
            "restricciones": DATOS_EVENTO["restricciones"],
            "objetivo": DATOS_EVENTO["objetivo"],
        }
    }

    orch_52 = OrquestadorInteligente52(tmp_path)
    preparado = orch_52._procesar_evento_completo(evento_52)
    assert preparado.get("ok") is True

    datos = preparado.get("datos") or {}
    ejecucion_previa = datos.get("ejecucion") or {}
    assert ejecucion_previa.get("modifico_datos_reales") is False
    assert len(ejecucion_previa.get("pendientes_confirmacion") or []) >= 1

    db = tmp_path / "DATOS" / "db"
    assert not (db / "compras_pedidos.json").exists()


def test_produccion_inteligente_evento_completo_ordena_por_hora_y_dependencia(tmp_path: Path) -> None:
    _seed_produccion_inteligente_base(tmp_path)

    generado = generar_flujo_operativo_evento(
        {
            "tipo": "boda",
            "personas": 80,
            "fecha": "2026-10-22",
            "hora_servicio": "12:30",
            "menu": "menu boda",
            "lugar": "Mas Boronat",
            "restricciones": "sin restricciones",
            "objetivo": "flujo completo",
        }
    )
    flujo = generado.get("flujo") or {}
    flujo = (seleccionar_paso(flujo, "PRODUCCION_PLAN").get("flujo") or flujo)
    flujo = (registrar_confirmacion(flujo, "PRODUCCION_PLAN", True).get("flujo") or flujo)

    ejecucion = ejecutar_flujo_operativo(flujo, confirmar=True, codigo_paso="PRODUCCION_PLAN", contexto={"base_dir": str(tmp_path)})

    assert ejecucion.get("ok") is True
    detalle = (((ejecucion.get("paso") or {}).get("resultado") or {}).get("detalle") or {})
    propuesta = detalle.get("propuesta_produccion_integrada") or {}
    elaboraciones = list(propuesta.get("elaboraciones") or [])
    assert elaboraciones
    horas = [str(item.get("hora_servicio") or "") for item in elaboraciones]
    assert horas == sorted(horas)
    nombres = [str(item.get("nombre") or "") for item in elaboraciones]
    assert nombres.index("Carrillera braseada") < nombres.index("Salsa reducción")
    assert propuesta.get("datos_reales_modificados") is False
    motor = propuesta.get("motor_reutilizado") or {}
    assert motor.get("servicio") == "ProduccionAutomaticaEvento556F"
    assert motor.get("solo_lectura") is True


def test_produccion_inteligente_detecta_receta_sin_tiempos_y_escandallo_ausente(tmp_path: Path) -> None:
    _seed_produccion_inteligente_base(tmp_path, postre_sin_tiempos=True, incluir_fantasma=True)

    generado = generar_flujo_operativo_evento(
        {
            "tipo": "boda",
            "personas": 80,
            "fecha": "2026-10-22",
            "hora_servicio": "18:00",
            "menu": "menu boda",
            "lugar": "Mas Boronat",
            "restricciones": "sin restricciones",
            "objetivo": "flujo completo",
        }
    )
    flujo = (seleccionar_paso(generado.get("flujo") or {}, "PRODUCCION_PLAN").get("flujo") or generado.get("flujo") or {})
    flujo = (registrar_confirmacion(flujo, "PRODUCCION_PLAN", True).get("flujo") or flujo)

    ejecucion = ejecutar_flujo_operativo(flujo, confirmar=True, codigo_paso="PRODUCCION_PLAN", contexto={"base_dir": str(tmp_path)})
    propuesta = (((ejecucion.get("paso") or {}).get("resultado") or {}).get("detalle") or {}).get("propuesta_produccion_integrada") or {}
    riesgos = list(propuesta.get("riesgos") or [])
    advertencias = " ".join(str(x) for x in (propuesta.get("advertencias") or []))

    assert any(r.get("tipo") == "dato_faltante" for r in riesgos)
    assert any("duración utilizable" in str(r.get("mensaje") or "") for r in riesgos)
    assert any("escandallos" in str(r.get("mensaje") or "") for r in riesgos)
    assert any("ficha de producción validada" in str(r.get("mensaje") or "") for r in riesgos)
    banderas = propuesta.get("banderas_seguridad") or {}
    assert banderas.get("datos_reales_modificados") is False
    assert banderas.get("no_modificar_produccion") is True
    assert "inicio/fin" in advertencias.lower()


def test_produccion_inteligente_detecta_stock_insuficiente_y_sugiere_compras(tmp_path: Path) -> None:
    _seed_produccion_inteligente_base(tmp_path, stock_bajo=True)

    generado = generar_flujo_operativo_evento(
        {
            "tipo": "boda",
                "personas": 80,
            "fecha": "2026-10-22",
            "hora_servicio": "12:30",
            "menu": "menu boda",
            "lugar": "Mas Boronat",
            "restricciones": "sin restricciones",
            "objetivo": "flujo completo",
        }
    )
    flujo = (seleccionar_paso(generado.get("flujo") or {}, "PRODUCCION_PLAN").get("flujo") or generado.get("flujo") or {})
    flujo = (registrar_confirmacion(flujo, "PRODUCCION_PLAN", True).get("flujo") or flujo)

    ejecucion = ejecutar_flujo_operativo(flujo, confirmar=True, codigo_paso="PRODUCCION_PLAN", contexto={"base_dir": str(tmp_path)})
    propuesta = (((ejecucion.get("paso") or {}).get("resultado") or {}).get("detalle") or {}).get("propuesta_produccion_integrada") or {}
    riesgos = propuesta.get("riesgos") or []
    banderas = propuesta.get("banderas_seguridad") or {}

    assert any(r.get("tipo") == "stock" for r in riesgos)
    assert propuesta.get("sugerir_compras_preparar") is True
    assert banderas.get("no_modificar_stock") is True
    assert banderas.get("no_crear_movimientos") is True


def test_produccion_inteligente_detecta_plan_parcial_existente(tmp_path: Path) -> None:
    _seed_produccion_inteligente_base(tmp_path, plan_parcial=True)

    generado = generar_flujo_operativo_evento(
        {
            "tipo": "boda",
            "personas": 80,
            "fecha": "2026-10-22",
            "hora_servicio": "12:30",
            "menu": "menu boda",
            "lugar": "Mas Boronat",
            "restricciones": "sin restricciones",
            "objetivo": "flujo completo",
        }
    )
    flujo = (seleccionar_paso(generado.get("flujo") or {}, "PRODUCCION_PLAN").get("flujo") or generado.get("flujo") or {})
    flujo = (registrar_confirmacion(flujo, "PRODUCCION_PLAN", True).get("flujo") or flujo)

    ejecucion = ejecutar_flujo_operativo(flujo, confirmar=True, codigo_paso="PRODUCCION_PLAN", contexto={"base_dir": str(tmp_path)})
    propuesta = (((ejecucion.get("paso") or {}).get("resultado") or {}).get("detalle") or {}).get("propuesta_produccion_integrada") or {}

    assert propuesta.get("estado") in {"propuesta_produccion_preparada", "propuesta_produccion_integrada"}
    assert any("producción parcial previa" in str(r.get("mensaje") or "") for r in (propuesta.get("riesgos") or []))
    assert propuesta.get("datos_reales_modificados") is False


def test_produccion_inteligente_compatibilidad_52_y_orquestador_canonicos(tmp_path: Path) -> None:
    _seed_produccion_inteligente_base(tmp_path)
    evento_52 = {
        "evento": {
            "tipo": DATOS_EVENTO["tipo"],
            "personas": DATOS_EVENTO["personas"],
            "fecha": DATOS_EVENTO["fecha"],
            "hora_servicio": DATOS_EVENTO["hora_servicio"],
            "menu": DATOS_EVENTO["menu"],
            "lugar": DATOS_EVENTO["lugar"],
            "restricciones": DATOS_EVENTO["restricciones"],
            "objetivo": DATOS_EVENTO["objetivo"],
        }
    }

    orch_directo = OrquestadorFlujoOperativo(tmp_path)
    orch_52 = OrquestadorInteligente52(tmp_path)

    flujo_directo = (orch_directo.iniciar_flujo_operativo(DATOS_EVENTO).get("flujo") or {})
    flujo_52 = ((orch_52._procesar_evento_completo(evento_52).get("datos") or {}).get("flujo") or {})

    assert any(p.get("codigo") == "PRODUCCION_PLAN" for p in (flujo_directo.get("pasos") or []))
    assert any(p.get("codigo") == "PRODUCCION_PLAN" for p in (flujo_52.get("pasos") or []))

    seleccion = orch_directo.seleccionar_accion_en_flujo("PRODUCCION_PLAN", flujo_directo)
    assert seleccion.get("ok") is True
    confirmacion = orch_52._continuar_flujo_confirmado({"tipo": "confirmar_todo"})
    assert confirmacion.get("ok") is True
    assert bool((confirmacion.get("datos") or {}).get("modifico_datos_reales")) is False


def test_host_ai_executive_integracion_workflow_unificado_seguro_y_persistente(tmp_path: Path, monkeypatch) -> None:
    _seed_produccion_inteligente_base(tmp_path, stock_bajo=True)
    db = tmp_path / "DATOS" / "db"
    _write_json(db / "planes_produccion.json", [])
    _write_json(db / "proveedores.json", [{"codigo": "PRV-1", "nombre": "Proveedor Demo"}])

    before_planes = (db / "planes_produccion.json").read_text(encoding="utf-8")
    before_stock_mov = (db / "stock_movimientos.json").read_text(encoding="utf-8")
    before_proveedores = (db / "proveedores.json").read_text(encoding="utf-8")

    llamadas = {"iniciar": 0, "ejecutar_flujo": 0, "ejecutar_paso": 0}
    _orig_iniciar = OrquestadorFlujoOperativo.iniciar_flujo_operativo
    _orig_ejecutar_flujo = OrquestadorFlujoOperativo.ejecutar_flujo_seguro
    _orig_ejecutar_paso = OrquestadorFlujoOperativo.ejecutar_paso_seguro

    def _spy_iniciar(self, datos_evento):
        llamadas["iniciar"] += 1
        return _orig_iniciar(self, datos_evento)

    def _spy_ejecutar_flujo(self, flujo, confirmar=False, codigo_paso=None):
        llamadas["ejecutar_flujo"] += 1
        return _orig_ejecutar_flujo(self, flujo, confirmar=confirmar, codigo_paso=codigo_paso)

    def _spy_ejecutar_paso(self, flujo, codigo_paso=None):
        llamadas["ejecutar_paso"] += 1
        return _orig_ejecutar_paso(self, flujo, codigo_paso=codigo_paso)

    monkeypatch.setattr(OrquestadorFlujoOperativo, "iniciar_flujo_operativo", _spy_iniciar)
    monkeypatch.setattr(OrquestadorFlujoOperativo, "ejecutar_flujo_seguro", _spy_ejecutar_flujo)
    monkeypatch.setattr(OrquestadorFlujoOperativo, "ejecutar_paso_seguro", _spy_ejecutar_paso)

    servicio = HostAIExecutive(tmp_path)
    datos = {
        "tipo": "boda",
        "personas": 80,
        "fecha": "2026-10-22",
        "hora_servicio": "12:30",
        "menu": "menu boda",
        "lugar": "Mas Boronat",
        "restricciones": "sin restricciones",
        "objetivo": "flujo completo",
    }
    resultado = servicio.analizar_evento(datos)

    assert resultado.get("ok") is True
    assert resultado.get("estado") == "analisis_completo"
    assert resultado.get("datos_reales_modificados") is False

    workflows = list(resultado.get("workflows_priorizados") or [])
    workflows_ejecutados = list(resultado.get("workflows_ejecutados") or [])
    pendientes = list(resultado.get("pendientes") or [])
    riesgos = list(resultado.get("riesgos") or [])
    recomendaciones = list(resultado.get("recomendaciones") or [])
    flujo = dict(resultado.get("flujo") or {})

    assert any(w.get("workflow") == "PRODUCCION_INTELIGENTE" for w in workflows)
    assert any(w.get("workflow") == "COMPRAS_INTELIGENTES" for w in workflows)
    prioridad_produccion = min(int(w.get("prioridad") or 99) for w in workflows if w.get("workflow") == "PRODUCCION_INTELIGENTE")
    prioridad_compras = min(int(w.get("prioridad") or 99) for w in workflows if w.get("workflow") == "COMPRAS_INTELIGENTES")
    assert prioridad_produccion < prioridad_compras

    assert llamadas["iniciar"] >= 1
    assert llamadas["ejecutar_flujo"] >= 1
    assert llamadas["ejecutar_paso"] >= 1 or len(workflows_ejecutados) >= 1

    # Executive coordina; no debe incorporar llamadas directas a motores de negocio.
    source_exec = inspect.getsource(HostAIExecutive)
    assert "MotorPlanificacionRecetasReales" not in source_exec
    assert "ProduccionAutomaticaEvento556F" not in source_exec
    assert "CruceStockProduccion556C" not in source_exec

    assert any(item.get("workflow") == "PRODUCCION_INTELIGENTE" for item in workflows_ejecutados)
    assert any(item.get("workflow") == "COMPRAS_INTELIGENTES" for item in workflows_ejecutados)
    assert all(bool(item.get("datos_reales_modificados")) is False for item in workflows_ejecutados)

    pasos_con_resultado = [p for p in (flujo.get("pasos") or []) if isinstance((p or {}).get("resultado"), dict)]
    assert pasos_con_resultado

    resumen = str(resultado.get("resumen_ejecutivo") or "")
    assert "Prioridad inmediata" in resumen
    assert "Modo seguro" in resumen
    assert recomendaciones
    assert pendientes
    assert riesgos

    assert (db / "planes_produccion.json").read_text(encoding="utf-8") == before_planes
    assert (db / "stock_movimientos.json").read_text(encoding="utf-8") == before_stock_mov
    assert (db / "proveedores.json").read_text(encoding="utf-8") == before_proveedores
    assert not (db / "compras_pedidos.json").exists()

    guardado = servicio.orquestador_flujo.guardar_flujo(flujo)
    assert guardado.get("ok") is True
    cargado = servicio.orquestador_flujo.reanudar_flujo_desde_archivo(ruta=Path(str(guardado.get("ruta"))))
    assert cargado.get("ok") is True

    flujo_cargado = dict(cargado.get("flujo") or {})
    informe = dict(flujo_cargado.get("informe_ejecutivo") or {})
    assert informe.get("estado") == "analisis_completo"
    assert isinstance(informe.get("workflows_ejecutados"), list)
    assert isinstance(informe.get("workflows_priorizados"), list)
    assert isinstance(informe.get("pendientes"), list)
    assert isinstance(informe.get("riesgos"), list)
    assert isinstance(informe.get("recomendaciones"), list)
    assert isinstance(informe.get("pendientes_operativos"), list)
    assert isinstance(informe.get("riesgos_operativos"), list)
    assert isinstance(informe.get("recomendaciones_operativas"), list)
    assert isinstance(informe.get("prioridad_inmediata"), dict)
    assert isinstance(informe.get("resumen_ejecutivo_lineas"), list)
    assert informe.get("resumen_ejecutivo") == resultado.get("resumen_ejecutivo")
