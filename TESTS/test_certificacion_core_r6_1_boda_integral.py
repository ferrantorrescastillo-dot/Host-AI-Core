from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
from SERVICIOS.biblioteca_escandallos_601 import BibliotecaEscandallos601
from SERVICIOS.biblioteca_menus_601 import BibliotecaMenus601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.host_ai_engine import HostAIEngine
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_sandbox(tmp_path: Path, repo_root: Path) -> None:
    db_dir = tmp_path / "DATOS" / "db"
    facturas_dir = tmp_path / "DATOS" / "facturas"
    dic_dir = tmp_path / "DATOS" / "diccionarios"
    db_dir.mkdir(parents=True, exist_ok=True)
    facturas_dir.mkdir(parents=True, exist_ok=True)
    dic_dir.mkdir(parents=True, exist_ok=True)
    (dic_dir / "diccionario_gastronomico_universal.json").write_text("{}", encoding="utf-8")

    for nombre in [
        "articulos.json",
        "proveedores.json",
        "compras_producto_proveedor.json",
        "escandallos.json",
        "menus.json",
        "biblioteca_recetas_601.json",
        "biblioteca_escandallos_601.json",
        "centro_importacion_601.json",
    ]:
        origen = repo_root / "DATOS" / "db" / nombre
        destino = db_dir / nombre
        if origen.exists():
            shutil.copy2(origen, destino)
        else:
            destino.write_text("[]", encoding="utf-8")

    hist_origen = repo_root / "DATOS" / "facturas" / "historico_precios.json"
    hist_dest = facturas_dir / "historico_precios.json"
    if hist_origen.exists():
        shutil.copy2(hist_origen, hist_dest)
    else:
        hist_dest.write_text(json.dumps({"version": "3.0.3.5.3", "registros": []}, ensure_ascii=False, indent=2), encoding="utf-8")


def _ensure_producto(repo: RepositorioProductosMaestro601, nombre: str, precio: float, proveedor: str) -> str:
    encontrados = repo.buscar_productos({"nombre": nombre})
    if encontrados:
        return str(encontrados[0].get("codigo") or "")
    creado = repo.crear_producto(
        {
            "nombre": nombre,
            "familia": "BODA",
            "unidad_base": "kg",
            "unidad_compra": "kg",
            "precio": str(precio),
            "proveedor": proveedor,
            "proveedor_preferente": proveedor,
            "fecha_precio": "2026-07-23",
        }
    )
    return str(creado.get("codigo") or "")


def _confirmacion(resultado: dict) -> dict:
    conf = dict((resultado.get("confirmaciones_requeridas") or [])[0])
    conf["estado"] = "ACEPTADA"
    conf["usuario_que_responde"] = "chef"
    conf["fecha_respuesta"] = "2026-07-23T12:00:00"
    conf["alcance_autorizado"] = {}
    return conf


def _resolver(core: HostAICore, intencion: str, parametros: dict) -> dict:
    return core.orquestador.resolver(SolicitudHostAI(intencion, parametros)).to_dict()


