# HOST AI Context Router (APP-02)

Estado: Implementado
Fecha: 2026-07-23

## 1) Uso del contexto por el router

El router determinista identifica intenciones y referencias contextuales. El servicio de chat decide la ejecucion final con base en `HostAISessionContext`.

Intenciones contextuales nuevas:

- `ABRIR_REFERENCIA_RESULTADO`
- `MOSTRAR_ESCANDALLO_ACTUAL`
- `MOSTRAR_MENU_ACTUAL`
- `CONSULTAR_MARGEN_ACTUAL`

## 2) Resolucion de referencias

Patrones admitidos:

- abre la primera
- abre la segunda
- abre la ultima
- esta receta / este evento / este escandallo / este menu

Proceso:

1. Router detecta patron.
2. Chat consulta `ultima_lista_mostrada` y `contexto_activo`.
3. Si hay coincidencia inequívoca, construye `NavigationRequest`.
4. Shell ejecuta la navegacion.

## 3) Prevencion de ambiguedad

El sistema no adivina.

Casos de seguridad:

- sin lista activa -> advertencia
- referencia fuera de rango -> advertencia
- falta de contexto de receta/menu/escandallo -> advertencia

## 4) Integracion con NavigationRequest

`NavigationRequest` incluye:

- `target_module`
- `target_view`
- `filter_data`
- `entity_id`
- `source`
- `preserve_chat_session`
- `message`
- `context_update`

`context_update` permite sincronizar:

- contexto_activo
- receta_activa
- escandallo_activo
- menu_activo
- evento_activo
- produccion_activa

## 5) Limites funcionales APP-02

- no IA real
- no escritura
- no cambio de reglas de negocio
- no persistencia de conversaciones

## 6) Evolucion prevista APP-02.5

- ampliar referencias a entidades cruzadas (evento->menu->produccion)
- desambiguacion guiada multiopcion
- filtros de vista enriquecidos por modulo
