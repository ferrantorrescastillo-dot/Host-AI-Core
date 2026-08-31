# HOST_AI_CURRENT_STATE

Estado del documento: Oficial de traspaso operativo (handover) y cierre de congelacion Core 1.0
Fecha: 2026-07-29
Alcance: fotografía del estado actual real del repositorio abierto

## Estado oficial vigente

HOST AI CORE 1.0 - CERTIFICADO Y CONGELADO

Indicadores de cierre:

- TOTAL_CYCLES = 0
- CYCLE_601_PRESENT = False
- datos_reales_modificados = False
- Certificacion final de regresion representativa: 105 passed

## 0) Alcance y límites de este documento

Este documento describe el estado actual del proyecto tal como se observa en código y documentación vigente del repositorio.

No reescribe documentación histórica.
No sustituye la documentación de detalle por dominio.
No deduce información sin evidencia.

Cuando un dato no puede afirmarse con evidencia directa en esta revisión, se declara explícitamente como no verificado.

## 1) ¿Qué es Host AI?

Host AI es una plataforma operativa para cocina profesional orientada a funcionar como segundo de cocina digital: coordina operación diaria (producción, stock, compras, eventos, recetas/escandallos, recepción) y añade una capa conversacional/IA desacoplada de la lógica crítica.

Identidad confirmada por fuentes oficiales:

- [DEVKIT/KNOWLEDGE_CORE/01_IDENTIDAD.md](DEVKIT/KNOWLEDGE_CORE/01_IDENTIDAD.md)
- [DEVKIT/KNOWLEDGE_CORE/03_REGLAS.md](DEVKIT/KNOWLEDGE_CORE/03_REGLAS.md)
- [AGENTS.md](AGENTS.md)

Principio operativo vigente: la IA interpreta/orquesta, pero la autoridad de cálculo y reglas pertenece a motores/servicios/Core.

## 2) Estado actual del proyecto

### 2.1 Partes terminadas

- Núcleo operativo Python local con una única ruta oficial de arranque: [main.py](main.py) -> [SERVICIOS/lanzador_piloto_01.py](SERVICIOS/lanzador_piloto_01.py) -> modo piloto.
- Core con composición central en [CORE/host_ai_core.py](CORE/host_ai_core.py).
- Orquestación IA del núcleo en [CORE/orquestador.py](CORE/orquestador.py).
- Dominio amplio implementado (motores, servicios, pipelines, modelos, tests).
- Capa APP reciente de shell/chat/contexto/tool framework implementada:
  - [APP/app_shell_host_ai.py](APP/app_shell_host_ai.py)
  - [SERVICIOS/chat_host_ai_shell_service.py](SERVICIOS/chat_host_ai_shell_service.py)
  - [SERVICIOS/host_ai_deterministic_intent_router.py](SERVICIOS/host_ai_deterministic_intent_router.py)
  - [SERVICIOS/host_ai_home_read_service.py](SERVICIOS/host_ai_home_read_service.py)
  - [SERVICIOS/host_ai_session_context.py](SERVICIOS/host_ai_session_context.py)
  - [SERVICIOS/host_ai_tool_registry.py](SERVICIOS/host_ai_tool_registry.py)
  - [SERVICIOS/host_ai_tool_resolver.py](SERVICIOS/host_ai_tool_resolver.py)
  - [SERVICIOS/host_ai_tool_executor.py](SERVICIOS/host_ai_tool_executor.py)

### 2.2 Partes certificadas

Con certificación explícita localizada:

- Host AI Core 1.0 congelado: [HOST_AI_CORE_1_0_FROZEN.md](HOST_AI_CORE_1_0_FROZEN.md)
- Release notes de cierre Core 1.0: [HOST_AI_CORE_1_0_RELEASE_NOTES.md](HOST_AI_CORE_1_0_RELEASE_NOTES.md)

- PILOTO-1.3: [CERTIFICACION/CERTIFICACION_PILOTO-1.3.md](CERTIFICACION/CERTIFICACION_PILOTO-1.3.md)
- PILOTO-1.4: [CERTIFICACION/CERTIFICACION_PILOTO-1.4.md](CERTIFICACION/CERTIFICACION_PILOTO-1.4.md)

Con validación técnica documentada (sin certificado formal independiente localizado en este barrido):

