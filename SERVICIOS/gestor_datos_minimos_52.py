from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class EventoMinimo52:
    tipo_evento: str = "evento"
    pax: Optional[int] = None
    fecha: Optional[str] = None
    hora_servicio: Optional[str] = None
    tipo_menu: Optional[str] = None
    lugar: Optional[str] = None
    restricciones: Optional[str] = None
    objetivo: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GestorDatosMinimos52:
    """
    Host AI 5.2 - Gestor de datos mínimos y preguntas inteligentes.

    Evita que el orquestador invente datos. Si el usuario pide organizar un
    evento pero faltan datos mínimos, guía la conversación paso a paso antes de
    permitir producción, compras o rentabilidad.
    """

    CAMPOS_OBLIGATORIOS = [
        "pax",
        "fecha",
        "hora_servicio",
        "tipo_menu",
        "lugar",
        "restricciones",
        "objetivo",
    ]

    PREGUNTAS = {
        "pax": "¿Para cuántas personas es el evento?",
        "fecha": "¿Qué día exacto es el evento?",
        "hora_servicio": "¿A qué hora es el servicio?",
        "tipo_menu": "¿Qué tipo de menú quieres trabajar? Por ejemplo: paella, BBQ, aperitivos + principal, cóctel o menú cerrado.",
        "lugar": "¿Dónde será el evento? Restaurante, finca, domicilio, hotel o catering exterior.",
        "restricciones": "¿Hay alergias, vegetarianos, niños o alguna restricción alimentaria? Si no hay, dime 'sin restricciones'.",
        "objetivo": "¿Qué quieres que prepare primero: producción, compras, coste/rentabilidad o todo el flujo completo?",
    }

    def __init__(self):
        self.contexto: Dict[str, Any] = {}

    def normalizar(self, texto: str) -> str:
        texto = (texto or "").lower().strip()
        texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
        texto = re.sub(r"\s+", " ", texto)
        return texto

    def es_peticion_evento(self, texto: str) -> bool:
        t = self.normalizar(texto)
        claves_evento = ["boda", "evento", "catering", "banquete", "comunion", "empresa", "cumpleanos", "servicio para"]
        return any(c in t for c in claves_evento)

    def hay_evento_pendiente(self) -> bool:
        return "evento_minimo_52" in self.contexto

    def procesar(self, texto: str) -> Dict[str, Any]:
        texto = (texto or "").strip()
        if not texto:
            return {"gestionado": False, "ok": False, "mensaje": ""}

        if self.hay_evento_pendiente():
            evento = EventoMinimo52(**self.contexto["evento_minimo_52"])
            campo_esperado = self.contexto.get("campo_esperado_52")
            self._actualizar_evento(evento, texto, campo_preferente=campo_esperado)
            return self._respuesta_estado(evento)

        if not self.es_peticion_evento(texto):
            return {"gestionado": False, "ok": True, "mensaje": "No es una petición de evento con datos mínimos."}

        evento = self._extraer_evento_inicial(texto)
        return self._respuesta_estado(evento)

    def _extraer_evento_inicial(self, texto: str) -> EventoMinimo52:
        t = self.normalizar(texto)
        evento = EventoMinimo52()

        for tipo in ["boda", "comunion", "catering", "banquete", "empresa", "cumpleanos"]:
            if tipo in t:
                evento.tipo_evento = tipo
                break

        pax = re.search(r"(\d{1,4})\s*(pax|personas|invitados|comensales)?", t)
        if pax:
            try:
                evento.pax = int(pax.group(1))
            except ValueError:
                pass

        evento.fecha = self._extraer_fecha(t)
        evento.hora_servicio = self._extraer_hora(t)
        evento.tipo_menu = self._extraer_menu(t)
        evento.lugar = self._extraer_lugar(t)
        evento.restricciones = self._extraer_restricciones(t)
        evento.objetivo = self._extraer_objetivo(t)
        return evento

    def _actualizar_evento(self, evento: EventoMinimo52, texto: str, campo_preferente: Optional[str] = None) -> None:
        t = self.normalizar(texto)
        if campo_preferente == "pax" or evento.pax is None:
            m = re.search(r"(\d{1,4})\s*(pax|personas|invitados|comensales)?", t)
            if m:
                evento.pax = int(m.group(1))
        if campo_preferente == "fecha" or evento.fecha is None:
            fecha = self._extraer_fecha(t)
            if fecha:
                evento.fecha = fecha
        if campo_preferente == "hora_servicio" or evento.hora_servicio is None:
            hora = self._extraer_hora(t)
            if hora:
                evento.hora_servicio = hora
        if campo_preferente == "tipo_menu" or evento.tipo_menu is None:
            menu = self._extraer_menu(t)
            if menu:
                evento.tipo_menu = menu
            elif campo_preferente == "tipo_menu" and len(t) >= 3:
                evento.tipo_menu = texto.strip()
        if campo_preferente == "lugar" or evento.lugar is None:
            lugar = self._extraer_lugar(t)
            if lugar:
                evento.lugar = lugar
            elif campo_preferente == "lugar" and len(t) >= 3:
                evento.lugar = texto.strip()
        if campo_preferente == "restricciones" or evento.restricciones is None:
            restr = self._extraer_restricciones(t)
            if restr:
                evento.restricciones = restr
            elif campo_preferente == "restricciones" and len(t) >= 2:
                evento.restricciones = texto.strip()
        if campo_preferente == "objetivo" or evento.objetivo is None:
            obj = self._extraer_objetivo(t)
            if obj:
                evento.objetivo = obj
            elif campo_preferente == "objetivo" and len(t) >= 2:
                evento.objetivo = texto.strip()

    def _extraer_fecha(self, t: str) -> Optional[str]:
        m = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", t)
        if m:
            return m.group(0)
        for palabra in ["hoy", "manana", "pasado manana", "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]:
            if palabra in t:
                return palabra
        return None

    def _extraer_hora(self, t: str) -> Optional[str]:
        # 5.4.9: buscar primero horas explícitas para no confundir "150 personas"
        # con una hora y perder un "a las 15:00" posterior en la misma frase.
        patrones = [
            r"(?:a las|sobre las|servicio a las|hora del servicio|hora)\s*(\d{1,2})(?:[:\.](\d{2}))?\s*(h|horas)?\b",
            r"\b(\d{1,2})[:\.](\d{2})\s*(h|horas)?\b",
            r"\b(\d{1,2})\s*(h|horas)\b",
        ]
        for patron in patrones:
            for m in re.finditer(patron, t):
                hh = int(m.group(1))
                mm = m.group(2) or "00"
                if 0 <= hh <= 23 and 0 <= int(mm) <= 59:
                    return f"{hh:02d}:{int(mm):02d}"
        return None

    def _extraer_menu(self, t: str) -> Optional[str]:
        opciones = {
            "paella": "paella",
            "bbq": "BBQ",
            "barbacoa": "BBQ",
            "aperitivos": "aperitivos + principal",
            "cocktail": "cóctel",
            "coctel": "cóctel",
            "menu cerrado": "menú cerrado",
            "vegetariano": "menú vegetariano",
        }
        for k, v in opciones.items():
            if k in t:
                return v
        return None

    def _extraer_lugar(self, t: str) -> Optional[str]:
        patrones = [
            r"en (el restaurante|la finca|un hotel|el hotel|casa|domicilio|exterior|terraza|salon|masia)",
            r"lugar[: ]+([a-z0-9 ñçáéíóúàèòü\-]+)",
        ]
        for p in patrones:
            m = re.search(p, t)
            if m:
                return m.group(1).strip()
        return None

    def _extraer_restricciones(self, t: str) -> Optional[str]:
        if t.strip() in {"no", "ninguna", "ninguno", "sin", "sin restricciones"} or "sin restricciones" in t or "sin alerg" in t:
            return "sin restricciones"
        claves = ["alerg", "vegetarian", "vegano", "celiaco", "gluten", "lactosa", "ninos", "niños"]
        if any(c in t for c in claves):
            return t
        return None

    def _extraer_objetivo(self, t: str) -> Optional[str]:
        if "todo" in t or "completo" in t or "desde hoy" in t:
            return "flujo completo"
        if "compra" in t or "pedido" in t or "comprar" in t:
            return "compras"
        if "produccion" in t or "produc" in t or "planning" in t or "plan" in t:
            return "producción"
        if "coste" in t or "margen" in t or "rentabilidad" in t:
            return "coste/rentabilidad"
        return None

    def campos_faltantes(self, evento: EventoMinimo52) -> List[str]:
        return [c for c in self.CAMPOS_OBLIGATORIOS if getattr(evento, c) in (None, "")]

    def _respuesta_estado(self, evento: EventoMinimo52) -> Dict[str, Any]:
        faltantes = self.campos_faltantes(evento)
        if faltantes:
            siguiente = faltantes[0]
            self.contexto["evento_minimo_52"] = evento.to_dict()
            self.contexto["campo_esperado_52"] = siguiente
            return {
                "gestionado": True,
                "ok": True,
                "estado": "faltan_datos",
                "evento": evento.to_dict(),
                "faltantes": faltantes,
                "siguiente_campo": siguiente,
                "mensaje": self._mensaje_faltan_datos(evento, faltantes, siguiente),
            }

        self.contexto.pop("evento_minimo_52", None)
        self.contexto.pop("campo_esperado_52", None)
        return {
            "gestionado": True,
            "ok": True,
            "estado": "datos_completos",
            "evento": evento.to_dict(),
            "faltantes": [],
            "siguiente_campo": None,
            "mensaje": self._mensaje_datos_completos(evento),
        }

    def _mensaje_faltan_datos(self, evento: EventoMinimo52, faltantes: List[str], siguiente: str) -> str:
        lineas = []
        lineas.append("Perfecto. Antes de organizar el evento necesito cerrar unos datos mínimos para no inventar nada.")
        lineas.append("")
        lineas.append("Datos detectados:")
        lineas.append(f"- Tipo: {evento.tipo_evento}")
        lineas.append(f"- Personas: {evento.pax if evento.pax is not None else 'pendiente'}")
        lineas.append(f"- Fecha: {evento.fecha or 'pendiente'}")
        lineas.append(f"- Hora servicio: {evento.hora_servicio or 'pendiente'}")
        lineas.append(f"- Menú: {evento.tipo_menu or 'pendiente'}")
        lineas.append(f"- Lugar: {evento.lugar or 'pendiente'}")
        lineas.append(f"- Restricciones: {evento.restricciones or 'pendiente'}")
        lineas.append(f"- Objetivo: {evento.objetivo or 'pendiente'}")
        lineas.append("")
        lineas.append("Datos que faltan:")
        for campo in faltantes:
            lineas.append(f"- {self._nombre_campo(campo)}")
        lineas.append("")
        lineas.append(self.PREGUNTAS[siguiente])
        return "\n".join(lineas)

    def _mensaje_datos_completos(self, evento: EventoMinimo52) -> str:
        return (
            "Ya tengo los datos mínimos del evento.\n"
            f"- Tipo: {evento.tipo_evento}\n"
            f"- Personas: {evento.pax}\n"
            f"- Fecha: {evento.fecha}\n"
            f"- Hora servicio: {evento.hora_servicio}\n"
            f"- Menú: {evento.tipo_menu}\n"
            f"- Lugar: {evento.lugar}\n"
            f"- Restricciones: {evento.restricciones}\n"
            f"- Objetivo: {evento.objetivo}\n\n"
            "Ahora ya puedo pasar a orquestar producción, stock, compras y rentabilidad sin inventar datos.\n"
            "Siguiente paso recomendado: generar el flujo operativo completo y pedir confirmación antes de modificar datos reales."
        )

    def _nombre_campo(self, campo: str) -> str:
        nombres = {
            "pax": "número de personas",
            "fecha": "fecha",
            "hora_servicio": "hora del servicio",
            "tipo_menu": "tipo de menú",
            "lugar": "lugar del evento",
            "restricciones": "restricciones alimentarias",
            "objetivo": "qué quieres que prepare primero",
        }
        return nombres.get(campo, campo)


__all__ = ["GestorDatosMinimos52", "EventoMinimo52"]
