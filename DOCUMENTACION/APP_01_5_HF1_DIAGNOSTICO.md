# APP-01.5-HF1 Diagnostico

Estado: Implementado y validado
Fecha: 2026-07-23
Sprint: APP-01.5-HF1 Correccion del flujo chat y navegacion

## 1) Sintoma observado

- Consulta en chat: "que eventos hay?" devolvia datos, pero disparaba apertura de Eventos dentro del bucle de chat.
- Al salir de Eventos con "0", el control volvía al chat y los siguientes "0" se interpretaban como mensajes.
- Se observaba desalineacion visual: Sidebar en Eventos mientras Main Content seguia mostrando Home.
- En actividad reciente podia emerger un error tecnico relacionado con la clave `mensaje`.

## 2) Causa raiz del modulo anidado

Causa raiz confirmada:

- El chat devolvia `accion_navegacion` incluso para intenciones de consulta (`MOSTRAR_EVENTOS_PROXIMOS`, listas, busquedas).
- El shell ejecutaba `_aplicar_accion_desde_chat(...)` inmediatamente dentro de `_chat_panel(...)`.
- Esa ejecucion llamaba `_navegar(...)` desde el bucle del chat, anidando menus heredados interactivos dentro del chat.

## 3) Causa raiz de incoherencia de ruta activa

Causa raiz confirmada:

- `_navegar(...)` fijaba `_active_sidebar` al destino antes de abrir modulo y no restauraba ruta al volver.
- El shell siempre renderiza Main Content como Home, por lo que podia quedar Eventos marcado con Home visible.

## 4) Causa raiz del error 'mensaje'

Causa raiz probable y mitigacion implementada:

- La actividad reciente consumia elementos heterogeneos y accedia a campos como `m['mensaje']` sin fallback.
- Cualquier item malformado o con contrato alternativo (`texto` en lugar de `mensaje`) podia romper renderizado o dejar trazas tecnicas.
- Se introdujo normalizacion defensiva de actividad y render seguro con fallback.

## 5) Arquitectura corregida

Flujo nuevo:

Chat UI
-> Chat Application Service
-> Intent Router / Orquestador
-> NavigationRequest (opcional)
-> Chat devuelve control al Shell
-> Shell procesa NavigationRequest
-> Shell abre modulo

Medidas aplicadas:

1. Contrato `NavigationRequest` en servicio de chat.
2. Separacion estricta Consulta vs Navegacion explicita:
   - Consulta de eventos: responde y ofrece accion sugerida, no abre modulo.
   - "Abre eventos": emite `navigation_request` y devuelve control al shell.
3. Chat UI con acciones estructuradas:
   - menu local de acciones sugeridas: `1` ejecutar, `0` seguir conversando.
4. Eliminacion de apertura inmediata de modulo desde chat.
5. Shell como unico responsable de ejecutar navegacion.
6. Adaptador de ruta activa:
   - guarda ruta previa,
   - marca temporalmente destino durante ejecucion,
   - restaura ruta previa al devolver control.
7. Actividad reciente normalizada con `ActivityItem` y fallback seguro.

## 6) Contratos introducidos/corregidos

### NavigationRequest

Campos:

- `target_module`
- `target_view` (opcional)
- `filter_data` (opcional)
- `entity_id` (opcional)
- `source`
- `preserve_chat_session`
- `message` (opcional)

### ActivityItem

Campos:

- `activity_type`
- `message`
- `timestamp`
- `module` (opcional)
- `status`
- `navigation_target` (opcional)
- `metadata` (opcional)

## 7) Pluralizacion corregida

Se corrige singular/plural en bandeja, incluyendo:

- "Hay 1 tarea de produccion bloqueada."
- "Hay 2 tareas de produccion bloqueadas."

Y equivalentes en recetas, escandallos, incidencias y stock.

## 8) Pruebas automaticas (HF1)

Archivo nuevo:

- `TESTS/test_app_01_5_hf1_chat_navegacion.py`

Cubre, entre otros:

1. Consulta eventos no abre modulo automaticamente.
2. "Abre eventos" genera `NavigationRequest`.
3. Chat UI no llama directo a Eventos en consulta.
4. Shell procesa `NavigationRequest`.
5. Shell abre Eventos.
6. Al cerrar Eventos se recupera ruta coherente.
7. Home no aparece con Eventos marcado tras volver.
8. Enter vacio sale de chat.
9. `/volver` sale de chat.
10. `0` en menu de accion no se convierte en mensaje de chat.
11. Sesion chat se conserva tras navegar.
12. Actividad normaliza contratos heterogeneos.
13. Item malformado no rompe Home.
14. No aparece error tecnico `mensaje`.
15. Singular correcto.
16. Plural correcto.
17. Sin escrituras de negocio por chat.
18. Proveedor sigue SIMULADO.

## 9) Resultado de pruebas ejecutadas

- `TESTS/test_app_01_5_hf1_chat_navegacion.py`
- `TESTS/test_app_01_5_home_chat_deterministic.py`
- `TESTS/test_app_01_shell_host_ai.py`

Resultado:

- `36 passed in 7.21s`

Regresion complementaria:

- `TESTS/test_piloto_01_estabilizacion.py`
- `TESTS/test_host_ai_engine_smoke.py`

Resultado:

- `13 passed in 5.61s`

## 10) Evidencia de prueba manual obligatoria

Secuencia ejecutada en sandbox aislado (`HostAICore(tmp_path)`):

- STEP_01 True
- STEP_04_STAY_CHAT True
- STEP_05_NAV_EXPLICIT True
- STEP_06_OPENED_FROM_SHELL True
- STEP_09_SIDEBAR_MAIN_COHERENT True
- STEP_11_SESSION_KEPT True
- STEP_13_ACTIVITY_OK True
- STEP_14_NO_MENSAJE_KEY_ERROR True
- STEP_15_NO_WRITES True
- EVENT_QUERY_NO_AUTO_OPEN True

Interpretacion:

- "que eventos hay?" permanece en chat y no abre modulo automaticamente.
- "abre eventos" devuelve control al shell y el shell abre el modulo.
- No hay bucle anidado heredado dentro del chat.
- No se detectaron escrituras en datos de negocio durante la secuencia.

## 11) Riesgos pendientes

1. Modulos heredados siguen siendo interactivos bloqueantes; el adaptador actual evita anidamiento, pero no convierte esos modulos en no bloqueantes.
2. Si aparecen nuevos productores de actividad fuera del contrato, dependeran de la normalizacion defensiva (se recomienda converger contratos en todo el shell).
3. Filtros avanzados por modulo desde chat siguen como capacidad futura (actualmente se conserva navegacion segura sin prometer filtros inexistentes).

## 12) Garantias de alcance

- No se modifico el Core de negocio.
- No se alteraron reglas, calculos ni persistencia de dominio.
- No se conecto IA real ni proveedores externos.
- El proveedor activo sigue siendo `SIMULADO`.
- No se inicia APP-02.