- APP-01.5: [DOCUMENTACION/APP_01_5_AUDITORIA.md](DOCUMENTACION/APP_01_5_AUDITORIA.md)
- APP-01.5-HF1: [DOCUMENTACION/APP_01_5_HF1_DIAGNOSTICO.md](DOCUMENTACION/APP_01_5_HF1_DIAGNOSTICO.md)
- APP-02 Session Context: [DOCUMENTACION/HOST_AI_SESSION_CONTEXT.md](DOCUMENTACION/HOST_AI_SESSION_CONTEXT.md)
- PLATFORM-01 Tool Framework: [DOCUMENTACION/HOST_AI_TOOL_REGISTRY.md](DOCUMENTACION/HOST_AI_TOOL_REGISTRY.md), [DOCUMENTACION/HOST_AI_ACTION_FRAMEWORK.md](DOCUMENTACION/HOST_AI_ACTION_FRAMEWORK.md)

### 2.3 Partes en desarrollo o estabilización

- Estabilización global de suite completa: no cerrada.
  Evidencia de no aprobación global en una ejecución integral: [INFORME_RR1.6.2_AUTOMATICO.md](INFORME_RR1.6.2_AUTOMATICO.md).
- Convivencia de líneas históricas y activas en el mismo repositorio (alto volumen de tests/documentación legacy).

### 2.4 Partes que todavía no existen (evidencia directa)

- No existe [DEVKIT/KNOWLEDGE_CORE/02_ARQUITECTURA.md](DEVKIT/KNOWLEDGE_CORE/02_ARQUITECTURA.md).
- No existe [DEVKIT/KNOWLEDGE_CORE/06_MEMORIA_TECNICA.md](DEVKIT/KNOWLEDGE_CORE/06_MEMORIA_TECNICA.md).
- No existe [DEVKIT/KNOWLEDGE_CORE/07_MEMORIA_OPERATIVA.md](DEVKIT/KNOWLEDGE_CORE/07_MEMORIA_OPERATIVA.md).
- No existe CODEX.md único (sí existen [CODEX-01.md](CODEX-01.md) y [CODEX-02.md](CODEX-02.md)).
- PLATFORM-02 no está iniciada como implementación; solo aparece como evolución futura en documentación.

## 3) Arquitectura actual (organización vigente)

Organización técnica observable hoy:

- Arranque y lanzadores:
  - Ruta oficial única: [main.py](main.py) -> [SERVICIOS/lanzador_piloto_01.py](SERVICIOS/lanzador_piloto_01.py) -> [APP/consola_piloto_01.py](APP/consola_piloto_01.py)
  - Ruta secundaria de desarrollo: [SERVICIOS/host_ai_launcher.py](SERVICIOS/host_ai_launcher.py)
  - Ruta secundaria de compatibilidad legacy: [SERVICIOS/lanzador_host_ai_base_603.py](SERVICIOS/lanzador_host_ai_base_603.py)
- Núcleo/Core:
  - [CORE/host_ai_core.py](CORE/host_ai_core.py)
  - [CORE/orquestador.py](CORE/orquestador.py)
- Aplicación (piloto + shell):
  - [APP/consola_piloto_01.py](APP/consola_piloto_01.py)
  - [APP/app_shell_host_ai.py](APP/app_shell_host_ai.py)
- Capa conversacional/plataforma:
  - Chat service, router determinista, session context, tool registry/resolver/executor (SERVICIOS)
- Motor IA desacoplado por contratos:
  - [SERVICIOS/host_ai_engine/service.py](SERVICIOS/host_ai_engine/service.py)
  - [SERVICIOS/host_ai_engine/director.py](SERVICIOS/host_ai_engine/director.py)
  - [SERVICIOS/host_ai_engine/policy.py](SERVICIOS/host_ai_engine/policy.py)
  - [SERVICIOS/host_ai_engine/agent_registry.py](SERVICIOS/host_ai_engine/agent_registry.py)
  - [SERVICIOS/host_ai_engine/adapters.py](SERVICIOS/host_ai_engine/adapters.py)

## 4) Componentes existentes (reales) y estado

### 4.1 Núcleo y operación base

- HostAICore: ACTIVO
  - [CORE/host_ai_core.py](CORE/host_ai_core.py)
- OrquestadorHostAI: ACTIVO
  - [CORE/orquestador.py](CORE/orquestador.py)
- Registro de pipelines: ACTIVO
  - [CORE/registro_pipelines.py](CORE/registro_pipelines.py)
- Base de datos local (JSON): ACTIVO
  - [SERVICIOS/base_datos_local.py](SERVICIOS/base_datos_local.py)

### 4.2 Capa APP actual

- Modo piloto privado: ACTIVO
  - [APP/consola_piloto_01.py](APP/consola_piloto_01.py)
