from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.auditor_cierre_escandallos_555b74 import AuditorCierreEscandallos555B74


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "DATOS" / "db"
        info = base / "DATOS" / "informes"
        backups = db / "backups"
        db.mkdir(parents=True)
        info.mkdir(parents=True)
        backups.mkdir(parents=True)

        (db / "articulos.json").write_text(json.dumps([
            {"codigo": "A1", "nombre": "Patata", "precio": 2.0},
            {"codigo": "A2", "nombre": "Gamba", "precio": 10.0},
        ]), encoding="utf-8")

        # El PVP está en el envoltorio, igual que lo escribe la 7.3.2.
        (db / "escandallos_canonicos.json").write_text(json.dumps({"escandallos": [
            {
                "precio_venta_unitario": 9.5,
                "precio_venta_origen": "HOST_AI_5.5.5B.7.3.2",
                "receta": {
                    "codigo": "R1",
                    "nombre": "Ensaladilla",
                    "rendimiento": 4,
                    "unidad_rendimiento": "u",
                    "ingredientes": [
                        {"nombre": "Patata", "articulo_id": "A1", "cantidad": 0.4, "unidad": "kg"},
                        {"nombre": "Gamba", "articulo_id": "A2", "cantidad": 0.2, "unidad": "kg"},
                    ],
                },
            }
        ]}), encoding="utf-8")

        for nombre in ("preimportacion_555b.json", "resolucion_variantes_555b.json", "importacion_555b71.json"):
            (info / nombre).write_text("{}", encoding="utf-8")
        (backups / "escandallos_test.json.bak").write_text("{}", encoding="utf-8")

        auditor = AuditorCierreEscandallos555B74(base)
        auditor.MODULOS_REQUERIDOS = ()
        resultado = auditor.auditar()
        assert resultado["estado"] == "CIERRE_APROBADO", resultado
        assert resultado["resultado"]["ok"] == 10, resultado
        assert resultado["metricas"]["precios_venta_definidos"] == 1, resultado
        assert resultado["metricas"]["ingredientes"] == 2, resultado
        enlaces = next(c for c in resultado["comprobaciones"] if c["clave"] == "enlaces_articulos")
        assert enlaces["valor"]["no_enlazados"] == [], enlaces

    print("TEST OK 5.5.5B.7.4.1 - Corrección final de auditoría")


if __name__ == "__main__":
    main()
