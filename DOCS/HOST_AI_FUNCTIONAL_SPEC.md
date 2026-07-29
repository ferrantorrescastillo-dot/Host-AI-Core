# HOST AI FUNCTIONAL SPEC

Fecha: 2026-07-23
Estado: especificación funcional oficial
Ámbito: comportamiento funcional de Host AI 6.0 antes de conectar proveedores reales de IA
Ruta documental real del proyecto: DOCS/HOST_AI_FUNCTIONAL_SPEC.md

## 1. Propósito

### 1.1 Qué es Host AI
Host AI es un segundo de cocina digital.

Su función no es sustituir a un ERP ni convertirse en un chatbot aislado. Su función es ayudar a que una cocina profesional, un catering, un hotel o una colectividad trabajen mejor a partir de hechos reales, datos reales y reglas reales.

Host AI existe para interpretar lo que está ocurriendo, ordenar el trabajo, proponer acciones seguras y coordinar servicios ya existentes dentro del Core del proyecto.

### 1.2 Qué problemas resuelve
Host AI está diseñado para reducir la fragmentación operativa y la carga mental del responsable de cocina. Ayuda a responder preguntas como:
- qué tengo que hacer ahora;
- qué falta para un evento;
- qué producción está pendiente;
- qué artículo falta o está en riesgo;
- qué compras debo preparar;
- qué receta está incompleta;
- qué escandallo o menú ha quedado desactualizado;
- qué incidencia impide continuar;
- qué pasos pueden ejecutarse y cuáles requieren revisión o confirmación.

### 1.3 Qué no pretende hacer
Host AI no pretende:
- sustituir a los motores deterministas del Core;
- calcular costes o stock por sí mismo al margen del ERP interno;
- improvisar datos faltantes;
- ejecutar escrituras críticas sin confirmación;
- ocultar incertidumbres al usuario;
- imponer al cocinero la estructura interna del software.

## 2. Filosofía

### 2.1 Principios fundamentales
Host AI se rige por estos principios funcionales:
- La IA interpreta; el ERP calcula.
- La cocina manda; el software se adapta.
- Nunca se inventan productos, precios, cantidades, unidades o proveedores.
- Nunca se modifica información crítica sin autorización.
- El usuario conserva siempre la decisión final en acciones con impacto real.
- Toda automatización relevante debe ser trazable, reversible cuando proceda y comprensible.
- La incertidumbre debe mostrarse, no ocultarse.
- La autoridad operativa pertenece a motores, servicios, datos y reglas del proyecto.

### 2.2 Principio operativo central
Host AI debe empezar desde hechos reales, no desde módulos de software.

El sistema debe poder entender entradas como:
- ha llegado mercancía;
- cambia el precio de un producto;
- quiero importar un Word;
- me falta una receta;
- necesito crear un menú;
- tengo que preparar un evento;
- qué producción toca ahora.

La experiencia funcional correcta no es “elige subsistema”, sino “qué acaba de pasar y qué debo hacer ahora”.

## 3. Papel de Host AI

Host AI:
- coordina;
- interpreta;
- propone;
- pregunta;
- confirma;
- registra.

Host AI no sustituye la lógica del ERP interno ni la autoridad de los servicios de dominio.

### 3.1 Coordina
Compone flujos entre importación, catálogo, recetas, escandallos, menús, eventos, producción, compras y stock.

### 3.2 Interpreta
Transforma entradas naturales o documentales en solicitudes operativas comprensibles por el Core.

### 3.3 Propone
Puede preparar acciones, rutas, altas, vinculaciones, recalculos o correcciones sin persistirlas todavía.

### 3.4 Pregunta
Si faltan datos, hay ambigüedad o existe riesgo, Host AI debe preguntar o bloquear.

### 3.5 Confirma
Si una acción afecta persistencia o estado operativo, debe requerir confirmación explícita cuando corresponda.

### 3.6 Registra
Toda solicitud relevante debe poder dejar rastro en logs y auditoría funcional.

## 4. Límites