- App Shell Host AI: IMPLEMENTADO
  - [APP/app_shell_host_ai.py](APP/app_shell_host_ai.py)

### 4.3 Capa conversación/plataforma

- Chat Host AI Shell Service: IMPLEMENTADO
  - [SERVICIOS/chat_host_ai_shell_service.py](SERVICIOS/chat_host_ai_shell_service.py)
- Router determinista: IMPLEMENTADO
  - [SERVICIOS/host_ai_deterministic_intent_router.py](SERVICIOS/host_ai_deterministic_intent_router.py)
- Home Read Model: IMPLEMENTADO
  - [SERVICIOS/host_ai_home_read_service.py](SERVICIOS/host_ai_home_read_service.py)
- Session Context (memoria de sesión): IMPLEMENTADO
  - [SERVICIOS/host_ai_session_context.py](SERVICIOS/host_ai_session_context.py)
- NavigationRequest (contrato de navegación): IMPLEMENTADO
  - [SERVICIOS/chat_host_ai_shell_service.py](SERVICIOS/chat_host_ai_shell_service.py)
- Tool Registry: IMPLEMENTADO
  - [SERVICIOS/host_ai_tool_registry.py](SERVICIOS/host_ai_tool_registry.py)
- Tool Resolver: IMPLEMENTADO
  - [SERVICIOS/host_ai_tool_resolver.py](SERVICIOS/host_ai_tool_resolver.py)
- Tool Executor: IMPLEMENTADO
  - [SERVICIOS/host_ai_tool_executor.py](SERVICIOS/host_ai_tool_executor.py)

### 4.4 Engine / Director / Policy

- Host AI Engine: ACTIVO
  - [SERVICIOS/host_ai_engine/service.py](SERVICIOS/host_ai_engine/service.py)
- Director IA funcional: ACTIVO
  - [SERVICIOS/host_ai_engine/director.py](SERVICIOS/host_ai_engine/director.py)
- Policy de decisión: ACTIVA
  - [SERVICIOS/host_ai_engine/policy.py](SERVICIOS/host_ai_engine/policy.py)
- Registro de agentes + adapters: ACTIVO
  - [SERVICIOS/host_ai_engine/agent_registry.py](SERVICIOS/host_ai_engine/agent_registry.py)
  - [SERVICIOS/host_ai_engine/adapters.py](SERVICIOS/host_ai_engine/adapters.py)

### 4.5 Dominio amplio histórico/activo

Existen en el repositorio motores, servicios y pipelines de compras, stock, producción, eventos, costes, IA, importación y utilidades, pero no todos comparten el mismo nivel de estabilización actual.

Evidencia estructural cuantitativa:

- APP: 158 archivos Python
- SERVICIOS: 347 archivos Python
- CORE: 18 archivos Python
- TESTS: 398 archivos Python

## 5) Decisiones de arquitectura inamovibles

Decisiones observadas como cerradas en reglas + arquitectura reciente:

1. Core no debe depender de proveedores IA concretos en capa de interfaz.
2. La IA interpreta/orquesta; la lógica de negocio crítica reside en motores/servicios/Core.
3. El Chat no debe abrir módulos directamente; emite navegación y el Shell ejecuta.
4. NavigationRequest es el contrato de navegación entre Chat y Shell.
5. Tool Registry es la fuente oficial de herramientas registradas.
6. Tool Resolver decide tool_id; no ejecuta lógica.
7. Tool Executor valida y ejecuta; en PLATFORM-01 solo READ/NAVIGATION/ANALYSIS.
8. WRITE futuras se mantienen registradas pero deshabilitadas en PLATFORM-01.
9. Contexto conversacional es de sesión (en memoria), no persistente.
10. No conectar proveedores IA reales sin hardening y validación previa.
11. No modificar Core ni reglas de negocio sin evidencia, pruebas y actualización de memoria viva.
12. No escribir datos críticos fuera de rutas autorizadas con validación/confirmación.

Referencias principales:

- [AGENTS.md](AGENTS.md)
- [DEVKIT/KNOWLEDGE_CORE/03_REGLAS.md](DEVKIT/KNOWLEDGE_CORE/03_REGLAS.md)
- [DOCUMENTACION/HOST_AI_ACTION_FRAMEWORK.md](DOCUMENTACION/HOST_AI_ACTION_FRAMEWORK.md)
- [DOCUMENTACION/HOST_AI_TOOL_REGISTRY.md](DOCUMENTACION/HOST_AI_TOOL_REGISTRY.md)
- [DOCUMENTACION/APP_01_5_HF1_DIAGNOSTICO.md](DOCUMENTACION/APP_01_5_HF1_DIAGNOSTICO.md)

