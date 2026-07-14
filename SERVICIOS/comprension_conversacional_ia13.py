from __future__ import annotations

import copy
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from SERVICIOS.motor_intenciones_ia11 import MotorIntencionesIA11


@dataclass
class EstadoConversacionIA13:
    intent: str = ""
    modulo: str = ""
    accion: str = ""
    motor_sugerido: str = ""
    datos: Dict[str, Any] = field(default_factory=dict)
    faltan: List[str] = field(default_factory=list)
    ultimo_texto: str = ""
    turnos: int = 0


class ComprensionConversacionalIA13:
    """Comprensión multi-turno segura para Host AI IA1.3.

    Conserva contexto inmediato, resuelve órdenes incompletas y genera
    preguntas naturales. Nunca ejecuta motores ni modifica datos.
    """

    VERSION = "6.0.4-IA1.3"

    SINONIMOS = (
        (r"\bficha tecnica\b", "receta"),
        (r"\bficha\b", "receta"),
        (r"\belaboracion\b", "receta"),
        (r"\bplato\b", "receta"),
        (r"\bgenero\b", "articulo"),
        (r"\bmercancia\b", "stock"),
        (r"\bexistencias\b", "stock"),
        (r"\bcomanda de compra\b", "pedido"),
    )

    PREGUNTAS = {
        "pax": "¿Para cuántas personas?",
        "fecha": "¿Para qué fecha? Puedes decir, por ejemplo, 'mañana' o '22/10/2026'.",
        "hora": "¿A qué hora?",
        "tipo_evento": "¿Qué tipo de evento es: boda, catering, comunión u otro?",
        "articulo": "¿Qué artículo necesitas?",
        "cantidad": "¿Qué cantidad necesitas?",
        "unidad": "¿En qué unidad: kg, litros, unidades, cajas...?",
        "proveedor": "¿De qué proveedor?",
        "receta": "¿De qué receta o elaboración hablas?",
        "precio": "¿Qué precio quieres utilizar?",
        "cocineros": "¿Cuántos cocineros estarán disponibles?",
        "evento_id": "¿A qué evento te refieres?",
        "plan_id": "¿Qué plan de producción quieres utilizar?",
        "pedido_id": "¿Qué pedido quieres utilizar?",
    }

    def __init__(self, motor: Optional[MotorIntencionesIA11] = None) -> None:
        self.motor = motor or MotorIntencionesIA11()
        self._sesiones: Dict[str, EstadoConversacionIA13] = {}

    @staticmethod
    def _normalizar(texto: str) -> str:
        valor = (texto or "").strip().lower()
        valor = "".join(
            c for c in unicodedata.normalize("NFD", valor)
            if unicodedata.category(c) != "Mn"
        )
        return re.sub(r"\s+", " ", valor).strip()

    def _aplicar_sinonimos(self, texto: str) -> str:
        normalizado = self._normalizar(texto)
        for patron, reemplazo in self.SINONIMOS:
            normalizado = re.sub(patron, reemplazo, normalizado)
        return normalizado

    def reiniciar(self, sesion: str = "default") -> None:
        self._sesiones.pop(sesion, None)

    def obtener_estado(self, sesion: str = "default") -> Dict[str, Any]:
        estado = self._sesiones.get(sesion, EstadoConversacionIA13())
        return copy.deepcopy(estado.__dict__)

    def procesar(
        self,
        texto: str,
        sesion: str = "default",
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        contexto = dict(contexto or {})
        original = (texto or "").strip()
        if not original:
            return self._respuesta_vacia(sesion)

        if self._normalizar(original) in {"cancelar", "olvida", "olvidalo", "empezar de nuevo", "reiniciar"}:
            self.reiniciar(sesion)
            return {
                "version": self.VERSION,
                "estado": "cancelado",
                "intent": "conversacion_general",
                "datos": {},
                "faltan": [],
                "pregunta": "",
                "respuesta": "He cancelado la orden pendiente. Puedes empezar otra.",
                "requiere_aclaracion": False,
                "ejecutar": False,
            }

        anterior = self._sesiones.get(sesion)
        texto_interpretado = self._aplicar_sinonimos(original)

        # Si existe una orden pendiente, primero interpretamos la respuesta con
        # esa intención. Esto permite respuestas cortas como "5 kg".
        if anterior and anterior.intent and anterior.faltan:
            resultado = self.motor.clasificar(
                texto_interpretado,
                {**contexto, **anterior.datos, "modulo_activo": anterior.modulo},
            )
            extraccion = self.motor.extractor_datos_ia12.extraer(
                texto_interpretado,
                intent=anterior.intent,
                contexto={**contexto, **anterior.datos},
            )
            intent = anterior.intent
            modulo = anterior.modulo
            accion = anterior.accion
            motor_sugerido = anterior.motor_sugerido
            confianza_intencion = max(float(resultado.get("confianza", 0)), 0.70)
            datos = self._fusionar_datos(anterior.datos, extraccion.get("datos", {}))
            faltan = self.motor.extractor_datos_ia12._campos_faltantes(intent, datos)
        else:
            resultado = self.motor.clasificar(texto_interpretado, contexto)
            intent = resultado["intent"]
            modulo = resultado["modulo"]
            accion = resultado["accion"]
            motor_sugerido = resultado["motor_sugerido"]
            confianza_intencion = float(resultado.get("confianza", 0))
            datos = dict(resultado.get("datos", {}))
            faltan = list(resultado.get("faltan", []))

        estado = EstadoConversacionIA13(
            intent=intent,
            modulo=modulo,
            accion=accion,
            motor_sugerido=motor_sugerido,
            datos=datos,
            faltan=faltan,
            ultimo_texto=original,
            turnos=(anterior.turnos + 1 if anterior else 1),
        )
        self._sesiones[sesion] = estado

        pregunta = self._crear_pregunta(intent, faltan, datos, confianza_intencion)
        completo = intent != "conversacion_general" and not faltan and confianza_intencion >= 0.45
        if completo:
            respuesta = self._resumen_entendido(intent, datos)
            estado_conversacion = "comprendido"
        elif intent == "conversacion_general":
            respuesta = (
                "No he identificado todavía una operación concreta. "
                "Puedo ayudarte con eventos, stock, compras, escandallos, costes o producción."
            )
            estado_conversacion = "ambiguo"
        else:
            respuesta = pregunta
            estado_conversacion = "esperando_dato"

        return {
            "version": self.VERSION,
            "estado": estado_conversacion,
            "texto_original": original,
            "intent": intent,
            "modulo": modulo,
            "accion": accion,
            "motor_sugerido": motor_sugerido,
            "confianza": round(confianza_intencion, 2),
            "datos": copy.deepcopy(datos),
            "faltan": list(faltan),
            "pregunta": pregunta,
            "respuesta": respuesta,
            "requiere_aclaracion": not completo,
            "turnos": estado.turnos,
            "ejecutar": False,
        }

    @staticmethod
    def _fusionar_datos(anteriores: Dict[str, Any], nuevos: Dict[str, Any]) -> Dict[str, Any]:
        datos = copy.deepcopy(anteriores)
        for clave, valor in nuevos.items():
            if valor not in (None, "", []):
                datos[clave] = valor
        return datos

    def _crear_pregunta(
        self,
        intent: str,
        faltan: List[str],
        datos: Dict[str, Any],
        confianza: float,
    ) -> str:
        if intent == "conversacion_general" or confianza < 0.45:
            return "¿Quieres trabajar con eventos, stock, compras, escandallos, costes o producción?"
        if not faltan:
            return ""

        primero = faltan[0]
        # Compra: cantidad y unidad se preguntan juntas para reducir turnos.
        if primero == "cantidad" and "unidad" in faltan:
            articulo = datos.get("articulo")
            sufijo = f" de {articulo}" if articulo else ""
            return f"¿Qué cantidad{sufijo} necesitas y en qué unidad?"
        return self.PREGUNTAS.get(primero, f"Necesito el dato: {primero}.")

    @staticmethod
    def _resumen_entendido(intent: str, datos: Dict[str, Any]) -> str:
        etiquetas = {
            "crear_evento": "crear el evento",
            "registrar_necesidad_compra": "registrar la necesidad de compra",
            "consultar_stock": "consultar el stock",
            "crear_escandallo": "crear la receta o escandallo",
            "calcular_costes": "calcular los costes",
            "planificar_produccion": "planificar la producción",
            "generar_pedido": "generar el pedido",
            "consultar_evento_activo": "consultar el evento activo",
            "consultar_preparacion_evento": "consultar qué hay que preparar",
            "consultar_rentabilidad": "consultar la rentabilidad del evento",
        }
        accion = etiquetas.get(intent, intent.replace("_", " "))
        if datos:
            detalle = ", ".join(f"{clave}={valor}" for clave, valor in datos.items())
            return f"He entendido que quieres {accion}. Datos: {detalle}. No he ejecutado cambios."
        return f"He entendido que quieres {accion}. No he ejecutado cambios."

    def _respuesta_vacia(self, sesion: str) -> Dict[str, Any]:
        estado = self._sesiones.get(sesion)
        pregunta = self._crear_pregunta(
            estado.intent if estado else "conversacion_general",
            estado.faltan if estado else [],
            estado.datos if estado else {},
            0.70 if estado else 0.0,
        )
        return {
            "version": self.VERSION,
            "estado": "esperando_dato" if estado else "ambiguo",
            "intent": estado.intent if estado else "conversacion_general",
            "datos": copy.deepcopy(estado.datos) if estado else {},
            "faltan": list(estado.faltan) if estado else [],
            "pregunta": pregunta,
            "respuesta": pregunta or "Escribe qué necesitas.",
            "requiere_aclaracion": True,
            "ejecutar": False,
        }


__all__ = ["ComprensionConversacionalIA13", "EstadoConversacionIA13"]