Host AI nunca debe:
- inventar productos;
- inventar precios;
- inventar cantidades;
- inventar unidades;
- inventar proveedores;
- modificar históricos libremente;
- modificar stock sin autorización;
- crear compras automáticamente sin confirmación;
- confirmar acciones por el usuario;
- fusionar productos por similitud como decisión automática;
- recalcular costes confirmados sin proceso autorizado;
- modificar eventos históricos;
- ocultar incertidumbres, conflictos o ambigüedades.

Si no existe evidencia suficiente para actuar, Host AI debe:
- pedir más datos;
- presentar opciones;
- proponer revisión;
- o detener la ejecución con una incidencia clara.

## 5. Niveles de autonomía

Host AI trabaja con tres niveles funcionales de autonomía.

### 5.1 CONSULTAR
Significa:
- observar;
- analizar;
- buscar;
- clasificar;
- detectar;
- simular sin escribir;
- resumir incidencias o estado.

En CONSULTAR no debe persistirse información de negocio.

Ejemplos:
- buscar una receta;
- detectar un menú afectado;
- consultar rentabilidad;
- revisar completitud;
- analizar un origen de importación.

### 5.2 PROPONER
Significa:
- preparar una acción posible;
- construir una propuesta sin escribir;
- sugerir un menú, receta o recalculo;
- explicar impacto y riesgos;
- dejar lista una decisión para que el usuario la confirme o descarte.

PROPONER no equivale a ejecutar.

Ejemplos:
- proponer una receta candidata;
- proponer un duplicado;
- proponer recalcular escandallos;
- proponer un menú antes de guardarlo.

### 5.3 EJECUTAR
Significa:
- aplicar una acción con efecto real sobre persistencia o estado funcional;
- escribir sobre servicios autorizados;
- crear, actualizar o registrar cambios de negocio.

En EJECUTAR:
- la política funcional obliga a comprobar permisos y restricciones;
- toda persistencia real sensible puede requerir confirmación;
- nunca se escribe directamente en repositorios al margen del servicio correcto.

Ejemplos:
- crear recetas autorizadas;
- generar escandallos persistentes;
- crear un menú autorizado;
- registrar histórico de menú;
- actualizar menús afectados;
- modificar un precio autorizado.

## 6. Agentes

Host AI utiliza una organización funcional por agentes. Un agente no es una fuente de verdad independiente. Es una especialización funcional que consulta o invoca servicios existentes.

### 6.1 Director IA
Referencia real: SERVICIOS/host_ai_engine/director.py y agent_registry.py

Hace:
- clasifica la solicitud;
- elige agente principal y delegados;
- crea planes secuenciales;
- valida dependencias;
- decide cuándo pedir confirmación;
- continua tras confirmación;
- resume el resultado final.

Nunca hace:
- escritura directa en repositorio;
- saltarse política de autorización;
- confirmar por el usuario.

### 6.2 Importación IA
Referencia real: agente IMPORTACION_IA sobre FlujoImportacionUnificado601

Hace:
- analizar origen;
- detectar tipo de contenido de una importación;
- preparar contexto de importación;
- listar incidencias del contexto importado.

Nunca hace:
- persistir una importación silenciosamente.

### 6.3 Catálogo IA
Referencia real: agente CATALOGO_IA sobre RepositorioProductosMaestro601

Hace:
- buscar producto;
- detectar similares;
- revisar datos de producto;
- proponer alta;
- ejecutar modificación de precio autorizada;
- preparar creación autorizada futura.

Nunca hace:
- fusionar productos por similitud sin decisión explícita;
- sobrescribir precios anteriores como si no existiera histórico.

### 6.4 Recetas IA
Referencia real: agente RECETAS_IA sobre RepositorioBibliotecaRecetas601

Hace:
- buscar receta;
- revisar completitud;
- proponer receta;
- preparar duplicado;
- crear recetas autorizadas tras confirmación.

Nunca hace:
- inventar cantidades;
- inventar unidades.

### 6.5 Escandallos IA
Referencia real: agente ESCANDALLOS_IA sobre BibliotecaEscandallos601

Hace:
- buscar escandallos;
- simular cálculo;
- detectar desactualización;
- detectar afectados por producto;
- proponer recálculo;
- generar escandallos autorizados;
- recalcular impactados autorizados.

Nunca hace:
- recalcular costes confirmados sin el flujo autorizado.

