from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from SERVICIOS.host_ai_engine.adapters import HostAIAgentRouter
from SERVICIOS.host_ai_engine.agent_registry import AgentRegistry
from SERVICIOS.host_ai_engine.models import (
    AUTONOMIA_CONSULTAR,
    AUTONOMIA_EJECUTAR,
    AUTONOMIA_PROPONER,
    ConfirmationRequest,
    DecisionAuditEntry,
    HostAISolicitudOperativa,
    INC_ACCION_NO_AUTORIZADA,
    INC_CONFLICTO_FUENTES,
    INC_DATO_AMBIGUO,
    INC_DATO_OBLIGATORIO_AUSENTE,
    PlanStep,
    ESTADO_CONFIRMACION_ACEPTADA,
    ESTADO_CONFIRMACION_PARCIAL,
    ESTADO_CONFIRMACION_PENDIENTE,
    ESTADO_CONFIRMACION_RECHAZADA,
    ESTADO_PASO_BLOQUEADO,
    ESTADO_PASO_EJECUTADO,
    ESTADO_PASO_ERROR,
    ESTADO_PASO_OMITIDO,
    ESTADO_SOLICITUD_BLOQUEADA,
    ESTADO_SOLICITUD_CANCELADA,
    ESTADO_SOLICITUD_CLASIFICADA,
    ESTADO_SOLICITUD_COMPLETADA,
    ESTADO_SOLICITUD_COMPLETADA_CON_INCIDENCIAS,
    ESTADO_SOLICITUD_EN_EJECUCION,
    ESTADO_SOLICITUD_ERROR,
    ESTADO_SOLICITUD_ESPERANDO_CONFIRMACION,
    ESTADO_SOLICITUD_PLANIFICADA,
)
from SERVICIOS.host_ai_engine.policy import HostAIDecisionPolicy