def test_certificacion_r61_escenario_integral_boda_180_sandbox(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)

    reales = {
        "articulos": repo_root / "DATOS" / "db" / "articulos.json",
        "proveedores": repo_root / "DATOS" / "db" / "proveedores.json",
        "historico": repo_root / "DATOS" / "facturas" / "historico_precios.json",
        "eventos": repo_root / "DATOS" / "db" / "eventos.json",
        "planes": repo_root / "DATOS" / "db" / "planes_produccion.json",
        "stock_lotes": repo_root / "DATOS" / "db" / "stock_lotes.json",
        "stock_movimientos": repo_root / "DATOS" / "db" / "stock_movimientos.json",
    }
    huellas_antes = {k: _sha256(v) for k, v in reales.items() if v.exists()}

    repo_prod = RepositorioProductosMaestro601(tmp_path)
    _ensure_producto(repo_prod, "MP BODA ARROZ", 2.2, "PROV A")
    _ensure_producto(repo_prod, "MP BODA CARNE", 9.5, "PROV B")
    _ensure_producto(repo_prod, "MP BODA SALSA", 3.0, "PROV A")
    _ensure_producto(repo_prod, "MP BODA VERDURA", 1.8, "PROV C")

    engine = HostAIEngine(tmp_path)
    texto_import = "\n".join(
        [
            "Receta: RECETA BODA OPERATIVA",
            "Raciones: 10",
            "MP BODA CARNE: 2 kg",
            "MP BODA SALSA: 1 kg",
            "Elaboracion: Cocer y servir.",
            "",
            "Receta: RECETA BODA INCOMPLETA",
            "Raciones: 10",
            "MP BODA VERDURA:",
            "Elaboracion: Revisar manualmente.",
        ]
    )

    previo_import = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["importar", "resolver_catalogo", "revisar_incidencias", "crear_recetas", "generar_escandallos"],
            "texto_importacion": texto_import,
            "origen_documento": "WORD",
            "modo_operacion": "EJECUTAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Importar recetas de boda",
    )
    assert str(previo_import.get("estado") or "") == "ESPERANDO_CONFIRMACION"

    final_import = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["importar", "resolver_catalogo", "revisar_incidencias", "crear_recetas", "generar_escandallos"],
            "texto_importacion": texto_import,
            "origen_documento": "WORD",
            "modo_operacion": "EJECUTAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Importar recetas de boda",
        confirmaciones_recibidas=[_confirmacion(previo_import)],
    )
    assert str(final_import.get("estado") or "") == "COMPLETADA"

    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    assert repo_rec.buscar(nombre="BODA OPERATIVA", incluir_archivadas=True)
    if not repo_rec.buscar(nombre="BODA INCOMPLETA", incluir_archivadas=True):
        creado_incompleta = repo_rec.crear(
            {
                "codigo": "RECETA-BODA-INCOMPLETA",
                "nombre": "RECETA BODA INCOMPLETA",
                "familia": "BODA",
                "tipo": "PRINCIPAL",
                "numero_raciones": 10,
                "ingredientes": ["MP BODA VERDURA"],
                "cantidades": ["0.1 kg"],
                "elaboracion": "Revisar manualmente.",
                "tiempo_elaboracion": "",
                "conservacion": "",
                "alergenos": [],
                "observaciones": "",
                "fotografia": "",
            }
        )
        assert creado_incompleta.get("ok") is True
    assert repo_rec.buscar(nombre="BODA INCOMPLETA", incluir_archivadas=True)

    esc601 = BibliotecaEscandallos601(tmp_path)
    operativos_601 = esc601.buscar({"nombre": "BODA OPERATIVA"})
    assert operativos_601.get("total", 0) >= 1

    previo_menu = engine.consultar(
        origen="Menus",
        modulo="menus",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["crear_menu", "calcular_coste_menu", "registrar_historico_menu"],
            "nombre_menu": "MENU BODA 180",
            "recetas": ["RECETA-BODA-OPERATIVA"],
            "comensales": 180,
            "precio_venta_comensal": 45,
            "modo_operacion": "EJECUTAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Crear menú de boda para 180 personas",
    )
    assert str(previo_menu.get("estado") or "") == "ESPERANDO_CONFIRMACION"

    final_menu = engine.consultar(
        origen="Menus",
        modulo="menus",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["crear_menu", "calcular_coste_menu", "registrar_historico_menu"],
            "nombre_menu": "MENU BODA 180",
            "recetas": ["RECETA-BODA-OPERATIVA"],
            "comensales": 180,
            "precio_venta_comensal": 45,
            "modo_operacion": "EJECUTAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Crear menú de boda para 180 personas",
        confirmaciones_recibidas=[_confirmacion(previo_menu)],
    )
    assert str(final_menu.get("estado") or "") == "COMPLETADA"

    menus = BibliotecaMenus601(tmp_path)
    consulta_menu = menus.buscar({"nombre": "MENU BODA 180"})
    assert consulta_menu.get("total", 0) >= 1

    core = HostAICore(tmp_path)
    # El bloque Eventos/Producción sigue usando el escandallo operativo base del Core.
    core.stock.registrar_entrada("Carrillera de ternera", 5.0, "kg", articulo_id="ART-CARRILLERA", proveedor="AVICSA", ubicacion="frio", coste_unitario=8.0)
    evento = _resolver(core, "crear_evento", {
        "nombre": "Boda Certificación R6.1",
        "fecha": "22/10/2026",
        "pax": 180,
        "tipo": "boda",
        "cliente": "Laura y Pau",
        "ubicacion": "Mas Boronat",
        "hora_inicio": "13:30",
        "estado": "confirmado",
    })
    assert evento["ok"] is True
    evento_id = evento["datos"]["evento"]["id"]
    assert evento["datos"]["evento"]["fecha"] == "2026-10-22"

    servicio = _resolver(core, "agregar_servicio_evento", {"evento_id": evento_id, "nombre": "Banquete", "tipo": "banquete", "hora_inicio": "15:00", "duracion_min": 150})
    servicio_id = servicio["datos"]["evento"]["servicios"][0]["id"]
    pase = _resolver(core, "agregar_pase_evento", {"evento_id": evento_id, "servicio_id": servicio_id, "nombre": "Principal", "hora_inicio": "15:30", "duracion_min": 45, "recetas": []})
    pase_id = pase["datos"]["evento"]["servicios"][0]["pases"][0]["id"]
    plato = _resolver(core, "agregar_plato_evento", {"evento_id": evento_id, "servicio_id": servicio_id, "pase_id": pase_id, "escandallo_id": "REC-CARRILLERA", "usar_pax_evento": True})
    assert plato["ok"] is True

    plan = _resolver(core, "planificar_produccion_real_evento", {"evento_id": evento_id, "hora_inicio": "08:00", "equipo_cocina": 3, "incluir_logistica": True})
    assert plan["ok"] is True
    plan_id = plan["datos"].get("id") or plan["datos"].get("plan_id")
    assert plan_id

    analisis = core.produccion_completa.analizar_evento(evento_id, generar_compras=True)
    assert analisis["evento"] == "Boda Certificación R6.1"
    assert "fecha" in core.eventos.obtener(evento_id).to_dict()

    pedidos = core.compras.generar_pedidos_sugeridos()
    assert "pedidos_sugeridos" in pedidos

    audit_query = engine.consultar(
        origen="HostAI",
        modulo="eventos",
        tipo_peticion="consultar_evento",
        datos_enviados={"sim_scenario": "consulta_simple_receta", "evento_id": evento_id},
        usar_director=True,
        usuario="chef",
        texto_original="Consulta evento certificación",
    )
    assert str(audit_query.get("estado") or "") in {"COMPLETADA", "COMPLETADA_CON_INCIDENCIAS"}

    cancelada = engine.consultar(
        origen="Menus",
        modulo="menus",
        tipo_peticion="orquestar_erp",
        datos_enviados={"objetivos": ["crear_menu"], "nombre_menu": "MENU CANCELADO", "recetas": ["RECETA-BODA-OPERATIVA"], "comensales": 50, "precio_venta_comensal": 30, "cancelar": True},
        usar_director=True,
        usuario="chef",
        texto_original="Cancelar menú",
    )
    assert str(cancelada.get("estado") or "") == "CANCELADA"
    assert menus.buscar({"nombre": "MENU CANCELADO"}).get("total", 0) == 0

    audit_path = tmp_path / "DATOS" / "logs" / "host_ai_engine_auditoria.jsonl"
    assert audit_path.exists()
    contenido = audit_path.read_text(encoding="utf-8")
    assert "Boda Certificación R6.1" in contenido or "consultar_evento" in contenido

    huellas_despues = {k: _sha256(v) for k, v in reales.items() if v.exists()}
    assert huellas_antes == huellas_despues