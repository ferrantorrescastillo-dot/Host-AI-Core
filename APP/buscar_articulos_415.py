from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.buscador_inteligente_articulos_415 import BuscadorInteligenteArticulos415


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print('python APP\\buscar_articulos_415.py "aceite"')
        print('python APP\\buscar_articulos_415.py "arroz bomba" "Makro"')
        print('python APP\\buscar_articulos_415.py --diagnostico "arroz"')
        return

    ruta_db = ROOT / "DATOS" / "db" / "articulos.json"
    buscador = BuscadorInteligenteArticulos415(str(ruta_db))

    if sys.argv[1] == "--diagnostico":
        if len(sys.argv) < 3:
            print('Uso: python APP\\buscar_articulos_415.py --diagnostico "termino"')
            return
        informe = buscador.diagnosticar(sys.argv[2])
        titulo = "HOST AI 4.1.5.1 - Diagnóstico de artículos"
    else:
        consulta = sys.argv[1]
        proveedor = sys.argv[2] if len(sys.argv) >= 3 else None
        informe = buscador.buscar(consulta=consulta, proveedor=proveedor, limite=15)
        titulo = "HOST AI 4.1.5.1 - Buscador Inteligente de Artículos"

    print(titulo)
    print("Consulta:", informe.consulta)
    print("Proveedor filtro:", informe.proveedor_filtro or "-")
    print("Artículos revisados:", informe.total_articulos)
    print("Resultados:", informe.total_resultados)
    print("")

    if not informe.resultados:
        print("No se han encontrado artículos claros.")
        print("Consejo: prueba con menos palabras o usa --diagnostico.")
        return

    for idx, item in enumerate(informe.resultados, start=1):
        print(f"{idx}. {item.codigo} | {item.nombre}")
        print(f"   Proveedor: {item.proveedor or '-'} | Familia: {item.familia or '-'} | Precio: {item.precio}")
        print(f"   Parecido: {round(item.puntuacion * 100, 1)}% | {item.motivo}")


if __name__ == "__main__":
    main()
