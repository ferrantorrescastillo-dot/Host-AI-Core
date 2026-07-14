from pathlib import Path
from typing import Any, Dict, List

BLOQUES = {
    "4.1 Catalogo": ["411", "412", "413", "414", "415", "416", "417", "418", "419"],
    "4.2 Proveedores": ["421", "422", "423"],
    "4.3 Stock": ["431", "432", "433", "434", "435", "436", "437", "438", "439"],
    "4.4 Recepcion": ["441", "442", "443", "444", "445", "446", "447", "448", "449", "4410", "4411", "4412", "4413", "4414", "4415"],
    "4.5 Producto/Base": ["451", "452", "453", "454", "455", "456", "457", "458"],
    "4.6 Produccion": ["461", "462", "463", "464", "465", "466", "467", "468"],
    "4.7 Eventos": ["471", "472", "473", "474", "475", "476", "477", "478"],
    "4.8 Rentabilidad": ["481", "482", "483", "484", "485", "486", "487", "488"],
    "4.9 IA Operativa": ["491", "492", "493", "494", "495", "496", "497", "498"],
    "4.10 Auditoria/Cierre": ["4101", "4102", "4103", "4104", "4105", "4106", "4107", "4108"],
}

CARPETAS = ["APP", "SERVICIOS", "MOTORES", "CORE", "MODELOS", "PIPELINES", "TESTS", "DOCS"]


def _codigo_en_nombre(nombre: str) -> str | None:
    base = Path(nombre).stem.lower()
    partes = base.split("_")
    for parte in reversed(partes):
        if parte.isdigit() and parte.startswith("4"):
            return parte
    # algunos nombres pueden incluir el codigo junto a texto
    for codigo in sorted([c for codigos in BLOQUES.values() for c in codigos], key=len, reverse=True):
        if codigo in base:
            return codigo
    return None


def bloque_por_codigo(codigo: str | None) -> str:
    if not codigo:
        return "Historico/Sin bloque 4.x"
    for bloque, codigos in BLOQUES.items():
        if codigo in codigos:
            return bloque
    return "Historico/Sin bloque 4.x"


def generar_mapa_maestro(raiz: str | Path = ".") -> Dict[str, Any]:
    raiz = Path(raiz)
    resultado: Dict[str, Any] = {
        "raiz": str(raiz.resolve()),
        "bloques": {bloque: [] for bloque in BLOQUES},
        "historicos": [],
        "resumen_carpetas": {},
        "total_archivos_mapeados": 0,
    }

    for carpeta in CARPETAS:
        ruta = raiz / carpeta
        if not ruta.exists():
            resultado["resumen_carpetas"][carpeta] = {"existe": False, "archivos": 0}
            continue
        archivos = sorted([p for p in ruta.glob("*.py") if p.name != "__init__.py"])
        resultado["resumen_carpetas"][carpeta] = {"existe": True, "archivos": len(archivos)}
        for archivo in archivos:
            codigo = _codigo_en_nombre(archivo.name)
            bloque = bloque_por_codigo(codigo)
            item = {"carpeta": carpeta, "archivo": archivo.name, "codigo": codigo or ""}
            if bloque in resultado["bloques"]:
                resultado["bloques"][bloque].append(item)
            else:
                resultado["historicos"].append(item)
            resultado["total_archivos_mapeados"] += 1
    return resultado


def formatear_mapa_maestro(resultado: Dict[str, Any], limite: int = 25) -> str:
    lineas: List[str] = []
    lineas.append("=== HOST AI 4.10.7 - MAPA MAESTRO DE MODULOS ===")
    lineas.append(f"Raiz analizada: {resultado.get('raiz', '')}")
    lineas.append("Estado general: OK")
    lineas.append(f"Total archivos mapeados: {resultado.get('total_archivos_mapeados', 0)}")
    lineas.append("")
    lineas.append("Carpetas:")
    for carpeta, info in resultado.get("resumen_carpetas", {}).items():
        estado = "OK" if info.get("existe") else "NO EXISTE"
        lineas.append(f"- {carpeta}: {estado} ({info.get('archivos', 0)} archivos py)")
    lineas.append("")
    lineas.append("Bloques 4.x:")
    for bloque, items in resultado.get("bloques", {}).items():
        lineas.append(f"- {bloque}: {len(items)} archivos")
        for item in items[:limite]:
            lineas.append(f"  - {item['carpeta']}/{item['archivo']}")
        if len(items) > limite:
            lineas.append(f"  ... y {len(items) - limite} mas")
    lineas.append("")
    lineas.append(f"Historicos / sin bloque 4.x: {len(resultado.get('historicos', []))}")
    for item in resultado.get("historicos", [])[:limite]:
        lineas.append(f"  - {item['carpeta']}/{item['archivo']}")
    lineas.append("")
    lineas.append("Uso recomendado:")
    lineas.append("- Usar este mapa como referencia antes de crear Host AI 5.0.")
    lineas.append("- Conectar cada nueva interfaz 5.x con servicios ya mapeados, no con scripts sueltos.")
    return "\n".join(lineas)
