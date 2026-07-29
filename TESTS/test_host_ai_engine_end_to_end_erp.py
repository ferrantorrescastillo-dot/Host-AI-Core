from __future__ import annotations

import json
import shutil
from pathlib import Path

from SERVICIOS.biblioteca_escandallos_601 import BibliotecaEscandallos601
from SERVICIOS.biblioteca_menus_601 import BibliotecaMenus601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.host_ai_engine import HostAIEngine
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


def _seed_sandbox(tmp_path: Path, repo_root: Path) -> None:
    db_dir = tmp_path / "DATOS" / "db"
    facturas_dir = tmp_path / "DATOS" / "facturas"
    db_dir.mkdir(parents=True, exist_ok=True)
    facturas_dir.mkdir(parents=True, exist_ok=True)

    for nombre in ["articulos.json", "proveedores.json", "compras_producto_proveedor.json", "menus.json"]:
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


def _ensure_producto(repo: RepositorioProductosMaestro601, nombre: str, precio: float, unidad: str = "kg") -> str:
    encontrados = repo.buscar_productos({"nombre": nombre})
    if encontrados:
        return str(encontrados[0].get("codigo") or "")
    creado = repo.crear_producto(
        {
            "nombre": nombre,
            "familia": "TEST",
            "unidad_base": unidad,
            "unidad_compra": unidad,
            "precio": str(precio),
            "proveedor": "PROV TEST",
            "proveedor_preferente": "PROV TEST",
            "fecha_precio": "2026-07-23",
            "iva": "10",
        }
    )
    return str(creado.get("codigo") or "")


def _ensure_receta(repo: RepositorioBibliotecaRecetas601, codigo: str, nombre: str, ingrediente: str = "MP ERP TOMATE") -> str:
    actual = repo.obtener(codigo)
    if actual:
        return str(actual.get("codigo") or codigo)
    out = repo.crear(
        {
            "codigo": codigo,
            "nombre": nombre,
            "familia": "ERP",
            "tipo": "PRINCIPAL",
            "numero_raciones": 10,
            "ingredientes": [ingrediente],
            "cantidades": ["1 kg"],
            "elaboracion": "Mezclar y servir",
            "tiempo_elaboracion": "10 min",
            "conservacion": "Frio",
            "alergenos": [],
            "observaciones": "",
            "fotografia": "",
        }
    )
    assert out.get("ok") is True
    return codigo


def _confirmacion(resultado: dict, alcance: dict | None = None, estado: str = "ACEPTADA") -> dict:
    conf = dict((resultado.get("confirmaciones_requeridas") or [])[0])
    conf["estado"] = estado
    conf["usuario_que_responde"] = "chef"
    conf["fecha_respuesta"] = "2026-07-23T10:00:00"
    conf["alcance_autorizado"] = dict(alcance or {})
    return conf


def _resultado_paso_por_operacion(resultado: dict, operacion: str) -> dict:
    pasos = list(resultado.get("pasos") or [])
    mapa = dict(((resultado.get("resultado") or {}).get("resultados_por_paso") or {}))
    for paso in pasos:
        if str(paso.get("operacion") or "") == operacion:
            return dict(mapa.get(paso.get("orden")) or {})
    return {}


def _texto_importacion_recetas() -> str:
    return "\n".join(
        [
            "Receta: RECETA ERP UNO",
            "Raciones: 10",
            "MP ERP TOMATE: 1 kg",
            "MP ERP QUESO: 0.5 kg",
            "Elaboracion: Mezclar.",
            "",
            "Receta: RECETA ERP DOS",
            "Raciones: 8",
            "MP ERP TOMATE: 0.8 kg",
            "MP ERP QUESO: 0.4 kg",
            "Elaboracion: Hornear.",
        ]
    )


