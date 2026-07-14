from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from SERVICIOS.comprension_conversacional_ia13 import ComprensionConversacionalIA13


@dataclass(frozen=True)
class ContratoMotorIA14:
    intent: str
    pipeline: str
    accion: str
    lectura: bool = False
    requiere_confirmacion: bool = True
    campos_requeridos: tuple[str, ...] = field(default_factory=tuple)
    aliases: Dict[str, str] = field(default_factory=dict)
    valores_defecto: Dict[str, Any] = field(default_factory=dict)


class IntegracionMotoresIA14:
    """Conecta comprensión conversacional con contratos reales de pipelines.

    IA1.4 no ejecuta operaciones. Genera una propuesta técnica validada contra
    el RegistroPipelines del núcleo, traduce entidades conversacionales a los
    nombres de parámetros que espera cada pipeline y clasifica el riesgo.
    """

    VERSION = "6.0.4-IA1.4"

    def __init__(self, core: Any, comprension: Optional[ComprensionConversacionalIA13] = None) -> None:
        self.core = core
        self.comprension = comprension or core.comprension_conversacional_ia13
        self._contratos = self._crear_contratos()

    def analizar(
        self,
        texto: str,
        sesion: str = "default",
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        interpretacion = self.comprension.procesar(texto, sesion, contexto)
        intent = interpretacion.get("intent", "conversacion_general")
        contrato = self._contratos.get(intent)

        if interpretacion.get("requiere_aclaracion") or not contrato:
            return self._respuesta_sin_propuesta(interpretacion, contrato)

        parametros = self._traducir_parametros(contrato, interpretacion.get("datos", {}), contexto or {})
        faltan_motor = [campo for campo in contrato.campos_requeridos if parametros.get(campo) in (None, "", [])]
        pipeline = self.core.registro_pipelines.obtener(contrato.pipeline)
        pipeline_existe = pipeline is not None
        accion_soportada = bool(
            pipeline_existe
            and contrato.accion in getattr(pipeline, "acciones_soportadas", [])
        )

        propuesta_valida = pipeline_existe and accion_soportada and not faltan_motor
        tipo_operacion = "consulta" if contrato.lectura else "modificacion"
        requiere_confirmacion = bool(contrato.requiere_confirmacion and not contrato.lectura)
        riesgo = self._riesgo(tipo_operacion, contrato.accion)

        if propuesta_valida:
            if contrato.lectura:
                resumen = (
                    f"He preparado una consulta segura al motor '{contrato.pipeline}', "
                    f"acción '{contrato.accion}'. IA1.4 no la ha ejecutado."
                )
            else:
                resumen = (
                    f"He preparado la acción '{contrato.accion}' del motor "
                    f"'{contrato.pipeline}'. Requerirá confirmación antes de ejecutarse."
                )
        elif faltan_motor:
            resumen = "La intención está comprendida, pero faltan datos técnicos: " + ", ".join(faltan_motor) + "."
        else:
            resumen = "La intención está comprendida, pero el contrato técnico no está disponible en el proyecto."

        return {
            "version": self.VERSION,
            "estado": "propuesta_lista" if propuesta_valida else "propuesta_incompleta",
            "interpretacion": copy.deepcopy(interpretacion),
            "intent": intent,
            "modulo": interpretacion.get("modulo", ""),
            "pipeline": contrato.pipeline,
            "accion": contrato.accion,
            "parametros": parametros,
            "tipo_operacion": tipo_operacion,
            "riesgo": riesgo,
            "pipeline_existe": pipeline_existe,
            "accion_soportada": accion_soportada,
            "faltan_motor": faltan_motor,
            "propuesta_valida": propuesta_valida,
            "requiere_confirmacion": requiere_confirmacion,
            "puede_ejecutarse_en_ia2": propuesta_valida,
            "ejecutado": False,
            "respuesta": resumen,
        }

    def obtener_contratos(self) -> List[Dict[str, Any]]:
        return [
            {
                "intent": c.intent,
                "pipeline": c.pipeline,
                "accion": c.accion,
                "lectura": c.lectura,
                "requiere_confirmacion": c.requiere_confirmacion,
                "campos_requeridos": list(c.campos_requeridos),
            }
            for c in self._contratos.values()
        ]

    def _respuesta_sin_propuesta(
        self,
        interpretacion: Dict[str, Any],
        contrato: Optional[ContratoMotorIA14],
    ) -> Dict[str, Any]:
        intent = interpretacion.get("intent", "conversacion_general")
        if interpretacion.get("requiere_aclaracion"):
            respuesta = interpretacion.get("respuesta", "Necesito más información.")
            estado = "esperando_dato"
        elif contrato is None:
            respuesta = "He entendido la frase, pero todavía no existe un contrato IA1.4 para esa intención."
            estado = "sin_contrato"
        else:
            respuesta = "No se ha podido preparar la propuesta técnica."
            estado = "propuesta_incompleta"
        return {
            "version": self.VERSION,
            "estado": estado,
            "interpretacion": copy.deepcopy(interpretacion),
            "intent": intent,
            "modulo": interpretacion.get("modulo", ""),
            "pipeline": contrato.pipeline if contrato else "",
            "accion": contrato.accion if contrato else "",
            "parametros": {},
            "tipo_operacion": "",
            "riesgo": "",
            "pipeline_existe": False,
            "accion_soportada": False,
            "faltan_motor": list(interpretacion.get("faltan", [])),
            "propuesta_valida": False,
            "requiere_confirmacion": False,
            "puede_ejecutarse_en_ia2": False,
            "ejecutado": False,
            "respuesta": respuesta,
        }

    @staticmethod
    def _riesgo(tipo_operacion: str, accion: str) -> str:
        if tipo_operacion == "consulta":
            return "bajo"
        if accion in {"eliminar", "recibir_pedido", "consumir"}:
            return "alto"
        return "medio"

    @staticmethod
    def _traducir_parametros(
        contrato: ContratoMotorIA14,
        datos: Dict[str, Any],
        contexto: Dict[str, Any],
    ) -> Dict[str, Any]:
        parametros: Dict[str, Any] = copy.deepcopy(contrato.valores_defecto)
        fuente = {**contexto, **datos}
        for clave, valor in fuente.items():
            destino = contrato.aliases.get(clave, clave)
            if valor not in (None, "", []):
                parametros[destino] = copy.deepcopy(valor)

        # Adaptaciones de modelo conversacional -> contratos existentes.
        if "articulo" in fuente:
            parametros.setdefault("nombre", fuente["articulo"])
        if "proveedor" in fuente:
            parametros.setdefault("proveedor_preferente", fuente["proveedor"])
        if "receta" in fuente:
            parametros.setdefault("receta_id", fuente["receta"])
        if "precio" in fuente:
            parametros.setdefault("precio_venta_por_racion", fuente["precio"])
        if "cocineros" in fuente:
            parametros.setdefault("equipo_cocina", fuente["cocineros"])
        if "tipo_evento" in fuente:
            parametros.setdefault("tipo", fuente["tipo_evento"])
        if "hora" in fuente:
            parametros.setdefault("hora_inicio", fuente["hora"])
        if "fecha" in fuente:
            parametros.setdefault("fecha", fuente["fecha"])
        if "pax" in fuente and "nombre" not in parametros:
            tipo = fuente.get("tipo_evento", "Evento")
            parametros["nombre"] = f"{str(tipo).title()} {fuente['pax']} pax"
        return parametros

    @staticmethod
    def _crear_contratos() -> Dict[str, ContratoMotorIA14]:
        contratos = [
            ContratoMotorIA14("crear_evento", "evento", "crear", False, True,
                ("nombre", "fecha", "pax"),
                valores_defecto={"tipo": "evento", "estado": "pendiente"}),
            ContratoMotorIA14("consultar_eventos", "evento", "listar", True, False),
            ContratoMotorIA14("consultar_evento_activo", "evento", "diagnosticar", True, False,
                ("evento_id",)),
            ContratoMotorIA14("editar_evento", "evento", "editar", False, True,
                ("evento_id", "cambios")),
            ContratoMotorIA14("consultar_stock", "stock", "stock_actual", True, False),
            ContratoMotorIA14("registrar_entrada_stock", "stock", "registrar_entrada", False, True,
                ("nombre", "cantidad", "unidad"), valores_defecto={"motivo": "entrada mercancía"}),
            ContratoMotorIA14("registrar_merma", "stock", "consumir", False, True,
                ("nombre", "cantidad", "unidad"), valores_defecto={"motivo": "merma"}),
            ContratoMotorIA14("ajustar_inventario", "stock", "ajustar_minimo", False, True,
                ("nombre", "cantidad_minima")),
            ContratoMotorIA14("registrar_necesidad_compra", "compras", "registrar_necesidad", False, True,
                ("nombre", "cantidad", "unidad"), valores_defecto={"prioridad": 50}),
            ContratoMotorIA14("consultar_compras", "compras", "listar_necesidades", True, False,
                valores_defecto={"solo_pendientes": True}),
            ContratoMotorIA14("generar_pedido", "compras", "generar_pedidos_sugeridos", False, True),
            ContratoMotorIA14("recibir_pedido", "compras", "recibir_pedido", False, True,
                ("pedido_id",)),
            ContratoMotorIA14("crear_escandallo", "escandallos", "registrar_escandallo", False, True,
                ("receta_id", "nombre", "raciones"),
                aliases={"receta": "nombre"}, valores_defecto={"raciones": 1, "lineas": []}),
            ContratoMotorIA14("editar_escandallo", "escandallos", "editar_escandallo", False, True,
                ("receta_id", "cambios")),
            ContratoMotorIA14("calcular_escandallo", "escandallos", "calcular_receta", True, False,
                ("receta_id", "raciones"), valores_defecto={"raciones": 1}),
            ContratoMotorIA14("calcular_costes", "costes", "calcular_evento", True, False,
                ("evento_id",), valores_defecto={"precio_venta_por_pax": 0.0}),
            ContratoMotorIA14("consultar_rentabilidad", "costes", "diagnosticar_evento", True, False,
                ("evento_id",), valores_defecto={"food_cost_objetivo": 30.0}),
            ContratoMotorIA14("consultar_preparacion_evento", "produccion_real", "diagnosticar_plan", True, False,
                ("plan_id",)),
            ContratoMotorIA14("crear_plan_produccion", "produccion_real", "planificar_evento", False, True,
                ("evento_id",), valores_defecto={"hora_inicio": "08:00", "equipo_cocina": 2}),
            ContratoMotorIA14("planificar_produccion", "produccion_real", "planificar_evento", False, True,
                ("evento_id",), valores_defecto={"hora_inicio": "08:00", "equipo_cocina": 2}),
            ContratoMotorIA14("ejecutar_produccion", "produccion_real", "diagnosticar_plan", True, False,
                ("plan_id",)),
            ContratoMotorIA14("optimizar_produccion", "produccion_real", "diagnosticar_plan", True, False,
                ("plan_id",)),
        ]
        return {c.intent: c for c in contratos}


__all__ = ["IntegracionMotoresIA14", "ContratoMotorIA14"]
