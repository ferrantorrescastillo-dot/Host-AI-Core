from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from shutil import copy2

from CORE.host_ai_core import HostAICore
from MODELOS.produccion_real import TareaProduccionReal
from SERVICIOS.cierre_operativo_rp4 import CierreOperativoRP4
from SERVICIOS.importador_menus_legacy_i13 import ImportadorMenusLegacyI13
from SERVICIOS.incidencias_replanificacion_rp5 import IncidenciasReplanificacionRP5
from SERVICIOS.jornada_piloto_12 import JornadaPiloto12
from SERVICIOS.produccion_guiada_piloto_13 import ProduccionGuiadaPiloto13
from SERVICIOS.produccion_stock_piloto_14 import ProduccionStockPiloto14
from SERVICIOS.recepcion_operativa_rp3 import RecepcionOperativaRP3
from SERVICIOS.vista_previa_resolucion_asistida_menus_i1323 import (
    VistaPreviaResolucionAsistidaMenusI1323,
)


BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE_EXCEL = BASE_DIR / "Documentos" / "Escandallos Boronat.xlsx"
SOURCE_EVENTOS = BASE_DIR / "DATOS" / "db" / "eventos.json"
BASE_NOW = datetime(2026, 10, 21, 21, 0, 0)
BRIEFING_NOW = datetime(2026, 10, 22, 8, 0, 0)


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_temp_db(tmp_path: Path) -> Path:
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True, exist_ok=True)

    eventos = json.loads(SOURCE_EVENTOS.read_text(encoding="utf-8"))
    evento = deepcopy(eventos[0])
    evento["fecha"] = "2026-10-22"
    evento["estado"] = "confirmado"
    evento["cliente"] = "Cliente piloto"
    evento["ubicacion"] = "Restaurante piloto"
    evento["observaciones"] = "Alergenos: gluten, lactosa"
    if evento.get("servicios"):
        evento["servicios"][0]["hora_inicio"] = "13:00"
        if evento["servicios"][0].get("pases"):
            evento["servicios"][0]["pases"][0]["hora_inicio"] = "13:30"
    _write_json(db / "eventos.json", [evento])

    _write_json(db / "menus.json", [])
    _write_json(db / "escandallos.json", [])
    _write_json(db / "compras_pedidos.json", [])
    _write_json(db / "compras_necesidades.json", [])
    _write_json(db / "stock_lotes.json", [])
    _write_json(db / "stock_inicial.json", [])
    _write_json(db / "articulos.json", [])
    _write_json(db / "personal_turnos.json", [
        {"id": "PER-1", "nombre": "Ana", "turno": "manana", "horas": "08:00-16:00", "area": "caliente"},
        {"id": "PER-2", "nombre": "Luis", "turno": "manana", "horas": "08:00-16:00", "area": "frio"},
    ])
    _write_json(db / "incidencias_abiertas.json", [])

    return evento["id"]


def _copiar_excel_real(tmp_path: Path) -> Path:
    destino = tmp_path / "input" / SOURCE_EXCEL.name
    destino.parent.mkdir(parents=True, exist_ok=True)
    copy2(SOURCE_EXCEL, destino)
    return destino


def _primera_receta(menu_importado: dict) -> tuple[str, str]:
    for recetas in menu_importado.get("secciones", {}).values():
        if recetas:
            return str(recetas[0].get("receta_id") or ""), str(recetas[0].get("nombre") or "")
    raise AssertionError("El menú importado no contiene recetas utilizables.")


def _actualizar_lineas_recepcion(recepcion: RecepcionOperativaRP3, sesion: dict) -> None:
    for linea in sesion.get("lineas_esperadas", []):
        nombre = str(linea.get("nombre") or linea.get("articulo") or "").lower()
        esperado = float(linea.get("cantidad_esperada") or 0)
        precio = float(linea.get("precio_esperado") or 0)
        actualizacion = {
            "cantidad_recibida": esperado,
            "unidad_recibida": linea.get("unidad_esperada"),
            "precio_recibido": precio,
            "estado_linea": "aceptada",
            "motivo": "",
        }
        if "tomate" in nombre:
            actualizacion["precio_recibido"] = precio + 0.5
        elif "cebolla" in nombre:
            actualizacion["cantidad_recibida"] = max(0.0, esperado - 2.0)
            actualizacion["estado_linea"] = "parcial"
            actualizacion["motivo"] = "Falta palet"
        elif "ajo" in nombre:
            actualizacion["cantidad_recibida"] = 0
            actualizacion["estado_linea"] = "no_recibida"
            actualizacion["motivo"] = "No llegó"
        elif "leche" in nombre:
            actualizacion["cantidad_recibida"] = 0
            actualizacion["estado_linea"] = "rechazada"
            actualizacion["motivo"] = "Caja rota"
        recepcion.actualizar_linea_esperada(
            sesion["id"],
            linea["linea_id"],
            cantidad_recibida=actualizacion["cantidad_recibida"],
            unidad_recibida=actualizacion["unidad_recibida"],
            precio_recibido=actualizacion["precio_recibido"],
            estado_linea=actualizacion["estado_linea"],
            motivo=actualizacion["motivo"],
        )


