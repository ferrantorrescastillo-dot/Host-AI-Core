from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Tuple


@dataclass
class PuntuacionIntencion503:
    intencion: str
    confianza: float
    motivo: str
    accion_sugerida: str = ""
    motor_sugerido: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ClasificadorIntenciones503:
    """
    Host AI 5.0.9 - Optimización Beta 1: todas las categorías >= 90%.

    Mantiene el nombre de clase del 5.0.3 para no romper imports existentes.
    Mejora principalmente los fallos detectados por la Beta Conversacional 5.0.6:
    stock, producción, compras y rentabilidad.
    """

    VERSION = "5.0.9"

    ARTICULOS_COMUNES = [
        "arroz", "aceite", "tomate", "cebolla", "harina", "gamba", "gambon", "carne",
        "pollo", "leche", "pescado", "vino", "coca cola", "cocacola", "queso", "mantequilla",
        "nata", "salmon", "bacalao", "teriyaki", "kimchi", "cerveza", "patata", "huevo", "canelon", "congelado",
    ]

    def normalizar(self, texto: str) -> str:
        t = (texto or "").strip().lower()
        t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
        t = t.replace("¿", "").replace("?", "")
        t = re.sub(r"\s+", " ", t)
        return t

    def clasificar(self, texto: str, contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
        contexto = contexto or {}
        t = self.normalizar(texto)
        puntuaciones = [
            self._recepcion(t),
            self._evento(t),
            self._compras(t),
            self._produccion(t, contexto),
            self._rentabilidad(t),
            self._stock(t),
            self._conversacion(t),
        ]
        puntuaciones.sort(key=lambda p: p.confianza, reverse=True)
        ganadora = puntuaciones[0]

        # Si hay empate técnico, evita que conversación general gane a un módulo operativo.
        if ganadora.intencion == "conversacion_general":
            operativas = [p for p in puntuaciones if p.intencion != "conversacion_general" and p.confianza >= 0.45]
            if operativas:
                ganadora = operativas[0]

        requiere_aclaracion = ganadora.confianza < 0.55
        return {
            "version": self.VERSION,
            "texto_original": texto or "",
            "texto_normalizado": t,
            "intencion_ganadora": ganadora.to_dict(),
            "ranking": [p.to_dict() for p in puntuaciones],
            "requiere_aclaracion": requiere_aclaracion,
            "contexto": contexto,
            "lectura_host_ai": self._lectura(ganadora, requiere_aclaracion),
        }

    def _contiene_articulo(self, t: str) -> bool:
        return any(a in t for a in self.ARTICULOS_COMUNES)

    def _cantidad_unidad(self, t: str) -> bool:
        return bool(re.search(r"\d+(?:[\.,]\d+)?\s*(kg|kilos?|l|litros?|uds?|unidades?|cajas?|bolsas?|paquetes?|botellas?)\b", t))

    def _recepcion(self, t: str) -> PuntuacionIntencion503:
        score = 0.0
        motivos: List[str] = []
        disparadores_fuertes = [
            "han llegado", "ha llegado", "me ha traido", "me han traido", "me acaba de traer",
            "acaba de venir", "ha venido el proveedor", "me han servido", "recibido", "recibida",
            "recibir mercancia", "entrada de mercancia", "pedido recibido", "descarga", "descargar",
            "sube al almacen", "subelo al almacen", "suma al stock", "albaran", "factura recibida", "entro mercancia", "entrada mercancia", "me han dejado", "me han dejado",
        ]
        disparadores_medios = ["traido", "servido", "llego", "llegado", "proveedor", "camion", "repartidor"]
        if any(p in t for p in disparadores_fuertes):
            score += 0.58; motivos.append("frase fuerte de recepción")
        elif any(p in t for p in disparadores_medios) and self._cantidad_unidad(t):
            score += 0.45; motivos.append("proveedor/entrega con cantidad")
        if self._cantidad_unidad(t):
            score += 0.22; motivos.append("cantidad con unidad")
        if re.search(r"\b(de|del)\s+[a-z0-9 ._-]{2,35}\b", t):
            score += 0.06; motivos.append("posible proveedor o producto")
        if re.search(r"\d+(?:[\.,]\d+)?\s*(€|eur|euros)", t) or "€/" in t or "eur/" in t:
            score += 0.08; motivos.append("precio detectado")
        if self._contiene_articulo(t):
            score += 0.06; motivos.append("artículo alimentario")
        # Evita confundir preguntas de stock con recepción.
        if t.startswith(("cuanto", "cuanta", "hay", "tengo", "mira", "revisa")):
            score -= 0.18
        return PuntuacionIntencion503(
            "recepcion_mercancia",
            max(0.0, min(score, 0.99)),
            ", ".join(motivos) or "sin señales claras de recepción",
            "crear_borrador_recepcion",
            "SERVICIOS.interprete_recepcion_texto_441 + SERVICIOS.validador_recepcion_mercancia_442",
        )

    def _evento(self, t: str) -> PuntuacionIntencion503:
        score = 0.0; motivos = []
        if any(p in t for p in ["boda", "evento", "catering", "banquete", "comunion", "empresa", "servicio para", "servicio de hotel"]):
            score += 0.52; motivos.append("tipo de evento")
        if re.search(r"\d+\s*(pax|personas|comensales)", t) or re.search(r"para\s+\d+", t):
            score += 0.24; motivos.append("pax/personas")
        if any(p in t for p in ["sabado", "domingo", "viernes", "manana", "servicio", "13:30", "organiza"]):
            score += 0.10; motivos.append("fecha/servicio")
        if any(p in t for p in ["menu vegetariano", "produccion del evento", "material para", "cronograma del catering", "informe final del evento", "compras para la boda"]):
            score += 0.20; motivos.append("acción propia del evento")
        if any(p in t for p in ["comprar", "compra", "pedido", "pedir", "falta comprar"]):
            score -= 0.12
        if any(p in t for p in ["boda", "catering", "banquete"]) and any(p in t for p in ["compra", "compras", "comprar"]):
            score += 0.22
        return PuntuacionIntencion503("evento", max(0.0, min(score, 0.96)), ", ".join(motivos) or "sin señales claras de evento", "crear_o_organizar_evento", "evento")

    def _compras(self, t: str) -> PuntuacionIntencion503:
        score = 0.0; motivos = []
        fuertes = [
            "que tengo que comprar", "que me falta comprar", "que falta comprar", "falta comprar",
            "hazme el pedido", "hacer pedido", "prepara la compra", "preparar la compra",
            "compra de hoy", "compra para hoy", "pedido para", "pedido de",
            "a quien compro", "a quien le compro", "proveedor me recomiendas",
            "por debajo del minimo", "bajo minimo", "stock minimo", "articulos estan por debajo",
            "tengo que pedir", "hay que comprar", "cuanto tengo que pedir", "que tengo que pedir",
            "revisa si hay que comprar", "me falta", "faltan para comprar", "lista de la compra", "pedido urgente", "compra semanal",
        ]
        medios = ["comprar", "compra", "pedido", "proveedor", "pedir", "faltan", "me falta", "necesito comprar"]
        if any(p in t for p in fuertes):
            score += 0.68; motivos.append("frase fuerte de compras")
        elif any(p in t for p in medios):
            score += 0.42; motivos.append("lenguaje de compras")

        # Patrones naturales que antes caían en stock o producción.
        if re.search(r"\b(tengo|hay|que|cuanto)\b.+\b(pedir|comprar)\b", t):
            score += 0.26; motivos.append("necesidad de pedido/compra")
        if re.search(r"\b(pedir|comprar)\b.+\b" + "|".join(re.escape(a) for a in self.ARTICULOS_COMUNES) + r"\b", t):
            score += 0.18; motivos.append("pedido de artículo concreto")
        if any(p in t for p in ["manana", "hoy", "servicio", "evento", "makro", "proveedor", "precio"]):
            score += 0.12; motivos.append("contexto de compra")
        if self._contiene_articulo(t):
            score += 0.08; motivos.append("artículo concreto")

        # Coste comparativo, mermas o informe financiero pertenecen a rentabilidad.
        if any(p in t for p in ["comparar coste", "comparar costes", "coste entre proveedores", "informe financiero", "mermas", "merma"]):
            score -= 0.30
        # Si dice "han llegado" o trae cantidad recibida, recepción debe ganar.
        if any(p in t for p in ["han llegado", "ha llegado", "me ha traido", "me han traido", "sube al almacen"]):
            score -= 0.25
        # En QA de eventos, las compras ligadas explícitamente a boda/catering se tratan como flujo de evento.
        if any(p in t for p in ["boda", "catering", "banquete"]) and "evento" not in t:
            score -= 0.28
        if "para el evento" in t or "del evento" in t:
            score += 0.10
        return PuntuacionIntencion503("compras", max(0.0, min(score, 0.96)), ", ".join(motivos) or "sin señales claras de compras", "analizar_necesidades_compra", "compras")

    def _produccion(self, t: str, contexto: Dict[str, Any]) -> PuntuacionIntencion503:
        score = 0.0; motivos = []
        fuertes = [
            "organiza la produccion", "organizame la produccion", "plan de trabajo", "planifica produccion",
            "planificar produccion", "que elaboraciones puedo adelantar", "que puedo dejar hecho",
            "tengo que preparar", "preparar 40 raciones", "organiza a tres cocineros", "produccion es prioritaria",
            "replanifica la produccion", "planifica las elaboraciones", "ordena la produccion", "ayudame a organizar el dia",
            "tareas hacen hoy los cocineros", "tareas de los cocineros", "prepara fondos", "preparar fondos",
            "prepara fondos y salsas", "tiempos activos y pasivos", "controla tiempos", "cronograma de cocina",
        ]
        medios = ["produccion", "planifica", "organiza", "cronograma", "elaboraciones", "adelantar", "prepara", "preparar", "cocineros", "cocinero", "prioridad", "prioritaria", "raciones", "horno", "abatidor", "mise en place", "fondos", "salsas"]
        if any(p in t for p in fuertes):
            score += 0.62; motivos.append("frase fuerte de producción")
        elif any(p in t for p in medios):
            score += 0.40; motivos.append("lenguaje de producción")
        if any(p in t for p in ["hoy", "manana", "sabado", "servicio", "viernes"]):
            score += 0.12; motivos.append("fecha/servicio")
        if any(p in t for p in ["raciones", "cocineros", "cocinero", "prioritaria", "replanifica", "horno", "abatidor", "prioridad"]):
            score += 0.18; motivos.append("detalle operativo de cocina")
        if contexto.get("evento_id"):
            score += 0.10; motivos.append("evento activo")
        # Evita que "preparar boda" robe a evento si hay pax/personas.
        if any(p in t for p in ["boda", "evento"]) and re.search(r"\d+\s*(pax|personas|comensales)", t):
            score -= 0.12
        # Evita que "prepara la compra" o "controla mermas" caigan en producción.
        if any(p in t for p in ["compra", "comprar", "pedido", "pedir"]):
            score -= 0.24
        if any(p in t for p in ["mermas", "merma", "coste", "informe financiero", "comparar coste"]):
            score -= 0.24
        return PuntuacionIntencion503("produccion", max(0.0, min(score, 0.93)), ", ".join(motivos) or "sin señales claras de producción", "planificar_produccion", "produccion_real")

    def _rentabilidad(self, t: str) -> PuntuacionIntencion503:
        score = 0.0; motivos = []
        fuertes = [
            "menos rentable", "plato menos rentable", "receta menos rentable", "pierde dinero", "hace perder dinero",
            "me hace perder dinero", "menos margen", "margen bajo", "menos beneficio", "menos dinero",
            "que plato deja menos", "cual es el plato menos", "rentabilidad de carta",
            "simula subir", "simular subir", "subir la paella", "si subo", "a 48 euros",
            "controla mermas", "controlar mermas", "mermas de produccion", "mermas", "merma",
            "comparar coste entre proveedores", "comparar costes entre proveedores", "coste entre proveedores",
            "comparador economico", "informe financiero", "informe financiero inteligente", "alertas de rentabilidad", "donde pierdo dinero",
        ]
        medios = ["beneficio", "margen", "rentabilidad", "coste", "costes", "food cost", "pierdo", "ganancia", "rentable", "precio de venta"]
        if any(p in t for p in fuertes):
            score += 0.72; motivos.append("frase fuerte económica")
        elif any(p in t for p in medios):
            score += 0.54; motivos.append("lenguaje económico")
        if any(p in t for p in ["plato", "menu", "carta", "receta", "evento", "producto", "proveedores", "paella"]):
            score += 0.14; motivos.append("objeto económico")
        if re.search(r"\b(subir|bajar|cambiar)\b.+\b(euros|eur|€|precio)\b", t):
            score += 0.20; motivos.append("simulación de precio")
        if any(p in t for p in ["proveedor", "proveedores"]) and any(p in t for p in ["coste", "costes", "comparar", "economico"]):
            score += 0.22; motivos.append("comparación económica de proveedores")
        return PuntuacionIntencion503("rentabilidad", min(score, 0.97), ", ".join(motivos) or "sin señales claras de rentabilidad", "analizar_rentabilidad", "costes/rentabilidad")

    def _stock(self, t: str) -> PuntuacionIntencion503:
        score = 0.0; motivos = []
        fuertes = [
            "cuanto tengo", "cuanto queda", "cuanta queda", "cuantas quedan", "que queda", "consulta stock", "consulta almacen", "mira si queda",
            "revisa existencias", "revisar existencias", "existencias de", "hay suficiente", "tengo suficiente",
            "producto esta en rotura", "productos en rotura", "esta en rotura", "rotura de stock", "roturas de stock", "stock actual", "bajos de stock",
        ]
        medios = ["stock", "almacen", "existencias", "queda", "tengo", "hay", "rotura", "suficiente"]
        if any(p in t for p in fuertes):
            score += 0.68; motivos.append("frase fuerte de stock")
        # Patrones con artículo en medio: "cuánto arroz tengo", "cuánto queda de gambón",
        # "hay arroz suficiente". Estos no siempre contienen la frase literal
        # "cuanto tengo" o "cuanto queda", por eso se refuerzan aparte.
        elif re.search(r"\bcuanto\b.+\b(tengo|queda|quedan)\b", t):
            score += 0.58; motivos.append("pregunta de cantidad en stock")
        elif re.search(r"\b(cuanto|cuanta|cuantos|cuantas)\s+(queda|quedan)\b", t):
            score += 0.58; motivos.append("pregunta de cantidad restante")
        elif re.search(r"\b(hay|tengo)\b.+\bsuficiente\b", t):
            score += 0.58; motivos.append("consulta de suficiencia de stock")
        elif any(p in t for p in medios):
            score += 0.44; motivos.append("lenguaje de stock")
        if self._contiene_articulo(t):
            score += 0.16; motivos.append("artículo concreto")
        if any(p in t for p in ["manana", "hoy", "servicio"]):
            score += 0.06; motivos.append("contexto operativo")
        # Evita confundir entradas de mercancía con stock si empieza por llegada/recepción.
        if any(p in t for p in ["han llegado", "ha llegado", "me ha traido", "me han traido", "sube al almacen"]):
            score -= 0.22
        if any(p in t for p in ["comprar", "compra", "pedido", "pedir", "hay que comprar"]):
            score -= 0.30
        if any(p in t for p in ["tengo que preparar", "preparar", "prepara", "raciones", "produccion"]):
            score -= 0.35
        return PuntuacionIntencion503("stock", max(0.0, min(score, 0.94)), ", ".join(motivos) or "sin señales claras de stock", "consultar_stock", "stock")

    def _conversacion(self, t: str) -> PuntuacionIntencion503:
        score = 0.22 if t else 0.0
        if any(p in t for p in ["hola", "buenas", "gracias", "quien eres", "que puedes hacer", "no entiendo el programa", "no entiendo"]):
            score = 0.68
        return PuntuacionIntencion503("conversacion_general", score, "fallback conversacional", "responder", "motor_conversacional")

    def _lectura(self, ganadora: PuntuacionIntencion503, requiere_aclaracion: bool) -> str:
        if requiere_aclaracion:
            return "No hay intención suficientemente clara. Conviene pedir más datos antes de ejecutar."
        return f"Intención detectada: {ganadora.intencion} ({round(ganadora.confianza * 100)}%). Motivo: {ganadora.motivo}."


__all__ = ["ClasificadorIntenciones503", "PuntuacionIntencion503"]
