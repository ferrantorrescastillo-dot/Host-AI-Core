from __future__ import annotations

import calendar
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class EntidadExtraidaIA12:
    tipo: str
    valor: Any
    texto: str
    confianza: float
    inicio: int = -1
    fin: int = -1


class ExtractorDatosIA12:
    """Extractor determinista y extensible de entidades para Host AI IA1.2.

    Solo interpreta texto. No ejecuta acciones ni modifica datos.
    """

    VERSION = "6.0.4-IA1.2"

    MESES = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "setiembre": 9, "octubre": 10,
        "noviembre": 11, "diciembre": 12,
    }
    DIAS_SEMANA = {
        "lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3,
        "viernes": 4, "sabado": 5, "domingo": 6,
    }
    UNIDADES = {
        "kg": "kg", "kilo": "kg", "kilos": "kg", "kilogramo": "kg", "kilogramos": "kg",
        "g": "g", "gr": "g", "gramo": "g", "gramos": "g",
        "l": "L", "litro": "L", "litros": "L",
        "ml": "ml", "mililitro": "ml", "mililitros": "ml",
        "u": "u", "ud": "u", "uds": "u", "unidad": "u", "unidades": "u",
        "caja": "caja", "cajas": "caja", "paquete": "paquete", "paquetes": "paquete",
        "bandeja": "bandeja", "bandejas": "bandeja", "saco": "saco", "sacos": "saco",
    }
    TIPOS_EVENTO = ("boda", "catering", "comunion", "comunión", "evento", "banquete", "coctel", "cóctel")
    UBICACIONES = (
        "camara", "cámara", "congelador", "seco", "almacen", "almacén",
        "produccion", "producción", "obrador", "cocina", "evento", "frigorifico", "frigorífico",
    )
    PALABRAS_NUMERO = {
        "un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4,
        "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
        "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
        "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
        "veinte": 20, "treinta": 30, "cuarenta": 40, "cincuenta": 50,
        "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90,
        "cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300,
    }

    def extraer(
        self,
        texto: str,
        intent: str | None = None,
        contexto: Dict[str, Any] | None = None,
        fecha_referencia: date | None = None,
    ) -> Dict[str, Any]:
        contexto = contexto or {}
        original = texto or ""
        normalizado = self.normalizar(original)
        referencia = fecha_referencia or date.today()
        entidades: List[EntidadExtraidaIA12] = []

        self._agregar(entidades, self._extraer_fecha(original, normalizado, referencia))
        self._agregar(entidades, self._extraer_hora(original, normalizado))
        self._agregar(entidades, self._extraer_pax(original, normalizado))
        self._agregar_varios(entidades, self._extraer_cantidades_unidades(original, normalizado))
        self._agregar(entidades, self._extraer_precio(original, normalizado))
        self._agregar(entidades, self._extraer_tipo_evento(original, normalizado))
        self._agregar(entidades, self._extraer_proveedor(original, normalizado))
        self._agregar(entidades, self._extraer_cliente(original, normalizado))
        self._agregar(entidades, self._extraer_ubicacion(original, normalizado))
        self._agregar(entidades, self._extraer_receta(original, normalizado, intent))
        self._agregar(entidades, self._extraer_articulo(original, normalizado, intent))
        self._agregar(entidades, self._extraer_cocineros(original, normalizado))

        # Contexto explícito solo completa datos que no aparecen en el texto.
        tipos_presentes = {e.tipo for e in entidades}
        for tipo in ("evento_id", "receta_id", "pedido_id", "plan_id", "proveedor"):
            if tipo in contexto and tipo not in tipos_presentes and contexto[tipo] not in (None, ""):
                entidades.append(EntidadExtraidaIA12(tipo, contexto[tipo], "contexto", 0.75))

        datos: Dict[str, Any] = {}
        for entidad in entidades:
            if entidad.tipo in datos:
                previo = datos[entidad.tipo]
                datos[entidad.tipo] = previo + [entidad.valor] if isinstance(previo, list) else [previo, entidad.valor]
            else:
                datos[entidad.tipo] = entidad.valor

        faltan = self._campos_faltantes(intent or "", datos)
        confianza = self._confianza_global(entidades, normalizado)
        return {
            "version": self.VERSION,
            "texto_original": original,
            "texto_normalizado": normalizado,
            "intent": intent or "",
            "datos": datos,
            "entidades": [e.__dict__.copy() for e in entidades],
            "faltan": faltan,
            "confianza_extraccion": confianza,
            "requiere_aclaracion": bool(faltan),
            "ejecutar": False,
            "lectura_host_ai": self._lectura(datos, faltan),
        }

    @staticmethod
    def normalizar(texto: str) -> str:
        valor = (texto or "").strip().lower()
        valor = "".join(c for c in unicodedata.normalize("NFD", valor) if unicodedata.category(c) != "Mn")
        valor = valor.replace("¿", "").replace("?", "").replace("¡", "").replace("!", "")
        valor = valor.replace(",", ".")
        return re.sub(r"\s+", " ", valor).strip()

    @staticmethod
    def _agregar(destino: List[EntidadExtraidaIA12], entidad: Optional[EntidadExtraidaIA12]) -> None:
        if entidad is not None:
            destino.append(entidad)

    @staticmethod
    def _agregar_varios(destino: List[EntidadExtraidaIA12], entidades: Iterable[EntidadExtraidaIA12]) -> None:
        destino.extend(entidades)

    def _extraer_fecha(self, original: str, texto: str, referencia: date) -> Optional[EntidadExtraidaIA12]:
        relativos = {"hoy": 0, "manana": 1, "pasado manana": 2}
        for expresion, dias in sorted(relativos.items(), key=lambda x: len(x[0]), reverse=True):
            if re.search(rf"\b{re.escape(expresion)}\b", texto):
                valor = referencia + timedelta(days=dias)
                return EntidadExtraidaIA12("fecha", valor.isoformat(), expresion, 0.98)

        m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", texto)
        if m:
            dia, mes, anio = map(int, m.groups())
            if anio < 100:
                anio += 2000
            try:
                valor = date(anio, mes, dia)
                return EntidadExtraidaIA12("fecha", valor.isoformat(), m.group(0), 0.99, m.start(), m.end())
            except ValueError:
                pass

        m = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", texto)
        if m:
            anio, mes, dia = map(int, m.groups())
            try:
                valor = date(anio, mes, dia)
                return EntidadExtraidaIA12("fecha", valor.isoformat(), m.group(0), 0.99, m.start(), m.end())
            except ValueError:
                pass

        meses = "|".join(self.MESES)
        m = re.search(rf"\b(\d{{1,2}})(?: de)? ({meses})(?: de)? (\d{{4}})\b", texto)
        if m:
            try:
                valor = date(int(m.group(3)), self.MESES[m.group(2)], int(m.group(1)))
                return EntidadExtraidaIA12("fecha", valor.isoformat(), m.group(0), 0.98, m.start(), m.end())
            except ValueError:
                pass

        for nombre, weekday in self.DIAS_SEMANA.items():
            m = re.search(rf"\b(?:este |el |proximo |proxima )?{nombre}\b", texto)
            if m:
                dias = (weekday - referencia.weekday()) % 7
                if dias == 0:
                    dias = 7
                valor = referencia + timedelta(days=dias)
                return EntidadExtraidaIA12("fecha", valor.isoformat(), m.group(0), 0.88, m.start(), m.end())
        return None

    def _extraer_hora(self, original: str, texto: str) -> Optional[EntidadExtraidaIA12]:
        m = re.search(r"\b(?:a las?|hora)?\s*(\d{1,2})(?::|\.)(\d{2})\s*(?:h|horas?)?\b", texto)
        if m:
            hora, minuto = int(m.group(1)), int(m.group(2))
            if 0 <= hora <= 23 and 0 <= minuto <= 59:
                return EntidadExtraidaIA12("hora", f"{hora:02d}:{minuto:02d}", m.group(0).strip(), 0.98, m.start(), m.end())
        m = re.search(r"\ba las (\d{1,2})\b", texto)
        if m:
            hora = int(m.group(1))
            if 0 <= hora <= 23:
                return EntidadExtraidaIA12("hora", f"{hora:02d}:00", m.group(0), 0.84, m.start(), m.end())
        return None

    def _extraer_pax(self, original: str, texto: str) -> Optional[EntidadExtraidaIA12]:
        m = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:pax|personas?|comensales?|invitados?)\b", texto)
        if m:
            return EntidadExtraidaIA12("pax", int(float(m.group(1))), m.group(0), 0.99, m.start(), m.end())
        for palabra, numero in self.PALABRAS_NUMERO.items():
            m = re.search(rf"\b{palabra}\s+(?:pax|personas?|comensales?|invitados?)\b", texto)
            if m:
                return EntidadExtraidaIA12("pax", numero, m.group(0), 0.90, m.start(), m.end())
        return None

    def _extraer_cantidades_unidades(self, original: str, texto: str) -> List[EntidadExtraidaIA12]:
        unidades = "|".join(sorted((re.escape(u) for u in self.UNIDADES), key=len, reverse=True))
        encontrados: List[EntidadExtraidaIA12] = []
        for m in re.finditer(rf"\b(\d+(?:\.\d+)?)\s*({unidades})\b", texto):
            # Evitar tratar pax como cantidad genérica.
            despues = texto[m.end():m.end()+15]
            if re.match(r"\s*(?:pax|personas?|comensales?)", despues):
                continue
            cantidad = float(m.group(1))
            if cantidad.is_integer():
                cantidad = int(cantidad)
            unidad = self.UNIDADES[m.group(2)]
            encontrados.append(EntidadExtraidaIA12("cantidad", cantidad, m.group(0), 0.97, m.start(), m.end()))
            encontrados.append(EntidadExtraidaIA12("unidad", unidad, m.group(2), 0.98, m.start(2), m.end(2)))
            break
        return encontrados

    def _extraer_precio(self, original: str, texto: str) -> Optional[EntidadExtraidaIA12]:
        patrones = [
            r"(?:precio|vale|cuesta|a)\s*(?:de\s*)?(\d+(?:\.\d+)?)\s*(?:€|euros?)",
            r"(\d+(?:\.\d+)?)\s*(?:€|euros?)\s*(?:por|/)?\s*(kg|l|u|unidad|racion|persona)?",
        ]
        for patron in patrones:
            m = re.search(patron, texto)
            if m:
                return EntidadExtraidaIA12("precio", float(m.group(1)), m.group(0), 0.96, m.start(), m.end())
        return None

    def _extraer_tipo_evento(self, original: str, texto: str) -> Optional[EntidadExtraidaIA12]:
        for tipo in self.TIPOS_EVENTO:
            normal = self.normalizar(tipo)
            m = re.search(rf"\b{re.escape(normal)}\b", texto)
            if m:
                return EntidadExtraidaIA12("tipo_evento", normal, m.group(0), 0.96, m.start(), m.end())
        return None

    def _extraer_proveedor(self, original: str, texto: str) -> Optional[EntidadExtraidaIA12]:
        patrones = [
            r"(?:proveedor|de|a)\s+([a-z0-9][a-z0-9 .&'-]{1,35})\s*$",
            r"(?:se lo compro a|comprado a|pedir a|pedido a)\s+([a-z0-9][a-z0-9 .&'-]{1,35})",
        ]
        for patron in patrones:
            m = re.search(patron, texto)
            if m:
                valor = self._limpiar_entidad(m.group(1), ("para", "el", "la", "los", "las"))
                if valor and not re.fullmatch(r"\d+(?:\.\d+)?", valor):
                    return EntidadExtraidaIA12("proveedor", self._titulo(valor), m.group(0), 0.78, m.start(), m.end())
        return None

    def _extraer_cliente(self, original: str, texto: str) -> Optional[EntidadExtraidaIA12]:
        m = re.search(r"(?:cliente|para|a nombre de)\s+([a-z][a-z .'-]{2,40})(?=\s+(?:de|para|el|la|con|en|\d)|$)", texto)
        if m:
            valor = self._limpiar_entidad(m.group(1), ("una", "un", "boda", "evento", "catering"))
            if valor and valor not in {"comprar tomates", "hacer pedido"}:
                return EntidadExtraidaIA12("cliente", self._titulo(valor), m.group(0), 0.72, m.start(), m.end())
        return None

    def _extraer_ubicacion(self, original: str, texto: str) -> Optional[EntidadExtraidaIA12]:
        for ubicacion in self.UBICACIONES:
            normal = self.normalizar(ubicacion)
            m = re.search(rf"\b{re.escape(normal)}\b", texto)
            if m:
                return EntidadExtraidaIA12("ubicacion", normal, m.group(0), 0.90, m.start(), m.end())
        m = re.search(r"(?:ubicacion|lugar|en)\s+([a-z0-9][a-z0-9 .'-]{2,50})$", texto)
        if m:
            return EntidadExtraidaIA12("ubicacion", self._titulo(m.group(1)), m.group(0), 0.70, m.start(), m.end())
        return None

    def _extraer_receta(self, original: str, texto: str, intent: str | None) -> Optional[EntidadExtraidaIA12]:
        m = re.search(r"\bREC-[A-Z0-9_-]+\b", original, flags=re.I)
        if m:
            return EntidadExtraidaIA12("receta_id", m.group(0).upper(), m.group(0), 0.99, m.start(), m.end())
        if intent and any(x in intent for x in ("escandallo", "receta", "costes")):
            patrones = [
                r"(?:receta|escandallo|plato)\s+(?:de\s+)?([a-z0-9][a-z0-9 .'-]{2,60})",
                r"(?:coste|food cost|rentabilidad)\s+(?:de|del|de la)\s+([a-z0-9][a-z0-9 .'-]{2,60})",
            ]
            for patron in patrones:
                m = re.search(patron, texto)
                if m:
                    valor = self._cortar_en_palabras(m.group(1), ("para", "con", "a", "por", "el", "la"))
                    return EntidadExtraidaIA12("receta", self._titulo(valor), m.group(0), 0.82, m.start(), m.end())
        return None

    def _extraer_articulo(self, original: str, texto: str, intent: str | None) -> Optional[EntidadExtraidaIA12]:
        if not intent or not any(x in intent for x in ("stock", "compra", "pedido", "merma", "inventario")):
            return None
        patrones = [
            r"(?:necesito|tengo que|hay que|quiero)\s+comprar\s+(?:\d+(?:\.\d+)?\s*(?:kg|g|l|ml|u|ud|uds|unidades?|cajas?|paquetes?|bandejas?|sacos?)\s+(?:de\s+)?)?([a-z][a-z0-9 .'-]{1,60})",
            r"(?:comprar|compro|falta|stock de|queda de|entrada de|merma de|inventario de)\s+(?:\d+(?:\.\d+)?\s*(?:kg|g|l|ml|u|ud|uds|unidades?|cajas?|paquetes?|bandejas?|sacos?)\s+(?:de\s+)?)?([a-z][a-z0-9 .'-]{1,60})",
            r"(?:cuanto|cuánto)\s+(?:stock\s+)?(?:tengo|queda)\s+(?:de\s+)?([a-z][a-z0-9 .'-]{1,60})",
        ]
        for patron in patrones:
            m = re.search(patron, texto)
            if m:
                valor = self._cortar_en_palabras(
                    m.group(1),
                    ("de", "para", "a", "con", "del", "proveedor", "y", "mañana", "manana", "hoy", "kg", "g", "l", "u")
                )
                valor = re.sub(r"\b\d+(?:\.\d+)?\b.*$", "", valor).strip()
                if valor:
                    return EntidadExtraidaIA12("articulo", self._titulo(valor), m.group(0), 0.82, m.start(), m.end())
        return None

    def _extraer_cocineros(self, original: str, texto: str) -> Optional[EntidadExtraidaIA12]:
        m = re.search(r"\b(\d+)\s+cociner[oa]s?\b", texto)
        if m:
            return EntidadExtraidaIA12("cocineros", int(m.group(1)), m.group(0), 0.97, m.start(), m.end())
        for palabra, numero in self.PALABRAS_NUMERO.items():
            m = re.search(rf"\b{palabra}\s+cociner[oa]s?\b", texto)
            if m:
                return EntidadExtraidaIA12("cocineros", numero, m.group(0), 0.90, m.start(), m.end())
        return None

    @staticmethod
    def _limpiar_entidad(valor: str, palabras_invalidas: Sequence[str]) -> str:
        valor = valor.strip(" .,-")
        for palabra in palabras_invalidas:
            if valor == palabra:
                return ""
        return valor

    @staticmethod
    def _cortar_en_palabras(valor: str, cortes: Sequence[str]) -> str:
        patron = r"\s+(?=" + "|".join(rf"\b{re.escape(c)}\b" for c in cortes) + r")"
        return re.split(patron, valor, maxsplit=1)[0].strip(" .,-")

    @staticmethod
    def _titulo(valor: str) -> str:
        return " ".join(p.capitalize() if not p.isupper() else p for p in valor.split())

    @staticmethod
    def _campos_faltantes(intent: str, datos: Dict[str, Any]) -> List[str]:
        requeridos = {
            "crear_evento": ("tipo_evento", "pax"),
            "registrar_entrada_stock": ("articulo", "cantidad", "unidad"),
            "registrar_merma": ("articulo", "cantidad", "unidad"),
            "ajustar_inventario": ("articulo", "cantidad", "unidad"),
            "registrar_necesidad_compra": ("articulo", "cantidad", "unidad"),
            "crear_escandallo": ("receta",),
            "calcular_escandallo": ("receta",),
            "calcular_costes": ("receta",),
            "planificar_produccion": (),
        }
        return [campo for campo in requeridos.get(intent, ()) if datos.get(campo) in (None, "", [])]

    @staticmethod
    def _confianza_global(entidades: Sequence[EntidadExtraidaIA12], texto: str) -> float:
        if not texto:
            return 0.0
        if not entidades:
            return 0.30
        return round(min(0.99, sum(e.confianza for e in entidades) / len(entidades)), 2)

    @staticmethod
    def _lectura(datos: Dict[str, Any], faltan: Sequence[str]) -> str:
        if not datos:
            return "No he extraído datos operativos concretos de la frase."
        resumen = ", ".join(f"{k}={v}" for k, v in datos.items())
        if faltan:
            return f"He extraído: {resumen}. Faltan: {', '.join(faltan)}."
        return f"He extraído: {resumen}. IA1.2 no ejecuta cambios."


__all__ = ["ExtractorDatosIA12", "EntidadExtraidaIA12"]
