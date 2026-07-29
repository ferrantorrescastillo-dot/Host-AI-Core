from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook

from SERVICIOS.biblioteca_escandallos_601 import BibliotecaEscandallos601
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
            "tipo": "PLATO",
            "numero_raciones": 10,
            "ingredientes": ["MP ESC QUESO"],
            "cantidades": ["1 kg"],
            "elaboracion": "Mezclar",
            "tiempo_elaboracion": "10 min",
            "conservacion": "Frio",
            "alergenos": ["lactosa"],
            "observaciones": "",
            "fotografia": "",
        }
    )
    assert out.get("ok") is True


def test_importacion_escandallos_centro_601_texto_excel_en_sandbox(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)

    reales = {
        "articulos": repo_root / "DATOS" / "db" / "articulos.json",
        "proveedores": repo_root / "DATOS" / "db" / "proveedores.json",
        "asociaciones": repo_root / "DATOS" / "db" / "compras_producto_proveedor.json",
        "historico": repo_root / "DATOS" / "facturas" / "historico_precios.json",
    }
    huellas_antes = {k: _sha256(v) for k, v in reales.items() if v.exists()}

    repo_prod = RepositorioProductosMaestro601(tmp_path)
    _ensure_producto(repo_prod, "MP ESC QUESO", 8.0, "kg")
    _ensure_producto(repo_prod, "MP ESC PAN", 2.0, "kg")

    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    _ensure_receta(repo_rec, "REC-ESC-IMPORT", "Escandallo Importado")

    flujo = FlujoImportacionUnificado601(tmp_path)
    servicio_esc = BibliotecaEscandallos601(tmp_path)

    # 1) Texto con escandallo válido + producto inexistente + coste discrepante.
    texto = "\n".join(
        [
            "Escandallo;Receta;Raciones;Producto;Cantidad;Unidad;Merma;Precio;Proveedor;Coste linea;Precio venta;Observaciones",
            "ESC TEXTO 1;Escandallo Importado;10;MP ESC QUESO;1;kg;0;8;PROV TEST;99;20;Linea con coste discrepante",
            "ESC TEXTO 1;Escandallo Importado;10;MP NO EXISTE;1;kg;0;5;PROV TEST;5;20;Linea producto inexistente",
        ]
    )
    doc_texto = flujo.crear_documento_escandallos_desde_texto(texto)
    ctx_texto = flujo.ejecutar(doc_texto)

    assert ctx_texto.get("tipo") == "ESCANDALLOS"
    assert len(ctx_texto.get("modelo_intermedio", [])) == 2
    tipos = {i.get("tipo") for i in ctx_texto.get("incidencias", [])}
    assert "PRODUCTO_INEXISTENTE" in tipos
    assert "COSTE_IMPORTADO_DISCREPANTE" in tipos

    # 2) Resolver una incidencia y dejar otra pendiente.
    respuestas = iter([
        "s",  # Resolver incidencias ahora
        "3",  # Proveedor inexistente -> pendiente
        "1",  # Coste discrepante -> usar sistema
        "3",  # Producto inexistente -> dejar pendiente
        "4",  # Cualquier discrepancia adicional -> pendiente
    ])
    with patch("builtins.input", side_effect=lambda *_: next(respuestas)):
        res_texto = flujo.confirmar_importacion(ctx_texto, guardar_pendientes=False)

    assert res_texto.get("escandallos_guardados", 0) >= 1
    assert len(res_texto.get("incidencias", [])) >= 1

    consulta_texto = servicio_esc.buscar({"nombre": "ESC TEXTO 1"})
    assert consulta_texto.get("total", 0) >= 1

    # 3) Cancelación sin persistencia.
    texto_cancel = "Escandallo;Receta;Raciones;Producto;Cantidad;Unidad\nESC CANCEL;Escandallo Importado;4;MP ESC PAN;1;kg"
    doc_cancel = flujo.crear_documento_escandallos_desde_texto(texto_cancel)
    ctx_cancel = flujo.ejecutar(doc_cancel)

    path_esc = tmp_path / "DATOS" / "db" / "biblioteca_escandallos_601.json"
    antes_cancel = path_esc.read_text(encoding="utf-8") if path_esc.exists() else ""
    cancelado = flujo.cancelar_importacion(ctx_cancel)
    despues_cancel = path_esc.read_text(encoding="utf-8") if path_esc.exists() else ""

    assert cancelado["importacion"]["estado"] == "CANCELADA"
    assert antes_cancel == despues_cancel

    # 4) Excel con dos hojas + mapeo + corrección manual.
    excel = tmp_path / "escandallos_multihoja.xlsx"
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "Hoja_A"
    ws1.append(["Escandallo", "Receta", "Raciones", "Producto", "Cantidad", "UM", "Merma", "Precio compra", "Proveedor", "Importe", "Precio venta", "Observaciones"])
    ws1.append(["ESC EXCEL 1", "Escandallo Importado", "6", "MP ESC PAN", "1", "kg", "0", "2", "PROV TEST", "2", "12", "OK"])

    ws2 = wb.create_sheet("Hoja_B")
    # Cabeceras intencionalmente no estándar para forzar corrección de mapeo.
    ws2.append(["COL_A", "COL_B", "COL_C", "COL_D", "COL_E", "COL_F", "COL_G", "COL_H", "COL_I", "COL_J", "COL_K", "COL_L"])
    ws2.append(["ESC EXCEL 2", "Escandallo Importado", "8", "MP ESC QUESO", "0.5", "kg", "0", "8", "PROV TEST", "4", "20", "OK"])
    wb.save(excel)

    insp = flujo.inspeccionar_excel_escandallos(str(excel))
    assert set(insp.get("hojas", [])) >= {"Hoja_A", "Hoja_B"}

    mapping_manual = {
        "nombre_escandallo": 0,
        "receta": 1,
        "raciones": 2,
        "producto": 3,
        "cantidad": 4,
        "unidad": 5,
        "merma": 6,
        "precio": 7,
        "proveedor": 8,
        "coste_linea": 9,
        "precio_venta": 10,
        "observaciones": 11,
    }
    doc_excel = flujo.crear_documento_escandallos_desde_excel(str(excel), hojas=["Hoja_A", "Hoja_B"], mapping_forzado=mapping_manual)
    ctx_excel = flujo.ejecutar(doc_excel)

    assert ctx_excel.get("tipo") == "ESCANDALLOS"
    assert len(ctx_excel.get("modelo_intermedio", [])) == 2

    with patch("builtins.input", side_effect=["n"]):
        res_excel = flujo.confirmar_importacion(ctx_excel, guardar_pendientes=False)

    assert res_excel.get("escandallos_guardados", 0) >= 1

    consulta_excel = servicio_esc.buscar({"nombre": "ESC EXCEL"})
    assert consulta_excel.get("total", 0) >= 1

    # 5) Conservación de históricos del Centro.
    historial = flujo.repo_importaciones.listar_historial()
    assert len(historial) >= 3
    assert any(h.get("estado") == "CANCELADA" for h in historial)
    assert any(str(h.get("origen") or "").startswith("ESCANDALLOS_") for h in historial)

    # 6) Comprobar que texto y Excel usan el mismo motor (ambos generan escandallos con fecha_calculo y lineas calculadas).
    todos = servicio_esc.ver_todos().get("escandallos", [])
    assert any(str(e.get("nombre") or "").startswith("ESC TEXTO") for e in todos)
    assert any(str(e.get("nombre") or "").startswith("ESC EXCEL") for e in todos)
    assert all("fecha_calculo" in e for e in todos if str(e.get("nombre") or "").startswith("ESC "))

    # 7) Datos reales intactos.
    huellas_despues = {k: _sha256(v) for k, v in reales.items() if v.exists()}
    assert huellas_antes == huellas_despues
