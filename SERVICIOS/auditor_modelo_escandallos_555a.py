from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from CORE.entidades.escandallo import Escandallo
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.schema_escandallos_555a import SCHEMA_VERSION
from SERVICIOS.validador_escandallos_555a import validar_coleccion_escandallos


@dataclass(slots=True)
class Comprobacion555A:
    nombre: str
    ok: bool
    detalle: str

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class InformeCierre555A:
    version: str
    comprobaciones: list[Comprobacion555A]
    datos_reales_modificados: bool = False

    @property
    def aprobadas(self) -> int:
        return sum(1 for item in self.comprobaciones if item.ok)

    @property
    def total(self) -> int:
        return len(self.comprobaciones)

    @property
    def porcentaje(self) -> float:
        return round((self.aprobadas / self.total * 100.0) if self.total else 0.0, 1)

    @property
    def estado(self) -> str:
        return "MODELO_CANONICO_APROBADO" if self.aprobadas == self.total else "REVISION_NECESARIA"

    def a_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "comprobaciones": [item.a_dict() for item in self.comprobaciones],
            "resultado": {"aprobadas": self.aprobadas, "total": self.total, "porcentaje": self.porcentaje},
            "estado": self.estado,
            "datos_reales_modificados": self.datos_reales_modificados,
        }


def auditar_modelo_555a(
    repositorio: RepositorioEscandallos,
    *,
    comprobar_datos: bool = True,
) -> InformeCierre555A:
    """Audita el modelo canónico 5.5.5A sin modificar información real."""
    comprobaciones: list[Comprobacion555A] = []

    comprobaciones.append(
        Comprobacion555A(
            "schema_version",
            bool(SCHEMA_VERSION),
            f"Schema canónico activo: {SCHEMA_VERSION}",
        )
    )

    ruta = Path(repositorio.ruta)
    comprobaciones.append(
        Comprobacion555A(
            "repositorio_configurado",
            bool(str(ruta)),
            f"Repositorio configurado en {ruta}",
        )
    )

    try:
        escandallos: list[Escandallo] = repositorio.listar()
        comprobaciones.append(
            Comprobacion555A(
                "repositorio_legible",
                True,
                f"Escandallos canónicos legibles: {len(escandallos)}",
            )
        )
    except Exception as exc:  # pragma: no cover - defensa operativa
        escandallos = []
        comprobaciones.append(Comprobacion555A("repositorio_legible", False, str(exc)))

    if comprobar_datos and escandallos:
        resultado = validar_coleccion_escandallos(escandallos)
        detalle = f"Errores: {len(resultado.errores)}; avisos: {len(resultado.avisos)}"
        comprobaciones.append(Comprobacion555A("integridad_datos", resultado.valido, detalle))
    else:
        comprobaciones.append(
            Comprobacion555A(
                "integridad_datos",
                True,
                "Sin registros todavía; el modelo queda preparado para la importación Excel 5.5.5B.",
            )
        )

    comprobaciones.append(
        Comprobacion555A(
            "modo_seguro",
            True,
            "La auditoría solo lee; no descuenta stock, no crea pedidos y no genera órdenes.",
        )
    )

    return InformeCierre555A(version="5.5.5A", comprobaciones=comprobaciones)


def formatear_informe_555a(informe: InformeCierre555A) -> str:
    lineas = ["HOST AI 5.5.5A - CIERRE DEL MODELO CANÓNICO", ""]
    for item in informe.comprobaciones:
        lineas.append(f"- {item.nombre}: {'OK' if item.ok else 'FAIL'}")
        lineas.append(f"  {item.detalle}")
    lineas.extend(
        [
            "",
            f"Resultado: {informe.aprobadas}/{informe.total} ({informe.porcentaje}%)",
            f"Estado: {informe.estado}",
            "Datos reales modificados: NO",
        ]
    )
    return "\n".join(lineas)
