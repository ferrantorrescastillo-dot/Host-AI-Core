from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.configuracion_central_4414 import GestorConfiguracionCentral4414


def main():
    gestor = GestorConfiguracionCentral4414(ROOT)
    gestor.crear_si_no_existe()

    while True:
        print("\n=== HOST AI 4.4.14 - CONFIGURACIÓN CENTRAL ===")
        print("1. Ver resumen")
        print("2. Validar configuración")
        print("3. Cambiar restaurante")
        print("4. Cambiar IVA")
        print("5. Activar/desactivar OCR")
        print("6. Activar/desactivar IA")
        print("7. Asegurar rutas")
        print("0. Salir")
        opcion = input("Selecciona: ").strip()

        if opcion == "1":
            resumen = gestor.resumen_configuracion()
            for k, v in resumen.items():
                print(f"{k}: {v}")
        elif opcion == "2":
            validacion = gestor.validar_configuracion()
            print(validacion["lectura_host_ai"])
            if validacion["errores"]:
                print("Errores:", validacion["errores"])
            if validacion["avisos"]:
                print("Avisos:", validacion["avisos"])
        elif opcion == "3":
            nombre = input("Nombre del restaurante: ").strip()
            if nombre:
                gestor.actualizar_configuracion({"restaurante": nombre})
                print("Restaurante actualizado.")
        elif opcion == "4":
            iva = input("IVA por defecto (%): ").strip().replace(",", ".")
            try:
                gestor.actualizar_configuracion({"iva_default": float(iva)})
                print("IVA actualizado.")
            except ValueError:
                print("IVA no válido.")
        elif opcion == "5":
            actual = gestor.cargar_configuracion()
            nuevo = not bool(actual.get("ocr_activo"))
            gestor.actualizar_configuracion({"ocr_activo": nuevo})
            print(f"OCR activo: {nuevo}")
        elif opcion == "6":
            actual = gestor.cargar_configuracion()
            nuevo = not bool(actual.get("ia_activa"))
            gestor.actualizar_configuracion({"ia_activa": nuevo})
            print(f"IA activa: {nuevo}")
        elif opcion == "7":
            resultado = gestor.asegurar_rutas_configuradas()
            print(resultado["lectura_host_ai"])
        elif opcion == "0":
            break
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()
