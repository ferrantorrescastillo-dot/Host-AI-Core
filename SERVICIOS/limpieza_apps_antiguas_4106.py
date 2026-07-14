from pathlib import Path
from typing import Dict, List, Any


def _clave_modulo(nombre: str) -> str:
    base = Path(nombre).stem.lower()
    partes = base.split("_")
    if partes and partes[-1].isdigit():
        partes = partes[:-1]
    return "_".join(partes)


def analizar_apps_antiguas(raiz: str | Path = ".") -> Dict[str, Any]:
    raiz = Path(raiz)
    app_dir = raiz / "APP"
    servicios_dir = raiz / "SERVICIOS"
    tests_dir = raiz / "TESTS"
    resultado: Dict[str, Any] = {
        "raiz": str(raiz.resolve()),
        "apps_total": 0,
        "wrappers_validos": [],
        "apps_sin_servicio": [],
        "apps_sin_test": [],
        "candidatas_revision": [],
    }
    if not app_dir.exists():
        resultado["error"] = "No existe la carpeta APP"
        return resultado

    servicios = list(servicios_dir.glob("*.py")) if servicios_dir.exists() else []
    tests = list(tests_dir.glob("test_*.py")) if tests_dir.exists() else []
    claves_servicios = {_clave_modulo(s.name) for s in servicios}
    claves_tests = {_clave_modulo(t.name.replace("test_", "", 1)) for t in tests}

    for app in sorted(app_dir.glob("*.py")):
        if app.name == "__init__.py":
            continue
        resultado["apps_total"] += 1
        clave = _clave_modulo(app.name)
        tiene_servicio = clave in claves_servicios
        tiene_test = clave in claves_tests or any(clave in c or c in clave for c in claves_tests)
        item = app.name
        if tiene_servicio:
            resultado["wrappers_validos"].append(item)
        else:
            resultado["apps_sin_servicio"].append(item)
        if not tiene_test:
            resultado["apps_sin_test"].append(item)
        if not tiene_servicio or not tiene_test:
            resultado["candidatas_revision"].append({
                "app": item,
                "tiene_servicio": tiene_servicio,
                "tiene_test": tiene_test,
                "accion_recomendada": "revisar_conexion" if tiene_servicio else "crear_servicio_o_marcar_wrapper_legacy",
            })
    return resultado


def formatear_limpieza_apps(resultado: Dict[str, Any], limite: int = 30) -> str:
    lineas: List[str] = []
    lineas.append("=== HOST AI 4.10.6 - LIMPIEZA DE APPS ANTIGUAS ===")
    lineas.append(f"Raiz analizada: {resultado.get('raiz', '')}")
    if resultado.get("error"):
        lineas.append(f"Estado general: ERROR - {resultado['error']}")
        return "\n".join(lineas)
    lineas.append("Estado general: OK")
    lineas.append(f"APPs detectadas: {resultado.get('apps_total', 0)}")
    lineas.append(f"Wrappers con servicio parecido: {len(resultado.get('wrappers_validos', []))}")
    lineas.append(f"APPs sin servicio parecido: {len(resultado.get('apps_sin_servicio', []))}")
    lineas.append(f"APPs sin test parecido: {len(resultado.get('apps_sin_test', []))}")
    lineas.append("")
    lineas.append("APPs candidatas a revision:")
    for item in resultado.get("candidatas_revision", [])[:limite]:
        lineas.append(
            f"  - {item['app']} | servicio={item['tiene_servicio']} | test={item['tiene_test']} | accion={item['accion_recomendada']}"
        )
    restantes = len(resultado.get("candidatas_revision", [])) - limite
    if restantes > 0:
        lineas.append(f"  ... y {restantes} mas")
    lineas.append("")
    lineas.append("Regla de limpieza recomendada:")
    lineas.append("- No borrar nada automaticamente.")
    lineas.append("- Mantener APP como wrapper si llama a SERVICIOS y tiene test.")
    lineas.append("- Revisar o documentar APPs sin servicio antes de construir interfaz 5.0.")
    return "\n".join(lineas)
