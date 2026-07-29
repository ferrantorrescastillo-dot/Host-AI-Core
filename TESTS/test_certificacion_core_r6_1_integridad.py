from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from SERVICIOS.base_datos_local import BaseDatosLocal
from SERVICIOS.biblioteca_escandallos_601 import RepositorioBibliotecaEscandallos601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.centro_importacion_601 import FlujoImportacionUnificado601, LectorImagen601, LectorPdf601, LectorWord601
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_sandbox(tmp_path: Path, repo_root: Path) -> None:
    db_dir = tmp_path / "DATOS" / "db"
    facturas_dir = tmp_path / "DATOS" / "facturas"
    db_dir.mkdir(parents=True, exist_ok=True)
    facturas_dir.mkdir(parents=True, exist_ok=True)
    for nombre in [
        "articulos.json",
        "proveedores.json",
        "compras_producto_proveedor.json",
        "biblioteca_recetas_601.json",
        "biblioteca_escandallos_601.json",
        "centro_importacion_601.json",
        "menus.json",
    ]:
        origen = repo_root / "DATOS" / "db" / nombre
        destino = db_dir / nombre
        if origen.exists():
            shutil.copy2(origen, destino)
        else:
            if nombre.endswith(".json"):
                destino.write_text("[]", encoding="utf-8")

    hist_origen = repo_root / "DATOS" / "facturas" / "historico_precios.json"
    hist_destino = facturas_dir / "historico_precios.json"
    if hist_origen.exists():
        shutil.copy2(hist_origen, hist_destino)
    else:
        hist_destino.write_text(json.dumps({"version": "3.0.3.5.3", "registros": []}, ensure_ascii=False, indent=2), encoding="utf-8")


def test_certificacion_r61_integridad_persistencia_y_aislamiento(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)

    reales = {
        "articulos": repo_root / "DATOS" / "db" / "articulos.json",
        "proveedores": repo_root / "DATOS" / "db" / "proveedores.json",
        "historico": repo_root / "DATOS" / "facturas" / "historico_precios.json",
        "menus": repo_root / "DATOS" / "db" / "menus.json",
        "eventos": repo_root / "DATOS" / "db" / "eventos.json",
        "planes": repo_root / "DATOS" / "db" / "planes_produccion.json",
    }
    huellas_antes = {k: _sha256(v) for k, v in reales.items() if v.exists()}

    # BaseDatosLocal debe tolerar JSON inválido devolviendo lista vacía.
    db = BaseDatosLocal(tmp_path)
    path_stock = tmp_path / "DATOS" / "db" / "stock_lotes.json"
    path_stock.write_text("{ json roto", encoding="utf-8")
    assert db.cargar("stock_lotes") == []

    # Repositorios 601 deben recuperarse de JSON inválido sin explotar.
    path_rec = tmp_path / "DATOS" / "db" / "biblioteca_recetas_601.json"
    path_esc = tmp_path / "DATOS" / "db" / "biblioteca_escandallos_601.json"
    path_rec.write_text("{ roto", encoding="utf-8")
    path_esc.write_text("{ roto", encoding="utf-8")
    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    repo_esc = RepositorioBibliotecaEscandallos601(tmp_path)
    assert repo_rec.listar() == []
    assert repo_esc.listar() == []

    # Repositorio maestro: crear y archivar sin eliminación física.
    repo_prod = RepositorioProductosMaestro601(tmp_path)
    producto = repo_prod.crear_producto(
        {
            "nombre": "MP CERT R61",
            "familia": "TEST",
            "unidad_base": "kg",
            "unidad_compra": "kg",
            "precio": "2.5",
            "proveedor": "PROV CERT",
            "proveedor_preferente": "PROV CERT",
            "fecha_precio": "2026-07-23",
        }
    )
    archivado = repo_prod.archivar_producto(str(producto.get("codigo") or ""))
    assert str(archivado.get("estado") or "") == "ARCHIVADO"
    assert repo_prod.obtener_producto(str(producto.get("codigo") or "")) is not None

    # Escrituras 601 atómicas: no deben quedar .tmp huérfanos tras guardar.
    _ = repo_rec.crear(
        {
            "codigo": "REC-CERT-R61",
            "nombre": "Receta Cert R61",
            "familia": "TEST",
            "tipo": "PRINCIPAL",
            "numero_raciones": 4,
            "ingredientes": ["MP CERT R61"],
            "cantidades": ["1 kg"],
            "elaboracion": "Preparar.",
            "tiempo_elaboracion": "10 min",
            "conservacion": "Frio",
            "alergenos": ["ninguno"],
            "observaciones": "",
            "fotografia": "",
        }
    )
    assert not list((tmp_path / "DATOS" / "db").glob("*.tmp"))

    huellas_despues = {k: _sha256(v) for k, v in reales.items() if v.exists()}
    assert huellas_antes == huellas_despues


def test_certificacion_r61_importadores_informan_limitaciones_honestas(tmp_path: Path) -> None:
    flujo = FlujoImportacionUnificado601(tmp_path)
    lector_word = LectorWord601().leer("C:/fake/doc.docx")
    lector_pdf = LectorPdf601().leer("C:/fake/file.pdf")
    lector_img = LectorImagen601().leer("C:/fake/img.jpg")

    assert any("pendiente" in a.lower() for a in lector_word.advertencias)
    assert any("pendiente" in a.lower() for a in lector_pdf.advertencias)
    assert any("pendiente" in a.lower() for a in lector_img.advertencias)

    doc = flujo.crear_documento_menus_desde_texto("Menu: MENU HONESTO\nPrincipales: Plato demo")
    ctx = flujo.ejecutar(doc)
    cancelada = flujo.cancelar_importacion(ctx)
    assert str((cancelada.get("importacion") or {}).get("estado") or "") == "CANCELADA"