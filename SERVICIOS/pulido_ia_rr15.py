from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional


class PulidoIARR15:
    """Capa de experiencia conversacional RR1.5 sobre IA1.4.

    No ejecuta acciones. Enriquece contexto activo, reduce preguntas repetidas y
    convierte la propuesta técnica en una respuesta operativa para cocina.
    """

    VERSION = "6.0.4-RR1.6.1-D"

    ETIQUETAS = {
        "pax": "personas",
        "fecha": "fecha",
        "hora": "hora",
        "tipo_evento": "tipo de evento",
        "articulo": "artículo",
        "cantidad": "cantidad",
        "unidad": "unidad",
        "proveedor": "proveedor",
        "receta": "receta",
        "receta_id": "receta",
        "precio": "precio",
        "cocineros": "cocineros",
        "evento_id": "evento",
        "plan_id": "plan de producción",
        "pedido_id": "pedido",
        "nombre": "nombre",
        "raciones": "raciones",
    }

    def __init__(self, core: Any) -> None:
        self.core = core
        self.integracion = core.integracion_motores_ia14
        self._contextos: Dict[str, Dict[str, Any]] = {}

    def reiniciar(self, sesion: str = "default") -> None:
        self._contextos.pop(sesion, None)
        self.core.comprension_conversacional_ia13.reiniciar(sesion)

    def procesar(
        self,
        texto: str,
        sesion: str = "default",
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        contexto_total = self._fusionar_contexto(sesion, contexto or {})
        texto_contextual = self._resolver_referencias_contextuales(texto, contexto_total)
        resultado = self.integracion.analizar(texto_contextual, sesion, contexto_total)
        resultado["texto_contextual"] = texto_contextual
        self._recordar_contexto(sesion, resultado, contexto_total)

        respuesta_natural = self._crear_respuesta(resultado)
        salida = copy.deepcopy(resultado)
        salida["version_rr"] = self.VERSION
        salida["respuesta_tecnica"] = resultado.get("respuesta", "")
        salida["respuesta"] = respuesta_natural
        salida["contexto_activo"] = copy.deepcopy(self._contextos.get(sesion, {}))
        salida["ejecutado"] = False
        return salida

    @staticmethod
    def _resolver_referencias_contextuales(texto: str, contexto: Dict[str, Any]) -> str:
        original = (texto or "").strip()
        normalizado = original.lower()
        if contexto.get("plan_id") and any(frase in normalizado for frase in (
            "que tengo que preparar", "qué tengo que preparar", "que tengo que cocinar",
            "qué tengo que cocinar", "que preparo primero", "qué preparo primero",
            "que toca preparar", "qué toca preparar", "la produccion", "la producción"
        )):
            return "qué tengo que preparar para la boda"
        if contexto.get("evento_id") and any(frase in normalizado for frase in (
            "la boda", "el evento", "este evento"
        )):
            if any(p in normalizado for p in ("cuanto voy a ganar", "cuánto voy a ganar", "cuanto gano", "rentabilidad", "beneficio", "margen")):
                return "cuánto voy a ganar con esta boda"
            if any(p in normalizado for p in ("resumen", "como va", "cómo va", "que hay", "qué hay")):
                return "resumen de la boda"
        if contexto.get("pedido_id") and normalizado in {"el pedido", "ver el pedido", "como va el pedido", "cómo va el pedido"}:
            return "qué tengo que comprar"
        return original

    def _fusionar_contexto(self, sesion: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        anterior = self._contextos.get(sesion, {})
        combinado = copy.deepcopy(anterior)
        for clave, valor in contexto.items():
            if valor not in (None, "", []):
                combinado[clave] = copy.deepcopy(valor)
        return combinado

    def _recordar_contexto(
        self,
        sesion: str,
        resultado: Dict[str, Any],
        contexto: Dict[str, Any],
    ) -> None:
        activo = copy.deepcopy(contexto)
        parametros = resultado.get("parametros", {}) or {}
        interpretacion = resultado.get("interpretacion", {}) or {}
        datos = interpretacion.get("datos", {}) or {}
        for clave in ("evento_id", "plan_id", "pedido_id", "receta_id"):
            valor = parametros.get(clave, datos.get(clave))
            if valor not in (None, "", []):
                activo[clave] = copy.deepcopy(valor)
        modulo = resultado.get("modulo")
        if modulo:
            activo["modulo_activo"] = modulo
        self._contextos[sesion] = activo

    def _crear_respuesta(self, resultado: Dict[str, Any]) -> str:
        estado = resultado.get("estado", "")
        interpretacion = resultado.get("interpretacion", {}) or {}
        intent = resultado.get("intent", "conversacion_general")

        if intent == "conversacion_general":
            return (
                "No he entendido todavía qué quieres hacer. Puedes decirme, por ejemplo: "
                "'¿qué stock tengo?', 'necesito comprar 5 kg de tomate', "
                "'tengo una boda para 80 personas' o 'planifica la producción'."
            )

        if estado == "esperando_dato":
            pregunta = interpretacion.get("pregunta") or interpretacion.get("respuesta")
            if pregunta:
                return pregunta
            faltan = interpretacion.get("faltan", [])
            return self._pregunta_faltantes(faltan)

        if intent == "conversacion_general":
            return (
                "No he entendido todavía qué quieres hacer. Puedes decirme, por ejemplo: "
                "'¿qué stock tengo?', 'necesito comprar 5 kg de tomate', "
                "'tengo una boda para 80 personas' o 'planifica la producción'."
            )

        if resultado.get("propuesta_valida"):
            return self._resumen_propuesta(resultado)

        if resultado.get("faltan_motor"):
            faltan = resultado.get("faltan_motor", [])
            return (
                "He entendido la operación, pero me falta "
                + self._lista_natural([self.ETIQUETAS.get(x, x) for x in faltan])
                + "."
            )

        if not resultado.get("pipeline_existe"):
            return (
                "He entendido lo que quieres hacer, pero ese motor todavía no está disponible "
                "en esta versión de Host AI."
            )

        return resultado.get("respuesta", "No he podido preparar la operación.")

    def _resumen_propuesta(self, resultado: Dict[str, Any]) -> str:
        tipo = resultado.get("tipo_operacion")
        pipeline = resultado.get("pipeline", "")
        accion = resultado.get("accion", "")
        parametros = resultado.get("parametros", {}) or {}
        detalle = self._detalle_parametros(parametros)

        if tipo == "consulta":
            base = self._frase_consulta(pipeline, accion)
            if detalle:
                base += f" ({detalle})"
            return base + ". Es una consulta segura y no modifica datos."

        base = self._frase_modificacion(pipeline, accion)
        if detalle:
            base += f": {detalle}"
        return base + ". No he realizado cambios; esta acción necesitará tu confirmación."

    @staticmethod
    def _frase_consulta(pipeline: str, accion: str) -> str:
        frases = {
            ("stock", "stock_actual"): "He entendido que quieres consultar el stock actual",
            ("evento", "listar"): "He entendido que quieres consultar los eventos",
            ("evento", "diagnosticar"): "He entendido que quieres revisar el evento activo",
            ("compras", "listar_necesidades"): "He entendido que quieres ver las compras pendientes",
            ("escandallos", "calcular_receta"): "He preparado el cálculo del escandallo",
            ("costes", "calcular_evento"): "He preparado el cálculo de costes del evento",
            ("costes", "diagnosticar_evento"): "He preparado el análisis de rentabilidad del evento",
            ("produccion_real", "diagnosticar_plan"): "He preparado la consulta del plan de producción activo",
        }
        return frases.get((pipeline, accion), f"He preparado una consulta de {pipeline}")

    @staticmethod
    def _frase_modificacion(pipeline: str, accion: str) -> str:
        frases = {
            ("evento", "crear"): "He preparado la creación del evento",
            ("evento", "editar"): "He preparado la modificación del evento",
            ("stock", "registrar_entrada"): "He preparado la entrada de stock",
            ("stock", "consumir"): "He preparado el movimiento de merma",
            ("compras", "registrar_necesidad"): "He preparado la necesidad de compra",
            ("compras", "generar_pedidos_sugeridos"): "He preparado la generación del pedido",
            ("compras", "recibir_pedido"): "He preparado la recepción del pedido",
            ("escandallos", "registrar_escandallo"): "He preparado la creación del escandallo",
            ("escandallos", "editar_escandallo"): "He preparado la modificación del escandallo",
            ("produccion_real", "planificar_evento"): "He preparado la planificación de producción",
        }
        return frases.get((pipeline, accion), f"He preparado la acción de {pipeline}")

    def _detalle_parametros(self, parametros: Dict[str, Any]) -> str:
        ignorar = {"estado", "prioridad", "motivo", "lineas", "cambios", "food_cost_objetivo"}
        partes: List[str] = []
        orden = (
            "nombre", "tipo", "pax", "fecha", "hora_inicio", "articulo",
            "cantidad", "unidad", "proveedor_preferente", "proveedor",
            "receta_id", "raciones", "precio_venta_por_racion", "evento_id",
            "plan_id", "pedido_id", "equipo_cocina",
        )
        vistos = set()
        for clave in orden:
            if clave in parametros and parametros[clave] not in (None, "", [], {}) and clave not in ignorar:
                etiqueta = self.ETIQUETAS.get(clave, clave.replace("_", " "))
                partes.append(f"{etiqueta}: {parametros[clave]}")
                vistos.add(clave)
        for clave, valor in parametros.items():
            if clave in vistos or clave in ignorar or valor in (None, "", [], {}):
                continue
            etiqueta = self.ETIQUETAS.get(clave, clave.replace("_", " "))
            partes.append(f"{etiqueta}: {valor}")
        return ", ".join(partes)

    def _pregunta_faltantes(self, faltan: List[str]) -> str:
        if not faltan:
            return "Necesito un poco más de información."
        etiquetas = [self.ETIQUETAS.get(x, x) for x in faltan]
        return "Me falta " + self._lista_natural(etiquetas) + "."

    @staticmethod
    def _lista_natural(valores: List[str]) -> str:
        if not valores:
            return "información"
        if len(valores) == 1:
            return valores[0]
        return ", ".join(valores[:-1]) + " y " + valores[-1]


__all__ = ["PulidoIARR15"]