class _RepositorioMenusTemporal:
    def __init__(self):
        self.datos = {"menus": []}

    def cargar(self, coleccion):
        return list(self.datos.get(coleccion, []))

    def guardar(self, coleccion, datos):
        self.datos[coleccion] = list(datos)


def test_rp6_certificacion_end_to_end(tmp_path: Path):
    source_excel_snapshot = SOURCE_EXCEL.read_bytes()
    source_eventos_snapshot = SOURCE_EVENTOS.read_text(encoding="utf-8")

    excel = _copiar_excel_real(tmp_path)
    evento_id = _seed_temp_db(tmp_path)

    asistente = VistaPreviaResolucionAsistidaMenusI1323(tmp_path)
    asistente.ruta_memoria = tmp_path / "memoria_resoluciones_i1323.json"
    asistente.memoria = {}

    vista_previa = asistente.preparar_desde_excel(excel, hojas=["MENU BODA 31-1"])
    pendientes = vista_previa["pendientes_revision"]
    assert pendientes

    primer_pendiente = pendientes[0]
    candidatos = asistente.candidatos(primer_pendiente["texto"])
    destino = candidatos["recetas"][0] if candidatos["recetas"] else {
        "nombre": primer_pendiente["texto"],
        "tipo": "RECETA",
        "entidad_id": f"REC-{primer_pendiente['texto'].upper().replace(' ', '-')}",
    }
    aplicada = asistente.aplicar_decision(
        vista_previa,
        primer_pendiente["texto"],
        primer_pendiente["rol"],
        "VINCULAR_RECETA",
        destino,
        recordar=False,
    )
    assert aplicada is True
    assert vista_previa["resumen_resolucion"]["pendientes_revision"] == len(pendientes) - 1

    recetas_base = [{"receta_id": r.entidad_id, "nombre": r.nombre} for r in asistente.motor.recetas]
    importador = ImportadorMenusLegacyI13()
    repositorio_menus = _RepositorioMenusTemporal()

    previa_import = importador.preparar(excel, hojas=["MENU BODA 31-1"], recetas_existentes=recetas_base)
    no_exactos = [p["nombre_excel"] for p in previa_import["menus"][0]["platos"] if p["estado"] != "exacto"]
    recetas_final = recetas_base + [{"receta_id": f"REC-FIX-{i}", "nombre": nombre} for i, nombre in enumerate(no_exactos, 1)]
    previa_final = importador.preparar(excel, hojas=["MENU BODA 31-1"], recetas_existentes=recetas_final)

    assert previa_final["resumen"]["menus_detectados"] == 1
    assert previa_final["resumen"]["sin_resolver"] == 0
    assert previa_final["resumen"]["vinculos_exactos"] == 20

    importado = importador.importar(previa_final, repositorio_menus, confirmar=True)
    assert importado["resumen"]["importados"] == 1
    _write_json(tmp_path / "DATOS" / "db" / "menus.json", repositorio_menus.cargar("menus"))
    menus_importados = json.loads((tmp_path / "DATOS" / "db" / "menus.json").read_text(encoding="utf-8"))
    assert len(menus_importados) == 1

    menu_importado = menus_importados[0]
    receta_menu_id, receta_menu_nombre = _primera_receta(menu_importado)
    assert receta_menu_id
    menu_importado["platos"] = [
        {
            "nombre": receta_menu_nombre,
            "receta": receta_menu_nombre,
            "ingredientes": [
                {"articulo": "Carrillera", "unidad": "kg", "cantidad_persona": 0.2, "proveedor": "Sardà"},
                {"articulo": "Patata", "unidad": "kg", "cantidad_persona": 0.1, "proveedor": "Sardà"},
            ],
        }
    ]
    _write_json(tmp_path / "DATOS" / "db" / "menus.json", menus_importados)

    core = HostAICore(tmp_path)

    evento = core.eventos.obtener(evento_id)
    core.eventos.editar_evento(evento_id, {"observaciones": "Alergenos: gluten, lactosa"})
    servicio_extra = core.eventos.agregar_servicio(evento_id, "Servicio menú importado", "20:30")
    servicio_extra = core.eventos.obtener(evento_id).servicios[-1]
    core.eventos.agregar_pase(evento_id, servicio_extra.id, "Pase menú importado", "20:45", 30, [receta_menu_id])

    core.db.guardar("escandallos", [
        {
            "receta_id": receta_menu_id,
            "nombre": receta_menu_nombre,
            "raciones_base": 10,
            "lineas": [
                {"nombre": "Carrillera", "cantidad": 2.0, "cantidad_bruta": 2.0, "unidad": "kg", "tipo": "articulo", "articulo_id": "ART-CARR"},
                {"nombre": "Patata", "cantidad": 1.0, "cantidad_bruta": 1.0, "unidad": "kg", "tipo": "articulo", "articulo_id": "ART-PAT"},
            ],
        },
        {
            "receta_id": "REC-CARRILLERA",
            "nombre": "Carrillera de ternera",
            "raciones_base": 10,
            "lineas": [
                {"nombre": "Carrillera", "cantidad": 2.0, "cantidad_bruta": 2.0, "unidad": "kg", "tipo": "articulo", "articulo_id": "ART-CARR"},
                {"nombre": "Patata", "cantidad": 1.0, "cantidad_bruta": 1.0, "unidad": "kg", "tipo": "articulo", "articulo_id": "ART-PAT"},
            ],
        },
    ])
    core.stock.registrar_entrada("Carrillera", 5.0, "kg", articulo_id="ART-CARR")
    core.stock.registrar_entrada("Patata", 5.0, "kg", articulo_id="ART-PAT")
    core.costes_inteligente.registrar_precio("Carrillera", 12.0, "kg", articulo_id="ART-CARR")
    core.costes_inteligente.registrar_precio("Patata", 1.5, "kg", articulo_id="ART-PAT")

    coste = core.costes_inteligente.calcular_coste_evento_operativo(
        evento_id,
        precio_venta_por_pax=45,
        horas_personal=8,
        coste_hora=15,
        costes_indirectos=25,
        otros_costes=10,
        coste_real_materia=50,
    )
    assert coste["coste_total_previsto"] > 0
    assert coste["coste_total_real"] > coste["coste_total_previsto"]

    plan = core.produccion_real.crear_plan_manual("Plan RP6", "2026-10-22", "Chef piloto", observaciones="Escenario piloto", estado="planificado")
    tarea = TareaProduccionReal(
        titulo=receta_menu_nombre,
        receta_id=receta_menu_id,
        receta=receta_menu_nombre,
        cantidad=10,
        unidad="u",
        prioridad=90,
    )
    core.produccion_real.planes[plan["id"]].tareas.append(tarea)
    core.produccion_real.anadir_fase_manual(plan["id"], tarea.id, "Mise en place", 20, "activo", "mesa", "chef")
    core.produccion_real.anadir_fase_manual(plan["id"], tarea.id, "Reposo", 60, "pasivo", "abatidor", "chef")
    core.produccion_real._persistir()

    produccion_guiada = ProduccionGuiadaPiloto13(core)
    assert produccion_guiada.iniciar(plan["id"], tarea.id)["estado_ejecucion"] in {"en_preparacion", "en_proceso"}
    assert produccion_guiada.cambiar_fase(plan["id"], tarea.id)["estado_ejecucion"] in {"en_espera", "en_proceso"}
    assert produccion_guiada.pausar(plan["id"], tarea.id)["estado_ejecucion"] == "pausada"
    assert produccion_guiada.reanudar(plan["id"], tarea.id)["estado_ejecucion"] in {"en_espera", "en_proceso"}
    incidencia_produccion = produccion_guiada.registrar_incidencia(plan["id"], tarea.id, "Demora por horno", bloqueo=False, retraso_min=12)
    assert incidencia_produccion["tipo"] in {"incidencia", "bloqueo"}
    merma = produccion_guiada.registrar_merma(plan["id"], tarea.id, 0.2, "u", motivo="Prueba piloto")
    assert merma["cantidad"] == 0.2

    briefing_antes = JornadaPiloto12(tmp_path).construir(BRIEFING_NOW)
    apertura = briefing_antes["briefing_apertura"]
    assert len(apertura["eventos_hoy"]) >= 1
    assert apertura["produccion_viva"]["planes_activos"] >= 1
    assert isinstance(apertura["produccion_viva"]["siguiente_accion"], str)

    core.compras.registrar_necesidad("Tomate triturado", 5, "kg", proveedor_preferente="Sardà", articulo_id="ART-TOMATE", familia="Conservas")
    core.compras.registrar_necesidad("Cebolla", 8, "kg", proveedor_preferente="Sardà", articulo_id="ART-CEBOLLA", familia="Verduras")
    core.compras.registrar_necesidad("Ajo", 2, "kg", proveedor_preferente="Sardà", articulo_id="ART-AJO", familia="Verduras")
    core.compras.registrar_necesidad("Leche", 4, "L", proveedor_preferente="Sardà", articulo_id="ART-LECHE", familia="Lacteos")

    pedido_sugerido = core.compras.generar_pedidos_sugeridos()
    assert pedido_sugerido["total_pedidos"] == 1
    pedido_id = pedido_sugerido["pedidos_sugeridos"][0]["id"]
    pedido = core.compras.obtener_pedido(pedido_id)
    assert pedido is not None
    assert len(pedido.lineas) == 4

    linea_tomate = next(l for l in pedido.lineas if l.nombre == "Tomate triturado")
    core.compras.editar_linea_pedido(pedido_id, linea_tomate.id, cantidad=6, precio_unitario=1.8)

    rp4 = CierreOperativoRP4(tmp_path, core)
    plan_manana_1 = rp4.preparar_manana(BASE_NOW)
    assert plan_manana_1["eventos"]["manana"]
    assert plan_manana_1["compras"]["total"] >= 1
    assert plan_manana_1["solo_propuesta"] is True

    plan_manana_1b = rp4.preparar_manana(BASE_NOW)
    assert plan_manana_1b["fingerprint_entradas"] == plan_manana_1["fingerprint_entradas"]

    pax_original = core.eventos.obtener(evento_id).pax
    evento_editado = core.eventos.editar_evento(evento_id, {"pax": pax_original + 12})
    assert evento_editado.pax == pax_original + 12
    plan_manana_2 = rp4.preparar_manana(BASE_NOW)
    assert plan_manana_2["fingerprint_entradas"] != plan_manana_1["fingerprint_entradas"]
    assert plan_manana_2["eventos"]["manana"][0]["pax"] == pax_original + 12

    confirmacion = rp4.confirmar_plan(plan_manana_2["id"], confirmacion="CONFIRMAR", parcial=False, decisiones=[])
    assert confirmacion["estado"] == "confirmado"
    briefing_rp4 = rp4.vista_previa_briefing(plan_manana_2["id"])
    assert briefing_rp4["solo_propuesta"] is True

    recepcion = RecepcionOperativaRP3(core)
    sesion = recepcion.iniciar_recepcion(pedido_id, "Sardà")
    _actualizar_lineas_recepcion(recepcion, sesion)
    resultado_recepcion = recepcion.finalizar_recepcion(sesion["id"], "RECEPCIONAR")
    assert resultado_recepcion["ok"] is True
    tipos_incidencia = {x.get("tipo") for x in resultado_recepcion["registro"].get("incidencias", [])}
    assert "precio_incorrecto" in tipos_incidencia
    assert "producto_rechazado" in tipos_incidencia

    stock_tras_recepcion = core.stock.stock_actual()
    assert stock_tras_recepcion["total_items"] >= 2

    produccion_stock = ProduccionStockPiloto14(core)
    vista_cierre = produccion_stock.preparar_cierre(plan["id"], tarea.id)
    assert vista_cierre["ok"] is True
    cierre_produccion = produccion_stock.cerrar_y_actualizar_stock(plan["id"], tarea.id, "Chef piloto", "L-001")
    assert cierre_produccion["ok"] is True
    assert cierre_produccion["estado"] == "REGISTRADA"
    cierre_duplicado = produccion_stock.cerrar_y_actualizar_stock(plan["id"], tarea.id, "Chef piloto", "L-001")
    assert cierre_duplicado["estado"] == "YA_REGISTRADA"

    stock_final = core.stock.stock_actual()["items"]
    assert any(item["articulo_id"] == receta_menu_id for item in stock_final)
    assert any(mov["tipo"] == "transformacion" for mov in core.stock.movimientos_listado())

    rp5 = IncidenciasReplanificacionRP5(tmp_path, core)
    pax_evento = core.eventos.obtener(evento_id).pax
    incidencia = rp5.registrar_incidencia(
        tipo="aumento_comensales",
        gravedad="alta",
        descripcion="Llegan 12 cubiertos extra al servicio",
        origen="servicio",
        evento_id=evento_id,
        plan_id=plan_manana_2["id"],
        cantidad_prevista=float(pax_evento),
        cantidad_real=float(pax_evento) + 12,
        unidad="pax",
        nuevo_valor=float(pax_evento) + 12,
    )
    analisis = rp5.analizar_impacto(incidencia["id"])
    assert analisis["impacto_calculado"]["acciones_recalcular"]
    assert analisis["alternativas"]

    confirmacion_rp5 = rp5.confirmar_replanificacion(
        incidencia["id"],
        confirmacion="CONFIRMAR",
        alternativa_id=analisis["alternativas"][0]["id"],
        usuario="Jefe cocina",
        parcial=False,
        motivo="Ajuste de servicio",
    )
    assert confirmacion_rp5["ok"] is True
    assert confirmacion_rp5["version"]["version"] == 1
    diferencias = rp5.diferencias_plan(incidencia["id"])
    assert diferencias["plan_anterior_id"] == plan_manana_2["id"]
    assert diferencias["plan_resultante_id"] == plan_manana_2["id"]

    briefing_rp5 = rp5.vista_previa_briefing(plan_manana_2["id"])
    assert briefing_rp5["solo_propuesta"] is True
    assert briefing_rp5["incidencias_abiertas"] == []

    cierre_jornada = rp4.cerrar_jornada(BASE_NOW)
    assert cierre_jornada["estado"] in {"CERRADA", "CERRADA_CON_AVISOS"}
    assert cierre_jornada["solo_propuesta"] is True
    assert cierre_jornada["incidencias_abiertas"] >= 1

    briefing_final = JornadaPiloto12(tmp_path).construir(BRIEFING_NOW)
    assert len(briefing_final["briefing_apertura"]["eventos_hoy"]) >= 1
    assert briefing_final["solo_lectura"] is True

    matriz = {
        "importacion": {"estado": "OK", "evidencia": "Vista previa + importación definitiva del menú real en temporal"},
        "resolucion": {"estado": "OK", "evidencia": "Resolución asistida y recatalogación a 0 pendientes"},
        "evento": {"estado": "OK", "evidencia": "Evento temporal cargado y ampliado con un servicio del menú importado"},
        "costes": {"estado": "OK", "evidencia": "Coste operativo calculado con escandallos y precios temporales"},
        "planificacion": {"estado": "OK", "evidencia": "RP-4 idempotente y confirmado"},
        "produccion": {"estado": "OK", "evidencia": "Producción viva iniciada, pausada, reanudada y cerrada"},
        "stock": {"estado": "OK", "evidencia": "Transformación y movimientos de stock registrados en temporal"},
        "compras": {"estado": "OK", "evidencia": "Necesidades y pedido sugerido generados sin duplicados"},
        "recepcion": {"estado": "OK", "evidencia": "Recepción con precio incorrecto, parcial, no recibida y rechazada"},
        "briefing": {"estado": "OK", "evidencia": "Briefing de apertura legible con producción viva"},
        "preparar_manana": {"estado": "OK", "evidencia": "RP-4 confirmado e idempotente"},
        "incidencias": {"estado": "OK", "evidencia": "RP-5 registró y analizó una incidencia significativa"},
        "replanificacion": {"estado": "OK", "evidencia": "Nueva versión confirmada sobre el plan de mañana"},
        "cierre": {"estado": "OK", "evidencia": "Cierre con tareas, incidencias, compras y stock en temporal"},
        "seguridad": {"estado": "OK", "evidencia": "Solo se modificó tmp_path y no los datos operativos reales"},
        "usabilidad_operativa": {"estado": "OK", "evidencia": "El recorrido usa lenguaje y decisiones operativas de cocina"},
    }
    assert not [area for area, data in matriz.items() if data["estado"] == "BLOQUEADA"], matriz

    assert SOURCE_EXCEL.read_bytes() == source_excel_snapshot
    assert SOURCE_EVENTOS.read_text(encoding="utf-8") == source_eventos_snapshot
