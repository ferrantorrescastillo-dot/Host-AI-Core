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
        (db / "escandallos_canonicos.json").write_text(json.dumps({"escandallos": [
            {"receta": {"codigo": "R1", "nombre": "Ensaladilla", "rendimiento": 4, "unidad_rendimiento": "u", "precio_venta_unitario": 9.5,
                        "ingredientes": [{"nombre": "Patata", "articulo_id": "A1", "cantidad": 0.4, "unidad": "kg"}, {"nombre": "Gamba", "articulo_id": "A2", "cantidad": 0.2, "unidad": "kg"}]}}
        ]}), encoding="utf-8")
        for nombre in ("preimportacion_555b.json", "resolucion_variantes_555b.json", "importacion_555b71.json"):
            (info / nombre).write_text("{}", encoding="utf-8")
        (backups / "escandallos_test.json.bak").write_text("{}", encoding="utf-8")

        auditor = AuditorCierreEscandallos555B74(base)
        auditor.MODULOS_REQUERIDOS = ()
        resultado = auditor.auditar()
        assert resultado["estado"] == "CIERRE_APROBADO", resultado
        assert resultado["metricas"]["escandallos"] == 1
        assert resultado["metricas"]["ingredientes"] == 2
        assert resultado["datos_reales_modificados"] is False
        assert resultado["resultado"]["error"] == 0

    print("TEST OK 5.5.5B.7.4 - Cierre, versionado y auditoría del importador de escandallos")


if __name__ == "__main__":
    main()