class DirectorIAFuncional:
    VERSION = "1.0"
    GOAL_TO_OPERATIONS = {
        "importar": ["analizar_origen", "preparar_importacion"],
        "resolver_catalogo": ["detectar_similares"],
        "resolver_ingredientes": ["detectar_similares"],
        "revisar_incidencias": ["proponer_receta", "listar_incidencias"],
        "crear_recetas": ["proponer_receta", "crear_recetas_autorizadas"],
        "generar_escandallos": ["generar_escandallos_autorizados"],
        "simular_escandallos": ["simular_calculo"],
        "detectar_menus_afectados": ["detectar_afectados_escandallos"],
        "actualizar_menus_afectados": ["actualizar_menus_afectados"],
        "modificar_precio": ["revisar_datos_producto", "modificar_precio_autorizado"],
        "detectar_escandallos_afectados": ["detectar_afectados_producto"],
        "recalcular_escandallos": ["recalcular_impactados_autorizado"],
        "crear_menu": ["proponer_menu", "crear_menu_autorizado", "registrar_historico_menu"],
        "calcular_coste_menu": ["proponer_menu"],
        "registrar_historico_menu": ["registrar_historico_menu"],
        "nueva_receta": ["analizar_origen", "preparar_importacion", "detectar_similares", "proponer_receta", "crear_recetas_autorizadas", "generar_escandallos_autorizados", "detectar_pendiente_menu"],
        "pendiente_menu": ["detectar_pendiente_menu"],
    }
    OPERATION_AGENT = {
        "analizar_origen": "IMPORTACION_IA",
        "preparar_importacion": "IMPORTACION_IA",
        "listar_incidencias": "IMPORTACION_IA",
        "buscar_producto": "CATALOGO_IA",
        "detectar_similares": "CATALOGO_IA",
        "revisar_datos_producto": "CATALOGO_IA",
        "proponer_alta_producto": "CATALOGO_IA",
        "modificar_precio_autorizado": "CATALOGO_IA",
        "buscar_receta": "RECETAS_IA",
        "revisar_completitud": "RECETAS_IA",
        "proponer_receta": "RECETAS_IA",
        "preparar_duplicado": "RECETAS_IA",
        "crear_recetas_autorizadas": "RECETAS_IA",
        "buscar_escandallo": "ESCANDALLOS_IA",
        "simular_calculo": "ESCANDALLOS_IA",
        "detectar_desactualizacion": "ESCANDALLOS_IA",
        "detectar_afectados_producto": "ESCANDALLOS_IA",
        "proponer_recalculo": "ESCANDALLOS_IA",
        "generar_escandallos_autorizados": "ESCANDALLOS_IA",
        "recalcular_impactados_autorizado": "ESCANDALLOS_IA",
        "buscar_menu": "MENUS_IA",
        "calcular_rentabilidad": "MENUS_IA",
        "detectar_incidencias": "MENUS_IA",
        "detectar_afectados_escandallos": "MENUS_IA",
        "proponer_duplicado": "MENUS_IA",
        "proponer_menu": "MENUS_IA",
        "crear_menu_autorizado": "MENUS_IA",
        "registrar_historico_menu": "MENUS_IA",
        "actualizar_menus_afectados": "MENUS_IA",
        "detectar_pendiente_menu": "MENUS_IA",
        "consultar_evento": "EVENTOS_IA",
        "consultar_plan": "PRODUCCION_IA",
        "consultar_necesidades": "COMPRAS_IA",
        "consultar_existencias": "STOCK_IA",
    }
    OPERATION_DEPENDENCIES = {
        "preparar_importacion": ["analizar_origen"],
        "detectar_similares": ["preparar_importacion"],
        "proponer_receta": ["preparar_importacion"],
        "listar_incidencias": ["preparar_importacion"],
        "crear_recetas_autorizadas": ["proponer_receta", "listar_incidencias"],
        "generar_escandallos_autorizados": ["crear_recetas_autorizadas"],
        "simular_calculo": ["crear_recetas_autorizadas"],
        "detectar_afectados_escandallos": ["generar_escandallos_autorizados", "detectar_afectados_producto", "recalcular_impactados_autorizado"],
        "actualizar_menus_afectados": ["detectar_afectados_escandallos"],
        "modificar_precio_autorizado": ["revisar_datos_producto", "detectar_afectados_producto", "detectar_afectados_escandallos"],
        "recalcular_impactados_autorizado": ["modificar_precio_autorizado", "detectar_afectados_producto"],
        "crear_menu_autorizado": ["proponer_menu"],
        "registrar_historico_menu": ["crear_menu_autorizado"],
        "detectar_pendiente_menu": ["generar_escandallos_autorizados"],
    }
    OPERATION_LEVEL = {
        "analizar_origen": AUTONOMIA_CONSULTAR,
        "preparar_importacion": AUTONOMIA_CONSULTAR,
        "listar_incidencias": AUTONOMIA_CONSULTAR,
        "buscar_producto": AUTONOMIA_CONSULTAR,
        "detectar_similares": AUTONOMIA_CONSULTAR,
        "revisar_datos_producto": AUTONOMIA_CONSULTAR,
        "proponer_alta_producto": AUTONOMIA_PROPONER,
        "modificar_precio_autorizado": AUTONOMIA_EJECUTAR,
        "buscar_receta": AUTONOMIA_CONSULTAR,
        "revisar_completitud": AUTONOMIA_CONSULTAR,
        "proponer_receta": AUTONOMIA_PROPONER,
        "preparar_duplicado": AUTONOMIA_PROPONER,
        "crear_recetas_autorizadas": AUTONOMIA_EJECUTAR,
        "buscar_escandallo": AUTONOMIA_CONSULTAR,
        "simular_calculo": AUTONOMIA_CONSULTAR,
        "detectar_desactualizacion": AUTONOMIA_CONSULTAR,
        "detectar_afectados_producto": AUTONOMIA_CONSULTAR,
        "proponer_recalculo": AUTONOMIA_PROPONER,
        "generar_escandallos_autorizados": AUTONOMIA_EJECUTAR,
        "recalcular_impactados_autorizado": AUTONOMIA_EJECUTAR,
        "buscar_menu": AUTONOMIA_CONSULTAR,
        "calcular_rentabilidad": AUTONOMIA_CONSULTAR,
        "detectar_incidencias": AUTONOMIA_CONSULTAR,
        "detectar_afectados_escandallos": AUTONOMIA_CONSULTAR,
        "proponer_duplicado": AUTONOMIA_PROPONER,
        "proponer_menu": AUTONOMIA_PROPONER,
        "crear_menu_autorizado": AUTONOMIA_EJECUTAR,
        "registrar_historico_menu": AUTONOMIA_EJECUTAR,
        "actualizar_menus_afectados": AUTONOMIA_EJECUTAR,
        "detectar_pendiente_menu": AUTONOMIA_CONSULTAR,
        "consultar_evento": AUTONOMIA_CONSULTAR,
        "consultar_plan": AUTONOMIA_CONSULTAR,
        "consultar_necesidades": AUTONOMIA_CONSULTAR,
        "consultar_existencias": AUTONOMIA_CONSULTAR,
    }

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.registry = AgentRegistry()
        self.policy = HostAIDecisionPolicy()
        self.router = HostAIAgentRouter(self.base_dir)

    def procesar(self, solicitud: HostAISolicitudOperativa) -> dict[str, Any]:
        inicio = time.perf_counter()
        auditoria: list[DecisionAuditEntry] = []
        try:
            modo_operacion = str((solicitud.datos_de_entrada or {}).get("modo_operacion") or "EJECUTAR").strip().upper()
            if str((solicitud.datos_de_entrada or {}).get("cancelar") or "").strip().lower() in {"1", "true", "s", "si", "sí"}:
                solicitud.estado = ESTADO_SOLICITUD_CANCELADA
                solicitud.resultado = {"mensaje": "Solicitud cancelada antes de ejecutar pasos."}
                auditoria.append(self._audit("cancelacion", "Solicitud cancelada antes de ejecución."))
                return self._finalizar(solicitud, inicio, auditoria)

            clasificacion = self._clasificar(solicitud)
            solicitud.agente_principal = clasificacion["agente_principal"]
            solicitud.agentes_delegados = clasificacion["agentes_delegados"]
            solicitud.intencion = clasificacion["intencion"]
            solicitud.estado = ESTADO_SOLICITUD_CLASIFICADA
            auditoria.append(self._audit("clasificacion", "Solicitud clasificada.", clasificacion))

            incidencias_clasificacion = self._validar_entrada(solicitud)
            if incidencias_clasificacion:
                solicitud.incidencias.extend(incidencias_clasificacion)
                solicitud.estado = ESTADO_SOLICITUD_BLOQUEADA
                solicitud.resultado = {"mensaje": "Faltan datos o hay ambigüedad; no puedo continuar con seguridad."}
                auditoria.append(self._audit("bloqueo", "Solicitud bloqueada por validación de entrada.", {"incidencias": incidencias_clasificacion}))
                return self._finalizar(solicitud, inicio, auditoria)

            pasos = self._crear_plan(solicitud)
            solicitud.pasos = pasos
            solicitud.plan = {
                "tipo": "SECUENCIAL",
                "total_pasos": len(pasos),
                "agentes": [paso.agente for paso in pasos],
            }
            solicitud.estado = ESTADO_SOLICITUD_PLANIFICADA
            plan_hash = self._plan_hash(solicitud.pasos)
            solicitud.contexto["plan_hash"] = plan_hash
            auditoria.append(self._audit("planificacion", "Plan secuencial generado.", {"plan_hash": plan_hash, "pasos": [p.to_dict() for p in pasos]}))

            dependency_results: dict[int, dict[str, Any]] = {}
            solicitud.estado = ESTADO_SOLICITUD_EN_EJECUCION
            for step in solicitud.pasos:
                if not self._dependencias_resueltas(step, dependency_results):
                    step.estado = ESTADO_PASO_BLOQUEADO
                    step.error = "Dependencias no resueltas"
                    solicitud.errores.append(step.error)
                    solicitud.estado = ESTADO_SOLICITUD_BLOQUEADA
                    auditoria.append(self._audit("bloqueo_dependencias", f"Paso {step.orden} bloqueado por dependencias.", step.to_dict()))
                    break

                agent = self.registry.obtener(step.agente)
                capability = self.registry.obtener_capacidad(step.agente, step.operacion)
                decision = self.policy.evaluar(agent, capability, step)
                if decision.bloqueada:
                    step.estado = ESTADO_PASO_BLOQUEADO
                    step.error = decision.motivo
                    solicitud.incidencias.append({"tipo": decision.tipo_incidencia or INC_ACCION_NO_AUTORIZADA, "detalle": decision.motivo, "paso": step.orden})
                    solicitud.estado = ESTADO_SOLICITUD_BLOQUEADA
                    auditoria.append(self._audit("bloqueo_politica", decision.motivo, {"paso": step.to_dict(), "decision": decision.to_dict()}))
                    break

                if decision.requiere_confirmacion:
                    if modo_operacion == "SIMULAR":
                        step.estado = ESTADO_PASO_OMITIDO
                        step.resultado_real = {"mensaje": "Paso persistente omitido en modo simulación.", "simulacion": True}
                        solicitud.acciones_propuestas.append({"paso": step.orden, "agente": step.agente, "operacion": step.operacion, "entradas": step.entradas})
                        solicitud.resultado = self._resumen_final(solicitud, dependency_results, simulacion=True)
                        solicitud.estado = ESTADO_SOLICITUD_COMPLETADA_CON_INCIDENCIAS if solicitud.incidencias else ESTADO_SOLICITUD_COMPLETADA
                        auditoria.append(self._audit("simulacion", "La ejecución se detuvo antes de la primera escritura persistente.", step.to_dict()))
                        break
                    confirmacion = self._resolver_confirmacion(solicitud, step, plan_hash)
                    if confirmacion is None:
                        solicitud.confirmaciones_requeridas = self._crear_confirmacion_agrupada(solicitud, plan_hash)
                        solicitud.estado = ESTADO_SOLICITUD_ESPERANDO_CONFIRMACION
                        auditoria.append(self._audit("esperando_confirmacion", "Se requiere confirmación antes de ejecutar escrituras.", {"confirmaciones": [c.to_dict() for c in solicitud.confirmaciones_requeridas]}))
                        break
                    if confirmacion.estado == ESTADO_CONFIRMACION_RECHAZADA:
                        step.estado = ESTADO_PASO_OMITIDO
                        step.resultado_real = {"mensaje": "Acción rechazada por el usuario."}
                        solicitud.estado = ESTADO_SOLICITUD_CANCELADA
                        solicitud.resultado = {"mensaje": "Solicitud cancelada por rechazo de confirmación."}
                        auditoria.append(self._audit("confirmacion_rechazada", "El usuario rechazó la acción persistente.", confirmacion.to_dict()))
                        break
                    scope = dict(confirmacion.alcance_autorizado or {}) if confirmacion.estado in {ESTADO_CONFIRMACION_ACEPTADA, ESTADO_CONFIRMACION_PARCIAL} else {}
                    resultado = self._ejecutar_paso(step, solicitud, dependency_results, scope)
                else:
                    resultado = self._ejecutar_paso(step, solicitud, dependency_results, {})

                dependency_results[step.orden] = resultado

            if solicitud.estado == ESTADO_SOLICITUD_EN_EJECUCION:
                solicitud.resultado = self._resumen_final(solicitud, dependency_results, simulacion=False)
                solicitud.estado = ESTADO_SOLICITUD_COMPLETADA_CON_INCIDENCIAS if solicitud.incidencias else ESTADO_SOLICITUD_COMPLETADA
                auditoria.append(self._audit("completada", "Solicitud completada.", solicitud.resultado))

            if solicitud.estado == ESTADO_SOLICITUD_ESPERANDO_CONFIRMACION:
                solicitud.resultado = self._resumen_final(solicitud, dependency_results, simulacion=False)

            return self._finalizar(solicitud, inicio, auditoria)
        except Exception as exc:
            solicitud.estado = ESTADO_SOLICITUD_ERROR
            solicitud.errores.append(str(exc))
            solicitud.resultado = {"mensaje": f"Error ejecutando Director IA: {exc}"}
            auditoria.append(self._audit("error", "Error no controlado en Director IA.", {"error": str(exc)}))
            return self._finalizar(solicitud, inicio, auditoria)

    def _clasificar(self, solicitud: HostAISolicitudOperativa) -> dict[str, Any]:
        tipo = str(solicitud.intencion or solicitud.datos_de_entrada.get("tipo_peticion") or "consulta_simple").lower()
        texto = str(solicitud.texto_original or "").lower()
        modulo = str(solicitud.modulo_origen or "").lower()
        objetivos = self._normalizar_objetivos(solicitud)
        if objetivos:
            operaciones = self._expandir_operaciones(objetivos)
            agentes = [self.OPERATION_AGENT.get(op, "DIRECTOR_IA") for op in operaciones]
            unicos = []
            for agente in agentes:
                if agente not in unicos:
                    unicos.append(agente)
            principal = "DIRECTOR_IA" if len(unicos) > 1 else (unicos[0] if unicos else "DIRECTOR_IA")
            delegados = [a for a in unicos if a != principal]
            return {"agente_principal": principal, "agentes_delegados": delegados, "intencion": tipo or "orquestar_erp", "objetivos": list(objetivos), "operaciones": operaciones}
        if tipo in {"buscar_receta", "consulta_receta"} or "receta" in modulo:
            return {"agente_principal": "RECETAS_IA", "agentes_delegados": [], "intencion": "buscar_receta"}
        if tipo in {"buscar_menu", "calcular_rentabilidad_menu"} or "menu" in modulo:
            return {"agente_principal": "MENUS_IA", "agentes_delegados": [], "intencion": "buscar_menu" if "buscar" in tipo else "calcular_rentabilidad"}
        if "importa" in texto and "escandallo" in texto and "receta" in texto:
            return {"agente_principal": "DIRECTOR_IA", "agentes_delegados": ["IMPORTACION_IA", "CATALOGO_IA", "RECETAS_IA", "ESCANDALLOS_IA"], "intencion": "importar_word_crear_recetas_generar_escandallos"}
        if tipo == "importar_word_crear_recetas_generar_escandallos":
            return {"agente_principal": "DIRECTOR_IA", "agentes_delegados": ["IMPORTACION_IA", "CATALOGO_IA", "RECETAS_IA", "ESCANDALLOS_IA"], "intencion": tipo}
        agent_map = {
            "catalogo": "CATALOGO_IA",
            "recetas": "RECETAS_IA",
            "escandallos": "ESCANDALLOS_IA",
            "menus": "MENUS_IA",
            "eventos": "EVENTOS_IA",
            "produccion": "PRODUCCION_IA",
            "compras": "COMPRAS_IA",
            "stock": "STOCK_IA",
            "importacion": "IMPORTACION_IA",
        }
        for key, agent in agent_map.items():
            if key in modulo or key in tipo:
                return {"agente_principal": agent, "agentes_delegados": [], "intencion": tipo or "consulta_simple"}
        return {"agente_principal": "DIRECTOR_IA", "agentes_delegados": [], "intencion": tipo or "consulta_simple"}

    def _validar_entrada(self, solicitud: HostAISolicitudOperativa) -> list[dict[str, Any]]:
        incidencias: list[dict[str, Any]] = []
        tipo = str(solicitud.intencion or "")
        data = dict(solicitud.datos_de_entrada or {})
        objetivos = self._normalizar_objetivos(solicitud)
        if tipo == "buscar_receta" and not any(str(data.get(k) or "").strip() for k in ["nombre", "codigo"]):
            incidencias.append({"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Para buscar receta necesito nombre o código."})
        if tipo == "importar_word_crear_recetas_generar_escandallos" and not str(data.get("texto_importacion") or solicitud.texto_original or "").strip():
            incidencias.append({"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Falta el contenido del documento a importar."})
        if "importar" in objetivos and not str(data.get("texto_importacion") or solicitud.texto_original or "").strip():
            incidencias.append({"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Falta contenido para la importación."})
        if "modificar_precio" in objetivos and not str(data.get("producto_codigo") or "").strip():
            incidencias.append({"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Falta producto_codigo para el cambio de precio."})
        if "modificar_precio" in objetivos and str(data.get("precio") or "").strip() == "":
            incidencias.append({"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Falta el nuevo precio para el cambio solicitado."})
        if "crear_menu" in objetivos and not any(list(data.get(k) or []) for k in ["recetas", "escandallos"]):
            incidencias.append({"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Para crear menú necesito recetas y/o escandallos seleccionados."})
        if "nueva_receta" in objetivos and not str(data.get("nombre_receta") or "").strip() and not str(data.get("texto_importacion") or solicitud.texto_original or "").strip():
            incidencias.append({"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Falta nombre o contenido para la nueva receta."})
        if str(data.get("ambiguous_request") or "").strip().lower() in {"1", "true", "s", "si", "sí"}:
            incidencias.append({"tipo": INC_DATO_AMBIGUO, "detalle": "La solicitud contiene una ambigüedad marcada explícitamente."})
        if str(data.get("conflict_sources") or "").strip().lower() in {"1", "true", "s", "si", "sí"}:
            incidencias.append({"tipo": INC_CONFLICTO_FUENTES, "detalle": "Se ha detectado conflicto entre fuentes de entrada."})
        return incidencias

    def _crear_plan(self, solicitud: HostAISolicitudOperativa) -> list[PlanStep]:
        tipo = str(solicitud.intencion or "")
        data = dict(solicitud.datos_de_entrada or {})
        objetivos = self._normalizar_objetivos(solicitud)
        if objetivos:
            return self._crear_plan_desde_objetivos(objetivos, solicitud)
        if tipo == "buscar_receta":
            return [
                PlanStep(1, "RECETAS_IA", "buscar_receta", AUTONOMIA_CONSULTAR, {"nombre": data.get("nombre", ""), "codigo": data.get("codigo", "")}, [], "Receta localizada o explicación de ausencia.", False, capacidad_identificador="recetas.buscar_receta"),
            ]
        if tipo == "calcular_rentabilidad":
            return [
                PlanStep(1, "MENUS_IA", "calcular_rentabilidad", AUTONOMIA_CONSULTAR, {"id_o_codigo": data.get("id_o_codigo", "")}, [], "Rentabilidad calculada.", False, capacidad_identificador="menus.calcular_rentabilidad"),
            ]
        if tipo == "importar_word_crear_recetas_generar_escandallos":
            return [
                PlanStep(1, "IMPORTACION_IA", "analizar_origen", AUTONOMIA_CONSULTAR, {"origen_documento": data.get("origen_documento", "WORD"), "formato_entrada": data.get("formato_entrada", solicitud.formato_entrada), "texto_importacion": data.get("texto_importacion", solicitud.texto_original)}, [], "Origen clasificado.", False, capacidad_identificador="importacion.analizar_origen"),
                PlanStep(2, "IMPORTACION_IA", "preparar_importacion", AUTONOMIA_CONSULTAR, {"tipo_contenido": "RECETAS", "texto_importacion": data.get("texto_importacion", solicitud.texto_original)}, [1], "Recetas detectadas y contexto preparado.", False, capacidad_identificador="importacion.preparar_importacion"),
                PlanStep(3, "CATALOGO_IA", "detectar_similares", AUTONOMIA_CONSULTAR, {}, [2], "Ingredientes comparados con catálogo.", False, capacidad_identificador="catalogo.detectar_similares"),
                PlanStep(4, "RECETAS_IA", "proponer_receta", AUTONOMIA_PROPONER, {}, [2], "Recetas propuestas sin guardar.", False, capacidad_identificador="recetas.proponer_receta"),
                PlanStep(5, "IMPORTACION_IA", "listar_incidencias", AUTONOMIA_CONSULTAR, {}, [2, 3, 4], "Incidencias consolidadas.", False, capacidad_identificador="importacion.listar_incidencias"),
                PlanStep(6, "RECETAS_IA", "crear_recetas_autorizadas", AUTONOMIA_EJECUTAR, {}, [4, 5], "Recetas persistidas tras confirmación.", True, capacidad_identificador="recetas.crear_recetas_autorizadas", persistencia_real=True),
                PlanStep(7, "ESCANDALLOS_IA", "simular_calculo", AUTONOMIA_CONSULTAR, {}, [6], "Escandallos simulados para recetas creadas.", False, capacidad_identificador="escandallos.simular_calculo"),
            ]
        if tipo == "consultar_evento":
            return [PlanStep(1, "EVENTOS_IA", "consultar_evento", AUTONOMIA_CONSULTAR, data, [], "Consulta de evento segura.", False, capacidad_identificador="eventos.consultar_evento")]
        return [PlanStep(1, solicitud.agente_principal or "DIRECTOR_IA", tipo or "consulta_simple", solicitud.nivel_de_autonomia or AUTONOMIA_CONSULTAR, data, [], "Resultado funcional del agente principal.", False)]

    def _dependencias_resueltas(self, step: PlanStep, dependency_results: dict[int, dict[str, Any]]) -> bool:
        return all(dep in dependency_results for dep in list(step.dependencias or []))

    def _ejecutar_paso(self, step: PlanStep, solicitud: HostAISolicitudOperativa, dependency_results: dict[int, dict[str, Any]], confirmation_scope: dict[str, Any]) -> dict[str, Any]:
        resultado = self.router.ejecutar_paso(solicitud, step, dependency_results, confirmation_scope)
        if resultado.get("ok"):
            step.estado = ESTADO_PASO_EJECUTADO
            step.resultado_real = resultado
        else:
            step.estado = ESTADO_PASO_ERROR
            step.resultado_real = resultado
            step.error = "; ".join(str(e) for e in list(resultado.get("errores") or [])) or "Paso no resuelto"
            for incidencia in list(resultado.get("incidencias") or []):
                solicitud.incidencias.append({**incidencia, "paso": step.orden})
        return resultado

    def _crear_confirmacion_agrupada(self, solicitud: HostAISolicitudOperativa, plan_hash: str) -> list[ConfirmationRequest]:
        acciones = [
            {"paso": step.orden, "agente": step.agente, "operacion": step.operacion, "persistencia_real": step.persistencia_real}
            for step in solicitud.pasos
            if step.requiere_confirmacion
        ]
        if not acciones:
            return []
        return [
            ConfirmationRequest(
                id_confirmacion=f"CONF-{solicitud.id_solicitud}",
                id_solicitud=solicitud.id_solicitud,
                acciones_incluidas=acciones,
                resumen_visible="Se requiere autorización explícita para ejecutar acciones persistentes del plan.",
                impacto="Puede crear o modificar datos a través de servicios autorizados.",
                riesgos=["Cambios persistentes en sandbox o entorno de datos activo según base_dir.", "Si cambia el plan, la confirmación actual dejará de ser válida."],
                fecha_solicitud=datetime.now().isoformat(timespec="seconds"),
                plan_hash=plan_hash,
            )
        ]

    def _resolver_confirmacion(self, solicitud: HostAISolicitudOperativa, step: PlanStep, plan_hash: str) -> ConfirmationRequest | None:
        for confirmacion in list(solicitud.confirmaciones_recibidas or []):
            if confirmacion.plan_hash != plan_hash:
                solicitud.incidencias.append({"tipo": INC_ACCION_NO_AUTORIZADA, "detalle": "La confirmación recibida no coincide con el plan actual.", "paso": step.orden})
                continue
            acciones = {int(a.get("paso")) for a in list(confirmacion.acciones_incluidas or []) if str(a.get("paso") or "").isdigit()}
            if step.orden in acciones:
                return confirmacion
        return None

    def _resumen_final(self, solicitud: HostAISolicitudOperativa, dependency_results: dict[int, dict[str, Any]], simulacion: bool) -> dict[str, Any]:
        pasos_ejecutados = [p for p in solicitud.pasos if p.estado == ESTADO_PASO_EJECUTADO]
        agentes_utilizados = []
        servicios_utilizados = []
        objetos_creados: list[dict[str, Any]] = []
        objetos_modificados: list[dict[str, Any]] = []
        advertencias: list[str] = []
        for paso in pasos_ejecutados:
            if paso.agente not in agentes_utilizados:
                agentes_utilizados.append(paso.agente)
            capacidad = self.registry.obtener_capacidad(paso.agente, paso.operacion)
            if capacidad and capacidad.servicio_objetivo not in servicios_utilizados:
                servicios_utilizados.append(capacidad.servicio_objetivo)
            resultado = dict(paso.resultado_real or {})
            for creado in list(resultado.get("creadas") or []):
                objetos_creados.append({"tipo": "receta", **creado})
            for creado in list(resultado.get("escandallos_generados") or []):
                objetos_creados.append({"tipo": "escandallo", **creado})
            if resultado.get("menu_creado"):
                objetos_creados.append({"tipo": "menu", **dict(resultado.get("menu_creado") or {})})
            if resultado.get("producto_actualizado"):
                objetos_modificados.append({"tipo": "producto", **dict(resultado.get("producto_actualizado") or {})})
            for mod in list(resultado.get("escandallos_recalculados") or []):
                objetos_modificados.append({"tipo": "escandallo", **mod})
            for mod in list(resultado.get("menus_actualizados") or []):
                objetos_modificados.append({"tipo": "menu", **mod})
            if resultado.get("menu_historizado"):
                objetos_modificados.append({"tipo": "menu_historico", **dict(resultado.get("menu_historizado") or {})})
            advertencias.extend(list(resultado.get("errores_generacion") or []))
            advertencias.extend(list(resultado.get("errores_recalculo") or []))
        return {
            "id_solicitud": solicitud.id_solicitud,
            "estado": solicitud.estado,
            "agente_principal": solicitud.agente_principal,
            "agentes_participantes": [solicitud.agente_principal] + list(solicitud.agentes_delegados or []),
            "agentes_utilizados": agentes_utilizados,
            "servicios_utilizados": servicios_utilizados,
            "simulacion": simulacion,
            "pasos_ejecutados": [p.to_dict() for p in solicitud.pasos if p.estado == ESTADO_PASO_EJECUTADO],
            "pasos_bloqueados": [p.to_dict() for p in solicitud.pasos if p.estado == ESTADO_PASO_BLOQUEADO],
            "pasos_omitidos": [p.to_dict() for p in solicitud.pasos if p.estado == ESTADO_PASO_OMITIDO],
            "objetos_creados": objetos_creados,
            "objetos_modificados": objetos_modificados,
            "incidencias": list(solicitud.incidencias or []),
            "advertencias": advertencias,
            "errores": list(solicitud.errores or []),
            "resultados_por_paso": dependency_results,
        }

    def _normalizar_objetivos(self, solicitud: HostAISolicitudOperativa) -> list[str]:
        data = dict(solicitud.datos_de_entrada or {})
        objetivos = [str(x).strip().lower() for x in list(data.get("objetivos") or []) if str(x).strip()]
        tipo = str(solicitud.intencion or "").lower()
        texto = str(solicitud.texto_original or "").lower()
        if objetivos:
            return objetivos
        if tipo == "orquestar_erp":
            if "import" in texto and "receta" in texto:
                objetivos.extend(["importar", "resolver_catalogo", "revisar_incidencias", "crear_recetas", "generar_escandallos", "detectar_menus_afectados", "actualizar_menus_afectados"])
            elif "precio" in texto:
                objetivos.extend(["modificar_precio", "detectar_escandallos_afectados", "detectar_menus_afectados", "recalcular_escandallos", "actualizar_menus_afectados"])
            elif "menú" in texto or "menu" in texto:
                objetivos.extend(["crear_menu", "calcular_coste_menu", "registrar_historico_menu"])
            elif "nueva receta" in texto or ("receta" in texto and "ingrediente" in texto):
                objetivos.extend(["nueva_receta", "pendiente_menu"])
        if tipo == "importar_word_crear_recetas_generar_escandallos":
            objetivos.extend(["importar", "resolver_catalogo", "revisar_incidencias", "crear_recetas", "generar_escandallos"])
        return objetivos

    def _expandir_operaciones(self, objetivos: list[str]) -> list[str]:
        operaciones: list[str] = []
        for objetivo in objetivos:
            for operacion in self.GOAL_TO_OPERATIONS.get(objetivo, []):
                if operacion not in operaciones:
                    operaciones.append(operacion)
        return operaciones

    def _crear_plan_desde_objetivos(self, objetivos: list[str], solicitud: HostAISolicitudOperativa) -> list[PlanStep]:
        operaciones = self._expandir_operaciones(objetivos)
        pasos: list[PlanStep] = []
        indices: dict[str, int] = {}
        for operacion in operaciones:
            dependencias_ops = [dep for dep in self.OPERATION_DEPENDENCIES.get(operacion, []) if dep in operaciones]
            dependencias = [indices[dep] for dep in dependencias_ops if dep in indices]
            agent = self.OPERATION_AGENT.get(operacion, solicitud.agente_principal or "DIRECTOR_IA")
            nivel = self.OPERATION_LEVEL.get(operacion, solicitud.nivel_de_autonomia or AUTONOMIA_CONSULTAR)
            capacidad = self.registry.obtener_capacidad(agent, operacion)
            persistencia_real = bool(capacidad and nivel == AUTONOMIA_EJECUTAR)
            entradas = self._entradas_para_operacion(operacion, solicitud)
            paso = PlanStep(
                len(pasos) + 1,
                agent,
                operacion,
                nivel,
                entradas,
                dependencias,
                self._resultado_esperado(operacion),
                persistencia_real,
                capacidad_identificador=getattr(capacidad, "identificador", ""),
                persistencia_real=persistencia_real,
            )
            pasos.append(paso)
            indices[operacion] = paso.orden
        return pasos

    @staticmethod
    def _resultado_esperado(operacion: str) -> str:
        return {
            "analizar_origen": "Origen y tipo de contenido detectados.",
            "preparar_importacion": "Contexto de importación preparado.",
            "listar_incidencias": "Incidencias consolidadas.",
            "detectar_similares": "Coincidencias de catálogo evaluadas.",
            "proponer_receta": "Recetas propuestas sin persistir.",
            "crear_recetas_autorizadas": "Recetas autorizadas creadas.",
            "generar_escandallos_autorizados": "Escandallos generados desde recetas.",
            "detectar_afectados_escandallos": "Menús afectados identificados.",
            "actualizar_menus_afectados": "Menús afectados actualizados o marcados.",
            "modificar_precio_autorizado": "Precio actualizado en catálogo.",
            "detectar_afectados_producto": "Escandallos afectados identificados.",
            "recalcular_impactados_autorizado": "Escandallos recalculados con precio nuevo.",
            "proponer_menu": "Menú preparado con cálculo de coste.",
            "crear_menu_autorizado": "Menú creado.",
            "registrar_historico_menu": "Histórico económico del menú registrado.",
            "detectar_pendiente_menu": "Estado pendiente de menú determinado.",
        }.get(operacion, "Resultado funcional del paso.")

    def _entradas_para_operacion(self, operacion: str, solicitud: HostAISolicitudOperativa) -> dict[str, Any]:
        data = dict(solicitud.datos_de_entrada or {})
        if operacion in {"analizar_origen", "preparar_importacion"}:
            return {"origen_documento": data.get("origen_documento", "TEXTO"), "formato_entrada": data.get("formato_entrada", solicitud.formato_entrada), "texto_importacion": data.get("texto_importacion", solicitud.texto_original), "tipo_contenido": data.get("tipo_contenido", "RECETAS")}
        if operacion == "revisar_datos_producto":
            return {"producto": {"codigo": data.get("producto_codigo"), "nombre": data.get("producto_nombre"), "precio": data.get("precio"), "unidad_base": data.get("unidad_base")}}
        if operacion == "modificar_precio_autorizado":
            return {"codigo": data.get("producto_codigo"), "precio": data.get("precio"), "fecha_precio": data.get("fecha_precio")}
        if operacion == "detectar_afectados_producto":
            return {"codigo": data.get("producto_codigo"), "nombre": data.get("producto_nombre")}
        if operacion in {"proponer_menu", "crear_menu_autorizado", "registrar_historico_menu"}:
            return {"nombre_menu": data.get("nombre_menu"), "recetas": list(data.get("recetas") or []), "escandallos": list(data.get("escandallos") or []), "comensales": data.get("comensales"), "precio_venta_comensal": data.get("precio_venta_comensal"), "precio_venta_total": data.get("precio_venta_total")}
        if operacion == "buscar_receta":
            return {"nombre": data.get("nombre", ""), "codigo": data.get("codigo", "")}
        return {}

    @staticmethod
    def _plan_hash(steps: list[PlanStep]) -> str:
        payload = [
            {
                "orden": s.orden,
                "agente": s.agente,
                "operacion": s.operacion,
                "nivel_autonomia": s.nivel_autonomia,
                "entradas": s.entradas,
                "dependencias": s.dependencias,
                "persistencia_real": s.persistencia_real,
            }
            for s in steps
        ]
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _audit(tipo: str, detalle: str, datos: dict[str, Any] | None = None) -> DecisionAuditEntry:
        return DecisionAuditEntry(datetime.now().isoformat(timespec="seconds"), tipo, detalle, datos or {})

    def _finalizar(self, solicitud: HostAISolicitudOperativa, inicio: float, auditoria: list[DecisionAuditEntry]) -> dict[str, Any]:
        solicitud.duracion_ms = int((time.perf_counter() - inicio) * 1000)
        salida = solicitud.to_dict()
        salida["auditoria"] = [a.to_dict() for a in auditoria]
        return salida


__all__ = ["DirectorIAFuncional"]