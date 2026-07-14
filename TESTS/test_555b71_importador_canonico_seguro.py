from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.importador_canonico_seguro_555b71 import ImportadorCanonicoSeguro555B71
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos


def ficha(codigo: str, nombre: str, *, tipo=None, estado="PREPARADA") -> dict:
    return {
        "codigo": codigo,
        "nombre": nombre,
        "estado": estado,
        "accion": "CREAR",
        "motivo": "test",
        "hoja": "M.P TEST",
        "fila_inicio": 4,
        "fila_fin": 12,
        "rendimiento": 4.0,
        "unidad_rendimiento": "u",
        "tipo_duplicado": tipo,
        "ingredientes": [
            {
                "codigo": "ART001",
                "nombre": "Arroz bomba",
                "cantidad": 0.4,
                "unidad": "kg",
                "articulo_id": "ART001",
                "precio_unitario": 2.0,
                "metadata": {},
            }
        ],
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        raiz = Path(td)
        pre = raiz / "pre.json"
        res = raiz / "res.json"
        destino = raiz / "escandallos.json"
        diario = raiz / "diario.json"

        pre.write_text(json.dumps({
            "fichas": [
                ficha("REC-1", "Paella base"),
                ficha("REC-2", "Vinagreta", tipo="DUPLICADO_EXACTO"),
                ficha("REC-3", "Vinagreta", tipo="DUPLICADO_EXACTO"),
                ficha("REC-4", "Patatas Bravas"),
                ficha("REC-5", "KG", estado="REVISAR"),
            ],
            "errores": [],
        }), encoding="utf-8")
        res.write_text(json.dumps({
            "decisiones": [
                {
                    "nombre": "Vinagreta",
                    "accion_propuesta": "SELECCIONAR_MEJOR_FICHA",
                    "ficha_recomendada": "REC-2",
                    "requiere_confirmacion": False,
                },
                {
                    "nombre": "Patatas Bravas",
                    "accion_propuesta": "MANTENER_COMO_VARIANTES",
                    "requiere_confirmacion": True,
                },
            ],
            "fichas_individuales": [
                {"codigo": "REC-5", "accion_propuesta": "REVISAR_TITULO"}
            ],
            "errores": [],
        }), encoding="utf-8")

        servicio = ImportadorCanonicoSeguro555B71(destino)
        vista = servicio.ejecutar(pre, res, confirmar=False, ruta_diario=diario)
        assert vista["datos_reales_modificados"] is False
        assert not destino.exists()
        assert vista["resumen"]["crear"] == 2, vista["resumen"]
        assert vista["resumen"]["pendientes_confirmacion"] == 1

        real = servicio.ejecutar(pre, res, confirmar=True, ruta_diario=diario)
        assert real["datos_reales_modificados"] is True, real
        assert destino.exists()
        assert diario.exists()
        nombres = sorted(e.receta.nombre for e in RepositorioEscandallos(destino).listar())
        assert nombres == ["Paella base", "Vinagreta"], nombres

        segunda = servicio.ejecutar(pre, res, confirmar=False, ruta_diario=diario)
        assert segunda["resumen"]["sin_cambios"] == 2, segunda["resumen"]

    print("TEST OK 5.5.5B.7.1 - Motor de importación canónica segura")


if __name__ == "__main__":
    main()
