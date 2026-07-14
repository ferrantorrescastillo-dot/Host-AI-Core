from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.integracion_operativa_539 import cerrar_inteligencia_operativa_539, formatear_cierre_operativo_539


def main() -> None:
    datos = {
        "tipo": "boda",
        "personas": 180,
        "fecha": "sabado",
        "hora_servicio": "15:00",
        "menu": "menu boda",
        "lugar": "Mas Boronat",
        "restricciones": "sin restricciones",
        "objetivo": "flujo completo",
    }
    contexto = {
        "stock": [
            {"nombre": "arroz bomba", "disponible": 8, "necesario": 18, "unidad": "kg", "imprescindible": True},
            {"nombre": "aceite oliva", "disponible": 12, "necesario": 10, "unidad": "l"},
        ],
        "recursos": [
            {"nombre": "horno 1", "estado": "ocupado", "detalle": "Reservado por otro evento hasta las 12:00"},
        ],
        "proveedores": [
            {"nombre": "Proveedor habitual", "disponible": False, "detalle": "No reparte mañana"},
        ],
        "personal": {"disponibles": 2, "necesarios": 3},
        "conflictos": [
            {"titulo": "Produccion y evento pisan el mismo recurso", "nivel": "alto", "detalle": "El horno esta reservado por servicio y produccion."}
        ],
    }
    resultado = cerrar_inteligencia_operativa_539(datos, contexto)
    print(formatear_cierre_operativo_539(resultado))


if __name__ == "__main__":
    main()
