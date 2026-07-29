# WEB-01 - APLICACION WEB DE HOST AI

Estado: Propuesto como linea de producto activa
Fecha: 2026-07-24
Alcance: primera aplicacion web de Host AI

## 1. Objetivo funcional

Construir la primera aplicacion web de Host AI para que el producto deje de depender de la consola como interfaz principal y pase a ofrecer una experiencia visual unificada para la operacion diaria de cocina.

La web debe mostrar de forma inmediata:

- que esta ocurriendo hoy
- que necesita atencion
- que tareas son prioritarias
- que problemas existen
- que decisiones puede tomar el usuario

## 2. Valor para el producto

Host AI debe sentirse como el sistema operativo de una cocina profesional, no como un ERP ni como un chatbot.

La web aporta valor si:

- unifica la operacion en un solo lugar
- hace mas visible el estado operativo global
- integra la IA dentro del flujo de trabajo
- reduce la friccion para usuarios finales
- reutiliza las capacidades existentes sin duplicar logica

## 3. Principios inamovibles

- No modificar el Core.
- No duplicar logica de negocio.
- No mover reglas al frontend.
- La IA interpreta y orquesta.
- El Core mantiene toda la autoridad funcional.
- La web reutiliza las capacidades existentes.
- La arquitectura debe servir al producto.
- El producto nunca debe detenerse para seguir construyendo infraestructura.

## 4. Fases de WEB-01

### Fase 1

Diseñar la experiencia general:

- estructura de navegacion
- layout principal
- identidad visual
- organizacion de modulos
- experiencia del usuario

### Fase 2

Construir el frontend base:

- aplicacion web
- layout principal
- sidebar
- topbar
- navegacion
- home
- chat integrado
- sistema de vistas
- contenedores para modulos

### Fase 3

Integrar progresivamente los modulos reales existentes:

- reutilizando Core
- sin reescribir logica
- sin duplicar funcionalidades

### Fase 4

Diseñar Platform Facade solo si la web lo requiere de forma real:

- desacoplar frontend del Core
- exponer contratos estables
- evitar infraestructura preventiva

### Fase 5

Una vez validada la aplicacion web:

- integrar proveedor de IA real
- mantener el desacoplamiento existente del Engine

## 5. Experiencia buscada

La primera pantalla debe comunicar estado y prioridad, no abrumar con botones.

La interfaz debe mostrar primero:

- estado operativo general
- alertas y prioridades
- acciones utiles
- acceso a chat
- contexto activo

La conversacion debe estar disponible de forma permanente pero integrada en la operacion, no como producto aislado.

## 6. Componentes que ya sirven de base

- [HOST_AI_CURRENT_STATE.md](../HOST_AI_CURRENT_STATE.md)
- [APP/app_shell_host_ai.py](../APP/app_shell_host_ai.py)
- [SERVICIOS/chat_host_ai_shell_service.py](../SERVICIOS/chat_host_ai_shell_service.py)
- [SERVICIOS/host_ai_deterministic_intent_router.py](../SERVICIOS/host_ai_deterministic_intent_router.py)
- [SERVICIOS/host_ai_home_read_service.py](../SERVICIOS/host_ai_home_read_service.py)
- [SERVICIOS/host_ai_session_context.py](../SERVICIOS/host_ai_session_context.py)
- [SERVICIOS/host_ai_tool_registry.py](../SERVICIOS/host_ai_tool_registry.py)
- [SERVICIOS/host_ai_tool_resolver.py](../SERVICIOS/host_ai_tool_resolver.py)
- [SERVICIOS/host_ai_tool_executor.py](../SERVICIOS/host_ai_tool_executor.py)
- [SERVICIOS/host_ai_engine/service.py](../SERVICIOS/host_ai_engine/service.py)
- [CORE/host_ai_core.py](../CORE/host_ai_core.py)

## 7. Criterio de prioridad

Si una propuesta solo mejora infraestructura y no aporta valor directo a Host AI como sistema operativo durante WEB-01, debe tratarse como evolucion futura salvo bloqueo real.

## 8. Resultado esperado

La primera version web debe convertir a Host AI en la interfaz principal del sistema sin romper la autoridad del Core ni la coherencia operativa existente.
