from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.auditoria_sistema_457 import AuditoriaSistema457


def main() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        auditoria = AuditoriaSistema457(Path(tmpdir))
        creado = auditoria.registrar_accion(
            modulo="stock",
            accion="entrada_mercancia",
            usuario="Ferran",
            restaurante="Boronat",
            entidad="articulo",
            entidad_id="ARROZ001",
            valor_anterior={"stock": 10},
            valor_nuevo={"stock": 25},
            detalle="Llegaron 15 kg de arroz.",
        )
        assert creado["ok"] is True
        listado = auditoria.listar_acciones(modulo="stock")
        assert listado["total"] == 1
        assert listado["acciones"][0]["valor_nuevo"]["stock"] == 25
        resumen = auditoria.resumen_auditoria()
        assert resumen["total"] == 1
        assert resumen["errores"] == 0

    print("TEST OK 4.5.7 - Auditoría sistema")


if __name__ == "__main__":
    main()
