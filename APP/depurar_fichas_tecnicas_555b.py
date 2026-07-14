from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.depurador_fichas_tecnicas_555b import DepuradorFichasTecnicas555B


def main() -> int:
    if len(sys.argv) < 2:
        print('Uso: python APP/depurar_fichas_tecnicas_555b.py "ruta\\archivo.xlsx"')
        return 2

    resultado = DepuradorFichasTecnicas555B().depurar_archivo(sys.argv[1])
    print("HOST AI 5.5.5B - PARTE 4")
    print("DEPURACIÓN, DUPLICADOS, UNIDADES Y ELABORACIONES\n")
    print(f"Archivo: {resultado.get('archivo')}")
    resumen = resultado.get("resumen", {})
    print(f"- Fichas analizadas: {resumen.get('fichas_analizadas', 0)}")
    print(f"- Preparadas: {resumen.get('preparadas', 0)}")
    print(f"- A revisar: {resumen.get('a_revisar', 0)}")
    print(f"- Rechazadas: {resumen.get('rechazadas', 0)}")
    print(f"- Grupos duplicados/variantes: {resumen.get('grupos_duplicados', 0)}")
    print(f"- Elaboraciones referenciadas: {resumen.get('elaboraciones_referenciadas', 0)}")
    print(f"- Incidencias detectadas: {resumen.get('incidencias', 0)}")

    if resultado.get("errores"):
        print("\nERRORES")
        for error in resultado["errores"]:
            print(f"- {error}")

    print("\nFICHAS QUE REQUIEREN REVISIÓN")
    pendientes = [f for f in resultado.get("fichas", []) if f.get("estado") != "PREPARADA"]
    if not pendientes:
        print("- Ninguna.")
    for ficha in pendientes:
        print(f"\n- {ficha.get('nombre_original')} [{ficha.get('estado')}]")
        print(f"  Hoja: {ficha.get('hoja')} | Filas: {ficha.get('fila_inicio')}-{ficha.get('fila_fin')}")
        for incidencia in ficha.get("incidencias", []):
            if incidencia.get("nivel") in {"CRITICO", "ALTO", "MEDIO"}:
                print(f"  · [{incidencia.get('nivel')}] {incidencia.get('mensaje')}")

    print("\nGRUPOS DE DUPLICADOS O VARIANTES")
    grupos = resultado.get("grupos_duplicados", [])
    if not grupos:
        print("- Ninguno.")
    for grupo in grupos:
        print(f"- {grupo['id']} | {grupo['tipo']} | {grupo['nombre_normalizado']} | fichas: {len(grupo['fichas'])}")

    print("\nSEGURIDAD")
    print("- Depuración en modo vista previa y solo lectura.")
    print("- Escandallos importados: 0.")
    print("- Datos reales modificados: NO.")
    return 0 if not resultado.get("errores") else 1


if __name__ == "__main__":
    raise SystemExit(main())
