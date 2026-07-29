from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from SERVICIOS.biblioteca_escandallos_601 import BibliotecaEscandallos601
from SERVICIOS.biblioteca_menus_601 import BibliotecaMenus601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.centro_importacion_601 import FlujoImportacionUnificado601
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_sandbox(tmp_path: Path, repo_root: Path) -> None:
    db_dir = tmp_path / "DATOS" / "db"
    facturas_dir = tmp_path / "DATOS" / "facturas"
    db_dir.mkdir(parents=True, exist_ok=True)
    facturas_dir.mkdir(parents=True, exist_ok=True)

    for nombre in ["articulos.json", "proveedores.json", "compras_producto_proveedor.json"]:
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


def _ensure_producto(repo: RepositorioProductosMaestro601, nombre: str, precio: float, unidad: str = "kg") -> None:
    if repo.buscar_productos({"nombre": nombre}):
        return
    repo.crear_producto(
        {
            "nombre": nombre,
            "familia": "TEST",
            "unidad_base": unidad,
            "unidad_compra": unidad,
            "precio": str(precio),
            "proveedor": "PROV TEST",
            "proveedor_preferente": "PROV TEST",
            "fecha_precio": "2026-07-22",
            "iva": "10",
        }
    )


def _ensure_receta(repo: RepositorioBibliotecaRecetas601, codigo: str, nombre: str) -> None:
    if repo.obtener(codigo):
        return
    out = repo.crear(
        {
            "codigo": codigo,
            "nombre": nombre,
            "familia": "PRUEBAS",
            "tipo": "PRINCIPAL",
            "numero_raciones": 10,
            "ingredientes": ["MP MENU ARROZ"],
            "cantidades": ["1 kg"],
            "elaboracion": "Cocer y servir",
            "tiempo_elaboracion": "30 min",
            "conservacion": "Caliente",
            "alergenos": [],
            "observaciones": "",
            "fotografia": "",
        }
    )
    assert out.get("ok") is True


