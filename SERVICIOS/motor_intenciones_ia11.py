from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Sequence

from SERVICIOS.extractor_datos_ia12 import ExtractorDatosIA12


@dataclass(frozen=True)
class ReglaIntencionIA11:
    nombre: str
    modulo: str
    accion: str
    motor_sugerido: str
    patrones_fuertes: Sequence[str]
    patrones_medios: Sequence[str] = ()
    exclusiones: Sequence[str] = ()
    ejemplos: Sequence[str] = ()


class MotorIntencionesIA11:
    """Clasificador extensible de intenciones para Host AI 6.0.4 IA1.1.

    Este motor solo interpreta. No ejecuta acciones ni modifica datos.
    """

    VERSION = "6.0.4-IA1.2"

    def __init__(self) -> None:
        self._reglas: List[ReglaIntencionIA11] = []
        self.extractor_datos_ia12 = ExtractorDatosIA12()
        self._registrar_catalogo_base()

    @staticmethod
    def normalizar(texto: str) -> str:
        valor = (texto or "").strip().lower()
        valor = "".join(
            c for c in unicodedata.normalize("NFD", valor)
            if unicodedata.category(c) != "Mn"
        )
        valor = valor.replace("¿", "").replace("?", "").replace("¡", "").replace("!", "")
        return re.sub(r"\s+", " ", valor).strip()

    def registrar_intencion(self, regla: ReglaIntencionIA11) -> None:
        self._reglas = [r for r in self._reglas if r.nombre != regla.nombre]
        self._reglas.append(regla)

    def listar_intenciones(self) -> List[Dict[str, Any]]:
        return [asdict(regla) for regla in self._reglas]

    def clasificar(self, texto: str, contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
        contexto = contexto or {}
        normalizado = self.normalizar(texto)
        candidatos = [self._puntuar(regla, normalizado, contexto) for regla in self._reglas]
        candidatos.sort(key=lambda item: (item["confianza"], item["puntuacion"]), reverse=True)
        mejor = candidatos[0] if candidatos else self._resultado_general()

        if not normalizado or mejor["confianza"] < 0.45:
            mejor = self._resultado_general()

        extraccion = self.extractor_datos_ia12.extraer(
            texto, intent=mejor["intent"], contexto=contexto
        )
        requiere_aclaracion = mejor["confianza"] < 0.60 or bool(extraccion["faltan"])
        return {
            "version": self.VERSION,
            "texto_original": texto or "",
            "texto_normalizado": normalizado,
            "intent": mejor["intent"],
            "modulo": mejor["modulo"],
            "accion": mejor["accion"],
            "motor_sugerido": mejor["motor_sugerido"],
            "confianza": mejor["confianza"],
            "requiere_aclaracion": requiere_aclaracion,
            "motivos": mejor["motivos"],
            "contexto": contexto,
            "ranking": candidatos[:5],
            "datos": extraccion["datos"],
            "entidades": extraccion["entidades"],
            "faltan": extraccion["faltan"],
            "confianza_extraccion": extraccion["confianza_extraccion"],
            "ejecutar": False,
            "lectura_host_ai": self._lectura_ia12(mejor, extraccion),
        }

    def _puntuar(self, regla: ReglaIntencionIA11, texto: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        score = 0.0
        motivos: List[str] = []
        fuertes = [p for p in regla.patrones_fuertes if self._coincide(p, texto)]
        medios = [p for p in regla.patrones_medios if self._coincide(p, texto)]
        exclusiones = [p for p in regla.exclusiones if self._coincide(p, texto)]

        if fuertes:
            score += min(0.74, 0.56 + 0.06 * (len(fuertes) - 1))
            motivos.append("patrón fuerte: " + ", ".join(fuertes[:3]))
        if medios:
            score += min(0.30, 0.12 * len(medios))
            motivos.append("contexto: " + ", ".join(medios[:3]))
        if exclusiones:
            score -= min(0.50, 0.20 * len(exclusiones))
            motivos.append("exclusión: " + ", ".join(exclusiones[:2]))

        modulo_activo = str(contexto.get("modulo_activo", "")).lower()
        if modulo_activo and modulo_activo == regla.modulo:
            score += 0.08
            motivos.append("módulo activo")
        if contexto.get("evento_id") and regla.modulo in {"eventos", "produccion", "costes"}:
            score += 0.03

        confianza = round(max(0.0, min(score, 0.99)), 2)
        return {
            "intent": regla.nombre,
            "modulo": regla.modulo,
            "accion": regla.accion,
            "motor_sugerido": regla.motor_sugerido,
            "confianza": confianza,
            "puntuacion": round(score, 3),
            "motivos": motivos or ["sin señales suficientes"],
        }

    @staticmethod
    def _coincide(patron: str, texto: str) -> bool:
        if patron.startswith("re:"):
            return bool(re.search(patron[3:], texto))
        return patron in texto

    @staticmethod
    def _resultado_general() -> Dict[str, Any]:
        return {
            "intent": "conversacion_general",
            "modulo": "conversacion",
            "accion": "aclarar",
            "motor_sugerido": "motor_conversacional",
            "confianza": 0.30,
            "puntuacion": 0.30,
            "motivos": ["no se ha detectado una intención operativa clara"],
        }

    @staticmethod
    def _lectura(resultado: Dict[str, Any]) -> str:
        if resultado["intent"] == "conversacion_general":
            return "No he identificado todavía una operación concreta. Necesito una aclaración."
        return (
            f"He entendido la intención '{resultado['intent']}' "
            f"del módulo {resultado['modulo']} con confianza {resultado['confianza']:.0%}. "
            "IA1.1 no ejecuta cambios."
        )


    @staticmethod
    def _lectura_ia12(resultado: Dict[str, Any], extraccion: Dict[str, Any]) -> str:
        if resultado["intent"] == "conversacion_general":
            return "No he identificado todavía una operación concreta. Necesito una aclaración."
        base = (
            f"He entendido la intención '{resultado['intent']}' "
            f"del módulo {resultado['modulo']} con confianza {resultado['confianza']:.0%}."
        )
        datos = extraccion.get("datos", {})
        faltan = extraccion.get("faltan", [])
        if datos:
            base += " Datos: " + ", ".join(f"{k}={v}" for k, v in datos.items()) + "."
        if faltan:
            base += " Faltan: " + ", ".join(faltan) + "."
        return base + " IA1.2 no ejecuta cambios."

    def _registrar_catalogo_base(self) -> None:
        reglas: Iterable[ReglaIntencionIA11] = [
            ReglaIntencionIA11("crear_evento", "eventos", "crear", "motor_eventos", (
                "crear un evento", "crea un evento", "tengo una boda", "prepara una boda",
                "tengo un catering", "organiza una comunion", "nuevo evento",
                "re:^(haz|monta|prepara).*(boda|evento|catering|comunion)"
            ), ("pax", "personas", "comensales", "fecha"), ("que eventos", "listar eventos")),
            ReglaIntencionIA11("consultar_eventos", "eventos", "consultar", "motor_eventos", (
                "que eventos tengo", "listar eventos", "ver eventos", "proximos eventos", "busca el evento"
            ), ("evento", "boda", "catering")),
            ReglaIntencionIA11("consultar_evento_activo", "eventos", "diagnosticar", "motor_eventos", (
                "que tengo para la boda", "que hay en la boda", "resumen de la boda", "resumen del evento",
                "que tengo para el evento", "como va la boda", "como va el evento"
            ), ("la boda", "el evento", "este evento")),
            ReglaIntencionIA11("editar_evento", "eventos", "editar", "motor_eventos", (
                "editar evento", "modifica el evento", "cambia el evento", "cambia los pax", "cambia la fecha"
            ), ("evento", "boda")),
            ReglaIntencionIA11("consultar_stock", "stock", "consultar", "motor_stock", (
                "que stock tengo", "cuanto stock", "cuanto me queda", "que me queda", "consulta el stock",
                "ver stock", "hay suficiente", "re:^cuanto .* (tengo|queda)"
            ), ("stock", "existencias", "almacen", "queda"), ("comprar", "pedido")),
            ReglaIntencionIA11("registrar_entrada_stock", "stock", "registrar_entrada", "motor_stock", (
                "registrar entrada", "entrada de mercancia", "han llegado", "ha llegado", "recibir mercancia",
                "sumalo al stock", "añade al stock", "anade al stock"
            ), ("kg", "litros", "unidades", "proveedor"), ("que stock", "cuanto queda")),
            ReglaIntencionIA11("registrar_merma", "stock", "registrar_merma", "motor_stock", (
                "registrar merma", "he tirado", "se ha estropeado", "perdida de producto", "descuenta por merma"
            ), ("merma", "caducado", "roto")),
            ReglaIntencionIA11("ajustar_inventario", "stock", "ajustar_inventario", "motor_stock", (
                "ajustar inventario", "inventario fisico", "realmente tengo", "corrige el stock"
            ), ("stock", "cantidad real")),
            ReglaIntencionIA11("registrar_necesidad_compra", "compras", "registrar_necesidad", "motor_compras", (
                "necesito comprar", "hay que comprar", "tengo que comprar", "me falta comprar", "apunta para comprar"
            ), ("proveedor", "kg", "unidades"), ("que tengo que comprar", "haz el pedido")),
            ReglaIntencionIA11("consultar_compras", "compras", "consultar", "motor_compras", (
                "que tengo que comprar", "que falta comprar", "lista de la compra", "necesidades pendientes"
            ), ("compras", "pendiente", "falta")),
            ReglaIntencionIA11("generar_pedido", "compras", "generar_pedido", "motor_compras", (
                "haz el pedido", "genera el pedido", "prepara el pedido", "crear pedido", "manda el pedido"
            ), ("proveedor", "compras")),
            ReglaIntencionIA11("recibir_pedido", "compras", "recibir_pedido", "motor_compras", (
                "recibir pedido", "pedido recibido", "ha llegado el pedido", "confirma la recepcion"
            ), ("proveedor", "stock")),
            ReglaIntencionIA11("crear_escandallo", "escandallos", "crear", "motor_escandallos", (
                "crear escandallo", "crea una receta", "nueva receta", "registra esta receta", "crear ficha tecnica"
            ), ("ingredientes", "raciones", "elaboracion")),
            ReglaIntencionIA11("editar_escandallo", "escandallos", "editar", "motor_escandallos", (
                "editar escandallo", "modifica la receta", "cambia la receta", "añade ingrediente", "anade ingrediente"
            ), ("receta", "ingrediente")),
            ReglaIntencionIA11("calcular_escandallo", "escandallos", "calcular", "motor_escandallos", (
                "calcula el escandallo", "coste de la receta", "cuanto cuesta la receta", "food cost de la receta"
            ), ("receta", "raciones", "coste")),
            ReglaIntencionIA11("calcular_costes", "costes", "calcular", "motor_costes", (
                "calcula el coste", "coste del evento", "coste real", "coste previsto", "cuanto ha costado"
            ), ("evento", "mano de obra", "indirectos")),
            ReglaIntencionIA11("consultar_rentabilidad", "costes", "analizar_rentabilidad", "motor_costes", (
                "que rentabilidad", "beneficio del evento", "margen del evento", "es rentable", "donde pierdo dinero",
                "cuanto voy a ganar", "cuanto gano con la boda", "cuanto gano con el evento",
                "cuanto voy a ganar con esta boda", "rentabilidad de la boda"
            ), ("food cost", "beneficio", "margen", "rentabilidad", "la boda", "el evento")),
            ReglaIntencionIA11("crear_plan_produccion", "produccion", "crear_plan", "motor_produccion_real", (
                "crear plan de produccion", "nueva produccion", "prepara la produccion", "haz un plan de trabajo"
            ), ("evento", "recetas", "tareas")),
            ReglaIntencionIA11("consultar_preparacion_evento", "produccion", "consultar_preparacion", "motor_produccion_real", (
                "que tengo que preparar para la boda", "que tengo que preparar para el evento",
                "que tengo que cocinar para la boda", "que tengo que cocinar primero",
                "que preparo primero", "que toca preparar", "que toca cocinar",
                "dime la produccion de la boda", "ver la produccion del evento"
            ), ("la boda", "el evento", "la produccion", "el plan")),
            ReglaIntencionIA11("planificar_produccion", "produccion", "planificar", "motor_produccion_real", (
                "planifica la produccion", "organiza la produccion", "reparte entre cocineros", "ordena las tareas"
            ), ("cocineros", "horno", "abatidor", "prioridades")),
            ReglaIntencionIA11("ejecutar_produccion", "produccion", "ejecutar", "motor_produccion_real", (
                "inicia la tarea", "pausa la tarea", "reanuda la tarea", "finaliza la tarea", "empieza la produccion"
            ), ("tarea", "plan", "produccion")),
            ReglaIntencionIA11("optimizar_produccion", "produccion", "optimizar", "motor_produccion_real", (
                "optimiza la produccion", "mejora la planificacion", "busca cuellos de botella", "optimiza recursos", "optimiza los recursos"
            ), ("horno", "abatidor", "tiempos muertos", "recursos")),
        ]
        for regla in reglas:
            self.registrar_intencion(regla)


__all__ = ["MotorIntencionesIA11", "ReglaIntencionIA11"]
