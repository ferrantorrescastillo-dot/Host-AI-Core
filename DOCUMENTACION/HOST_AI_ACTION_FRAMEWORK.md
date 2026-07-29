# HOST AI Action Framework (PLATFORM-01)

Estado: Implementado
Fecha: 2026-07-24

## 1) Flujo completo

Chat
↓
Intento
↓
Tool
↓
Policy (futuro para WRITE)
↓
Core (solo cuando aplique y autorizado)
↓
Respuesta

En este sprint, la ejecución efectiva es READ/NAVIGATION/ANALYSIS y se apoya en servicios certificados de solo lectura y adaptadores de navegación.

## 2) Integración Chat

El chat ya no resuelve operaciones por servicios concretos.

Ahora:

1. detecta intención
2. resuelve `tool_id`
3. ejecuta herramienta por executor
4. devuelve salida normalizada
5. emite `navigation_request` cuando corresponde

## 3) Integración con contexto

Cada herramienta puede emitir `contexto_actualizado`.

Además, `navigation_request` incluye `context_update` para sincronizar:

- contexto_activo
- receta_activa
- escandallo_activo
- menu_activo
- evento_activo
- produccion_activa

## 4) Integración con Shell

El Shell:

- procesa `navigation_request` como única vía de apertura de módulos desde chat
- sincroniza contexto al navegar
- mantiene coherencia entre Sidebar/Main Content
- conserva sesión de chat en navegación (`preserve_chat_session=true`)

## 5) Observabilidad

Se registra auditoría de herramienta:

- tool_id
- estado
- duración
- errores
- advertencias
- contexto
- timestamp

Sin datos sensibles.

## 6) Límites de PLATFORM-01

- no ejecuta WRITE
- no conecta IA externa
- no modifica Core
- no altera reglas de negocio
- no persiste conversaciones/contexto

## 7) Evolución hacia PLATFORM-02

Prioridades recomendadas:

1. policy ejecutable para WRITE con confirmación humana
2. auditoría funcional ampliada por trazas de dominio
3. perfiles/permisos granulares por herramienta
4. catálogos de herramientas por entorno
