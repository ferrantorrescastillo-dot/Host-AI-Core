from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


Category = str
Domain = str


@dataclass(frozen=True)
class Classification:
    category: Category
    reason: str
    domain_tags: tuple[Domain, ...]


KNOWN_DOMAINS: tuple[Domain, ...] = (
    "produccion",
    "stock",
    "compras",
    "recepcion",
    "eventos",
    "escandallos",
    "costes",
    "arquitectura",
    "ia",
    "general",
)


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(n in text for n in needles)


def classify_document(relative_path: str) -> Classification:
    """Clasifica un documento por ruta relativa y devuelve motivo trazable."""
    path_l = relative_path.replace("\\", "/").lower()
    name_l = PurePosixPath(path_l).name

    tags: set[Domain] = {"general"}

    if _contains_any(path_l, ("produccion", "piloto-1.3", "piloto-1.4", "prod")):
        tags.add("produccion")
    if _contains_any(path_l, ("stock", "inventario")):
        tags.add("stock")
    if _contains_any(path_l, ("compras", "pedido", "proveedor")):
        tags.add("compras")
    if _contains_any(path_l, ("recepcion", "albaran", "mercancia")):
        tags.add("recepcion")
    if _contains_any(path_l, ("eventos", "evento", "banquete")):
        tags.add("eventos")
    if _contains_any(path_l, ("escandallo", "receta", "coste_receta")):
        tags.add("escandallos")
    if _contains_any(path_l, ("coste", "rentabilidad", "margen")):
        tags.add("costes")
    if _contains_any(path_l, ("arquitectura", "roc", "knowledge_core", "devkit")):
        tags.add("arquitectura")
    if _contains_any(path_l, ("ia", "codex", "agent", "agents")):
        tags.add("ia")

    if name_l in {"agents.md", "master_plan.md", "codex-01.md", "codex-02.md"}:
        return Classification(
            category="gobierno",
            reason="Documento de gobernanza y método operativo del repositorio",
            domain_tags=tuple(sorted(tags)),
        )

    if "roc/" in path_l or name_l.startswith("roc-"):
        return Classification(
            category="arquitectura",
            reason="Documento ROC de arquitectura y dominio",
            domain_tags=tuple(sorted(tags | {"arquitectura"})),
        )

    if _contains_any(path_l, ("knowledge_core", "reglas", "identidad", "certificaciones")):
        return Classification(
            category="gobierno",
            reason="Normativa oficial de proyecto (DEVKIT/Knowledge Core)",
            domain_tags=tuple(sorted(tags | {"arquitectura"})),
        )

    if _contains_any(path_l, ("arquitectura", "architecture")):
        return Classification(
            category="arquitectura",
            reason="Describe arquitectura, componentes o dependencias",
            domain_tags=tuple(sorted(tags | {"arquitectura"})),
        )

    if _contains_any(path_l, ("agent", "codex", "prompt", "manual operativo")):
        return Classification(
            category="ejecucion de agentes",
            reason="Guía de operación para agentes o IA",
            domain_tags=tuple(sorted(tags | {"ia"})),
        )

    if _contains_any(path_l, ("roadmap", "plan", "sprint", "pendientes")):
        return Classification(
            category="referencia",
            reason="Planificación, backlog o referencia de ejecución",
            domain_tags=tuple(sorted(tags)),
        )

    if _contains_any(path_l, ("changelog", "historico", "legacy", "stable", "rr")):
        return Classification(
            category="historico",
            reason="Documento histórico o de trazabilidad de versiones",
            domain_tags=tuple(sorted(tags)),
        )

    if _contains_any(path_l, ("produccion", "stock", "compras", "recepcion", "eventos", "escandallos", "coste")):
        return Classification(
            category="dominio funcional",
            reason="Documento funcional orientado a un dominio operativo",
            domain_tags=tuple(sorted(tags)),
        )

    return Classification(
        category="desconocido",
        reason="No coincide con reglas explícitas de clasificación",
        domain_tags=tuple(sorted(tags)),
    )


def default_category_rank(category: Category) -> int:
    """Orden de prioridad base si no hay reglas más fuertes."""
    rank = {
        "gobierno": 10,
        "arquitectura": 20,
        "ejecucion de agentes": 30,
        "dominio funcional": 40,
        "referencia": 50,
        "historico": 60,
        "desconocido": 70,
    }
    return rank.get(category, 90)
