from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.preimportador_escandallos_555b import PreimportadorEscandallosExcel555B


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Host AI 5.5.5B Parte 5 - Preimportación segura de escandallos")
    parser.add_argument("excel", help="Ruta al archivo Excel de escandallos")
    parser.add_argument("--confirmar", action="store_true", help="Confirma la escritura en la base canónica")
    parser.add_argument("--articulos", default="DATOS/db/articulos.json", help="Ruta al catálogo de artículos")
    parser.add_argument(
        "--destino", default="DATOS/db/escandallos_canonicos.json", help="Ruta del repositorio canónico"
    )
    parser.add_argument("--informe", help="Guarda el informe completo en JSON")
    return parser


def main() -> int:
    args = _parser().parse_args()
    servicio = PreimportadorEscandallosExcel555B(args.articulos, args.destino)
    resultado = servicio.ejecutar(args.excel, confirmar=args.confirmar)
    resumen = resultado.get("resumen", {})

    print("HOST AI 5.5.5B - PARTE 5")
    print("PREIMPORTACIÓN E IMPORTACIÓN SEGURA AL MODELO CANÓNICO\n")
    print(f"Excel: {resultado.get('archivo_excel')}")
    print(f"Destino: {resultado.get('ruta_destino')}")
    print(f"Modo: {resultado.get('modo')}")
    print(f"- Fichas analizadas: {resumen.get('fichas_analizadas', 0)}")
    print(f"- Nuevas: {resumen.get('crear', 0)}")
    print(f"- Actualizaciones: {resumen.get('actualizar', 0)}")
    print(f"- Sin cambios: {resumen.get('sin_cambios', 0)}")
    print(f"- Omitidas: {resumen.get('omitidas', 0)}")
    print(f"- A revisar: {resumen.get('a_revisar', 0)}")
    print(f"- Ingredientes enlazados: {resumen.get('ingredientes_enlazados', 0)}")
    print(f"- Ingredientes con candidatos: {resumen.get('ingredientes_con_candidatos', 0)}")
    print(f"- Ingredientes sin enlace: {resumen.get('ingredientes_sin_enlace', 0)}")

    if resultado.get("errores"):
        print("\nERRORES")
        for error in resultado["errores"]:
            print(f"- {error}")

    print("\nFICHAS OMITIDAS O A REVISAR")
    pendientes = [
        f for f in resultado.get("fichas", []) if f.get("accion") == "OMITIR" or f.get("estado") == "REVISAR"
    ]
    if not pendientes:
        print("- Ninguna.")
    for ficha in pendientes[:30]:
        print(f"- {ficha.get('nombre')} | {ficha.get('accion')} | {ficha.get('motivo')}")
    if len(pendientes) > 30:
        print(f"- ... y {len(pendientes) - 30} más.")

    if args.informe:
        ruta = Path(args.informe)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nInforme guardado: {ruta}")

    print("\nSEGURIDAD")
    if args.confirmar:
        print(f"- Escandallos creados/actualizados: {resumen.get('importados', 0)}")
        print(f"- Copia de seguridad: {resultado.get('copia_seguridad') or 'No necesaria; destino nuevo'}")
        print(f"- Datos reales modificados: {'SÍ' if resultado.get('datos_reales_modificados') else 'NO'}")
    else:
        print("- Vista previa: no se ha escrito ningún escandallo.")
        print("- Para importar, revisa el informe y vuelve a ejecutar con --confirmar.")
        print("- Datos reales modificados: NO")

    return 1 if resultado.get("errores") else 0


if __name__ == "__main__":
    raise SystemExit(main())
