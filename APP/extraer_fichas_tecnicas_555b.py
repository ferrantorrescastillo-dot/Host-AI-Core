from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.extractor_fichas_tecnicas_excel_555b import ExtractorFichasTecnicasExcel555B


def _fmt_num(valor):
    if valor is None:
        return "pendiente"
    return f"{valor:g}" if isinstance(valor, (int, float)) else str(valor)


def main() -> int:
    if len(sys.argv) < 2:
        print('Uso: python APP/extraer_fichas_tecnicas_555b.py "C:\\ruta\\archivo.xlsx"')
        return 2

    resultado = ExtractorFichasTecnicasExcel555B().extraer(sys.argv[1])
    print("HOST AI 5.5.5B - PARTE 3")
    print("EXTRACCIÓN Y NORMALIZACIÓN DE FICHAS TÉCNICAS\n")
    print(f"Archivo: {resultado['archivo']}")
    resumen = resultado["resumen"]
    print(f"- Fichas detectadas: {resumen['fichas_detectadas']}")
    print(f"- Válidas para importar: {resumen['fichas_validas_para_importar']}")
    print(f"- A revisar: {resumen['fichas_a_revisar']}")
    print(f"- Ingredientes extraídos: {resumen['ingredientes_extraidos']}")

    for ficha in resultado["fichas"]:
        estado = "PREPARADA" if ficha["valida_para_importar"] else "REVISAR"
        print(f"\nFICHA: {ficha['nombre']} [{estado}]")
        print(f"- Hoja: {ficha['hoja']} | Filas: {ficha['fila_inicio']}-{ficha['fila_fin']}")
        print(f"- Rendimiento: {_fmt_num(ficha['rendimiento'])} {ficha['unidad_rendimiento'] or ''}".rstrip())
        print(f"- Ingredientes: {len(ficha['ingredientes'])}")
        print(f"- Confianza: {ficha['confianza']}%")
        for ingrediente in ficha["ingredientes"][:8]:
            print(f"  · {ingrediente['nombre']}: {_fmt_num(ingrediente['cantidad'])} {ingrediente['unidad']}")
        if len(ficha["ingredientes"]) > 8:
            print(f"  · ... y {len(ficha['ingredientes']) - 8} más")
        for aviso in ficha["avisos"]:
            print(f"- AVISO: {aviso}")
        for error in ficha["errores"]:
            print(f"- ERROR: {error}")

    for error in resultado.get("errores", []):
        print(f"\nERROR GENERAL: {error}")
    print("\nSEGURIDAD")
    print("- Extracción en modo vista previa y solo lectura.")
    print("- Escandallos importados: 0.")
    print("- Datos reales modificados: NO.")
    return 0 if not resultado.get("errores") else 1


if __name__ == "__main__":
    raise SystemExit(main())
