from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.lector_escandallos_excel_555b import LectorEscandallosExcel555B


def formatear(resultado: dict) -> str:
    lineas = ["HOST AI 5.5.5B - PARTE 1", "VISTA PREVIA DE ESCANDALLOS EXCEL", ""]
    if resultado.get("errores"):
        lineas.append("ERRORES")
        lineas.extend(f"- {error}" for error in resultado["errores"])
        return "\n".join(lineas)

    lineas.append(f"Archivo: {resultado.get('archivo', '')}")
    lineas.append(f"Hojas candidatas: {resultado.get('hojas_candidatas', 0)}")
    for hoja in resultado.get("hojas", []):
        estado = "CANDIDATA" if hoja.get("candidata_escandallos") else "REVISAR"
        lineas.extend([
            "",
            f"HOJA: {hoja.get('nombre')} [{estado}]",
            f"- Cabecera detectada en fila: {hoja.get('fila_cabecera')}",
            f"- Filas con datos: {hoja.get('filas_con_datos')}",
            f"- Confianza: {hoja.get('confianza')}%",
            f"- Campos faltantes: {', '.join(hoja.get('campos_faltantes', [])) or 'ninguno'}",
            "- Mapeo sugerido:",
        ])
        for origen, destino in hoja.get("mapeo_sugerido", {}).items():
            lineas.append(f"  {origen} -> {destino}")

    lineas.extend([
        "",
        "SEGURIDAD",
        "- Lectura en modo solo lectura.",
        "- Escandallos importados: 0.",
        "- Datos reales modificados: NO.",
    ])
    return "\n".join(lineas)


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python APP/vista_previa_importador_escandallos_555b.py <archivo.xlsx>")
        return 2
    resultado = LectorEscandallosExcel555B().analizar(sys.argv[1])
    print(formatear(resultado))
    if "--json" in sys.argv:
        print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))
    return 1 if resultado.get("errores") else 0


if __name__ == "__main__":
    raise SystemExit(main())