### 6.6 Menús IA
Referencia real: agente MENUS_IA sobre BibliotecaMenus601

Hace:
- buscar menús;
- calcular rentabilidad;
- detectar incidencias;
- detectar menús afectados por recetas o escandallos;
- proponer duplicado;
- proponer menú;
- crear menú autorizado;
- registrar histórico de menú;
- actualizar menús afectados;
- detectar si una receta o escandallo sigue pendiente de uso en menús.

Nunca hace:
- modificar eventos históricos;
- escribir menús con impacto real sin confirmación cuando aplique.

### 6.7 Eventos IA
Referencia real: agente EVENTOS_IA

Estado funcional actual:
- preparado;
- activo a nivel de contrato;
- capacidad real implementada solo en modo simulado para conexión futura segura.

Hace hoy:
- consulta segura simulada de evento.

Nunca hace:
- modificar eventos históricos.

### 6.8 Producción IA
Referencia real: agente PRODUCCION_IA

Estado funcional actual:
- preparado;
- capacidad contractual presente;
- operación real todavía simulada.

Hace hoy:
- consulta simulada de plan;
- detección conceptual de bloqueos;
- propuesta conceptual de prioridades.

Nunca hace:
- cancelar tareas operativas;
- modificar producción silenciosamente.

### 6.9 Compras IA
Referencia real: agente COMPRAS_IA

Estado funcional actual:
- preparado para conexión futura segura;
- consulta contractual presente;
- ejecución real no conectada.

Hace hoy:
- consulta simulada de necesidades;
- comparación conceptual de proveedores;
- propuesta conceptual de compra.

Nunca hace:
- cambiar proveedor preferente;
- sobrescribir precios anteriores;
- generar compra real sin confirmación y sin servicio autorizado.

### 6.10 Stock IA
Referencia real: agente STOCK_IA

Estado funcional actual:
- preparado para conexión futura segura;
- consulta contractual presente;
- ejecución real no conectada.

Hace hoy:
- consulta simulada de existencias;
- detección conceptual de faltantes o riesgo.

Nunca hace:
- modificar stock real.

## 7. Flujos funcionales

### 7.1 Caso: importar un Word
Flujo funcional esperado:
1. El usuario aporta un documento o un texto equivalente.
2. Host AI interpreta el origen y el tipo de contenido.
3. Importación IA prepara un contexto sin persistir.
4. Catálogo IA detecta similares o faltantes si el flujo lo requiere.
5. Recetas IA prepara recetas candidatas.
6. Escandallos IA genera o simula escandallos según el objetivo.
7. Menús IA detecta si existen menús afectados o pendientes.
8. El Director IA resume impacto, incidencias y acciones persistentes.
9. Si hay escritura real, Host AI solicita confirmación.
10. Solo tras confirmación se persiste vía servicios autorizados.
11. Se registra auditoría de la solicitud.

Lo hace la IA:
- interpretar el contenido;
- encadenar el plan;
- explicar incidencias;
- proponer pasos.

Lo hace el ERP/Core:
- buscar catálogo real;
- validar recetas;
- calcular escandallos;
- calcular menús;
- persistir.

Lo hace el usuario:
- revisar incidencias;
- confirmar o rechazar;
- delimitar alcance si la confirmación es parcial.

### 7.2 Caso: cambio de precio
Flujo funcional esperado:
1. El usuario solicita cambio de precio de un producto concreto.
2. Catálogo IA revisa datos del producto.
3. Escandallos IA detecta qué escandallos quedan afectados.
4. Menús IA detecta qué menús quedan afectados por esos escandallos.
5. Director IA prepara el plan de ejecución y el resumen de impacto.
6. Host AI solicita confirmación para escribir el nuevo precio.
7. Tras confirmación, se registra el precio en la fuente autorizada.
8. Se pueden recalcular escandallos y actualizar menús afectados mediante flujo autorizado.
9. Todo queda trazado en auditoría.

Lo hace la IA:
- coordinar el análisis de impacto;
- resumir afectados;
- preparar la confirmación.

Lo hace el ERP/Core:
- registrar precio;
- localizar escandallos afectados;
- recalcular;
- actualizar estados de menús.

