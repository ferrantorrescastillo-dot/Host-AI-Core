from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import unicodedata


@dataclass
class CambioFamiliaProveedor:
    codigo: str
    nombre: str
    proveedor: Optional[str]
    familia_anterior: Optional[str]
    familia_nueva: str
    motivo: str


@dataclass
class InformeClasificacionProveedor:
    total_articulos: int
    sin_familia_antes: int
    familias_aplicadas: int
    sin_familia_despues: int
    cambios: List[CambioFamiliaProveedor] = field(default_factory=list)
    estado: str = "sin_datos"


class ClasificadorFamiliasProveedor4112:
    """
    Clasifica familias pendientes usando proveedor + palabras.

    Regla:
    - Solo rellena artículos sin familia.
    - No pisa familias existentes.
    - Primero usa palabras del nombre.
    - Si no hay palabra clara, usa proveedor como pista.
    """

    REGLAS_NOMBRE = [
        ("Verduras", ["tomate", "cebolla", "ajo", "puerro", "zanahoria", "pimiento", "patata", "lechuga", "escarola", "berenjena", "calabacin", "calabacín"]),
        ("Frutas", ["naranja", "limon", "limón", "manzana", "pera", "uva", "melon", "melón", "fresa", "mandarina"]),
        ("Carnes", ["pollo", "ternera", "cerdo", "butifarra", "secreto", "costilla", "chuleta", "hamburguesa", "longaniza"]),
        ("Pescados", ["bacalao", "merluza", "salmon", "salmón", "atun", "atún"]),
        ("Mariscos", ["gamba", "langostino", "calamar", "sepia", "pulpo", "mejillon", "mejillón", "almeja"]),
        ("Lácteos", ["queso", "leche", "nata", "mantequilla", "burrata"]),
        ("Bebidas", ["vino", "agua", "cerveza", "coca cola", "fanta", "refresco", "cava"]),
        ("Salsas", ["salsa", "mayonesa", "alioli", "romesco"]),
        ("Panadería", ["pan", "brioche", "briox", "mollete", "baguette"]),
    ]

    REGLAS_PROVEEDOR = [
        ("pau gavalda", "Verduras", "Proveedor habitual de fruta/verdura."),
        ("carnes palau", "Carnes", "Proveedor de carnes."),
        ("avicSA".lower(), "Carnes", "Proveedor de carnes/aves."),
        ("disbesa", "Bebidas", "Proveedor de bebidas."),
        ("bundo", "Panadería", "Proveedor asociado a panadería/pastelería."),
    ]

    def __init__(self, ruta_db: str = "DATOS/db/articulos.json") -> None:
        self.ruta_db = Path(ruta_db)

    def clasificar_y_actualizar(self) -> InformeClasificacionProveedor:
        articulos = self._leer_articulos()
        sin_familia_antes = sum(1 for a in articulos if not self._texto(a.get("familia")))
        cambios: List[CambioFamiliaProveedor] = []

        for articulo in articulos:
            if self._texto(articulo.get("familia")):
                continue

            nombre = str(articulo.get("nombre", "") or "")
            proveedor = self._texto(articulo.get("proveedor"))
            familia, motivo = self._proponer(nombre, proveedor)

            if not familia:
                continue

            articulo["familia"] = familia
            articulo["familia_asignada_por_proveedor"] = True

            cambios.append(
                CambioFamiliaProveedor(
                    codigo=str(articulo.get("codigo", "") or ""),
                    nombre=nombre,
                    proveedor=proveedor,
                    familia_anterior=None,
                    familia_nueva=familia,
                    motivo=motivo,
                )
            )

        self._guardar_articulos(articulos)
        sin_familia_despues = sum(1 for a in articulos if not self._texto(a.get("familia")))

        return InformeClasificacionProveedor(
            total_articulos=len(articulos),
            sin_familia_antes=sin_familia_antes,
            familias_aplicadas=len(cambios),
            sin_familia_despues=sin_familia_despues,
            cambios=cambios,
            estado=self._estado(len(articulos), sin_familia_despues),
        )

    def exportar_informe_txt(self, ruta_destino: str = "DATOS/db/informe_familias_proveedor_4_1_12.txt") -> InformeClasificacionProveedor:
        informe = self.clasificar_y_actualizar()
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.1.12 - CLASIFICADOR FAMILIAS POR PROVEEDOR",
            "=" * 70,
            f"Artículos: {informe.total_articulos}",
            f"Sin familia antes: {informe.sin_familia_antes}",
            f"Familias aplicadas: {informe.familias_aplicadas}",
            f"Sin familia después: {informe.sin_familia_despues}",
            f"Estado: {informe.estado}",
            "",
            "CAMBIOS",
            "-" * 70,
        ]

        for cambio in informe.cambios[:250]:
            lineas.append(f"{cambio.codigo} | {cambio.nombre} | {cambio.proveedor or '-'} -> {cambio.familia_nueva} | {cambio.motivo}")

        if len(informe.cambios) > 250:
            lineas.append(f"... {len(informe.cambios) - 250} cambios más")

        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return informe

    def _proponer(self, nombre: str, proveedor: Optional[str]) -> tuple[Optional[str], str]:
        nombre_norm = self._normalizar(nombre)
        proveedor_norm = self._normalizar(proveedor)

        for familia, palabras in self.REGLAS_NOMBRE:
            for palabra in palabras:
                if self._normalizar(palabra) in nombre_norm:
                    return familia, f"Palabra detectada: {palabra}"

        for proveedor_regla, familia, motivo in self.REGLAS_PROVEEDOR:
            if proveedor_regla and proveedor_regla in proveedor_norm:
                return familia, motivo

        return None, "Sin regla clara."

    def _leer_articulos(self) -> List[Dict[str, Any]]:
        if not self.ruta_db.exists():
            return []
        try:
            contenido = json.loads(self.ruta_db.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return contenido if isinstance(contenido, list) else []

    def _guardar_articulos(self, articulos: List[Dict[str, Any]]) -> None:
        self.ruta_db.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_db.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

    def _texto(self, valor: Any) -> Optional[str]:
        if valor is None:
            return None
        texto = str(valor).strip()
        return texto if texto else None

    def _normalizar(self, valor: Any) -> str:
        texto = "" if valor is None else str(valor)
        texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
        return texto.lower().strip().replace(".", "")

    def _estado(self, total: int, sin_familia: int) -> str:
        if total == 0:
            return "sin_datos"
        if sin_familia == 0:
            return "apto"
        return "apto_con_observaciones"


__all__ = [
    "ClasificadorFamiliasProveedor4112",
    "InformeClasificacionProveedor",
    "CambioFamiliaProveedor",
]
