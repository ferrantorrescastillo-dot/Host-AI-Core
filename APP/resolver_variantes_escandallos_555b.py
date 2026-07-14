from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.resolutor_variantes_escandallos_555b import ResolutorInteligenteEscandallos555B


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Host AI 5.5.5B Parte 6 - Resolución inteligente de duplicados y variantes"
    )
    parser.add_argument("excel", help="Ruta al Excel de escandallos")
    parser.add_argument("--preimportacion", help="Informe JSON generado por la Parte 5")
    parser.add_argument("--articulos", default="DATOS/db/articulos.json")
    parser.add_argument("--destino", default="DATOS/db/escandallos_canonicos.json")
    parser.add_argument("--informe", default="DATOS/informes/resolucion_variantes_555b.json")
    return parser


def main() -> int:
    args = _parser().parse_args()
    servicio = ResolutorInteligenteEscandallos555B(args.articulos, args.destino)
    resultado = servicio.ejecutar(args.excel, informe_preimportacion=args.preimportacion)
    resumen = resultado.get("resumen", {})

    print("HOST AI 5.5.5B - PARTE 6")
    print("RESOLUCIÓN INTELIGENTE DE DUPLICADOS Y VARIANTES\n")
    print(f"Excel: {resultado.get('archivo_excel')}")
    print(f"- Grupos analizados: {resumen.get('grupos_analizados', 0)}")
    print(f"- Seleccionar mejor ficha: {resumen.get('seleccionar_una', 0)}")
    print(f"- Fusiones propuestas: {resumen.get('fusionar_duplicados', 0)}")
    print(f"- Variantes reales: {resumen.get('mantener_variantes', 0)}")
    print(f"- Títulos a revisar: {resumen.get('revisar_titulo', 0)}")
    print(f"- Decisiones automáticas seguras: {resumen.get('listas_sin_confirmacion', 0)}")
    print(f"- Decisiones que requieren confirmación: {resumen.get('requieren_confirmacion', 0)}")

    if resultado.get("errores"):
        print("\nERRORES")
        for error in resultado["errores"]:
            print(f"- {error}")

    print("\nPROPUESTAS POR GRUPO")
    decisiones = resultado.get("decisiones") or []
    if not decisiones:
        print("- No se han detectado grupos duplicados o variantes.")
    for d in decisiones:
        print(f"- {d.get('nombre')} | {d.get('tipo')} | {d.get('accion_propuesta')}")
        print(f"  Confianza: {d.get('confianza')}%")
        print(f"  Motivo: {d.get('motivo')}")
        if d.get("ficha_recomendada"):
            print(f"  Ficha recomendada: {d.get('ficha_recomendada')}")
        if d.get("nombres_propuestos"):
            for nombre in d["nombres_propuestos"]:
                print(f"  · {nombre}")

    pendientes = resultado.get("fichas_individuales") or []
    if pendientes:
        print("\nFICHAS INDIVIDUALES A REVISAR")
        for ficha in pendientes[:20]:
            print(f"- {ficha.get('nombre')} | {ficha.get('accion_propuesta')} | {ficha.get('motivo')}")

    ruta = Path(args.informe)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nInforme guardado: {ruta}")

    print("\nSEGURIDAD")
    print("- Solo genera propuestas de resolución.")
    print("- No modifica el Excel ni la base canónica.")
    print("- Los casos dudosos siguen requiriendo confirmación humana.")
    print("- Datos reales modificados: NO")
    return 1 if resultado.get("errores") else 0


if __name__ == "__main__":
    raise SystemExit(main())
