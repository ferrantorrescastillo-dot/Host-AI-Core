# HOST AI Session Context (APP-02)

Estado: Implementado
Fecha: 2026-07-23

## 1) Modelo

El modelo de sesion vive en memoria dentro del servicio de chat:

- `HostAISessionContext`
- `SessionActionItem`

Campos principales:

- usuario
- ultima_intencion
- ultimo_modulo
- ultima_navegacion
- ultima_busqueda
- ultima_lista_mostrada
- ultimo_elemento_seleccionado
- contexto_activo
- receta_activa
- escandallo_activo
- menu_activo
- evento_activo
- produccion_activa
- historial_corto_acciones
- actualizado_en

## 2) Ciclo de vida

1. Se crea al inicializar `ServicioChatHostAIShell`.
2. Se actualiza en cada intencion y en cada `NavigationRequest`.
3. Se limpia con `/clear` (o `chat.limpiar()`).
4. No se persiste en disco.

## 3) Actualizacion del contexto

Fuentes de actualizacion:

- Intenciones de consulta/listado:
  - actualizan `ultima_intencion` y `ultima_lista_mostrada`.
- Busqueda de recetas:
  - actualiza `ultima_busqueda`, `ultima_lista_mostrada`, `contexto_activo=RECETA`.
- Referencias (primera/segunda/ultima):
  - seleccionan elemento en `ultimo_elemento_seleccionado`.
- NavigationRequest:
  - actualiza `ultimo_modulo`, `ultima_navegacion` y contexto de dominio con `context_update`.
- Shell:
  - sincroniza contexto activo al entrar/salir de modulos heredados.

## 4) Limpieza

`/clear` limpia:

- conversacion
- busqueda
- lista mostrada
- seleccion
- contexto de dominio
- historial corto

El contexto vuelve a `HOME`.

## 5) Referencias soportadas

- abrir la primera
- abrir la segunda
- abrir la ultima
- el actual / esta receta / este evento / este escandallo / este menu (via router contextual)

Regla:

- solo se resuelven si existe contexto inequívoco;
- si no hay lista/contexto suficiente, se responde con advertencia y solicitud de precision.

## 6) Prioridades de resolucion

1. NavigationRequest explicito (abrir modulo)
2. Referencia contextual (primera/segunda/ultima)
3. Intenciones de consulta contextual (escandallo/menu/margen)
4. Intenciones generales
5. Fallback seguro

## 7) Ejemplos

1. `busca receta paella`
2. `abre la primera`
3. `muestra el escandallo`
4. `muestra el menu`

El usuario no necesita repetir "paella" mientras la sesion siga activa.

## 8) Limites

- no hay persistencia permanente;
- no hay contexto entre usuarios/sesiones;
- no se adivinan referencias ambiguas;
- no se reutiliza contexto tras limpieza;
- no se escriben datos de negocio.
