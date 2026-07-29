from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook

from SERVICIOS.catalogo_maestro_productos_601 import (
    CatalogoMaestroProductos601,
    CatalogoMaestroProductosUI601,
)
from SERVICIOS.centro_importacion_601 import CentroImportacionUI601
from SERVICIOS.centro_importacion_601 import (
    DocumentoImportacion601,
    FlujoImportacionUnificado601,
    LectorExcel601,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _preparar_sandbox(tmp_path: Path, repo_root: Path) -> dict[str, Path]:
    db_dir = tmp_path / "DATOS" / "db"
    facturas_dir = tmp_path / "DATOS" / "facturas"
    db_dir.mkdir(parents=True, exist_ok=True)
    facturas_dir.mkdir(parents=True, exist_ok=True)

    archivos = {
        "articulos": "articulos.json",
        "proveedores": "proveedores.json",
        "asociaciones": "compras_producto_proveedor.json",
    }
    for _, nombre in archivos.items():
        origen = repo_root / "DATOS" / "db" / nombre
        destino = db_dir / nombre
        if origen.exists():
            shutil.copy2(origen, destino)
        else:
            destino.write_text("[]", encoding="utf-8")

    historico_origen = repo_root / "DATOS" / "facturas" / "historico_precios.json"
    historico_destino = facturas_dir / "historico_precios.json"
    if historico_origen.exists():
        shutil.copy2(historico_origen, historico_destino)
    else:
        historico_destino.write_text(json.dumps({"version": "3.0.3.5.3", "registros": []}, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "articulos": db_dir / "articulos.json",
        "proveedores": db_dir / "proveedores.json",
        "asociaciones": db_dir / "compras_producto_proveedor.json",
        "historico": facturas_dir / "historico_precios.json",
    }


def test_regresion_focal_catalogo_maestro_601_en_sandbox(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    rutas = _preparar_sandbox(tmp_path, repo_root)

    # Huellas de datos reales para verificar que no se alteran.
    reales = {
        "articulos": repo_root / "DATOS" / "db" / "articulos.json",
        "proveedores": repo_root / "DATOS" / "db" / "proveedores.json",
        "asociaciones": repo_root / "DATOS" / "db" / "compras_producto_proveedor.json",
        "historico": repo_root / "DATOS" / "facturas" / "historico_precios.json",
    }
    huellas_antes = {k: _sha256(v) for k, v in reales.items() if v.exists()}

    catalogo = CatalogoMaestroProductos601(tmp_path)
    ui = CatalogoMaestroProductosUI601(catalogo, base_dir=tmp_path)
    assert ui is not None

    # 1) Crear producto manual.
    alta = catalogo.crear(
        {
            "nombre": "MP TEST 601 EXISTENTE",
            "familia": "VERDURAS",
            "unidad_base": "kg",
            "unidad_compra": "kg",
            "precio": "10.50",
            "proveedor": "PROVEEDOR TEST 601",
            "proveedor_preferente": "PROVEEDOR TEST 601",
            "fecha_precio": "2026-07-22",
            "observaciones": "Alta manual en sandbox",
        }
    )
    assert alta["ok"] is True
    codigo = alta["producto"]["codigo"]

    # 2) Buscar producto.
    busqueda = catalogo.buscar({"nombre": "MP TEST 601 EXISTENTE"})
    assert busqueda["total"] >= 1

    # 3) Editar producto.
    edicion = catalogo.editar(codigo, {"marca": "MARCA TEST", "subfamilia": "HOJA", "observaciones": "Editado"})
    assert edicion["ok"] is True
    assert edicion["producto"].get("marca") == "MARCA TEST"

    # 4) Añadir precio nuevo conservando anterior (histórico).
    precio_nuevo = catalogo.registrar_precio_manual(
        {
            "codigo": codigo,
            "precio": "12.80",
            "unidad": "kg",
            "proveedor": "PROVEEDOR TEST 601",
            "fecha": "2026-07-23",
            "preferente": True,
        }
    )
    assert precio_nuevo["ok"] is True

    detalle = catalogo.obtener(codigo)
    historico = detalle.get("historico_precios", [])
    precios_producto = [float(r.get("precio") or 0) for r in historico if str(r.get("articulo_id") or "") == codigo]
    assert any(abs(p - 10.5) < 1e-6 for p in precios_producto)
    assert any(abs(p - 12.8) < 1e-6 for p in precios_producto)

    # 5) Archivar producto.
    archivado = catalogo.archivar(codigo)
    assert archivado["ok"] is True
    assert archivado["producto"].get("estado") == "ARCHIVADO"

    flujo = FlujoImportacionUnificado601(tmp_path)

    # 6) Importar texto con casuísticas.
    texto = "\n".join(
        [
            "Receta: DUPLICADA TEST 601",
            "MP TEST 601 EXISTENTE:",
            "Elaboracion: Primera versión",
            "Receta: DUPLICADA TEST 601",
            "MP TEST 601 EXISTENTE: 1 kg",
            "MP TEST 601 NUEVO: 2 kg",
            "Elaboracion: Segunda versión",
        ]
    )
    contexto = flujo.ejecutar(DocumentoImportacion601(origen="TEXTO", etiqueta_origen="sandbox", texto=texto))

    tipos = {i.get("tipo") for i in contexto.get("incidencias", [])}
    assert "PRODUCTO_INEXISTENTE" in tipos
    assert "PRODUCTO_SIN_PRECIO" in tipos
    assert "PRODUCTO_DUPLICADO" in tipos
    assert "PROVEEDOR_INEXISTENTE" in tipos
    assert "INGREDIENTE_SIN_CANTIDAD" in tipos

    # Resolver una incidencia y dejar otras pendientes.
    respuestas = iter(["s", "2", "3", "3", "4", "3"])
    with patch("builtins.input", side_effect=lambda *_: next(respuestas)):
        resultado_confirmacion = flujo.confirmar_importacion(contexto)

    estados = [str(i.get("estado") or "") for i in contexto.get("incidencias", [])]
    assert "RESUELTA" in estados
    assert "PENDIENTE" in estados
    assert resultado_confirmacion["importacion"]["estado"] in {"COMPLETADA", "CON_INCIDENCIAS"}

    # 7) Cancelar una segunda importación y verificar no persistencia de cambios funcionales.
    recetas_path = tmp_path / "DATOS" / "db" / "biblioteca_recetas_601.json"
    recetas_antes = recetas_path.read_text(encoding="utf-8") if recetas_path.exists() else ""

    contexto_cancel = flujo.ejecutar(
        DocumentoImportacion601(
            origen="TEXTO",
            etiqueta_origen="sandbox_cancel",
            texto="Receta: CANCELADA TEST 601\nMP TEST 601 EXISTENTE: 1 kg\nElaboracion: No debe persistir",
        )
    )
    cancelada = flujo.cancelar_importacion(contexto_cancel)
    assert cancelada["importacion"]["estado"] == "CANCELADA"

    recetas_despues = recetas_path.read_text(encoding="utf-8") if recetas_path.exists() else ""
    assert recetas_antes == recetas_despues

    # 8) Importar Excel temporal con mismas casuísticas.
    excel_path = tmp_path / "casuisticas_601.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Importacion"
    ws.append(["Receta: DUPLICADA EXCEL 601"])
    ws.append(["MP TEST 601 EXISTENTE", ""])
    ws.append(["Elaboracion", "Versión A"])
    ws.append(["Receta: DUPLICADA EXCEL 601"])
    ws.append(["MP TEST 601 EXISTENTE", "1 kg"])
    ws.append(["MP TEST 601 NUEVO EXCEL", "2 kg"])
    ws.append(["Elaboracion", "Versión B"])
    wb.save(excel_path)

    lector_excel = LectorExcel601()
    documento_excel = lector_excel.leer(str(excel_path))
    assert documento_excel.texto.strip() != ""

    contexto_excel = flujo.ejecutar(documento_excel)
    tipos_excel = {i.get("tipo") for i in contexto_excel.get("incidencias", [])}
    assert "PRODUCTO_INEXISTENTE" in tipos_excel
    assert "PRODUCTO_SIN_PRECIO" in tipos_excel
    assert "PRODUCTO_DUPLICADO" in tipos_excel
    assert "PROVEEDOR_INEXISTENTE" in tipos_excel
    assert "INGREDIENTE_SIN_CANTIDAD" in tipos_excel

    with patch("builtins.input", side_effect=["n"]):
        resultado_excel = flujo.confirmar_importacion(contexto_excel)
    assert resultado_excel["importacion"]["origen"] == "EXCEL"

    # 9) Historial y no catálogo paralelo.
    historial = flujo.repo_importaciones.listar_historial()
    assert len(historial) >= 3
    assert any(h.get("estado") == "CANCELADA" for h in historial)
    assert sum(1 for h in historial if h.get("origen") in {"TEXTO", "EXCEL"}) >= 2

    path_centro = tmp_path / "DATOS" / "db" / "centro_importacion_601.json"
    payload_centro = json.loads(path_centro.read_text(encoding="utf-8"))
    assert "catalogo_productos" not in payload_centro
    assert "catalogo_proveedores" not in payload_centro

    # 10) Verificación final: datos reales sin cambios.
    huellas_despues = {k: _sha256(v) for k, v in reales.items() if v.exists()}
    assert huellas_antes == huellas_despues

    # El sandbox sí debe haber cambiado.
    assert _sha256(rutas["articulos"]) != _sha256(reales["articulos"]) or _sha256(rutas["historico"]) != _sha256(reales["historico"])


def test_ui_catalogo_importar_excel_delega_en_centro_real(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _preparar_sandbox(tmp_path, repo_root)

    servicio = CatalogoMaestroProductos601(tmp_path)
    ui = CatalogoMaestroProductosUI601(servicio, base_dir=tmp_path)

    with patch.object(CentroImportacionUI601, "importar_excel", autospec=True) as mock_importar:
        ui._importar_excel()
        assert mock_importar.called is True
