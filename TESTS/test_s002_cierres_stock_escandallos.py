"""
HOST AI S-002 - Corrección de cierres Stock y Escandallos

Objetivo:
    Validar que los cierres de Stock (3.0.5.8) y Escandallos (3.0.7.8)
    pueden terminar en estado operativo OK cuando los datos de entrada son sanos.

Este test no sustituye los tests diagnósticos de cada bloque. Es el test específico
para preparar Host AI 3.0 Stable Candidate para pruebas controladas con restaurantes.

Ejecutar desde la raíz del proyecto:
    python TESTS\test_s002_cierres_stock_escandallos.py
"""
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


ESCANDALLOS_SANOS = [
    {
        "nombre": "Paella marisco piloto",
        "raciones": 10,
        "precio_venta_por_racion": 22,
        "tiempo_activo_min": 90,
        "tiempo_pasivo_min": 30,
        "ingredientes": [
            {"nombre": "Arroz", "cantidad": 1, "unidad": "kg", "precio_unitario": 2.4, "merma_pct": 3, "proveedor": "Proveedor A"},
            {"nombre": "Caldo", "cantidad": 3, "unidad": "l", "precio_unitario": 1.2, "merma_pct": 2, "proveedor": "Proveedor A"},
            {"nombre": "Gamba", "cantidad": 1.0, "unidad": "kg", "precio_unitario": 12, "merma_pct": 5, "proveedor": "Proveedor B"},
        ],
    },
    {
        "nombre": "Canelón piloto",
        "raciones": 10,
        "precio_venta_por_racion": 16,
        "tiempo_activo_min": 70,
        "tiempo_pasivo_min": 20,
        "ingredientes": [
            {"nombre": "Pasta", "cantidad": 1, "unidad": "kg", "precio_unitario": 2, "merma_pct": 2, "proveedor": "Proveedor A"},
            {"nombre": "Carne", "cantidad": 1.5, "unidad": "kg", "precio_unitario": 7, "merma_pct": 5, "proveedor": "Proveedor C"},
        ],
    },
]

HISTORICO_SANO = [
    {"nombre": "Paella marisco piloto", "coste_total": 19, "precio_venta": 210},
    {"nombre": "Paella marisco piloto", "coste_total": 18, "precio_venta": 220},
    {"nombre": "Canelón piloto", "coste_total": 12, "precio_venta": 160},
]

VENTAS_SANAS = [
    {"nombre": "Paella marisco piloto", "unidades_vendidas": 100},
    {"nombre": "Canelón piloto", "unidades_vendidas": 80},
]


def preparar_stock_sano(core: HostAICore) -> None:
    """Carga un escenario mínimo de stock sin roturas ni ubicaciones pendientes."""
    articulos = [
        ("Aceite oliva piloto", 30, "l", "S002-ACEITE", "Seco", 5, 10),
        ("Tomate piloto", 30, "kg", "S002-TOMATE", "Cámara", 2, 10),
        ("Harina piloto", 50, "kg", "S002-HARINA", "Seco", 1, 20),
    ]
    for nombre, cantidad, unidad, articulo_id, ubicacion, coste, minimo in articulos:
        entrada = core.orquestador.resolver(
            SolicitudHostAI(
                "registrar_entrada_stock",
                {
                    "nombre": nombre,
                    "cantidad": cantidad,
                    "unidad": unidad,
                    "articulo_id": articulo_id,
                    "ubicacion": ubicacion,
                    "coste_unitario": coste,
                },
            )
        )
        assert entrada.ok, entrada.mensaje

        minimo_resultado = core.orquestador.resolver(
            SolicitudHostAI(
                "ajustar_minimo_stock",
                {"nombre": nombre, "cantidad_minima": minimo, "articulo_id": articulo_id},
            )
        )
        assert minimo_resultado.ok, minimo_resultado.mensaje


def validar_cierre_stock(core: HostAICore) -> dict:
    cierre = core.orquestador.resolver(
        SolicitudHostAI("cerrar_gestion_inteligente_stock", {"horizonte_dias": 14})
    )
    assert cierre.ok, cierre.mensaje
    estado = cierre.datos.get("estado_general")
    assert estado == "ok", f"Stock debería cerrar OK en escenario sano, pero cerró como: {estado}. Datos: {cierre.datos}"
    assert cierre.datos.get("metricas", {}).get("alertas_stock", 0) == 0, cierre.datos
    assert cierre.datos.get("metricas", {}).get("lotes_sin_ubicacion", 0) == 0, cierre.datos
    return cierre.datos


def validar_cierre_escandallos(core: HostAICore) -> dict:
    cierre = core.orquestador.resolver(
        SolicitudHostAI(
            "comprobar_cierre_escandallos_inteligentes",
            {
                "escandallos": ESCANDALLOS_SANOS,
                "historico": HISTORICO_SANO,
                "ventas": VENTAS_SANAS,
            },
        )
    )
    assert cierre.ok, cierre.mensaje
    estado = cierre.datos.get("estado_general")
    assert estado == "ok", f"Escandallos debería cerrar OK en escenario sano, pero cerró como: {estado}. Datos: {cierre.datos}"
    metricas = cierre.datos.get("metricas", {})
    assert metricas.get("alertas_criticas", 0) == 0, cierre.datos
    assert metricas.get("platos_a_retirar", 0) == 0, cierre.datos
    return cierre.datos


def ejecutar_prueba() -> None:
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    preparar_stock_sano(core)
    cierre_stock = validar_cierre_stock(core)
    cierre_escandallos = validar_cierre_escandallos(core)

    print("TEST OK - Host AI S-002 Cierres Stock y Escandallos")
    print("Stock cierre:", cierre_stock["estado_general"])
    print("Stock alertas:", cierre_stock["metricas"].get("alertas_stock", 0))
    print("Escandallos cierre:", cierre_escandallos["estado_general"])
    print("Escandallos alertas críticas:", cierre_escandallos["metricas"].get("alertas_criticas", 0))


if __name__ == "__main__":
    ejecutar_prueba()
