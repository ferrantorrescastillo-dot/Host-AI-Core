from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.interprete_recepcion_texto_441 import InterpreteRecepcionTexto441


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print('python APP\\interpretar_recepcion_texto_441.py "De Makro han llegado 15 kg arroz bomba a 3,20 €/kg"')
        return

    texto = " ".join(sys.argv[1:])
    ruta_json = ROOT / "DATOS" / "db" / "recepcion_texto_4_4_1.json"

    interprete = InterpreteRecepcionTexto441()
    resultado = interprete.interpretar_y_guardar(texto, str(ruta_json))

    print("HOST AI 4.4.1 - Intérprete Recepción Texto")
    print("Archivo generado:", ruta_json)
    print("Estado:", resultado.estado)
    print("Proveedor general:", resultado.proveedor_general or "-")
    print("Líneas:", resultado.total_lineas)
    print("")

    for idx, linea in enumerate(resultado.lineas, start=1):
        print(f"{idx}. {linea.producto} | {linea.cantidad} {linea.unidad} | Proveedor: {linea.proveedor or resultado.proveedor_general or '-'} | Precio: {linea.precio_unitario}")

    if resultado.errores:
        print("")
        print("Errores:")
        for error in resultado.errores:
            print("-", error)


if __name__ == "__main__":
    main()
