from __future__ import annotations

from dataclasses import dataclass, asdict

from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.integrador_stock_escandallos_555a import calcular_necesidades_stock
from SERVICIOS.integrador_compras_escandallos_555a import preparar_compras_desde_faltantes
from SERVICIOS.integrador_produccion_escandallos_555a import preparar_plan_produccion


@dataclass(slots=True)
class ResultadoEventoEscandallado:
    evento: dict
    escandallo: str
    produccion: dict
    stock: list[dict]
    compras_propuestas: list[dict]
    incidencias: list[dict]
    datos_reales_modificados: bool = False

    def a_dict(self) -> dict:
        return asdict(self)


def analizar_evento_con_escandallo(
    evento: dict,
    repositorio: RepositorioEscandallos,
    ruta_stock: str = "DATOS/db/stock_inicial.json",
    ruta_articulos: str = "DATOS/db/articulos.json",
) -> ResultadoEventoEscandallado:
    """Integra evento, escandallo, producción, stock y compras en modo seguro."""
    personas = float(evento.get("personas", 0) or 0)
    menu = str(evento.get("menu") or evento.get("receta") or "").strip()
    if personas <= 0:
        raise ValueError("El evento necesita un número de personas válido")
    if not menu:
        raise ValueError("El evento necesita un menú o receta")

    coincidencias = repositorio.buscar_por_nombre(menu)
    if not coincidencias:
        raise LookupError(f"No existe un escandallo canónico para '{menu}'")
    escandallo = coincidencias[0]
    produccion = preparar_plan_produccion(escandallo, personas)
    necesidades = calcular_necesidades_stock(escandallo, personas, ruta_stock)
    compras = preparar_compras_desde_faltantes(necesidades, ruta_articulos)
    incidencias: list[dict] = []
    for linea in necesidades:
        if linea.faltante > 0:
            incidencias.append(
                {
                    "tipo": "falta_stock",
                    "gravedad": "ALTO" if linea.faltante >= linea.necesario * 0.5 else "MEDIO",
                    "articulo": linea.ingrediente,
                    "faltante": linea.faltante,
                    "unidad": linea.unidad,
                }
            )

    return ResultadoEventoEscandallado(
        evento=dict(evento),
        escandallo=escandallo.receta.nombre,
        produccion=produccion.a_dict(),
        stock=[x.a_dict() for x in necesidades],
        compras_propuestas=[x.a_dict() for x in compras],
        incidencias=incidencias,
    )
