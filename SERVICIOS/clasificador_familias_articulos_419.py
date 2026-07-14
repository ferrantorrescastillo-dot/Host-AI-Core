from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import unicodedata


@dataclass
class CambioFamiliaArticulo:
    codigo: str
    nombre: str
    familia_anterior: Optional[str]
    familia_nueva: str
    confianza: float
    motivo: str
    aplicado: bool


@dataclass
class InformeClasificacionFamilias:
    total_articulos: int
    sin_familia_antes: int
    familias_aplicadas: int
    sin_familia_despues: int
    cambios: List[CambioFamiliaArticulo] = field(default_factory=list)
    estado: str = "sin_datos"

    @property
    def total_cambios(self) -> int:
        return len(self.cambios)


class ClasificadorFamiliasArticulos419:
    """
    Clasifica familias de artículos reales.

    Fix 4.1.9.1:
    - Prioriza bebidas antes de panadería para evitar que "Coca Cola"
      se clasifique como "Panadería" por contener la palabra "coca".
    - Mantiene la regla de no pisar familias existentes.
    """

    REGLAS_PRIORITARIAS = [
        ("Bebidas", ["coca cola", "fanta", "sprite", "agua", "cerveza", "vino", "vermut", "tonica", "tónica", "refresco", "nestea", "aquarius", "cava"]),
    ]

    REGLAS_FAMILIA = [
        ("Aceites", ["aceite", "aove"]),
        ("Arroces y cereales", ["arroz", "fideo", "pasta", "quinoa", "cous cous", "cuscus"]),
        ("Harinas", ["harina", "maicena", "panko", "pan rallado"]),
        ("Carnes", ["pollo", "ternera", "cerdo", "secreto", "carrillera", "solomillo", "chuleta", "costilla", "pato", "butifarra", "hamburguesa", "longaniza", "beicon", "bacon"]),
        ("Pescados", ["bacalao", "merluza", "sardina", "salmon", "salmón", "corvina", "atun", "atún", "lubina", "dorada"]),
        ("Mariscos", ["gamba", "langostino", "sepia", "calamar", "pulpo", "mejillon", "mejillón", "almeja", "bogavante", "cigala"]),
        ("Verduras", ["tomate", "cebolla", "ajo", "puerro", "zanahoria", "pimiento", "alcachofa", "calcot", "calçot", "patata", "berenjena", "calabacin", "calabacín", "lechuga", "escarola", "espinaca"]),
        ("Frutas", ["limon", "limón", "naranja", "manzana", "uva", "pera", "maracuya", "maracuyá", "fresa", "melon", "melón"]),
        ("Lácteos", ["leche", "nata", "queso", "mantequilla", "yogur", "buratta", "burrata"]),
        ("Huevos", ["huevo", "huevos"]),
        ("Especias y condimentos", ["sal", "pimienta", "pimenton", "pimentón", "curry", "comino", "azafran", "azafrán", "jengibre", "canela", "oregano", "orégano"]),
        ("Panadería", ["pan", "brioche", "briox", "coca de", "coca salada", "tostad", "mollete", "baguette"]),
        ("Salsas", ["salsa", "romesco", "mayonesa", "alioli", "brava", "ketchup"]),
        ("Conservas", ["lata", "conserva", "anchoa", "oliva", "triturado", "tomate frito"]),
        ("Consumibles", ["servilleta", "caja", "bolsa", "film", "aluminio", "guante", "bandeja", "vaso", "tapa", "envase"]),
        ("Aperitivos", ["a.p", "aperitivo", "brocheta", "buñuelo", "degustacion", "degustación"]),
        ("Postres", ["postre", "tarta", "brownie", "flan", "helado", "sorbete", "mousse", "pastel"]),
        ("Elaboraciones", ["fondo", "caldo", "fumet", "base", "crema", "pure", "puré", "sofrito", "bechamel"]),
    ]

    def __init__(self, ruta_db: str = "DATOS/db/articulos.json") -> None:
        self.ruta_db = Path(ruta_db)

    def clasificar_y_actualizar(self) -> InformeClasificacionFamilias:
        articulos = self._leer_articulos()

        sin_familia_antes = sum(1 for articulo in articulos if not self._texto(articulo.get("familia")))
        cambios: List[CambioFamiliaArticulo] = []

        for articulo in articulos:
            familia_actual = self._texto(articulo.get("familia"))
            if familia_actual:
                continue

            nombre = str(articulo.get("nombre", "") or "")
            familia, confianza, motivo = self._proponer_familia(nombre)

            if familia:
                articulo["familia"] = familia
                cambios.append(
                    CambioFamiliaArticulo(
                        codigo=str(articulo.get("codigo", "")),
                        nombre=nombre,
                        familia_anterior=familia_actual,
                        familia_nueva=familia,
                        confianza=confianza,
                        motivo=motivo,
                        aplicado=True,
                    )
                )

        self._guardar_articulos(articulos)

        sin_familia_despues = sum(1 for articulo in articulos if not self._texto(articulo.get("familia")))
        estado = self._estado(len(articulos), sin_familia_despues)

        return InformeClasificacionFamilias(
            total_articulos=len(articulos),
            sin_familia_antes=sin_familia_antes,
            familias_aplicadas=len(cambios),
            sin_familia_despues=sin_familia_despues,
            cambios=cambios,
            estado=estado,
        )

    def exportar_informe_txt(self, ruta_destino: str = "DATOS/db/informe_familias_4_1_9.txt") -> InformeClasificacionFamilias:
        informe = self.clasificar_y_actualizar()
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.1.9.1 - CLASIFICADOR DE FAMILIAS",
            "=" * 58,
            f"Artículos: {informe.total_articulos}",
            f"Sin familia antes: {informe.sin_familia_antes}",
            f"Familias aplicadas: {informe.familias_aplicadas}",
            f"Sin familia después: {informe.sin_familia_despues}",
            f"Estado: {informe.estado}",
            "",
            "CAMBIOS APLICADOS",
            "-" * 58,
        ]

        for cambio in informe.cambios[:200]:
            lineas.append(f"{cambio.codigo} | {cambio.nombre} -> {cambio.familia_nueva} ({round(cambio.confianza*100, 1)}%)")

        if len(informe.cambios) > 200:
            lineas.append(f"... {len(informe.cambios) - 200} cambios más")

        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return informe

    def _proponer_familia(self, nombre: str) -> tuple[Optional[str], float, str]:
        nombre_norm = self._normalizar(nombre)

        if not nombre_norm:
            return None, 0.0, "Nombre vacío."

        for familia, palabras in self.REGLAS_PRIORITARIAS:
            for palabra in palabras:
                palabra_norm = self._normalizar(palabra)
                if palabra_norm and palabra_norm in nombre_norm:
                    return familia, 0.95, f"Detectado por regla prioritaria: {palabra}"

        for familia, palabras in self.REGLAS_FAMILIA:
            for palabra in palabras:
                palabra_norm = self._normalizar(palabra)
                if palabra_norm and palabra_norm in nombre_norm:
                    return familia, 0.90, f"Detectado por palabra clave: {palabra}"

        return None, 0.0, "Sin regla clara."

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

    def _normalizar(self, texto: Any) -> str:
        texto = "" if texto is None else str(texto)
        texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
        return texto.strip().lower()

    def _estado(self, total: int, sin_familia_despues: int) -> str:
        if total == 0:
            return "sin_datos"
        if sin_familia_despues == 0:
            return "apto"
        if sin_familia_despues < total:
            return "apto_con_observaciones"
        return "revisar"


__all__ = [
    "ClasificadorFamiliasArticulos419",
    "InformeClasificacionFamilias",
    "CambioFamiliaArticulo",
]
