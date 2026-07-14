from __future__ import annotations

import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from openpyxl import Workbook

from SERVICIOS.lector_escandallos_excel_555b import LectorEscandallosExcel555B
from SERVICIOS.perfil_mapeo_escandallos_555b import (
    PerfilMapeoEscandallos555B,
    sugerir_mapeo,
)


def crear_excel(ruta: Path) -> None:
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Escandallos"
    hoja.append(["Informe de recetas"])
    hoja.append([])
    hoja.append(["Plato", "Ingrediente", "Cantidad neta", "Unidad", "Raciones", "Precio compra"])
    hoja.append(["Paella de marisco", "Arroz bomba", 0.1, "kg", 10, 2.15])
    hoja.append(["Paella de marisco", "Caldo de pescado", 0.5, "l", 10, 1.20])
    libro.create_sheet("Notas")["A1"] = "Sin datos de escandallo"
    libro.save(ruta)


def main() -> None:
    with tempfile.TemporaryDirectory() as temporal:
        carpeta = Path(temporal)
        excel = carpeta / "escandallos_prueba.xlsx"
        crear_excel(excel)

        resultado = LectorEscandallosExcel555B().analizar(excel, filas_preview=3)
        assert not resultado["errores"], resultado["errores"]
        assert resultado["hojas_candidatas"] == 1
        candidata = next(hoja for hoja in resultado["hojas"] if hoja["candidata_escandallos"])
        assert candidata["fila_cabecera"] == 3
        assert candidata["filas_con_datos"] == 2
        assert candidata["mapeo_sugerido"]["Plato"] == "RECETA"
        assert candidata["mapeo_sugerido"]["Ingrediente"] == "INGREDIENTE"
        assert candidata["mapeo_sugerido"]["Cantidad neta"] == "CANTIDAD"
        assert candidata["mapeo_sugerido"]["Unidad"] == "UNIDAD"
        assert candidata["campos_faltantes"] == []
        assert resultado["datos_reales_modificados"] is False

        mapeo, confianza, faltantes = sugerir_mapeo(["Receta", "Producto", "Cantidad", "Ud."])
        assert not faltantes
        assert confianza >= 80

        perfil = PerfilMapeoEscandallos555B(
            nombre="Prueba",
            hoja="Escandallos",
            fila_cabecera=3,
            mapeo=mapeo,
        )
        ruta_perfil = carpeta / "perfil.json"
        perfil.guardar(ruta_perfil)
        cargado = PerfilMapeoEscandallos555B.cargar(ruta_perfil)
        assert cargado.mapeo == perfil.mapeo

    print("TEST OK 5.5.5B PARTE 1 - Lectura, cabeceras, vista previa y mapeo Excel")


if __name__ == "__main__":
    main()