## 6) Estado funcional (real / simulado / inexistente)

### 6.1 Funcionalidad real disponible

- Operativa por consola en modo piloto (ruta oficial) y modo base de compatibilidad.
- Flujos de dominio implementados (compras, stock, producción, eventos, recetas/escandallos, etc.).
- PILOTO-1.3 y PILOTO-1.4 certificados.
- Home read-only con agregación de módulos para shell.
- Chat con intenciones deterministas, navegación segura y contexto de sesión.
- Tool Framework activo para lectura/navegación/análisis.

### 6.2 Funcionalidad simulada

- Proveedor IA efectivo del Engine en este contexto: SIMULADO (con proveedores reales no conectados).
  - [SERVICIOS/host_ai_engine/service.py](SERVICIOS/host_ai_engine/service.py)
- Parte del catálogo de capacidades de agentes existe como preparada/no implementada para ejecución real.

### 6.3 Funcionalidad no existente todavía

- Plataforma web/móvil/API de producción como cliente oficial completo: no implementada como capa consolidada única.
- Habilitación de WRITE en Tool Framework con policy/confirmación operativa end-to-end en plataforma: no activa en PLATFORM-01.
- DEVKIT Knowledge Core completo (faltan 02, 06 y 07).

## 7) Estado técnico

### 7.1 Estabilizado

- Núcleo de arranque local y composición de dependencias.
- Pilotos 1.3 y 1.4 con certificación explícita.
- Capa APP reciente con documentación técnica propia (APP-01.5/HF1/APP-02/PLATFORM-01).

### 7.2 Necesita evolución

- Consolidación de contratos únicos para mapeos navegación/contexto/tool (evitar duplicidades).
- Reducción de complejidad concentrada en chat/director.
- Cierre de brecha entre documentación histórica y estado efectivo vigente.
- Estrategia clara de estabilización de la suite global completa.

### 7.3 Deuda técnica visible

- Coexistencia de líneas históricas y actuales en un único árbol con alto volumen de pruebas/documentos.
- Persistencia JSON con límites transaccionales señalados en documentación.
- Desalineaciones puntuales entre reportes históricos de estado y capa reciente APP/PLATFORM.

## 8) Próximo gran objetivo recomendado

Con base en estado real y sin reabrir decisiones cerradas:

Iniciar WEB-01 como interfaz principal del producto, reutilizando el Core, el Engine, el Chat Service, el Tool Framework, el Session Context y el App Shell existente como base de transición.

La Platform Facade queda como evolución futura condicionada a una necesidad real del frontend, no como prerrequisito obligatorio previo.

Esto permite construir la primera aplicación web sin duplicar lógica de negocio ni mover autoridad funcional al frontend.

## 9) Roadmap inmediato recomendado

1. Definir experiencia general de WEB-01: navegación, layout principal, identidad visual y organización de módulos.
2. Construir el frontend base: home, sidebar, topbar, vistas y chat integrado.
3. Integrar progresivamente módulos reales existentes sin reescribir lógica.
4. Reservar Platform Facade solo si aparece una necesidad técnica real del frontend.
5. Mantener la IA como interfaz inteligente, no como centro del producto.

## 10) Riesgos que no deben romperse

1. Romper separación IA/orquestación vs lógica de negocio del Core.
2. Permitir bypass chat->core o UI->persistencia sin rutas autorizadas.
3. Introducir escrituras por tools no activadas o sin confirmación/policy.
4. Duplicar autoridad de contexto/navegación entre módulos.
5. Reabrir debates de arquitectura ya cerrados por falta de referencia única de estado.

## 11) Documentación relacionada (referencia oficial por tema)

### 11.1 Identidad y reglas

- Identidad: [DEVKIT/KNOWLEDGE_CORE/01_IDENTIDAD.md](DEVKIT/KNOWLEDGE_CORE/01_IDENTIDAD.md)
- Reglas: [DEVKIT/KNOWLEDGE_CORE/03_REGLAS.md](DEVKIT/KNOWLEDGE_CORE/03_REGLAS.md)
- Estado DEVKIT: [DEVKIT/KNOWLEDGE_CORE/09_ESTADO_ACTUAL.md](DEVKIT/KNOWLEDGE_CORE/09_ESTADO_ACTUAL.md)

### 11.2 Método de trabajo y gobierno

