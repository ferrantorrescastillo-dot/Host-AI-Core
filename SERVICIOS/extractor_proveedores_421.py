from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict
import json
import unicodedata


@dataclass
class ProveedorHostAI:
    codigo: str
    nombre: str
    nombre_normalizado: str
    articulos_asociados: int
    variantes_detectadas: List[str] = field(default_factory=list)
    estado: str = "activo"
    observaciones: Optional[str] = None


@dataclass
class InformeExtraccionProveedores:
    total_articulos: int
    articulos_sin_proveedor: int
    proveedores_detectados: int
    duplicados_sospechosos: int
    ruta_destino: str
    estado: str
    recomendaciones: List[str] = field(default_factory=list)


class ExtractorProveedores421:
    """
    Extrae proveedores reales desde DATOS/db/articulos.json
    y genera DATOS/db/proveedores.json.
    """

    def __init__(
        self,
        ruta_articulos: str = "DATOS/db/articulos.json",
        ruta_proveedores: str = "DATOS/db/proveedores.json",
    ) -> None:
        self.ruta_articulos = Path(ruta_articulos)
        self.ruta_proveedores = Path(ruta_proveedores)

    def extraer(self) -> InformeExtraccionProveedores:
        articulos = self._leer_json_lista(self.ruta_articulos)

        grupos: Dict[str, List[str]] = defaultdict(list)
        conteo_articulos: Dict[str, int] = defaultdict(int)
        sin_proveedor = 0

        for articulo in articulos:
            proveedor = self._texto(articulo.get("proveedor"))

            if not proveedor:
                sin_proveedor += 1
                continue

            normalizado = self._normalizar_proveedor(proveedor)
            grupos[normalizado].append(proveedor)
            conteo_articulos[normalizado] += 1

        proveedores: List[ProveedorHostAI] = []
        duplicados_sospechosos = 0

        for indice, (normalizado, variantes) in enumerate(sorted(grupos.items()), start=1):
            variantes_unicas = sorted(set(v.strip() for v in variantes if v and v.strip()))
            nombre_principal = self._elegir_nombre_principal(variantes_unicas)
            codigo = f"PROV{indice:04d}"

            if len(variantes_unicas) > 1:
                duplicados_sospechosos += 1

            proveedores.append(
                ProveedorHostAI(
                    codigo=codigo,
                    nombre=nombre_principal,
                    nombre_normalizado=normalizado,
                    articulos_asociados=conteo_articulos[normalizado],
                    variantes_detectadas=variantes_unicas,
                    observaciones="Variantes detectadas. Revisar nombre oficial." if len(variantes_unicas) > 1 else None,
                )
            )

        self._guardar_proveedores(proveedores)

        estado = self._calcular_estado(
            total_articulos=len(articulos),
            sin_proveedor=sin_proveedor,
            duplicados_sospechosos=duplicados_sospechosos,
        )

        recomendaciones = self._recomendaciones(sin_proveedor, duplicados_sospechosos)

        return InformeExtraccionProveedores(
            total_articulos=len(articulos),
            articulos_sin_proveedor=sin_proveedor,
            proveedores_detectados=len(proveedores),
            duplicados_sospechosos=duplicados_sospechosos,
            ruta_destino=str(self.ruta_proveedores),
            estado=estado,
            recomendaciones=recomendaciones,
        )

    def _leer_json_lista(self, ruta: Path) -> List[Dict[str, Any]]:
        if not ruta.exists():
            return []
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return contenido if isinstance(contenido, list) else []

    def _guardar_proveedores(self, proveedores: List[ProveedorHostAI]) -> None:
        self.ruta_proveedores.parent.mkdir(parents=True, exist_ok=True)
        datos = [asdict(proveedor) for proveedor in proveedores]
        self.ruta_proveedores.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    def _texto(self, valor: Any) -> Optional[str]:
        if valor is None:
            return None
        texto = str(valor).strip()
        return texto if texto else None

    def _normalizar_proveedor(self, nombre: str) -> str:
        texto = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode("ascii")
        texto = texto.lower().strip()
        texto = texto.replace(".", "").replace(",", "").replace(";", "")
        texto = " ".join(texto.split())
        return texto

    def _elegir_nombre_principal(self, variantes: List[str]) -> str:
        if not variantes:
            return "SIN_NOMBRE"
        return sorted(variantes, key=lambda x: (len(x), x.lower()))[0]

    def _calcular_estado(self, total_articulos: int, sin_proveedor: int, duplicados_sospechosos: int) -> str:
        if total_articulos == 0:
            return "sin_datos"
        if duplicados_sospechosos or sin_proveedor:
            return "apto_con_observaciones"
        return "apto"

    def _recomendaciones(self, sin_proveedor: int, duplicados_sospechosos: int) -> List[str]:
        recomendaciones: List[str] = []

        if sin_proveedor:
            recomendaciones.append("Completar proveedor en artículos sin proveedor para mejorar compras y pedidos.")
        if duplicados_sospechosos:
            recomendaciones.append("Revisar variantes de proveedor para elegir un nombre oficial único.")
        if not recomendaciones:
            recomendaciones.append("Base de proveedores preparada para trabajar.")

        return recomendaciones


__all__ = ["ExtractorProveedores421", "ProveedorHostAI", "InformeExtraccionProveedores"]