def test_end_to_end_caso_1_importar_recetas_hasta_menus(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)
    repo_prod = RepositorioProductosMaestro601(tmp_path)
    _ensure_producto(repo_prod, "MP ERP TOMATE", 2.5)
    _ensure_producto(repo_prod, "MP ERP QUESO", 6.0)

    menus = BibliotecaMenus601(tmp_path)
    pre_menu = menus.nuevo_menu(
        {
            "nombre": "MENU ERP PLACEHOLDER",
            "tipo": "EVENTO",
            "comensales_recomendado": 20,
            "precio_venta_comensal": 18,
            "composicion": {
                "Aperitivos": [],
                "Entrantes": [],
                "Principales": [{"tipo_referencia": "RECETA", "referencia": "RECETA ERP UNO", "cantidad": 1}],
                "Postres": [],
                "Bodega": [],
                "Extras": [],
            },
        }
    )
    assert pre_menu.get("ok") is True

    engine = HostAIEngine(tmp_path)
    previo = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["importar", "resolver_catalogo", "revisar_incidencias", "crear_recetas", "generar_escandallos", "detectar_menus_afectados", "actualizar_menus_afectados"],
            "texto_importacion": _texto_importacion_recetas(),
            "origen_documento": "WORD",
            "modo_operacion": "EJECUTAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Importar recetas y actualizar menús afectados",
    )
    assert str(previo.get("estado") or "") == "ESPERANDO_CONFIRMACION"

    final = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["importar", "resolver_catalogo", "revisar_incidencias", "crear_recetas", "generar_escandallos", "detectar_menus_afectados", "actualizar_menus_afectados"],
            "texto_importacion": _texto_importacion_recetas(),
            "origen_documento": "WORD",
            "modo_operacion": "EJECUTAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Importar recetas y actualizar menús afectados",
        confirmaciones_recibidas=[_confirmacion(previo)],
    )

    assert str(final.get("estado") or "") == "COMPLETADA"
    resumen = final.get("resultado") or {}
    assert len(resumen.get("objetos_creados") or []) >= 4
    assert any(str(x.get("tipo") or "") == "menu" for x in list(resumen.get("objetos_modificados") or []))


def test_end_to_end_caso_2_cambio_precio_detecta_impacto_y_actualiza(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)
    repo_prod = RepositorioProductosMaestro601(tmp_path)
    cod_tomate = _ensure_producto(repo_prod, "MP ERP TOMATE", 2.5)

    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    _ensure_receta(repo_rec, "REC-ERP-PRICE", "RECETA ERP PRICE")
    esc = BibliotecaEscandallos601(tmp_path)
    gen = esc.generar_desde_receta("REC-ERP-PRICE", precio_venta_total=20)
    assert gen.get("ok") is True
    esc_data = gen.get("escandallo") or {}
    esc_ref = str(esc_data.get("codigo") or esc_data.get("id") or "")

    menus = BibliotecaMenus601(tmp_path)
    creado = menus.nuevo_menu(
        {
            "nombre": "MENU ERP PRECIO",
            "tipo": "EVENTO",
            "comensales_recomendado": 10,
            "precio_venta_comensal": 15,
            "composicion": {
                "Aperitivos": [],
                "Entrantes": [],
                "Principales": [{"tipo_referencia": "ESCANDALLO", "referencia": esc_ref, "cantidad": 1}],
                "Postres": [],
                "Bodega": [],
                "Extras": [],
            },
        }
    )
    assert creado.get("ok") is True

    engine = HostAIEngine(tmp_path)
    previo = engine.consultar(
        origen="Catalogo",
        modulo="catalogo",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["modificar_precio", "detectar_escandallos_afectados", "detectar_menus_afectados", "recalcular_escandallos", "actualizar_menus_afectados"],
            "producto_codigo": cod_tomate,
            "producto_nombre": "MP ERP TOMATE",
            "precio": 4.2,
            "modo_operacion": "EJECUTAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Cambiar precio del tomate y actualizar impactos",
    )
    assert str(previo.get("estado") or "") == "ESPERANDO_CONFIRMACION"

    final = engine.consultar(
        origen="Catalogo",
        modulo="catalogo",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["modificar_precio", "detectar_escandallos_afectados", "detectar_menus_afectados", "recalcular_escandallos", "actualizar_menus_afectados"],
            "producto_codigo": cod_tomate,
            "producto_nombre": "MP ERP TOMATE",
            "precio": 4.2,
            "modo_operacion": "EJECUTAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Cambiar precio del tomate y actualizar impactos",
        confirmaciones_recibidas=[_confirmacion(previo)],
    )

    assert str(final.get("estado") or "") == "COMPLETADA"
    resumen = final.get("resultado") or {}
    assert any(str(x.get("tipo") or "") == "producto" for x in list(resumen.get("objetos_modificados") or []))
    assert any(str(x.get("tipo") or "") == "escandallo" for x in list(resumen.get("objetos_modificados") or []))


