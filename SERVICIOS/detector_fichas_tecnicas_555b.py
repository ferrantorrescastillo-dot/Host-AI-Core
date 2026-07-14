from __future__ import annotations

from pathlib import Path
from typing import Any

from SERVICIOS.clasificador_hojas_excel_555b import ClasificadorHojasExcel555B


def detectar_fichas_tecnicas_555b(ruta_archivo: str | Path) -> list[dict[str, Any]]:
    resultado = ClasificadorHojasExcel555B().analizar(ruta_archivo)
    return [hoja for hoja in resultado.get("hojas", []) if hoja.get("tipo") == "FICHAS_TECNICAS"]
