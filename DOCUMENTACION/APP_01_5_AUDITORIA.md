# APP-01.5 AUDITORIA

Estado: Completada
Fecha: 2026-07-23
Sprint: APP-01.5 Experiencia real y conexion con ERP

## 1) Revision de APP-01 (13 artefactos revisados)

Se revisaron los archivos base de APP-01 y sus dependencias directas de chat/shell:

1. APP/app_shell_host_ai.py
2. APP/consola_piloto_01.py
3. SERVICIOS/chat_host_ai_shell_service.py
4. SERVICIOS/contexto_activo_host_ai.py
5. TESTS/test_app_01_shell_host_ai.py
6. TESTS/test_piloto_01_estabilizacion.py
7. DOCUMENTACION/APP_01_AUDITORIA_INTERFAZ.md
8. DOCUMENTACION/HOST_AI_APP_SHELL.md
9. DOCUMENTACION/HOST_AI_UX_VISION.md
10. DOCUMENTACION/HOST_AI_CHAT_SPEC.md
11. CORE/orquestador.py
12. SERVICIOS/host_ai_engine/service.py
13. SERVICIOS/host_ai_engine/providers.py

## 2) Identificacion de componentes

- Shell conversacional de apoyo (acceso desde modo piloto): APP/app_shell_host_ai.py
- Navegacion sidebar y acciones rapidas: APP/app_shell_host_ai.py
- Host AI Home: APP/app_shell_host_ai.py
- Servicio de chat: SERVICIOS/chat_host_ai_shell_service.py
- Orquestador: CORE/orquestador.py
- Contratos de mensajes: SERVICIOS/chat_host_ai_shell_service.py
- Modelo de contexto: SERVICIOS/contexto_activo_host_ai.py
- Proveedor simulado: SERVICIOS/host_ai_engine/providers.py
- Pruebas APP-01: TESTS/test_app_01_shell_host_ai.py, TESTS/test_piloto_01_estabilizacion.py

## 3) Verificacion de acceso a persistencia

Resultado: No se detecta acceso directo de APP shell a archivos de base de datos.

- La UI usa servicios y orquestador.
- El chat usa host_ai_engine_consulta con proveedor SIMULADO.

## 4) Flujo real del chat actual

Flujo confirmado:

UI -> ServicioChatHostAIShell -> SolicitudHostAI(host_ai_engine_consulta)
-> Orquestador -> HostAIEngine -> Proveedor SIMULADO -> respuesta normalizada

## 5) Datos simulados detectados en Home APP-01

- Bandeja con mensajes simulados hardcodeados.
- Indicadores basicos en modo texto "disponible" sin lectura real.

## 6) Servicios certificados candidatos para lectura

Sin modificar Core:

- Eventos proximos: core.eventos.listar_eventos()
- Recetas pendientes: RepositorioBibliotecaRecetas601.pendientes()
- Busqueda receta: RepositorioBibliotecaRecetas601.buscar(...)
- Escandallos desactualizados: RepositorioBibliotecaEscandallos601.listar(...)
- Incidencias abiertas: RepositorioCentroImportacion601.incidencias_pendientes()
- Compras abiertas: core.compras.listar_necesidades(solo_pendientes=True)
- Alertas stock: core.stock.diagnosticar_stock()
- Produccion pendiente/bloqueada: core.produccion_real.listar_planes()
- Menus con incidencias/desactualizados: BibliotecaMenus601.menus_con_incidencias()

## 7) Riesgos antes de integrar datos reales

1. Dependencia de modulos no disponibles en ciertos entornos.
2. Fallos parciales que oculten informacion global.
3. Reglas de prioridad no deterministas o no documentadas.
4. Acoplar UI a formatos heterogeneos de servicios.
5. Introducir escrituras por error en rutas de consulta.

## 8) Decision APP-01.5

- Crear agregador de lectura dedicado para Home (solo lectura).
- Mantener flujo del chat por Orquestador/Engine con proveedor SIMULADO.
- Añadir router determinista transparente para intenciones limitadas.
- Mantener fallback de navegacion existente en Modo Piloto Privado.

## 9) Prueba funcional manual (15 pasos) y evidencia

Entorno de prueba:

- Sandbox aislado con `HostAICore(tmp_path)`.
- Datos de prueba sembrados con fixtures (`_seed_datos`).
- Sin uso de datos de produccion.

Secuencia ejecutada:

1. Abrir Host AI Home.
2. Verificar indicadores reales.
3. Abrir una tarjeta de recetas/evento pendiente.
4. Volver a Home.
5. Enviar: "Busca receta paella".
6. Revisar resultados.
7. Enviar referencia: "abre la primera".
8. Volver al chat (misma sesion).
9. Enviar: "Que escandallos estan desactualizados".
10. Abrir Escandallos.
11. Enviar: "Abre produccion".
12. Verificar navegacion.
13. Enviar una orden no soportada.
14. Verificar respuesta segura.
15. Confirmar que no se modifico ningun dato.

Salida observada (resumen):

- `STEP_01_HOME_OK datos_disponibles`
- `STEP_02_INDICADORES 8`
- `STEP_05_INTENT BUSCAR_RECETA`
- `STEP_06_RESULTADOS 1`
- `STEP_09_INTENT LISTAR_ESCANDALLOS_DESACTUALIZADOS`
- `STEP_11_INTENT ABRIR_MODULO`
- `STEP_11_NAV 3`
- `STEP_13_INTENT DESCONOCIDA`
- `STEP_14_MSG Todavia no puedo interpretar esa peticion...`
- `STEP_15_NO_WRITES True`
- `NAV_TRACE eventos,escandallos_recetas,produccion`

Conclusion de la prueba manual:

- La secuencia funcional objetivo se ejecuta en modo seguro.
- El chat mantiene comportamiento determinista.
- La navegacion responde a acciones reconocidas.
- No se detectan escrituras de negocio en la secuencia validada.
