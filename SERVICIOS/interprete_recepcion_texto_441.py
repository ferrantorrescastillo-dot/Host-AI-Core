from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, List, Optional
from pathlib import Path
from datetime import datetime
import json
import re
import unicodedata


@dataclass
class LineaRecepcionTexto441:
    producto: str
    cantidad: float
    unidad: str
    proveedor: Optional[str] = None
    precio_unitario: Optional[float] = None
    texto_origen: str = ""


@dataclass
class ResultadoInterpretacionRecepcion441:
    texto_original: str
    proveedor_general: Optional[str]
    lineas: List[LineaRecepcionTexto441] = field(default_factory=list)
    errores: List[str] = field(default_factory=list)
    estado: str = "sin_datos"

    @property
    def total_lineas(self) -> int:
        return len(self.lineas)


class InterpreteRecepcionTexto441:
    """
    Host AI 4.4.1 — Intérprete de recepción por texto.

    Convierte frases de cocina en líneas estructuradas.

    Ejemplos:
    - "Han llegado 15 kg de arroz bomba de Makro a 3,20 €/kg"
    - "De Makro han llegado 15 kg arroz bomba, 6 l aceite oliva"
    - "Recibido 4 cajas coca cola de Disbesa"
    """

    UNIDADES = {
        "kg": "kg",
        "kilo": "kg",
        "kilos": "kg",
        "kilogramo": "kg",
        "kilogramos": "kg",
        "g": "g",
        "gr": "g",
        "gramo": "g",
        "gramos": "g",
        "l": "l",
        "litro": "l",
        "litros": "l",
        "lt": "l",
        "ml": "ml",
        "ud": "ud",
        "uds": "ud",
        "unidad": "ud",
        "unidades": "ud",
        "caja": "caja",
        "cajas": "caja",
        "bolsa": "bolsa",
        "bolsas": "bolsa",
        "bote": "bote",
        "botes": "bote",
        "paquete": "paquete",
        "paquetes": "paquete",
    }

    PALABRAS_ENTRADA = [
        "han llegado",
        "ha llegado",
        "recibido",
        "recibida",
        "recibidos",
        "entra",
        "entrada",
        "pedido recibido",
        "albaran",
        "albarán",
    ]

    def interpretar(self, texto: str) -> ResultadoInterpretacionRecepcion441:
        texto_original = texto or ""
        limpio = self._limpiar_texto(texto_original)

        if not limpio:
            return ResultadoInterpretacionRecepcion441(
                texto_original=texto_original,
                proveedor_general=None,
                errores=["Texto vacío."],
                estado="error",
            )

        proveedor_general = self._detectar_proveedor_general(texto_original)
        segmentos = self._segmentar_lineas(texto_original)

        lineas: List[LineaRecepcionTexto441] = []
        errores: List[str] = []

        for segmento in segmentos:
            linea = self._parsear_segmento(segmento, proveedor_general)
            if linea:
                lineas.append(linea)
            elif self._contiene_numero(segmento):
                errores.append(f"No he podido interpretar: {segmento.strip()}")

        estado = "ok" if lineas and not errores else "parcial" if lineas else "error"

        return ResultadoInterpretacionRecepcion441(
            texto_original=texto_original,
            proveedor_general=proveedor_general,
            lineas=lineas,
            errores=errores,
            estado=estado,
        )

    def guardar_resultado(
        self,
        resultado: ResultadoInterpretacionRecepcion441,
        ruta_destino: str = "DATOS/db/recepcion_texto_4_4_1.json",
    ) -> None:
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        datos = asdict(resultado)
        datos["fecha_interpretacion"] = datetime.now().isoformat(timespec="seconds")
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    def interpretar_y_guardar(
        self,
        texto: str,
        ruta_destino: str = "DATOS/db/recepcion_texto_4_4_1.json",
    ) -> ResultadoInterpretacionRecepcion441:
        resultado = self.interpretar(texto)
        self.guardar_resultado(resultado, ruta_destino)
        return resultado

    def _parsear_segmento(self, segmento: str, proveedor_general: Optional[str]) -> Optional[LineaRecepcionTexto441]:
        original = segmento.strip(" .;,\n\t")
        if not original:
            return None

        # Patrón principal: cantidad + unidad + producto + proveedor opcional + precio opcional.
        patron = re.compile(
            r"(?P<cantidad>\d+(?:[,.]\d+)?)\s*"
            r"(?P<unidad>kg|kilos?|kilogramos?|g|gr|gramos?|l|lt|litros?|ml|uds?|unidades?|cajas?|bolsas?|botes?|paquetes?)\s+"
            r"(?P<producto>.+?)"
            r"(?:\s+(?:de|del|a|por)\s+(?P<proveedor>[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 ._-]{2,30}))?"
            r"(?:\s+(?:a|precio|vale|precio\s+unitario)\s+(?P<precio>\d+(?:[,.]\d+)?)\s*(?:€|eur|euros)?(?:\s*/?\s*(?:kg|l|ud|unidad|caja))?)?$",
            re.IGNORECASE,
        )

        match = patron.search(original)
        if not match:
            return None

        cantidad = self._numero(match.group("cantidad"))
        unidad = self._normalizar_unidad(match.group("unidad"))
        producto = self._limpiar_producto(match.group("producto") or "")
        proveedor = self._limpiar_proveedor(match.group("proveedor")) or proveedor_general
        precio = self._numero(match.group("precio"))

        if cantidad is None or not unidad or not producto:
            return None

        # Si el proveedor capturado parece realmente precio o texto raro, lo descartamos.
        if proveedor and any(p in proveedor.lower() for p in ["precio", "vale", "euro", "€"]):
            proveedor = proveedor_general

        return LineaRecepcionTexto441(
            producto=producto,
            cantidad=cantidad,
            unidad=unidad,
            proveedor=proveedor,
            precio_unitario=precio,
            texto_origen=original,
        )

    def _segmentar_lineas(self, texto: str) -> List[str]:
        texto = texto.replace("\n", ",")

        # Protege comas decimales para no partir precios/cantidades tipo 3,20.
        protegidas: dict[str, str] = {}

        def proteger_decimal(match: re.Match) -> str:
            token = f"__DECIMAL_{len(protegidas)}__"
            protegidas[token] = match.group(0).replace(",", ".")
            return token

        texto = re.sub(r"\d+,\d+", proteger_decimal, texto)

        texto = re.sub(r"\s+y\s+(?=\d)", ", ", texto, flags=re.IGNORECASE)
        texto = re.sub(r"\s+ademas\s+(?=\d)", ", ", texto, flags=re.IGNORECASE)
        partes = [p.strip() for p in re.split(r"[,;]", texto) if p.strip()]

        resultado = []
        for parte in partes:
            for token, valor in protegidas.items():
                parte = parte.replace(token, valor)

            # Si una frase tiene introducción antes de la cantidad, la recortamos.
            recorte = re.search(r"\d+(?:[,.]\d+)?\s*(?:kg|kilos?|kilogramos?|g|gr|gramos?|l|lt|litros?|ml|uds?|unidades?|cajas?|bolsas?|botes?|paquetes?)\b.*", parte, re.IGNORECASE)
            resultado.append(recorte.group(0) if recorte else parte)

        return resultado

    def _detectar_proveedor_general(self, texto: str) -> Optional[str]:
        patrones = [
            r"\bde\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 ._-]{2,30})\s+(?:han|ha)\s+llegado\b",
            r"\bproveedor\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 ._-]{2,30})\b",
            r"\bpedido\s+de\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 ._-]{2,30})\b",
        ]
        for patron in patrones:
            m = re.search(patron, texto, re.IGNORECASE)
            if m:
                return self._limpiar_proveedor(m.group(1))
        return None

    def _limpiar_producto(self, producto: str) -> str:
        producto = producto.strip(" .;,\n\t")
        producto = re.sub(r"\s+(?:de|del|a|por)\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 ._-]{2,30}$", "", producto, flags=re.IGNORECASE)
        producto = re.sub(r"\s+(?:a|precio|vale)\s+\d+(?:[,.]\d+)?\s*(?:€|eur|euros)?.*$", "", producto, flags=re.IGNORECASE)
        return producto.strip(" .;,\n\t")

    def _limpiar_proveedor(self, proveedor: Optional[str]) -> Optional[str]:
        if proveedor is None:
            return None
        proveedor = proveedor.strip(" .;,\n\t")
        proveedor = re.sub(r"\s+(?:a|precio|vale)\s+.*$", "", proveedor, flags=re.IGNORECASE)
        return proveedor or None

    def _normalizar_unidad(self, unidad: str) -> str:
        return self.UNIDADES.get((unidad or "").strip().lower(), (unidad or "").strip().lower())

    def _numero(self, valor: Any) -> Optional[float]:
        if valor is None or str(valor).strip() == "":
            return None
        try:
            return float(str(valor).replace(",", ".").strip())
        except ValueError:
            return None

    def _contiene_numero(self, texto: str) -> bool:
        return bool(re.search(r"\d", texto or ""))

    def _limpiar_texto(self, texto: str) -> str:
        texto = unicodedata.normalize("NFKC", texto or "")
        return " ".join(texto.strip().split())


__all__ = [
    "InterpreteRecepcionTexto441",
    "LineaRecepcionTexto441",
    "ResultadoInterpretacionRecepcion441",
]
