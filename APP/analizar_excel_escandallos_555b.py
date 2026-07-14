from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.clasificador_hojas_excel_555b import ClasificadorHojasExcel555B


def formatear(resultado: dict) -> str:
    lineas = ["HOST AI 5.5.5B - PARTE 2", "CLASIFICACIÓN ESTRUCTURAL DEL EXCEL", ""]
    if resultado.get("errores"):
        lineas.append("ERRORES")
        lineas.extend(f"- {error}" for error in resultado["errores"])
        return "\n".join(lineas)

    lineas.append(f"Archivo: {resultado.get('archivo', '')}")
    resumen = resultado.get("resumen_tipos", {})
    for tipo in ("ARTICULOS", "FICHAS_TECNICAS", "MENUS", "RESUMENES", "AUXILIARES", "DESCONOCIDAS"):
        lineas.append(f"- {tipo}: {resumen.get(tipo, 0)}")
    lineas.append(f"- Bloques de ficha detectados: {resultado.get('bloques_detectados', 0)}")

    for hoja in resultado.get("hojas", []):
        lineas.extend([
            "",
            f"HOJA: {hoja['nombre']}",
            f"- Tipo: {hoja['tipo']}",
            f"- Confianza: {hoja['confianza']}%",
            f"- Acción: {hoja['accion_recomendada']}",
        ])
        if hoja.get("hoja_relacionada"):
            lineas.append(f"- Hoja relacionada: {hoja['hoja_relacionada']}")
        if hoja.get("motivos"):
            lineas.append(f"- Motivo: {'; '.join(hoja['motivos'])}")
        if hoja.get("bloques"):
            lineas.append(f"- Bloques detectados: {len(hoja['bloques'])}")
            for bloque in hoja["bloques"][:10]:
                lineas.append(
                    f"  · Filas {bloque['fila_inicio']}-{bloque['fila_fin']}: "
                    f"{bloque['titulo']} ({bloque['confianza']}%)"
                )

    lineas.extend([
        "",
        "SEGURIDAD",
        "- Análisis en modo solo lectura.",
        "- Escandallos importados: 0.",
        "- Datos reales modificados: NO.",
    ])
    return "\n".join(lineas)


def main() -> int:
    if len(sys.argv) < 2:
        print('Uso: python APP/analizar_excel_escandallos_555b.py "C:\\ruta\\archivo.xlsx"')
        return 2
    resultado = ClasificadorHojasExcel555B().analizar(sys.argv[1])
    print(formatear(resultado))
    return 1 if resultado.get("errores") else 0


if __name__ == "__main__":
    raise SystemExit(main())