def test_regresion_focal_biblioteca_menus_601_en_sandbox(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)

    reales = {
        "articulos": repo_root / "DATOS" / "db" / "articulos.json",
        "proveedores": repo_root / "DATOS" / "db" / "proveedores.json",
        "asociaciones": repo_root / "DATOS" / "db" / "compras_producto_proveedor.json",
        "historico": repo_root / "DATOS" / "facturas" / "historico_precios.json",
        "menus": repo_root / "DATOS" / "db" / "menus.json",
    }
    huellas_antes = {k: _sha256(v) for k, v in reales.items() if v.exists()}

    repo_prod = RepositorioProductosMaestro601(tmp_path)
    _ensure_producto(repo_prod, "MP MENU ARROZ", 3.0)
    _ensure_producto(repo_prod, "MP MENU BEBIDA", 1.5, "u")

    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    _ensure_receta(repo_rec, "REC-MENU-601", "Receta Menu 601")

    servicio_esc = BibliotecaEscandallos601(tmp_path)
    generado = servicio_esc.generar_desde_receta("REC-MENU-601", precio_venta_total=80.0)
    assert generado.get("ok") is True
    esc = generado.get("escandallo") or {}
    esc_ref = str(esc.get("codigo") or esc.get("id") or "")
    assert esc_ref

    menus = BibliotecaMenus601(tmp_path)

    nuevo = menus.nuevo_menu(
        {
            "nombre": "MENU PILOTO 601",
            "tipo": "BODA",
            "familia": "EVENTO",
            "comensales_recomendado": 20,
            "precio_venta_comensal": 18.0,
            "composicion": {
                "Aperitivos": [{"tipo_referencia": "PRODUCTO", "referencia": "MP MENU BEBIDA", "cantidad": 1}],
                "Entrantes": [],
                "Principales": [{"tipo_referencia": "ESCANDALLO", "referencia": esc_ref, "cantidad": 1}],
                "Postres": [],
                "Bodega": [],
                "Extras": [],
            },
        }
    )
    assert nuevo.get("ok") is True
    menu = nuevo.get("menu") or {}
    menu_id = str(menu.get("menu_id") or "")
    assert menu_id.startswith("MENU601-")
    assert str(menu.get("modelo_biblioteca") or "") == "MENU_601"

    busq = menus.buscar({"nombre": "PILOTO 601"})
    assert busq.get("ok") is True
    assert busq.get("total", 0) >= 1

    detalle = menus.ver_detalle(menu_id)
    assert detalle.get("ok") is True
    assert isinstance((detalle.get("menu") or {}).get("lineas"), list)

    edit = menus.editar_menu(menu_id, {"comensales_recomendado": 25})
    assert edit.get("ok") is True
    assert float((edit.get("menu") or {}).get("comensales_recomendado") or 0) == 25

    dup = menus.duplicar_menu(menu_id)
    assert dup.get("ok") is True
    assert str((dup.get("menu") or {}).get("menu_id") or "") != menu_id

    gen_menu = menus.generar_escandallo_menu(menu_id)
    assert gen_menu.get("ok") is True

    rent = menus.rentabilidad(menu_id)
    assert rent.get("ok") is True
    assert "margen_porcentual" in (rent.get("rentabilidad") or {})

    hist = menus.historial(menu_id)
    assert hist.get("ok") is True
    assert hist.get("total", 0) >= 1

    # Fuerza desactualización del snapshot del menú al cambiar el escandallo asociado.
    _ = servicio_esc.editar(
        str(esc.get("id") or esc.get("codigo") or ""),
        {
            "numero_raciones": 12,
            "lineas": [
                {
                    "producto": "MP MENU ARROZ",
                    "cantidad_texto": "1.2 kg",
                    "unidad_receta": "kg",
                    "merma_especifica": 0,
                }
            ],
        },
    )
    det2 = menus.ver_detalle(menu_id)
    assert det2.get("ok") is True
    assert str((det2.get("menu") or {}).get("estado") or "") in {"DESACTUALIZADO", "CON_INCIDENCIAS", "OPERATIVO"}

    arch = menus.archivar_menu(menu_id)
    assert arch.get("ok") is True
    assert str((arch.get("menu") or {}).get("estado") or "") == "ARCHIVADO"

    path_menus = tmp_path / "DATOS" / "db" / "menus.json"
    payload = json.loads(path_menus.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert any(str(m.get("modelo_biblioteca") or "") == "MENU_601" for m in payload)

    huellas_despues = {k: _sha256(v) for k, v in reales.items() if v.exists()}
    assert huellas_antes == huellas_despues


def test_importacion_menus_601_centro_texto_en_sandbox(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)

    repo_prod = RepositorioProductosMaestro601(tmp_path)
    _ensure_producto(repo_prod, "MP MENU ARROZ", 3.0)

    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    _ensure_receta(repo_rec, "REC-MENU-IMPORT", "Receta Menu Import")

    servicio_esc = BibliotecaEscandallos601(tmp_path)
    generado = servicio_esc.generar_desde_receta("REC-MENU-IMPORT", precio_venta_total=40.0)
    assert generado.get("ok") is True

    flujo = FlujoImportacionUnificado601(tmp_path)
    texto = "\n".join(
        [
            "Menu: MENU IMPORT 601",
            "Tipo: EMPRESA",
            "Comensales: 30",
            "Precio: 22",
            "Principales: Receta Menu Import",
            "Postres: ESCANDALLO NO EXISTE",
            "",
            "Menu: MENU IMPORT 601 B",
            "Comensales: 10",
            "Principales: Receta Menu Import",
        ]
    )

    doc = flujo.crear_documento_menus_desde_texto(texto)
    ctx = flujo.ejecutar(doc)

    assert ctx.get("tipo") == "MENUS"
    assert len(ctx.get("modelo_intermedio", [])) == 2
    tipos = {i.get("tipo") for i in ctx.get("incidencias", [])}
    assert "ESCANDALLO_INEXISTENTE" in tipos or "PLATO_INEXISTENTE" in tipos

    res = flujo.confirmar_importacion(ctx, guardar_pendientes=False)
    assert str((res.get("importacion") or {}).get("estado") or "") == "CON_INCIDENCIAS"
    assert res.get("menus_guardados", 0) >= 1

    biblioteca = BibliotecaMenus601(tmp_path)
    consulta = biblioteca.buscar({"nombre": "MENU IMPORT 601"})
    assert consulta.get("ok") is True
    assert consulta.get("total", 0) >= 1
