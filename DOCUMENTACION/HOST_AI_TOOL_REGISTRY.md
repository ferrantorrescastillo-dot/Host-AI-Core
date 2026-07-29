# HOST AI Tool Registry (PLATFORM-01)

Estado: Implementado
Fecha: 2026-07-24

## 1) Arquitectura

Flujo oficial:

Chat
↓
Intento
↓
Tool Resolver
↓
Tool Registry
↓
Tool Executor
↓
Servicio certificado
↓
Resultado normalizado

El Registry es la fuente oficial de herramientas.

## 2) Registro

Modelo `HostAITool` con campos:

- id
- nombre
- descripcion
- categoria
- tipo
- modulo
- servicio
- operacion
- solo_lectura
- requiere_confirmacion
- requiere_contexto
- contextos_compatibles
- permisos
- estado
- tags
- version

No se persiste en base de datos. Se registra por codigo.

## 3) Resolver

`HostAIToolResolver` transforma intención en `tool_id`.

Ejemplos:

- MOSTRAR_EVENTOS_PROXIMOS -> mostrar_eventos_proximos
- ABRIR_MODULO(sidebar=3) -> abrir_produccion

No ejecuta herramientas.

## 4) Executor

`HostAIToolExecutor`:

- valida existencia de herramienta
- valida estado (activa/deshabilitada)
- valida tipo permitido (READ/NAVIGATION/ANALYSIS en este sprint)
- valida contexto cuando aplica
- invoca servicio certificado (via Home Read Service o adaptador de navegacion)
- normaliza salida
- registra auditoría técnica estructurada

Nunca accede directamente al Core.

## 5) Categorías y tipos

Categorias en uso:

- CONSULTA
- NAVEGACION
- ANALISIS
- IMPORTACION
- ESCRITURA
- CONFIGURACION
- SISTEMA

Tipos en uso:

- READ
- WRITE
- NAVIGATION
- ANALYSIS
- IMPORT
- SYSTEM

## 6) Herramientas registradas

Activas (mínimo solicitado):

- buscar_recetas
- abrir_receta
- buscar_escandallos
- abrir_escandallo
- buscar_eventos
- abrir_evento
- mostrar_eventos
- abrir_produccion
- abrir_compras
- abrir_stock
- abrir_menus
- abrir_catalogo
- abrir_importaciones
- abrir_incidencias
- abrir_estadisticas
- abrir_configuracion
- mostrar_estado_general
- listar_recetas_pendientes
- listar_escandallos_desactualizados
- listar_incidencias
- mostrar_eventos_proximos

Futuras WRITE registradas y deshabilitadas:

- crear_receta
- duplicar_receta
- actualizar_precio
- recalcular_escandallo
- crear_evento
- aprobar_compra
- crear_menu
- importar_documento

## 7) Respuesta normalizada

Modelo `HostAIToolResult`:

- estado
- mensaje
- datos
- acciones
- contexto_actualizado
- navegacion
- errores
- advertencias
- duracion_ms
- tool_id

## 8) Seguridad

En PLATFORM-01:

- solo READ/NAVIGATION/ANALYSIS activas
- WRITE deshabilitadas
- sin conexión IA real
- sin escritura de datos de negocio
- sin modificación de Core

## 9) Confirmaciones y evolución

La ruta futura para WRITE queda preparada:

Policy
↓
Confirmacion
↓
Auditoria
↓
Tool Executor
↓
Core

No se activa todavía en PLATFORM-01.
