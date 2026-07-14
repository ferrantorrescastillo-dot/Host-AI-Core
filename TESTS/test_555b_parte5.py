from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.preimportador_escandallos_555b import PreimportadorEscandallosExcel555B


class PreimportadorPrueba(PreimportadorEscandallosExcel555B):
    def __init__(self, depurado, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._depurado = depurado

    def ejecutar(self, ruta_excel, *, confirmar=False):
        # Inyecta el resultado depurado sin necesidad de generar un Excel de prueba.
        from MODELOS.preimportacion_escandallos_555b import ResultadoPreimportacion555B
        from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos

        original = __import__("SERVICIOS.preimportador_escandallos_555b", fromlist=["DepuradorFichasTecnicas555B"])
        clase_original = original.DepuradorFichasTecnicas555B

        class Falso:
            def depurar_archivo(_self, _ruta):
                return self._depurado

        original.DepuradorFichasTecnicas555B = Falso
        try:
            return super().ejecutar(ruta_excel, confirmar=confirmar)
        finally:
            original.DepuradorFichasTecnicas555B = clase_original


def _ficha(nombre, fila, *, estado="PREPARADA", duplicado=None, tipo=None, ingredientes=None):
    return {
        "id_origen": f"excel:mp:{fila}",
        "hoja": "M.P TEST",
        "fila_inicio": fila,
        "fila_fin": fila + 10,
        "nombre_original": nombre,
        "nombre_normalizado": nombre,
        "rendimiento": 4.0,
        "unidad_rendimiento": "u",
        "ingredientes": ingredientes or [
            {
                "nombre": "Arroz bomba",
                "cantidad": 0.4,
                "unidad_original": "kg",
                "unidad_normalizada": "kg",
                "precio_unitario": 2.15,
                "fila_origen": fila + 1,
                "tipo": "ARTICULO",
                "referencia_elaboracion": None,
            }
        ],
        "incidencias": [],
        "elaboraciones_referenciadas": [],
        "grupo_duplicado": duplicado,
        "tipo_duplicado": tipo,
        "confianza_final": 95.0,
        "estado": estado,
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        articulos = base / "articulos.json"
        destino = base / "escandallos_canonicos.json"
        articulos.write_text(
            json.dumps(
                [
                    {"codigo": "ART-ARROZ", "nombre": "Arroz bomba", "precio": 2.15, "proveedor": "Makro"},
                    {"codigo": "ART-TOMATE", "nombre": "Tomate maduro", "precio": 1.4},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        depurado = {
            "archivo": "prueba.xlsx",
            "errores": [],
            "fichas": [
                _ficha("Paella base", 4),
                _ficha("Paella base", 30, duplicado="DUP-001", tipo="DUPLICADO_EXACTO"),
                _ficha("Salsa", 60, estado="REVISAR"),
                _ficha("Guiso", 90, duplicado="DUP-002", tipo="VARIANTES_MISMO_NOMBRE"),
            ],
        }
        servicio = PreimportadorPrueba(depurado, articulos, destino)

        previo = servicio.ejecutar("prueba.xlsx", confirmar=False)
        assert previo["datos_reales_modificados"] is False
        assert not destino.exists()
        assert previo["resumen"]["crear"] >= 1
        assert previo["resumen"]["ingredientes_enlazados"] >= 1
        assert previo["resumen"]["a_revisar"] >= 2

        importado = servicio.ejecutar("prueba.xlsx", confirmar=True)
        assert importado["datos_reales_modificados"] is True
        assert importado["resumen"]["importados"] >= 1
        assert destino.exists()
        contenido = json.loads(destino.read_text(encoding="utf-8"))
        assert contenido["escandallos"]

        segundo = servicio.ejecutar("prueba.xlsx", confirmar=False)
        assert segundo["resumen"]["sin_cambios"] >= 1
        assert segundo["datos_reales_modificados"] is False

    print("TEST OK 5.5.5B PARTE 5 - Preimportación, enlaces, comparación e importación segura")


if __name__ == "__main__":
    main()
