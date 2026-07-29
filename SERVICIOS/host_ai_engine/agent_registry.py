from __future__ import annotations

from SERVICIOS.host_ai_engine.models import (
    AUTONOMIA_CONSULTAR,
    AUTONOMIA_EJECUTAR,
    AUTONOMIA_PROPONER,
    AgentCapabilityContract,
    AgentContract,
)


def _cap(
    ident: str,
    nombre: str,
    descripcion: str,
    modulo: str,
    servicio: str,
    tipos: list[str],
    permitidas: list[str],
    conf: list[str],
    prohibidas: list[str],
    nivel: str,
    prioridad: int,
    implementada: bool,
) -> AgentCapabilityContract:
    return AgentCapabilityContract(
        identificador=ident,
        nombre=nombre,
        descripcion=descripcion,
        modulo_objetivo=modulo,
        servicio_objetivo=servicio,
        tipos_peticion_soportados=tipos,
        acciones_permitidas=permitidas,
        acciones_requieren_confirmacion=conf,
        acciones_prohibidas=prohibidas,
        nivel_minimo=nivel,
        prioridad=prioridad,
        implementada=implementada,
    )


def construir_registro_agentes() -> dict[str, AgentContract]:
    agentes: list[AgentContract] = [
        AgentContract(
            identificador="DIRECTOR_IA",
            nombre="Director IA",
            descripcion="Clasifica, planifica, delega, solicita confirmación y resume resultados.",
            modulos_que_puede_consultar=["host_ai_engine", "todos"],
            servicios_que_puede_invocar=["HostAIEngine", "DirectorIAFuncional"],
            tipos_peticion_soportados=["consulta_simple", "solicitud_compleja", "confirmacion", "cancelacion"],
            acciones_permitidas=["clasificar_solicitud", "crear_plan", "validar_dependencias", "solicitar_confirmacion", "continuar_tras_confirmacion", "cancelar_solicitud"],
            acciones_requieren_confirmacion=[],
            acciones_prohibidas=["escritura_directa_repositorio"],
            prioridad=100,
            activo=True,
            version_contrato="1.0",
            capacidades=[
                _cap("director.clasificar_solicitud", "clasificar_solicitud", "Determina agente principal y delegados.", "host_ai_engine", "DirectorIAFuncional", ["consulta_simple", "solicitud_compleja"], ["clasificar_solicitud"], [], ["escritura_directa_repositorio"], AUTONOMIA_CONSULTAR, 100, True),
                _cap("director.crear_plan", "crear_plan", "Compone pasos secuenciales y dependencias.", "host_ai_engine", "DirectorIAFuncional", ["solicitud_compleja"], ["crear_plan"], [], ["ejecucion_paralela"], AUTONOMIA_PROPONER, 100, True),
            ],
        ),
        AgentContract(
            identificador="IMPORTACION_IA",
            nombre="Importación IA",
            descripcion="Analiza orígenes, prepara importaciones y reúne incidencias.",
            modulos_que_puede_consultar=["centro_importacion_601"],
            servicios_que_puede_invocar=["FlujoImportacionUnificado601"],
            tipos_peticion_soportados=["analizar_origen", "detectar_tipo_contenido", "preparar_importacion", "listar_incidencias"],
            acciones_permitidas=["analizar_origen", "detectar_tipo_contenido", "preparar_importacion", "listar_incidencias"],
            acciones_requieren_confirmacion=[],
            acciones_prohibidas=["persistir_importacion_silenciosa"],
            prioridad=90,
            activo=True,
            version_contrato="1.0",
            capacidades=[
                _cap("importacion.analizar_origen", "analizar_origen", "Evalúa tipo de entrada y origen.", "centro_importacion_601", "FlujoImportacionUnificado601", ["analizar_origen"], ["analizar_origen"], [], ["persistir_importacion_silenciosa"], AUTONOMIA_CONSULTAR, 90, True),
                _cap("importacion.preparar_importacion", "preparar_importacion", "Construye contexto de importación sin persistir.", "centro_importacion_601", "FlujoImportacionUnificado601", ["preparar_importacion"], ["preparar_importacion"], [], ["persistir_importacion_silenciosa"], AUTONOMIA_CONSULTAR, 90, True),
                _cap("importacion.listar_incidencias", "listar_incidencias", "Resume incidencias del contexto importado.", "centro_importacion_601", "FlujoImportacionUnificado601", ["listar_incidencias"], ["listar_incidencias"], [], [], AUTONOMIA_CONSULTAR, 90, True),
            ],
        ),
        AgentContract(
            identificador="CATALOGO_IA",
            nombre="Catálogo IA",
            descripcion="Consulta catálogo maestro y detecta similitudes o faltantes.",
            modulos_que_puede_consultar=["catalogo_maestro_601"],
            servicios_que_puede_invocar=["RepositorioProductosMaestro601"],
            tipos_peticion_soportados=["buscar_producto", "detectar_similares", "revisar_datos_producto", "proponer_alta_producto", "crear_producto_autorizado"],
            acciones_permitidas=["buscar_producto", "detectar_similares", "revisar_datos_producto", "proponer_alta_producto", "crear_producto_autorizado"],
            acciones_requieren_confirmacion=["crear_producto_autorizado", "archivar_producto", "modificar_precio"],
            acciones_prohibidas=["fusionar_productos_por_similitud", "sobrescribir_precios_anteriores"],
            prioridad=85,
            activo=True,
            version_contrato="1.0",
            capacidades=[
                _cap("catalogo.buscar_producto", "buscar_producto", "Busca producto por nombre o código.", "catalogo_maestro_601", "RepositorioProductosMaestro601", ["buscar_producto"], ["buscar_producto"], [], [], AUTONOMIA_CONSULTAR, 85, True),
                _cap("catalogo.detectar_similares", "detectar_similares", "Busca candidatos similares para ingredientes importados.", "catalogo_maestro_601", "RepositorioProductosMaestro601", ["detectar_similares"], ["detectar_similares"], [], ["fusionar_productos_por_similitud"], AUTONOMIA_CONSULTAR, 85, True),
                _cap("catalogo.proponer_alta_producto", "proponer_alta_producto", "Prepara un alta sin persistir.", "catalogo_maestro_601", "RepositorioProductosMaestro601", ["proponer_alta_producto"], ["proponer_alta_producto"], [], [], AUTONOMIA_PROPONER, 85, True),
                _cap("catalogo.modificar_precio_autorizado", "modificar_precio_autorizado", "Actualiza precio vía servicio autorizado tras confirmación.", "catalogo_maestro_601", "RepositorioProductosMaestro601", ["modificar_precio_autorizado"], ["modificar_precio_autorizado"], ["modificar_precio_autorizado"], ["sobrescribir_precios_anteriores"], AUTONOMIA_EJECUTAR, 85, True),
                _cap("catalogo.crear_producto_autorizado", "crear_producto_autorizado", "Crea producto vía servicio autorizado solo tras confirmación.", "catalogo_maestro_601", "RepositorioProductosMaestro601", ["crear_producto_autorizado"], ["crear_producto_autorizado"], ["crear_producto_autorizado"], [], AUTONOMIA_EJECUTAR, 85, False),
            ],
        ),
        AgentContract(
            identificador="RECETAS_IA",
            nombre="Recetas IA",
            descripcion="Consulta recetas, revisa completitud y prepara propuestas o creación autorizada.",
            modulos_que_puede_consultar=["biblioteca_recetas_601"],
            servicios_que_puede_invocar=["RepositorioBibliotecaRecetas601"],
            tipos_peticion_soportados=["buscar_receta", "revisar_completitud", "proponer_receta", "preparar_duplicado", "crear_recetas_autorizadas"],
            acciones_permitidas=["buscar_receta", "revisar_completitud", "proponer_receta", "preparar_duplicado", "crear_recetas_autorizadas"],
            acciones_requieren_confirmacion=["crear_recetas_autorizadas", "modificar_receta"],
            acciones_prohibidas=["inventar_cantidades", "inventar_unidades"],
            prioridad=84,
            activo=True,
            version_contrato="1.0",
            capacidades=[
                _cap("recetas.buscar_receta", "buscar_receta", "Busca recetas existentes.", "biblioteca_recetas_601", "RepositorioBibliotecaRecetas601", ["buscar_receta"], ["buscar_receta"], [], [], AUTONOMIA_CONSULTAR, 84, True),
                _cap("recetas.revisar_completitud", "revisar_completitud", "Evalúa si una receta está completa.", "biblioteca_recetas_601", "RepositorioBibliotecaRecetas601", ["revisar_completitud"], ["revisar_completitud"], [], [], AUTONOMIA_CONSULTAR, 84, True),
                _cap("recetas.proponer_receta", "proponer_receta", "Prepara recetas candidatas sin guardar.", "biblioteca_recetas_601", "RepositorioBibliotecaRecetas601", ["proponer_receta"], ["proponer_receta"], [], [], AUTONOMIA_PROPONER, 84, True),
                _cap("recetas.crear_recetas_autorizadas", "crear_recetas_autorizadas", "Crea recetas en servicio autorizado tras confirmación.", "biblioteca_recetas_601", "RepositorioBibliotecaRecetas601", ["crear_recetas_autorizadas"], ["crear_recetas_autorizadas"], ["crear_recetas_autorizadas"], ["modificar_eventos_historicos"], AUTONOMIA_EJECUTAR, 84, True),
            ],
        ),
        AgentContract(
            identificador="ESCANDALLOS_IA",
            nombre="Escandallos IA",
            descripcion="Consulta escandallos, simula cálculos y detecta desactualizaciones.",
            modulos_que_puede_consultar=["biblioteca_escandallos_601"],
            servicios_que_puede_invocar=["BibliotecaEscandallos601"],
            tipos_peticion_soportados=["buscar_escandallo", "simular_calculo", "detectar_desactualizacion", "proponer_recalculo"],
            acciones_permitidas=["buscar_escandallo", "simular_calculo", "detectar_desactualizacion", "proponer_recalculo"],
            acciones_requieren_confirmacion=["confirmar_escandallo", "recalcular_escandallo_persistente"],
            acciones_prohibidas=["recalcular_costes_confirmados"],
            prioridad=83,
            activo=True,
            version_contrato="1.0",
            capacidades=[
                _cap("escandallos.buscar_escandallo", "buscar_escandallo", "Busca escandallos existentes.", "biblioteca_escandallos_601", "BibliotecaEscandallos601", ["buscar_escandallo"], ["buscar_escandallo"], [], [], AUTONOMIA_CONSULTAR, 83, True),
                _cap("escandallos.simular_calculo", "simular_calculo", "Calcula escandallos en modo no persistente.", "biblioteca_escandallos_601", "BibliotecaEscandallos601", ["simular_calculo"], ["simular_calculo"], [], [], AUTONOMIA_CONSULTAR, 83, True),
                _cap("escandallos.detectar_desactualizacion", "detectar_desactualizacion", "Detecta cambios pendientes.", "biblioteca_escandallos_601", "BibliotecaEscandallos601", ["detectar_desactualizacion"], ["detectar_desactualizacion"], [], [], AUTONOMIA_CONSULTAR, 83, True),
                _cap("escandallos.detectar_afectados_producto", "detectar_afectados_producto", "Localiza escandallos afectados por un producto.", "biblioteca_escandallos_601", "BibliotecaEscandallos601", ["detectar_afectados_producto"], ["detectar_afectados_producto"], [], [], AUTONOMIA_CONSULTAR, 83, True),
                _cap("escandallos.proponer_recalculo", "proponer_recalculo", "Prepara propuesta de recálculo.", "biblioteca_escandallos_601", "BibliotecaEscandallos601", ["proponer_recalculo"], ["proponer_recalculo"], [], ["recalcular_costes_confirmados"], AUTONOMIA_PROPONER, 83, True),
                _cap("escandallos.generar_escandallos_autorizados", "generar_escandallos_autorizados", "Genera escandallos persistentes desde recetas tras confirmación.", "biblioteca_escandallos_601", "BibliotecaEscandallos601", ["generar_escandallos_autorizados"], ["generar_escandallos_autorizados"], ["generar_escandallos_autorizados"], ["recalcular_costes_confirmados"], AUTONOMIA_EJECUTAR, 83, True),
                _cap("escandallos.recalcular_impactados_autorizado", "recalcular_impactados_autorizado", "Recalcula escandallos afectados tras confirmación.", "biblioteca_escandallos_601", "BibliotecaEscandallos601", ["recalcular_impactados_autorizado"], ["recalcular_impactados_autorizado"], ["recalcular_impactados_autorizado"], ["recalcular_costes_confirmados"], AUTONOMIA_EJECUTAR, 83, True),
            ],
        ),
        AgentContract(
            identificador="MENUS_IA",
            nombre="Menús IA",
            descripcion="Consulta menús, calcula rentabilidad y detecta incidencias.",
            modulos_que_puede_consultar=["biblioteca_menus_601"],
            servicios_que_puede_invocar=["BibliotecaMenus601"],
            tipos_peticion_soportados=["buscar_menu", "calcular_rentabilidad", "detectar_incidencias", "proponer_duplicado", "crear_menu_autorizado"],
            acciones_permitidas=["buscar_menu", "calcular_rentabilidad", "detectar_incidencias", "proponer_duplicado", "crear_menu_autorizado"],
            acciones_requieren_confirmacion=["crear_menu_autorizado", "modificar_menu", "asignar_menu_evento"],
            acciones_prohibidas=["modificar_eventos_historicos"],
            prioridad=82,
            activo=True,
            version_contrato="1.0",
            capacidades=[
                _cap("menus.buscar_menu", "buscar_menu", "Busca menús existentes.", "biblioteca_menus_601", "BibliotecaMenus601", ["buscar_menu"], ["buscar_menu"], [], [], AUTONOMIA_CONSULTAR, 82, True),
                _cap("menus.calcular_rentabilidad", "calcular_rentabilidad", "Consulta rentabilidad de menús.", "biblioteca_menus_601", "BibliotecaMenus601", ["calcular_rentabilidad"], ["calcular_rentabilidad"], [], [], AUTONOMIA_CONSULTAR, 82, True),
                _cap("menus.detectar_incidencias", "detectar_incidencias", "Consulta menús con incidencias.", "biblioteca_menus_601", "BibliotecaMenus601", ["detectar_incidencias"], ["detectar_incidencias"], [], [], AUTONOMIA_CONSULTAR, 82, True),
                _cap("menus.detectar_afectados_escandallos", "detectar_afectados_escandallos", "Localiza menús afectados por recetas o escandallos.", "biblioteca_menus_601", "BibliotecaMenus601", ["detectar_afectados_escandallos"], ["detectar_afectados_escandallos"], [], [], AUTONOMIA_CONSULTAR, 82, True),
                _cap("menus.proponer_duplicado", "proponer_duplicado", "Prepara duplicado sin persistir.", "biblioteca_menus_601", "BibliotecaMenus601", ["proponer_duplicado"], ["proponer_duplicado"], [], [], AUTONOMIA_PROPONER, 82, True),
                _cap("menus.proponer_menu", "proponer_menu", "Prepara un menú calculado sin persistir.", "biblioteca_menus_601", "BibliotecaMenus601", ["proponer_menu"], ["proponer_menu"], [], [], AUTONOMIA_PROPONER, 82, True),
                _cap("menus.crear_menu_autorizado", "crear_menu_autorizado", "Crea menú tras confirmación.", "biblioteca_menus_601", "BibliotecaMenus601", ["crear_menu_autorizado"], ["crear_menu_autorizado"], ["crear_menu_autorizado"], [], AUTONOMIA_EJECUTAR, 82, True),
                _cap("menus.registrar_historico_menu", "registrar_historico_menu", "Registra histórico de coste del menú tras confirmación.", "biblioteca_menus_601", "BibliotecaMenus601", ["registrar_historico_menu"], ["registrar_historico_menu"], ["registrar_historico_menu"], [], AUTONOMIA_EJECUTAR, 82, True),
                _cap("menus.actualizar_menus_afectados", "actualizar_menus_afectados", "Actualiza estado de menús afectados tras confirmación.", "biblioteca_menus_601", "BibliotecaMenus601", ["actualizar_menus_afectados"], ["actualizar_menus_afectados"], ["actualizar_menus_afectados"], [], AUTONOMIA_EJECUTAR, 82, True),
                _cap("menus.detectar_pendiente_menu", "detectar_pendiente_menu", "Indica si una receta o escandallo sigue sin uso en menús.", "biblioteca_menus_601", "BibliotecaMenus601", ["detectar_pendiente_menu"], ["detectar_pendiente_menu"], [], [], AUTONOMIA_CONSULTAR, 82, True),
            ],
        ),
        AgentContract(
            identificador="EVENTOS_IA",
            nombre="Eventos IA",
            descripcion="Consulta y analiza eventos sin modificar histórico.",
            modulos_que_puede_consultar=["eventos"],
            servicios_que_puede_invocar=["simulado"],
            tipos_peticion_soportados=["consultar_evento", "revisar_menu_evento", "detectar_datos_faltantes"],
            acciones_permitidas=["consultar_evento", "revisar_menu_evento", "detectar_datos_faltantes"],
            acciones_requieren_confirmacion=["asignar_menu_evento"],
            acciones_prohibidas=["modificar_eventos_historicos"],
            prioridad=80,
            activo=True,
            version_contrato="1.0",
            capacidades=[_cap("eventos.consultar_evento", "consultar_evento", "Capacidad simulada preparada para conexión futura segura.", "eventos", "simulado", ["consultar_evento"], ["consultar_evento"], [], ["modificar_eventos_historicos"], AUTONOMIA_CONSULTAR, 80, False)],
        ),
        AgentContract(
            identificador="PRODUCCION_IA",
            nombre="Producción IA",
            descripcion="Consulta planes y bloqueos sin alterar Producción.",
            modulos_que_puede_consultar=["produccion"],
            servicios_que_puede_invocar=["simulado"],
            tipos_peticion_soportados=["consultar_plan", "detectar_bloqueos", "proponer_prioridades"],
            acciones_permitidas=["consultar_plan", "detectar_bloqueos", "proponer_prioridades"],
            acciones_requieren_confirmacion=["modificar_produccion"],
            acciones_prohibidas=["cancelar_tareas_operativas", "modificar_produccion_silenciosa"],
            prioridad=79,
            activo=True,
            version_contrato="1.0",
            capacidades=[_cap("produccion.consultar_plan", "consultar_plan", "Capacidad simulada preparada para conexión futura segura.", "produccion", "simulado", ["consultar_plan"], ["consultar_plan"], [], ["cancelar_tareas_operativas"], AUTONOMIA_CONSULTAR, 79, False)],
        ),
        AgentContract(
            identificador="COMPRAS_IA",
            nombre="Compras IA",
            descripcion="Consulta necesidades y compara proveedores sin crear compras silenciosas.",
            modulos_que_puede_consultar=["compras"],
            servicios_que_puede_invocar=["simulado"],
            tipos_peticion_soportados=["consultar_necesidades", "comparar_proveedores", "proponer_compra"],
            acciones_permitidas=["consultar_necesidades", "comparar_proveedores", "proponer_compra"],
            acciones_requieren_confirmacion=["generar_compra", "cambiar_proveedor_preferente"],
            acciones_prohibidas=["cambiar_proveedor_preferente", "sobrescribir_precios_anteriores"],
            prioridad=78,
            activo=True,
            version_contrato="1.0",
            capacidades=[_cap("compras.consultar_necesidades", "consultar_necesidades", "Capacidad simulada preparada para conexión futura segura.", "compras", "simulado", ["consultar_necesidades"], ["consultar_necesidades"], [], ["cambiar_proveedor_preferente"], AUTONOMIA_CONSULTAR, 78, False)],
        ),
        AgentContract(
            identificador="STOCK_IA",
            nombre="Stock IA",
            descripcion="Consulta existencias y riesgos sin modificar stock real.",
            modulos_que_puede_consultar=["stock"],
            servicios_que_puede_invocar=["simulado"],
            tipos_peticion_soportados=["consultar_existencias", "detectar_faltantes", "detectar_riesgo_stock"],
            acciones_permitidas=["consultar_existencias", "detectar_faltantes", "detectar_riesgo_stock"],
            acciones_requieren_confirmacion=["modificar_stock", "operacion_masiva_stock"],
            acciones_prohibidas=["modificar_stock_real"],
            prioridad=77,
            activo=True,
            version_contrato="1.0",
            capacidades=[_cap("stock.consultar_existencias", "consultar_existencias", "Capacidad simulada preparada para conexión futura segura.", "stock", "simulado", ["consultar_existencias"], ["consultar_existencias"], [], ["modificar_stock_real"], AUTONOMIA_CONSULTAR, 77, False)],
        ),
    ]
    return {a.identificador: a for a in agentes}


class AgentRegistry:
    def __init__(self):
        self._agents = construir_registro_agentes()

    def listar(self, solo_activos: bool = True) -> list[AgentContract]:
        agentes = list(self._agents.values())
        if solo_activos:
            agentes = [a for a in agentes if a.activo]
        return sorted(agentes, key=lambda a: (-a.prioridad, a.identificador))

    def obtener(self, agent_id: str) -> AgentContract | None:
        return self._agents.get(str(agent_id or "").strip().upper())

    def obtener_capacidad(self, agent_id: str, operacion: str) -> AgentCapabilityContract | None:
        agent = self.obtener(agent_id)
        if not agent:
            return None
        op = str(operacion or "").strip()
        for capacidad in agent.capacidades:
            if capacidad.nombre == op or capacidad.identificador.endswith(op):
                return capacidad
        return None


__all__ = ["AgentRegistry", "construir_registro_agentes"]