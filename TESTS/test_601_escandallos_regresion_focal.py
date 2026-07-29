from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from SERVICIOS.biblioteca_escandallos_601 import BibliotecaEscandallos601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_sandbox(tmp_path: Path, repo_root: Path) -> dict[str, Path]:
    db_dir = tmp_path / "DATOS" / "db"
    facturas_dir = tmp_path / "DATOS" / "facturas"
    db_dir.mkdir(parents=True, exist_ok=True)
    facturas_dir.mkdir(parents=True, exist_ok=True)

    archivos_db = ["articulos.json", "proveedores.json", "compras_producto_proveedor.json"]
    for nombre in archivos_db:
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

    return {
        "articulos": db_dir / "articulos.json",
        "proveedores": db_dir / "proveedores.json",
        "asociaciones": db_dir / "compras_producto_proveedor.json",
        "historico": facturas_dir / "historico_precios.json",
    }


def _ensure_producto_basico(repo_prod: RepositorioProductosMaestro601, *, nombre: str, precio: float, unidad: str = "kg") -> str:
    existente = repo_prod.buscar_productos({"nombre": nombre})
    if existente:
        return str(existente[0].get("codigo") or "")

    creado = repo_prod.crear_producto(
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
            "observaciones": "Producto de test sandbox",
        }
    )
    return str(creado.get("codigo") or "")


def _seed_receta(repo_rec: RepositorioBibliotecaRecetas601, *, codigo: str = "REC-ESC-TEST") -> str:
    ex = repo_rec.obtener(codigo)
    if ex:
        return str(ex.get("codigo") or "")

    res = repo_rec.crear(
        {
            "codigo": codigo,
            "nombre": "Receta Escandallo Test",
            "familia": "PRUEBAS",
            "tipo": "ENTRANTE",
            "numero_raciones": 10,
            "ingredientes": ["MP ESC PATATA", "MP ESC MAYONESA"],
            "cantidades": ["2 kg", "0.5 kg"],
            "elaboracion": "Mezclar y reposar.",
            "tiempo_elaboracion": "30 min",
            "conservacion": "Frio",
            "alergenos": ["huevo"],
            "observaciones": "Receta de test",
            "fotografia": "",
        }
    )
    assert res.get("ok") is True
    return codigo


def test_regresion_focal_escandallos_601_en_sandbox(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    rutas = _seed_sandbox(tmp_path, repo_root)

    reales = {
        "articulos": repo_root / "DATOS" / "db" / "articulos.json",
        "proveedores": repo_root / "DATOS" / "db" / "proveedores.json",
        "asociaciones": repo_root / "DATOS" / "db" / "compras_producto_proveedor.json",
        "historico": repo_root / "DATOS" / "facturas" / "historico_precios.json",
    }
    huellas_antes = {k: _sha256(v) for k, v in reales.items() if v.exists()}

    repo_prod = RepositorioProductosMaestro601(tmp_path)
    cod_patata = _ensure_producto_basico(repo_prod, nombre="MP ESC PATATA", precio=2.0, unidad="kg")
    cod_mayo = _ensure_producto_basico(repo_prod, nombre="MP ESC MAYONESA", precio=4.0, unidad="kg")

    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    cod_receta = _seed_receta(repo_rec)

    servicio = BibliotecaEscandallos601(tmp_path)

    # 1) Generar desde receta.
    gen = servicio.generar_desde_receta(cod_receta, precio_venta_total=60.0)
    assert gen.get("ok") is True
    assert gen.get("guardado") is True
    esc = gen.get("escandallo") or {}
    esc_id = str(esc.get("id") or "")
    assert esc_id.startswith("ESC601-")
    assert float(esc.get("coste_total") or 0.0) > 0

    # 2) Buscar y detalle.
    busq = servicio.buscar({"nombre": "Receta Escandallo Test"})
    assert busq.get("total", 0) >= 1
    det = servicio.ver_detalle(esc_id)
    assert det.get("ok") is True

    # 3) Duplicar.
    dup = servicio.duplicar(esc_id)
    assert dup.get("ok") is True
    assert str((dup.get("escandallo") or {}).get("id")) != esc_id

    # 4) Recalcular simulación (opción 4) sin persistir.
    sim = servicio.recalcular(esc_id, 4)
    assert sim.get("ok") is True
    assert sim.get("simulacion") is True
    assert float((sim.get("resumen") or {}).get("coste_nuevo") or 0) > 0

    # 5) Recalcular persistiendo (opción 1 con precios actuales).
    recalc = servicio.recalcular(esc_id, 1)
    assert recalc.get("ok") is True
    assert recalc.get("simulacion") is False

    # 6) Historial de cálculos.
    hist = servicio.historial_calculos(esc_id)
    assert hist.get("ok") is True
    assert hist.get("total", 0) >= 1

    # 7) Editar escandallo.
    edit = servicio.editar(
        esc_id,
        {
            "numero_raciones": 8,
            "lineas": [
                {
                    "producto_codigo": cod_patata,
                    "producto": "MP ESC PATATA",
                    "cantidad_texto": "2 kg",
                    "unidad_receta": "kg",
                    "merma_especifica": 5,
                },
                {
                    "producto_codigo": cod_mayo,
                    "producto": "MP ESC MAYONESA",
                    "cantidad_texto": "0.4 kg",
                    "unidad_receta": "kg",
                    "merma_especifica": 0,
                },
            ],
        },
    )
    assert edit.get("ok") is True
    esc_edit = edit.get("escandallo") or {}
    assert float(esc_edit.get("numero_raciones") or 0) == 8

    # 8) Generación de pendientes (preview).
    pendientes = servicio.generar_pendientes(confirmar=False)
    assert pendientes.get("ok") is True
    assert "pendientes" in pendientes

    # 9) Escandallos con incidencias (puede ser 0 o más, pero estructura estable).
    inc = servicio.escandallos_con_incidencias()
    assert inc.get("ok") is True
    assert "escandallos" in inc

    # 10) Archivar.
    arch = servicio.archivar(esc_id)
    assert arch.get("ok") is True
    assert str((arch.get("escandallo") or {}).get("estado")) == "ARCHIVADO"

    # 11) Comprobación de persistencia en sandbox.
    path_esc = tmp_path / "DATOS" / "db" / "biblioteca_escandallos_601.json"
    payload = json.loads(path_esc.read_text(encoding="utf-8"))
    assert isinstance(payload.get("escandallos"), list)
    assert isinstance(payload.get("historial_calculos"), list)
    assert len(payload.get("escandallos") or []) >= 2

    # 12) Datos reales intactos.
    huellas_despues = {k: _sha256(v) for k, v in reales.items() if v.exists()}
    assert huellas_antes == huellas_despues

    # 13) Sandbox modificado.
    assert path_esc.exists()
    assert path_esc.stat().st_size > 0