def test_end_to_end_caso_3_nuevo_menu_con_simulacion_y_ejecucion(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)
    repo_prod = RepositorioProductosMaestro601(tmp_path)
    _ensure_producto(repo_prod, "MP ERP TOMATE", 2.5)
    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    _ensure_receta(repo_rec, "REC-ERP-MENU", "RECETA ERP MENU")
    esc = BibliotecaEscandallos601(tmp_path)
    gen = esc.generar_desde_receta("REC-ERP-MENU", precio_venta_total=20)
    assert gen.get("ok") is True
    esc_data = gen.get("escandallo") or {}
    esc_ref = str(esc_data.get("codigo") or esc_data.get("id") or "")

    engine = HostAIEngine(tmp_path)
    simulacion = engine.consultar(
        origen="Menus",
        modulo="menus",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["crear_menu", "calcular_coste_menu", "registrar_historico_menu"],
            "nombre_menu": "MENU ERP NUEVO",
            "recetas": ["REC-ERP-MENU"],
            "escandallos": [esc_ref],
            "comensales": 25,
            "precio_venta_comensal": 22,
            "modo_operacion": "SIMULAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Nuevo menú con cálculo",
    )
    assert str(simulacion.get("estado") or "") == "COMPLETADA"
    assert list(simulacion.get("acciones_propuestas") or [])

    previo = engine.consultar(
        origen="Menus",
        modulo="menus",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["crear_menu", "calcular_coste_menu", "registrar_historico_menu"],
            "nombre_menu": "MENU ERP NUEVO",
            "recetas": ["REC-ERP-MENU"],
            "escandallos": [esc_ref],
            "comensales": 25,
            "precio_venta_comensal": 22,
            "modo_operacion": "EJECUTAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Nuevo menú con cálculo",
    )
    final = engine.consultar(
        origen="Menus",
        modulo="menus",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["crear_menu", "calcular_coste_menu", "registrar_historico_menu"],
            "nombre_menu": "MENU ERP NUEVO",
            "recetas": ["REC-ERP-MENU"],
            "escandallos": [esc_ref],
            "comensales": 25,
            "precio_venta_comensal": 22,
            "modo_operacion": "EJECUTAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Nuevo menú con cálculo",
        confirmaciones_recibidas=[_confirmacion(previo)],
    )
    assert str(final.get("estado") or "") == "COMPLETADA"
    resumen = final.get("resultado") or {}
    assert any(str(x.get("tipo") or "") == "menu" for x in list(resumen.get("objetos_creados") or []))
    assert any(str(x.get("tipo") or "") == "menu_historico" for x in list(resumen.get("objetos_modificados") or []))


def test_end_to_end_caso_4_nueva_receta_hasta_pendiente_de_menu(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)
    repo_prod = RepositorioProductosMaestro601(tmp_path)
    _ensure_producto(repo_prod, "MP ERP TOMATE", 2.5)
    _ensure_producto(repo_prod, "MP ERP QUESO", 6.0)

    engine = HostAIEngine(tmp_path)
    previo = engine.consultar(
        origen="Recetas",
        modulo="recetas",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["nueva_receta", "pendiente_menu"],
            "texto_importacion": "Receta: RECETA ERP NUEVA\nRaciones: 5\nMP ERP TOMATE: 1 kg\nMP ERP QUESO: 0.2 kg\nElaboracion: Mezclar.",
            "origen_documento": "TEXTO",
            "modo_operacion": "EJECUTAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Nueva receta con escandallo y pendiente de menú",
    )
    assert str(previo.get("estado") or "") == "ESPERANDO_CONFIRMACION"

    final = engine.consultar(
        origen="Recetas",
        modulo="recetas",
        tipo_peticion="orquestar_erp",
        datos_enviados={
            "objetivos": ["nueva_receta", "pendiente_menu"],
            "texto_importacion": "Receta: RECETA ERP NUEVA\nRaciones: 5\nMP ERP TOMATE: 1 kg\nMP ERP QUESO: 0.2 kg\nElaboracion: Mezclar.",
            "origen_documento": "TEXTO",
            "modo_operacion": "EJECUTAR",
        },
        usar_director=True,
        usuario="chef",
        texto_original="Nueva receta con escandallo y pendiente de menú",
        confirmaciones_recibidas=[_confirmacion(previo)],
    )
    assert str(final.get("estado") or "") == "COMPLETADA"
    paso_final = _resultado_paso_por_operacion(final, "detectar_pendiente_menu")
    assert paso_final.get("pendiente_menu") is True