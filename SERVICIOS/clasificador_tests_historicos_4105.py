from pathlib import Path
from typing import Dict, List, Any

BLOQUES = {
    "4.1 Catalogo": ["catalogo", "articulo", "articulos", "familia", "familias", "codigo"],
    "4.2 Proveedores": ["proveedor", "proveedores"],
    "4.3 Stock": ["stock", "inventario", "movimiento", "pedido_sugerido", "entrada_stock", "salida"],
    "4.4 Recepcion": ["recepcion", "albaran", "factura", "ocr", "lineas_factura", "documento"],
    "4.5 Producto/Base": ["base_datos", "multi_restaurante", "usuario", "roles", "permiso", "auditoria", "backup", "copia", "instalador", "configuracion", "actualizador", "logs"],
    "4.6 Produccion": ["produccion", "cocinero", "recursos_cocina", "checklist", "replanificacion", "tiempos"],
    "4.7 Eventos": ["evento", "eventos", "banquete", "cronograma", "material_evento", "personal_evento", "menu_evento"],
    "4.8 Rentabilidad": ["coste", "margen", "rentabilidad", "merma", "financiero", "precio", "precios"],
    "4.9 IA Operativa": ["decision", "decisiones", "acciones_automaticas", "jefe_cocina", "flujo_diario", "urgencias", "recomendaciones", "panel_ia", "ia"],
}


def _normalizar(nombre: str) -> str:
    return nombre.lower().replace("-", "_")


def clasificar_test(nombre_archivo: str) -> str:
    n = _normalizar(nombre_archivo)
    # Prefijos numéricos directos de la versión 4.x
    prefijos = {
        "test_41": "4.1 Catalogo",
        "test_42": "4.2 Proveedores",
        "test_43": "4.3 Stock",
        "test_44": "4.4 Recepcion",
        "test_45": "4.5 Producto/Base",
        "test_46": "4.6 Produccion",
        "test_47": "4.7 Eventos",
        "test_48": "4.8 Rentabilidad",
        "test_49": "4.9 IA Operativa",
        "test_410": "4.10 Auditoria/Cierre",
    }
    for prefijo, bloque in sorted(prefijos.items(), key=lambda x: len(x[0]), reverse=True):
        if n.startswith(prefijo):
            return bloque
    for bloque, claves in BLOQUES.items():
        if any(clave in n for clave in claves):
            return bloque
    return "Sin clasificar"


def clasificar_tests_historicos(raiz: str | Path = ".") -> Dict[str, Any]:
    raiz = Path(raiz)
    carpeta_tests = raiz / "TESTS"
    resultado: Dict[str, Any] = {
        "raiz": str(raiz.resolve()),
        "total_tests": 0,
        "por_bloque": {},
        "sin_clasificar": [],
    }
    if not carpeta_tests.exists():
        resultado["error"] = "No existe la carpeta TESTS"
        return resultado

    for archivo in sorted(carpeta_tests.glob("test_*.py")):
        bloque = clasificar_test(archivo.name)
        resultado["total_tests"] += 1
        resultado["por_bloque"].setdefault(bloque, []).append(archivo.name)
        if bloque == "Sin clasificar":
            resultado["sin_clasificar"].append(archivo.name)
    return resultado


def formatear_clasificacion_tests(resultado: Dict[str, Any], limite: int = 30) -> str:
    lineas: List[str] = []
    lineas.append("=== HOST AI 4.10.5 - CLASIFICADOR DE TESTS HISTORICOS ===")
    lineas.append(f"Raiz analizada: {resultado.get('raiz', '')}")
    if resultado.get("error"):
        lineas.append(f"Estado general: ERROR - {resultado['error']}")
        return "\n".join(lineas)
    lineas.append("Estado general: OK")
    lineas.append(f"Total tests detectados: {resultado.get('total_tests', 0)}")
    lineas.append("")
    lineas.append("Tests clasificados por bloque:")
    for bloque in sorted(resultado.get("por_bloque", {})):
        tests = resultado["por_bloque"][bloque]
        lineas.append(f"- {bloque}: {len(tests)}")
    sin = resultado.get("sin_clasificar", [])
    lineas.append("")
    lineas.append(f"Tests sin clasificar: {len(sin)}")
    for nombre in sin[:limite]:
        lineas.append(f"  - {nombre}")
    if len(sin) > limite:
        lineas.append(f"  ... y {len(sin) - limite} mas")
    lineas.append("")
    lineas.append("Recomendaciones:")
    lineas.append("- Incorporar esta clasificacion al Runner de tests para ejecutar bloques completos.")
    lineas.append("- Revisar manualmente los tests sin clasificar antes de eliminar o renombrar archivos antiguos.")
    return "\n".join(lineas)
