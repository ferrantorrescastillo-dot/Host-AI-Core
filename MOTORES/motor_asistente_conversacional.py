from __future__ import annotations

import re
from typing import Dict, Any, List
from MODELOS.asistente_conversacional import IntencionConversacional, RespuestaConversacional
from SERVICIOS.clasificador_intenciones_503 import ClasificadorIntenciones503


class MotorAsistenteConversacional:
    """
    Asistente Conversacional Inicial v2.0.9.

    Primera versión determinista:
    - clasifica frases del usuario
    - extrae parámetros básicos
    - enruta hacia pipelines existentes
    - devuelve una respuesta legible

    No usa LLM externo todavía.
    """

    def __init__(self, core):
        self.core = core
        self.historial: List[RespuestaConversacional] = []
        self.clasificador_intenciones_503 = ClasificadorIntenciones503()

    def responder(self, texto: str, contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
        contexto = contexto or {}
        intencion = self.detectar_intencion(texto, contexto)
        resultado = {}

        if intencion.intencion == "recepcion_mercancia":
            resultado = self._ejecutar_borrador_recepcion(texto, intencion.parametros)
            respuesta_txt = self._redactar_recepcion(resultado)
            acciones = resultado.get("acciones_recomendadas", [])
            requiere = resultado.get("requiere_aprobacion", True)
        elif intencion.pipeline and intencion.accion:
            resultado_pipeline = self.core.director.ejecutar_pipeline(
                intencion.pipeline,
                intencion.accion,
                intencion.parametros,
            )
            resultado = resultado_pipeline.to_dict()
            respuesta_txt = self._redactar_respuesta(intencion, resultado_pipeline)
            acciones = resultado_pipeline.acciones_recomendadas
            requiere = resultado_pipeline.requiere_aprobacion
        else:
            respuesta_txt = self._respuesta_sin_accion(intencion)
            acciones = intencion.avisos or ["Dame más datos para poder actuar."]
            requiere = True

        respuesta = RespuestaConversacional(
            texto_usuario=texto,
            respuesta=respuesta_txt,
            intencion=intencion.to_dict(),
            resultado=resultado,
            acciones_recomendadas=acciones,
            requiere_aprobacion=requiere,
        )
        self.historial.append(respuesta)
        return {**respuesta.to_dict(), "lectura_host_ai": respuesta.respuesta}

    def detectar_intencion(self, texto: str, contexto: Dict[str, Any] | None = None) -> IntencionConversacional:
        contexto = contexto or {}
        t = texto.lower().strip()

        # Host AI 5.0.3: clasificador inteligente previo.
        # Solo toma el control cuando la intención es muy clara y evita romper las reglas legacy.
        clasificacion_503 = self.clasificador_intenciones_503.clasificar(texto, contexto)
        ganadora_503 = clasificacion_503.get("intencion_ganadora", {})
        if ganadora_503.get("intencion") == "recepcion_mercancia" and float(ganadora_503.get("confianza", 0)) >= 0.75:
            return IntencionConversacional(
                texto=texto,
                intencion="recepcion_mercancia",
                confianza=float(ganadora_503.get("confianza", 0.0)),
                parametros={
                    "texto": texto,
                    "clasificacion_503": clasificacion_503,
                    "modo": "borrador_seguro",
                },
                avisos=["Recepción detectada. Se crea borrador seguro antes de tocar stock."],
            )

        # Crear evento / boda / catering
        if any(p in t for p in ["boda", "evento", "catering"]) and any(p in t for p in ["tengo", "crear", "prepara", "organiza", "organízame", "monta"]):
            pax = self._extraer_pax(t) or contexto.get("pax") or 0
            tipo = "boda" if "boda" in t else "catering" if "catering" in t else "evento"
            nombre = self._extraer_nombre_evento(t, tipo)
            if pax:
                return IntencionConversacional(
                    texto=texto,
                    intencion="crear_evento",
                    confianza=0.86,
                    pipeline="evento",
                    accion="crear",
                    parametros={
                        "nombre": nombre,
                        "fecha": contexto.get("fecha", "pendiente"),
                        "pax": pax,
                        "tipo": tipo,
                        "cliente": contexto.get("cliente", ""),
                        "ubicacion": contexto.get("ubicacion", ""),
                    },
                )
            return IntencionConversacional(
                texto=texto,
                intencion="crear_evento_incompleto",
                confianza=0.55,
                avisos=["Faltan pax para crear el evento."],
            )

        # Proponer platos con stock / sobras
        if any(p in t for p in ["sobras", "stock", "aprovechar", "aprovechamiento"]) and any(p in t for p in ["plato", "comida", "hazme", "propón", "propon", "idea"]):
            return IntencionConversacional(
                texto=texto,
                intencion="proponer_platos_stock",
                confianza=0.9,
                pipeline="ia_culinaria",
                accion="proponer_platos_stock",
                parametros={
                    "objetivo": "comida_personal" if "personal" in t else "plato",
                    "raciones": self._extraer_pax(t) or contexto.get("raciones", 4),
                    "estilo": contexto.get("estilo", ""),
                    "limitar": contexto.get("limitar", 3),
                },
            )

        # Calcular coste evento
        if "coste" in t or "cuánto cuesta" in t or "cuanto cuesta" in t:
            evento_id = contexto.get("evento_id")
            precio = self._extraer_precio_pax(t) or contexto.get("precio_venta_por_pax", 0.0)
            if evento_id:
                return IntencionConversacional(
                    texto=texto,
                    intencion="calcular_coste_evento",
                    confianza=0.82,
                    pipeline="costes",
                    accion="calcular_evento",
                    parametros={
                        "evento_id": evento_id,
                        "precio_venta_por_pax": precio,
                        "extras": contexto.get("extras", []),
                    },
                )
            return IntencionConversacional(
                texto=texto,
                intencion="calcular_coste_evento_incompleto",
                confianza=0.45,
                avisos=["Necesito el evento_id o que primero crees/selecciones un evento."],
            )

        # Planificar producción real
        if any(p in t for p in ["planifica", "planificar", "producción", "produccion", "cronograma"]):
            evento_id = contexto.get("evento_id")
            if evento_id:
                return IntencionConversacional(
                    texto=texto,
                    intencion="planificar_produccion_real",
                    confianza=0.84,
                    pipeline="produccion_real",
                    accion="planificar_evento",
                    parametros={
                        "evento_id": evento_id,
                        "hora_inicio": contexto.get("hora_inicio", "08:00"),
                        "equipo_cocina": contexto.get("equipo_cocina", 2),
                        "incluir_logistica": contexto.get("incluir_logistica", True),
                    },
                )
            return IntencionConversacional(
                texto=texto,
                intencion="planificar_produccion_incompleto",
                confianza=0.45,
                avisos=["Necesito el evento_id para planificar producción."],
            )

        # Stock actual
        if "stock" in t and any(p in t for p in ["ver", "actual", "cuánto", "cuanto", "dime"]):
            return IntencionConversacional(
                texto=texto,
                intencion="stock_actual",
                confianza=0.78,
                pipeline="stock",
                accion="stock_actual",
                parametros={},
            )

        return IntencionConversacional(
            texto=texto,
            intencion="desconocida",
            confianza=0.2,
            avisos=[
                "No he entendido todavía qué flujo quieres ejecutar.",
                "Prueba con: 'tengo una boda de 80 pax', 'hazme un plato con stock', 'calcula coste del evento' o 'planifica producción'.",
            ],
        )

    def listar_historial(self) -> Dict[str, Any]:
        return {
            "historial": [h.to_dict() for h in self.historial],
            "total": len(self.historial),
            "lectura_host_ai": f"Historial conversacional: {len(self.historial)} mensajes.",
        }

    # ------------------------------------------------------------------
    # Host AI 5.0.3 - recepción desde chat
    # ------------------------------------------------------------------
    def _ejecutar_borrador_recepcion(self, texto: str, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un borrador de recepción usando motores 4.4.1 y 4.4.2.

        Importante: este paso NO modifica stock todavía. Solo interpreta y valida,
        para mantener la seguridad operativa hasta que el usuario confirme.
        """
        try:
            from dataclasses import asdict
            from SERVICIOS.interprete_recepcion_texto_441 import InterpreteRecepcionTexto441
            from SERVICIOS.validador_recepcion_mercancia_442 import ValidadorRecepcionMercancia442

            interpretacion = InterpreteRecepcionTexto441().interpretar(texto)
            borrador = ValidadorRecepcionMercancia442().validar_lineas(
                texto_original=interpretacion.texto_original,
                proveedor_general=interpretacion.proveedor_general,
                lineas=interpretacion.lineas,
                mensajes_generales=list(interpretacion.errores),
            )
            return {
                "ok": True,
                "tipo": "borrador_recepcion_mercancia",
                "interpretacion": asdict(interpretacion),
                "borrador": asdict(borrador),
                "acciones_recomendadas": [
                    "Revisar coincidencias antes de aplicar stock.",
                    "Confirmar artículos nuevos si aparecen como pendientes.",
                    "En el siguiente sprint se conectará la confirmación con aplicación real al stock.",
                ],
                "requiere_aprobacion": True,
            }
        except Exception as exc:
            return {
                "ok": False,
                "tipo": "borrador_recepcion_mercancia",
                "error": str(exc),
                "acciones_recomendadas": ["Revisar módulo de recepción 4.4.1/4.4.2."],
                "requiere_aprobacion": True,
            }

    def _redactar_recepcion(self, resultado: Dict[str, Any]) -> str:
        if not resultado.get("ok"):
            return "He detectado una recepción de mercancía, pero no he podido crear el borrador: " + resultado.get("error", "error desconocido")

        borrador = resultado.get("borrador", {})
        lineas = borrador.get("lineas_validadas", [])
        if not lineas:
            return "He detectado que quieres registrar una recepción, pero necesito artículo, cantidad y unidad para crear el borrador."

        resumen = []
        for item in lineas[:4]:
            resumen.append(
                f"{item.get('cantidad')} {item.get('unidad')} de {item.get('producto_texto')} "
                f"→ {item.get('accion_sugerida')}"
            )
        extra = "" if len(lineas) <= 4 else f" y {len(lineas) - 4} líneas más"
        proveedor = borrador.get("proveedor_general") or "proveedor no confirmado"
        return (
            f"He detectado una recepción de mercancía y he creado un borrador seguro ({len(lineas)} líneas, {proveedor}). "
            f"Resumen: " + "; ".join(resumen) + extra + ". "
            "No he modificado stock todavía: falta confirmar/aplicar la recepción."
        )

    # ------------------------------------------------------------------
    # Redacción
    # ------------------------------------------------------------------
    def _redactar_respuesta(self, intencion: IntencionConversacional, resultado_pipeline) -> str:
        if not resultado_pipeline.ok:
            return f"He entendido la intención ({intencion.intencion}), pero no he podido ejecutarla: {resultado_pipeline.mensaje}"

        if intencion.intencion == "crear_evento":
            evento = resultado_pipeline.datos.get("evento", {})
            return f"He creado el evento '{evento.get('nombre')}' para {evento.get('pax')} pax. Siguiente paso: añadir servicios, pases y recetas."

        if intencion.intencion == "proponer_platos_stock":
            ideas = resultado_pipeline.datos.get("ideas", [])
            if not ideas:
                return "He revisado el stock, pero no he encontrado una propuesta clara."
            nombres = ", ".join(i.get("nombre", "") for i in ideas[:3])
            return f"He revisado el stock y te propongo: {nombres}."

        if intencion.intencion == "calcular_coste_evento":
            return resultado_pipeline.mensaje

        if intencion.intencion == "planificar_produccion_real":
            return resultado_pipeline.mensaje

        if intencion.intencion == "stock_actual":
            return resultado_pipeline.mensaje

        return resultado_pipeline.mensaje

    def _respuesta_sin_accion(self, intencion: IntencionConversacional) -> str:
        if intencion.avisos:
            return "Necesito un dato más: " + " ".join(intencion.avisos)
        return "No puedo ejecutar esa petición todavía."

    # ------------------------------------------------------------------
    # Extracción simple
    # ------------------------------------------------------------------
    def _extraer_pax(self, texto: str) -> int:
        patrones = [
            r"(\d+)\s*(pax|personas|comensales)",
            r"para\s*(\d+)",
            r"de\s*(\d+)\s*(pax|personas|comensales)?",
        ]
        for patron in patrones:
            m = re.search(patron, texto)
            if m:
                try:
                    return int(m.group(1))
                except Exception:
                    pass
        return 0

    def _extraer_precio_pax(self, texto: str) -> float:
        patrones = [
            r"(\d+(?:[.,]\d+)?)\s*€/pax",
            r"(\d+(?:[.,]\d+)?)\s*euros por persona",
            r"a\s*(\d+(?:[.,]\d+)?)\s*euros",
        ]
        for patron in patrones:
            m = re.search(patron, texto)
            if m:
                return float(m.group(1).replace(",", "."))
        return 0.0

    def _extraer_nombre_evento(self, texto: str, tipo: str) -> str:
        pax = self._extraer_pax(texto)
        if pax:
            return f"{tipo.title()} {pax} pax"
        return f"{tipo.title()} nuevo"
