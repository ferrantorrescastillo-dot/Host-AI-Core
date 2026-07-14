from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.validador_recepcion_mercancia_442 import ValidadorRecepcionMercancia442


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print('python APP\\recepcion_mercancia_texto_442.py "De Makro han llegado 15 kg arroz bomba a 3,20 €/kg"')
        return

    texto = " ".join(sys.argv[1:])
    ruta_articulos = ROOT / "DATOS" / "db" / "articulos.json"
    ruta_json = ROOT / "DATOS" / "db" / "recepcion_borrador_4_4_2.json"
    ruta_txt = ROOT / "DATOS" / "db" / "recepcion_borrador_4_4_2.txt"

    validador = ValidadorRecepcionMercancia442(str(ruta_articulos))
    borrador = validador.validar_guardar_y_exportar(texto, str(ruta_json), str(ruta_txt))

    print("HOST AI 4.4.2 - Borrador Recepción Mercancía")
    print("JSON generado:", ruta_json)
    print("TXT generado:", ruta_txt)
    print("Estado:", borrador.estado)
    print("Proveedor general:", borrador.proveedor_general or "-")
    print("Líneas:", borrador.total_lineas)
    print("")

    for idx, linea in enumerate(borrador.lineas_validadas, start=1):
        print(f"{idx}. {linea.producto_texto} | {linea.cantidad} {linea.unidad}")
        print(f"   Acción: {linea.accion_sugerida}")
        print(f"   Artículo: {linea.articulo_encontrado or '-'} | Código: {linea.codigo_articulo or '-'} | Confianza: {round(linea.confianza*100, 1)}%")
        for mensaje in linea.mensajes:
            print(f"   - {mensaje}")


if __name__ == "__main__":
    main()