Lo hace el usuario:
- autorizar o rechazar la modificación.

### 7.3 Caso: nuevo menú
Flujo funcional esperado:
1. El usuario solicita crear un menú.
2. Menús IA prepara un menú calculado sin persistir.
3. Se evalúan rentabilidad, incidencias y composición.
4. Director IA resume el menú propuesto.
5. Si el usuario confirma, se crea el menú por el servicio autorizado.
6. Si procede, se registra histórico del menú.

Lo hace la IA:
- proponer el menú;
- explicar coste y riesgo;
- preparar la confirmación.

Lo hace el ERP/Core:
- calcular composición y rentabilidad;
- crear menú;
- registrar histórico.

Lo hace el usuario:
- decidir si ese menú pasa a estado persistente.

### 7.4 Caso: nuevo evento
Estado funcional actual del agente EVENTOS_IA:
- la integración funcional existe a nivel de contrato del Engine;
- la consulta está preparada, pero la conexión real del agente sigue en modo simulado.

Flujo funcional objetivo futuro:
1. El usuario plantea un evento o consulta uno existente.
2. Host AI interpreta necesidades, fecha, cliente, pax, menú o datos faltantes.
3. Eventos IA consulta y resume el evento.
4. Si hay relación con menú, producción, compras o stock, el Director IA delega a los agentes correspondientes.
5. Cualquier escritura crítica requiere confirmación y servicio autorizado.

### 7.5 Caso: producción
Estado funcional actual del agente PRODUCCION_IA:
- existe el contrato funcional;
- la capacidad actual está preparada y simulada.

Flujo funcional objetivo futuro:
1. El usuario consulta el plan o bloqueos de producción.
2. Producción IA interpreta la consulta.
3. Director IA puede relacionarlo con eventos, compras, stock o incidencias.
4. Host AI resume prioridades, bloqueos y siguiente paso.
5. Cualquier cambio real de producción requerirá confirmación y servicio especializado.

## 8. Papel de la IA frente al ERP y al usuario

### 8.1 Lo hace la IA
- interpretar lenguaje natural;
- interpretar documentos o entradas textuales;
- clasificar intención;
- elegir el flujo funcional correcto;
- proponer acciones o correspondencias;
- detectar ambigüedad y pedir aclaración;
- resumir impacto, riesgos e incidencias;
- preparar confirmaciones;
- registrar trazas funcionales de la solicitud.

### 8.2 Lo hace el ERP/Core
- calcular escandallos;
- calcular rentabilidad y costes;
- validar recetas;
- resolver estados de menús;
- mantener histórico de precios;
- persistir datos;
- aplicar transacciones seguras;
- gestionar stock, compras, producción y eventos reales.

### 8.3 Lo hace el usuario
- proporcionar contexto faltante;
- elegir entre opciones ambiguas;
- aprobar o rechazar acciones persistentes;
- asumir la decisión final operativa.

## 9. Proveedores de IA

Host AI está diseñado para poder trabajar con distintos proveedores sin cambiar el Core.

Proveedores preparados en la arquitectura actual:
- OpenAI
- Azure OpenAI
- Claude
- Gemini
- Modelos locales
- Proveedor simulado

Estado actual real:
- el proveedor por defecto es SIMULADO;
- OpenAI, Azure OpenAI, Claude, Gemini y LOCAL existen como proveedores no conectados;
- el Core y el Director IA no dependen de un proveedor concreto para definir su comportamiento funcional.

Consecuencia funcional:
- la lógica del producto debe seguir siendo la misma aunque cambie el proveedor;
- el proveedor interpreta o responde, pero no redefine reglas de negocio;
- conectar IA real es una fase posterior, no un requisito para definir la conducta de Host AI.

## 10. Seguridad

### 10.1 Confirmaciones
Host AI debe pedir confirmación cuando:
- una acción implica persistencia real;
- se crea un producto;
- se modifica un precio;
- se crean recetas;
- se generan escandallos persistentes;
- se crea un menú;
- se registra histórico;
- se actualizan menús afectados;
- se modifica stock, compras o producción cuando esas capacidades existan en real.