- Gobierno de agente: [AGENTS.md](AGENTS.md)
- Plan maestro operativo: [MASTER_PLAN.md](MASTER_PLAN.md)
- Manual operativo agente (parte 1 y 2): [CODEX-01.md](CODEX-01.md), [CODEX-02.md](CODEX-02.md)

### 11.3 Núcleo y dominios (ROC)

- Núcleo: [ROC/ROC-01A_NUCLEO.md](ROC/ROC-01A_NUCLEO.md), [ROC/ROC-01B_NUCLEO.md](ROC/ROC-01B_NUCLEO.md)
- Operación: [ROC/ROC-02A_OPERACION.md](ROC/ROC-02A_OPERACION.md)
- Negocio: [ROC/ROC-03A_NEGOCIO.md](ROC/ROC-03A_NEGOCIO.md)
- Cocina: [ROC/ROC-04A_COCINA.md](ROC/ROC-04A_COCINA.md)

### 11.4 Capa APP/Plataforma reciente

- App Shell: [DOCUMENTACION/HOST_AI_APP_SHELL.md](DOCUMENTACION/HOST_AI_APP_SHELL.md)
- Chat spec: [DOCUMENTACION/HOST_AI_CHAT_SPEC.md](DOCUMENTACION/HOST_AI_CHAT_SPEC.md)
- Home Read Model: [DOCUMENTACION/HOST_AI_HOME_READ_MODEL.md](DOCUMENTACION/HOST_AI_HOME_READ_MODEL.md)
- Deterministic intents: [DOCUMENTACION/HOST_AI_DETERMINISTIC_INTENTS.md](DOCUMENTACION/HOST_AI_DETERMINISTIC_INTENTS.md)
- Session context: [DOCUMENTACION/HOST_AI_SESSION_CONTEXT.md](DOCUMENTACION/HOST_AI_SESSION_CONTEXT.md)
- Context router: [DOCUMENTACION/HOST_AI_CONTEXT_ROUTER.md](DOCUMENTACION/HOST_AI_CONTEXT_ROUTER.md)
- Tool registry: [DOCUMENTACION/HOST_AI_TOOL_REGISTRY.md](DOCUMENTACION/HOST_AI_TOOL_REGISTRY.md)
- Action framework: [DOCUMENTACION/HOST_AI_ACTION_FRAMEWORK.md](DOCUMENTACION/HOST_AI_ACTION_FRAMEWORK.md)
- Revisión arquitectónica reciente: [DOCUMENTACION/HOST_AI_ARCHITECTURE_REVIEW.md](DOCUMENTACION/HOST_AI_ARCHITECTURE_REVIEW.md)

### 11.5 Certificaciones y comprobaciones

- Certificación piloto 1.3: [CERTIFICACION/CERTIFICACION_PILOTO-1.3.md](CERTIFICACION/CERTIFICACION_PILOTO-1.3.md)
- Certificación piloto 1.4: [CERTIFICACION/CERTIFICACION_PILOTO-1.4.md](CERTIFICACION/CERTIFICACION_PILOTO-1.4.md)
- Comprobaciones piloto: [COMPROBACION_PILOTO-1.3.txt](COMPROBACION_PILOTO-1.3.txt), [COMPROBACION_PILOTO-1.4.txt](COMPROBACION_PILOTO-1.4.txt)
- Suite RR1.6.3: [CERTIFICACION/suite_oficial_rr163.txt](CERTIFICACION/suite_oficial_rr163.txt)
- No aprobación global histórica (evidencia): [INFORME_RR1.6.2_AUTOMATICO.md](INFORME_RR1.6.2_AUTOMATICO.md)

## 12) Señales de contradicción detectadas y resolución de autoridad

Se detecta coexistencia de múltiples documentos de estado/roadmap con diferentes marcos temporales y líneas de producto (por ejemplo, DEVKIT histórico, DOCS legado, y DOCUMENTACION reciente APP/PLATFORM).

Regla aplicada en este handover:

1. Primero código real y componentes existentes.
2. Después certificaciones/evidencia ejecutable.
3. Después documentación reciente por sprint de capa APP/PLATFORM.
4. Finalmente documentación histórica como contexto, no como fuente única de estado actual.

## 13) Datos no verificados en esta revisión

- No se afirma aprobación de la suite completa total del repositorio en fecha de este handover.
- No se afirma despliegue web productivo activo.
- No se afirma conexión IA real en producción.

Si alguno de estos puntos cambia, debe actualizarse este documento con evidencia concreta (test/diagnóstico/certificación/documento de versión).