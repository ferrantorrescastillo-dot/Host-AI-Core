from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.importador_canonico_seguro_555b71 import ImportadorCanonicoSeguro555B71


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Host AI 5.5.5B.7.1 - Importación canónica segura")
    p.add_argument("--preimportacion", default="DATOS/informes/preimportacion_555b.json")
    p.add_argument("--resolucion", default="DATOS/informes/resolucion_variantes_555b.json")
    p.add_argument("--destino", default="DATOS/db/escandallos_canonicos.json")
    p.add_argument("--informe", default="DATOS/informes/importacion_555b71.json")
    p.add_argument("--confirmar", action="store_true", help="Escribe únicamente decisiones automáticas seguras")
    return p


def main() -> int:
    args = _parser().parse_args()
    resultado = ImportadorCanonicoSeguro555B71(args.destino).ejecutar(
        args.preimportacion,
        args.resolucion,
        confirmar=args.confirmar,
        ruta_diario=args.informe,
    )
    r = resultado.get("resumen", {})
    print("HOST AI 5.5.5B.7.1")
    print("MOTOR DE IMPORTACIÓN CANÓNICA SEGURA\n")
    print(f"Modo: {resultado.get('modo')}")
    print(f"Destino: {resultado.get('ruta_destino')}")
    print(f"- Analizadas: {r.get('analizadas', 0)}")
    print(f"- Crear: {r.get('crear', 0)}")
    print(f"- Actualizar: {r.get('actualizar', 0)}")
    print(f"- Sin cambios: {r.get('sin_cambios', 0)}")
    print(f"- Omitidas: {r.get('omitidas', 0)}")
    print(f"- Pendientes de confirmación humana: {r.get('pendientes_confirmacion', 0)}")
    print(f"- Escritas: {r.get('escritas', 0)}")

    if resultado.get("errores"):
        print("\nERRORES")
        for e in resultado["errores"]:
            print(f"- {e}")

    print("\nSEGURIDAD")
    if args.confirmar:
        print(f"- Datos reales modificados: {'SÍ' if resultado.get('datos_reales_modificados') else 'NO'}")
        if resultado.get("copia_seguridad"):
            print(f"- Copia de seguridad: {resultado.get('copia_seguridad')}")
        if resultado.get("diario_transaccion"):
            print(f"- Diario: {resultado.get('diario_transaccion')}")
    else:
        print("- Vista previa: no se ha escrito ningún escandallo.")
        print("- Para importar solo decisiones automáticas seguras, añade --confirmar.")
        print("- Datos reales modificados: NO")

    if not args.confirmar:
        Path(args.informe).parent.mkdir(parents=True, exist_ok=True)
        Path(args.informe).write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"- Informe guardado: {args.informe}")
    return 1 if resultado.get("errores") else 0


if __name__ == "__main__":
    raise SystemExit(main())