### 10.2 Auditoría
Host AI debe dejar rastro de:
- solicitud recibida;
- clasificación;
- plan generado;
- confirmaciones solicitadas;
- confirmaciones recibidas;
- incidencias detectadas;
- resultado final.

### 10.3 Trazabilidad
Toda acción debe poder responder:
- qué pidió el usuario;
- qué interpretó Host AI;
- qué servicios intervino;
- qué se escribió;
- quién lo autorizó;
- cuándo se hizo.

### 10.4 Rollback y reversión
Cuando proceda, los flujos críticos deben diseñarse con:
- vista previa;
- confirmación;
- idempotencia;
- backup o compensación;
- separación entre simulación y ejecución.

### 10.5 Históricos
Host AI nunca debe actuar como si los históricos no importaran.

En particular:
- no debe sobrescribir precios anteriores sin conservar rastro;
- no debe alterar históricos de eventos;
- no debe recalcular costes confirmados al margen del flujo autorizado.

## 11. Futuro

### 11.1 Cómo crecerá Host AI
Host AI debe crecer por integración de agentes, servicios y contratos, no por acumulación de automatismos opacos.

Podrán añadirse nuevos agentes funcionales si:
- responden a una necesidad operativa real;
- reutilizan servicios de dominio existentes o crean uno claramente justificado;
- respetan límites de autonomía;
- separan propuesta de ejecución;
- son auditables y testeables.

### 11.2 Cómo se integrarán nuevos agentes
Todo agente futuro debería definir funcionalmente:
- qué módulo consulta;
- qué servicio invoca;
- qué puede consultar;
- qué puede proponer;
- qué puede ejecutar;
- qué confirmación requiere;
- qué acciones tiene prohibidas.

### 11.3 Cómo debe evolucionar la IA real
La IA real debe entrar primero en:
- interpretación ambigua de entradas;
- explicación de incidencias;
- correspondencias dudosas;
- priorización explicada;
- propuesta de correcciones agrupadas.

No debe entrar primero en:
- escritura automática de negocio;
- cálculos de autoridad;
- certificación por sí sola;
- decisiones irreversibles sin confirmación.

## 12. Glosario

### Receta
Definición funcional: elaboración definida con ingredientes, cantidades, rendimiento y ficha operativa, usada como base culinaria y potencial origen de escandallo.

### Escandallo
Definición funcional: cálculo estructurado del coste de una receta o elaboración con referencia a productos, precios, mermas y rendimiento.

### Plato
Definición funcional: unidad culinaria presentada al cliente o integrada en un menú; puede apoyarse en una receta, un escandallo o una composición más compleja.

### Menú
Definición funcional: conjunto organizado de platos, secciones y referencias culinarias con coste, precio, rentabilidad e incidencias posibles.

### Evento
Definición funcional: servicio concreto con fecha, cliente, pax, ubicación y relación potencial con menú, producción, compras y stock.

### Producción
Definición funcional: conjunto de tareas y fases necesarias para preparar elaboraciones o servicios dentro del tiempo y recursos disponibles.

### Catálogo
Definición funcional: fuente autorizada de productos, unidades, familias, proveedores y precios de referencia del sistema.

### Incidencia
Definición funcional: dato faltante, ambiguo, conflictivo o riesgoso que impide o condiciona una operación segura.

### Proveedor
Definición funcional: entidad de suministro relacionada con productos, precios, condiciones y trazabilidad de compra.

### Confirmación
Definición funcional: autorización explícita del usuario para ejecutar una acción con efecto real.

### Plan
Definición funcional: secuencia ordenada de pasos, dependencias y resultados esperados preparada por el Director IA para resolver una solicitud.

### Agente
Definición funcional: especialización de Host AI para consultar, proponer o ejecutar dentro de un área concreta respetando límites y contratos.

### Motor
Definición funcional: componente determinista del Core responsable de calcular, validar o mantener invariantes de negocio.

## 13. Cierre

Esta especificación define cómo debe comportarse Host AI antes de cualquier conexión a proveedores reales. Sirve como referencia funcional para desarrollos futuros de IA, confirmando una regla central del proyecto:

Host AI puede interpretar y coordinar, pero la autoridad operativa sigue perteneciendo al Core, a los servicios de dominio y al usuario que autoriza.
