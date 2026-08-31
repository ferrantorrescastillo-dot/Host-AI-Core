\# HOST AI — MAPA TÉCNICO V1 Y ROADMAP REAL



\## BASE DE REFERENCIA



Rama de desarrollo:



`feature/compras-web`



Commit de referencia:



`42ea9194 — Actualiza Host AI al estado 31 agosto 2026`



Este documento conecta el \*\*Documento Maestro de Producto V1\*\* con el estado técnico actual del proyecto.



\---



\# 1. LEYENDA



🟢 \*\*Avanzado\*\*

Existe una base importante de implementación y pruebas.



🟡 \*\*Parcial\*\*

Existe parte de la arquitectura, pero falta integración o completar la experiencia V1.



🔴 \*\*Pendiente importante\*\*

No existe todavía una implementación suficiente para el objetivo V1.



⚪ \*\*Futuro / no prioritario ahora\*\*



\---



\# 2. IMPORTACIÓN INTELIGENTE



\## Estado: 🟢 AVANZADO — PRIORIDAD ACTUAL



Existe ya una arquitectura importante alrededor de:



\* modelo estándar `HostAIImportPackage`;

\* analizador de datos de restaurante;

\* analizador híbrido;

\* intérprete mediante IA;

\* exportación para IA;

\* conversión ChatGPT;

\* adaptación del paquete;

\* resolución de ambigüedades;

\* importación inteligente;

\* completado de recetas;

\* confirmaciones;

\* clasificación;

\* canonicalización;

\* escritura controlada;

\* costes IA.



También existe una superficie considerable de tests de importación, IA, ambigüedad y completado.



\### Falta cerrar



\* un pipeline oficial único;

\* end-to-end completo;

\* deduplicación/caché verificadas a gran escala;

\* revisión masiva;

\* modo sin IA;

\* certificación sobre repositorios temporales;

\* métricas finales;

\* demostrar una importación completa realista.



\### Acción



\*\*FASE 1 ACTUAL.\*\*



No comenzar todavía las fases siguientes.



\---



\# 3. BIBLIOTECA: ARTÍCULOS, RECETAS, MENÚS Y ESCANDALLOS



\## Estado: 🟢 AVANZADO



Host AI ya tiene una base fuerte alrededor de:



\* artículos;

\* recetas;

\* menús;

\* elaboraciones;

\* escandallos;

\* costes;

\* rendimientos;

\* subelaboraciones;

\* clasificación;

\* reclassification;

\* edición segura;

\* documentación de recetas.



Existen además servicios nuevos para coste recursivo, rendimiento físico y artículo económico canónico.



\### Falta para V1



Normalizar definitivamente:



`ARTÍCULO`

↔

`RECETA`

↔

`ELABORACIÓN`

↔

`PLATO`

↔

`MENÚ`



y garantizar IDs estables y relaciones limpias.



\### Importancia



🔥🔥🔥🔥🔥



Es una base imprescindible para producción, TPV y rentabilidad.



\---



\# 4. HOST AI CONVERSACIONAL



\## Estado: 🟢 MUY AVANZADO



Ya existen:



\* agente general;

\* modelos del agente;

\* policy;

\* observabilidad;

\* contexto de ejecución autorizado;

\* conversation brain;

\* tool catalog;

\* tool registry;

\* tool schemas;

\* tool executor;

\* abstracción de proveedores IA;

\* OpenAI provider;

\* runtime bridge.



Existe además una suite amplia de seguridad, tool-loop, presupuestos, contexto, autonomía de lectura y conversación.



\### Decisión



\*\*NO crear otro chatbot.\*\*



Todo el futuro producto debe ir dotando al agente actual de capacidades autorizadas.



\---



\# 5. PERMISOS Y USUARIOS



\## Estado: 🟡 PARCIAL



Ya existen conceptos importantes de:



\* policy;

\* contexto autorizado;

\* seguridad del agente;

\* autenticación MCP;

\* tenant MCP.



Pero todavía debemos convertirlo en el sistema universal de permisos del producto.



\### Necesitamos



Modelo:



`Usuario`

\+

`Perfil inicial`

\+

`Permisos individuales`



Ejemplos:



`produccion.ver`



`produccion.ejecutar`



`recetas.editar`



`stock.ajustar`



`compras.aprobar`



`negocio.ver\_beneficio`



`equipo.gestionar\_permisos`



\### Regla



Los permisos deben aplicarse en:



\* frontend;

\* API;

\* servicios;

\* agente Host AI.



Ocultar un botón NO equivale a autorización.



\### Prioridad



🔥🔥🔥🔥🔥



Debe resolverse antes de crecer mucho en Mi Jornada y Negocio.



\---



\# 6. MULTI-RESTAURANTE / TENANT



\## Estado: 🟡 BASE EXISTENTE



Hay arquitectura de tenant en MCP y contexto de sesión, pero debemos garantizar que el dominio completo V1 tenga aislamiento por restaurante.



\### Necesitamos



Toda nueva entidad importante debe poder pertenecer a:



`tenant\_id`



y/o



`restaurant\_id`.



No hace falta crear ahora la interfaz multi-restaurante.



Sí debemos evitar construir nuevas tablas/modelos que después sean imposibles de separar.



\### Prioridad arquitectónica



🔥🔥🔥🔥🔥



\---



\# 7. SISTEMA UNIVERSAL DE TAREAS



\## Estado: 🟡 PARCIAL



Host AI ya tiene históricamente bandeja de trabajo y producción, pero la V1 necesita un contrato único.



\### Entidad futura



`Tarea`



Tipos:



\* producción;

\* recepción;

\* inventario;

\* compra;

\* limpieza;

\* mantenimiento;

\* incidencia;

\* evento;

\* checklist;

\* revisión;

\* tarea manual.



\### Esto alimentará



\# MI JORNADA



No debemos construir un sistema de tareas independiente dentro de cada módulo.



\### Prioridad



🔥🔥🔥🔥🔥



\---



\# 8. MI JORNADA PROFESIONAL



\## Estado: 🟡 BASE EXISTENTE / V1 PENDIENTE



Mi Jornada ya forma parte del concepto histórico de Host AI.



Pero la versión final que hemos definido todavía necesita evolución.



\### Debe mostrar



\* qué hacer;

\* prioridad;

\* hora;

\* cantidad;

\* destino;

\* duración;

\* estado;

\* maquinaria;

\* dependencias;

\* receta asociada;

\* versión de receta;

\* ingredientes escalados;

\* pasos;

\* incidencias.



\### Acción crítica



Cada tarea de producción:



`TAREA`

→

`RECETA\_VERSIONADA`



Debe poder abrir la receta al instante.



\### Botón



`NECESITO ALGO`



con:



\* producto;

\* ayuda;

\* incidencia;

\* maquinaria;

\* retraso;

\* información.



\### Prioridad



🔥🔥🔥🔥🔥



Pero después del motor profesional de producción.



\---



\# 9. PRODUCCIÓN INTELIGENTE



\## Estado: 🟡 MEDIO



Ya existe:



`produccion\_inteligente\_workflow.py`



y pruebas:



\* workflow;

\* integración executor;

\* end-to-end.



Esto es una base importante.



Pero todavía debemos construir la visión profesional completa.



\### Motor final



Entradas:



\* reservas;

\* eventos;

\* previsión;

\* menús;

\* recetas;

\* stock;

\* elaboraciones existentes;

\* personal;

\* horarios;

\* capacidades;

\* habilidades;

\* maquinaria;

\* capacidad maquinaria;

\* tiempos activos;

\* tiempos pasivos;

\* dependencias;

\* conservación;

\* regeneración.



Salida:



`PLAN DE PRODUCCIÓN`



→ tareas



→ Mi Jornada.



\### Falta especialmente



\* workers;

\* horarios;

\* skills;

\* maquinaria;

\* capacidades;

\* planificación temporal;

\* trabajo paralelo;

\* planificación inversa;

\* dependencias;

\* replanificación.



\### Prioridad



🔥🔥🔥🔥🔥



Será uno de los principales diferenciadores comerciales.



\---



\# 10. STOCK



\## Estado: 🟢/🟡 AVANZADO



Ya existe una base importante:



\* lotes;

\* movimientos;

\* ajustes;

\* ubicaciones;

\* escritura segura de lotes;

\* APIs;

\* frontend;

\* pruebas de gestión segura.



\### Falta cerrar V1



La cadena:



`COMPRA`

→

`RECEPCIÓN`

→

`STOCK`

→

`PRODUCCIÓN`

→

`CONSUMO`

→

`VENTA`

→

`MERMA`



debe quedar completamente trazable.



\### Prioridad



🔥🔥🔥🔥🔥



\---



\# 11. MERMAS



\## Estado: 🟡 BASE DE STOCK DISPONIBLE



Tenemos los movimientos necesarios para construirlo sin crear un sistema enorme.



\### V1 sencilla



Registrar:



\* producto;

\* cantidad;

\* unidad;

\* coste;

\* motivo;

\* usuario;

\* fecha;

\* tarea/evento relacionado;

\* foto opcional.



\### Motivos



\* caducidad;

\* sobreproducción;

\* error;

\* conservación;

\* caída;

\* devolución;

\* proveedor;

\* otro.



\### Prioridad



🔥🔥🔥



Mucho valor con complejidad relativamente baja.



\---



\# 12. COMPRAS



\## Estado: 🟢 AVANZADO



Ya existen estructuras de:



\* pedidos;

\* propuestas;

\* proveedores;

\* registros;

\* recepciones;

\* incidencias;

\* producto-proveedor;

\* precios;

\* histórico;

\* comparadores/referencias de precio.



La actualización de agosto incluye servicios de recepción y referencias de precio, además de frontend de compras.



\### Falta V1



Unificar claramente:



`NECESIDAD`

→

`PROPUESTA`

→

`APROBACIÓN`

→

`PEDIDO`

→

`RECEPCIÓN`

→

`STOCK`.



\### Añadir necesidad



Permiso bastante abierto.



\### Aprobar/enviar



Permiso restringido.



\### Prioridad



🔥🔥🔥🔥



\---



\# 13. PROVEEDORES



\## Estado: 🟢/🟡 AVANZADO



Ya existe bastante dominio.



\### V1 debe responder fácilmente



\* proveedor actual;

\* precio actual;

\* histórico;

\* mejor referencia;

\* diferencia;

\* incidencias;

\* cumplimiento.



\### Alerta futura



“Este proveedor ha aumentado el precio un 11%.”



\### Prioridad



🔥🔥🔥



\---



\# 14. RECEPCIÓN



\## Estado: 🟢/🟡



Ya existe `compras\_recepciones\_service` y frontend/test de recepción.



\### Falta completar experiencia



\* cantidades;

\* diferencias;

\* foto;

\* albarán;

\* lote;

\* ubicación;

\* incidencia;

\* aceptación/rechazo;

\* impacto automático en stock.



\### Prioridad



🔥🔥🔥



\---



\# 15. RESERVAS Y EVENTOS



\## Estado: 🟢 AVANZADO



Agosto añadió:



\* endpoint reservas;

\* modelos;

\* read/write services;

\* páginas web;

\* panel de escritura;

\* tests;

\* acciones mediante chat.



\### Decisión



No ampliar demasiado ahora.



Su función principal V1 será alimentar:



\* previsión;

\* producción;

\* compras;

\* rentabilidad de eventos.



\### Prioridad



🔥🔥



\---



\# 16. MODELO ECONÓMICO OPERATIVO



\## Estado: 🟡 PARCIAL



Ya tenemos piezas importantes:



\* coste de escandallos;

\* artículo económico canónico;

\* rendimiento;

\* coste de subelaboraciones;

\* rentabilidad de escandallos;

\* precios de proveedores.



Pero todavía falta la pieza horizontal:



\# LIBRO ECONÓMICO OPERATIVO



\### Entradas



\* ventas TPV;

\* eventos;

\* otros ingresos.



\### Salidas



\* compras;

\* personal;

\* alquiler;

\* suministros;

\* comisiones;

\* mantenimiento;

\* otros gastos.



\### NO incluir inicialmente



\* contabilidad fiscal;

\* nóminas;

\* asientos;

\* declaraciones tributarias.



\### Prioridad



🔥🔥🔥🔥🔥



Será Fase 2.



\---



\# 17. TPV



\## Estado: 🔴 PENDIENTE



No debemos crear un TPV propio.



Necesitamos un modelo estándar:



`VentaHostAI`



y conectores.



\### Primeros conectores



1\. CSV/Excel genérico.

2\. Primer TPV real elegido para piloto.

3\. Otros TPV posteriormente.



\### Host AI debe recibir



\* producto;

\* cantidad;

\* precio;

\* descuento;

\* hora;

\* canal;

\* devolución;

\* anulación;

\* forma de pago.



\### Prioridad



🔥🔥🔥🔥🔥



Será Fase 3.



\---



\# 18. RENTABILIDAD



\## Estado: 🟡 BASE ECONÓMICA EXISTENTE



Tenemos cálculo de escandallos, pero falta la visión completa.



\### Debemos poder obtener



rentabilidad:



\* plato;

\* receta;

\* menú;

\* evento;

\* día;

\* turno;

\* canal;

\* restaurante.



\### Fórmula



Ventas reales

−

costes actualizados

−

costes variables imputables



=



resultado/margen.



\### Prioridad



🔥🔥🔥🔥🔥



\---



\# 19. INGENIERÍA DE MENÚ



\## Estado: 🔴 PENDIENTE COMO PRODUCTO



Cuando existan:



TPV

\+

escandallos



es relativamente sencilla.



Clasificación:



\* estrella;

\* caballo de batalla;

\* puzzle;

\* débil.



\### Prioridad



🔥🔥🔥



Mucho valor y complejidad moderada.



\---



\# 20. CENTRO DE ALERTAS



\## Estado: 🔴 PENDIENTE COMO MOTOR UNIVERSAL



No crear alertas independientes en cada módulo.



Necesitamos:



`AlertEngine`



recibiendo señales de:



\* stock;

\* precios;

\* producción;

\* ventas;

\* margen;

\* mermas;

\* eventos;

\* personal;

\* maquinaria.



\### Alerta



Debe contener:



\* qué ocurre;

\* gravedad;

\* evidencia;

\* impacto;

\* responsable;

\* recomendación;

\* estado.



\### Prioridad



🔥🔥🔥🔥🔥



\---



\# 21. OBJETIVOS DEL RESTAURANTE



\## Estado: 🔴 PENDIENTE



Necesitamos configuración sencilla:



\* food cost objetivo;

\* margen mínimo;

\* merma máxima;

\* días de cobertura;

\* coste laboral objetivo;

\* presupuestos;

\* mínimos de stock.



Las alertas compararán realidad contra estos objetivos.



\### Prioridad



🔥🔥🔥



\---



\# 22. PANTALLA “HOY”



\## Estado: 🟡 BASE EXISTENTE



Ya existen:



\* Dashboard;

\* Executive Dashboard;

\* `host\_ai\_home\_read\_service`;

\* síntesis operacional.



\### V1 final



Debe convertirse en:



\# HOY NECESITAS SABER



y mostrar:



\* negocio;

\* producción;

\* compras;

\* stock;

\* reservas;

\* alertas;

\* oportunidades.



\### Prioridad



🔥🔥🔥🔥



\---



\# 23. “QUÉ HA CAMBIADO”



\## Estado: 🔴/🟡



Tenemos trazas y observabilidad en diferentes áreas, pero no todavía una experiencia única.



Necesitamos poder preguntar:



“¿Qué cambió desde ayer?”



Y sintetizar:



\* ventas;

\* precios;

\* reservas;

\* eventos;

\* incidencias;

\* stock;

\* producción;

\* margen.



\### Prioridad



🔥🔥🔥



\---



\# 24. ENTREGA DE TURNO



\## Estado: 🔴 PENDIENTE COMO FUNCIÓN



Se puede construir sobre:



\* tareas;

\* producción;

\* incidencias;

\* compras;

\* stock.



\### Resultado



Resumen automático:



`TURNO A`

→

`TURNO B`



\### Prioridad



🔥🔥



Gran valor con coste relativamente bajo cuando exista el sistema universal de tareas.



\---



\# 25. INCIDENCIAS



\## Estado: 🟡 PARCIAL



Existen incidencias en áreas como compras.



Debe convertirse en concepto reutilizable.



Tipos:



\* producto;

\* proveedor;

\* maquinaria;

\* producción;

\* stock;

\* tarea;

\* cliente;

\* otro.



\### Prioridad



🔥🔥🔥



\---



\# 26. TRAZABILIDAD UNIVERSAL



\## Estado: 🟡 BASE IMPORTANTE



Host AI ya tiene escritura segura, auditoría en varias áreas y observabilidad.



Pero la V1 debe establecer una regla universal.



Toda acción sensible:



`QUIÉN`

\+

`CUÁNDO`

\+

`QUÉ`

\+

`ANTES`

\+

`DESPUÉS`

\+

`MOTIVO`

\+

`ORIGEN`.



\### Prioridad



🔥🔥🔥🔥🔥



\---



\# 27. PROCEDENCIA UNIVERSAL



\## Estado: 🟡 MUY AVANZADO EN IMPORTACIÓN



La importación está obligando a diferenciar:



\* real;

\* catálogo;

\* regla;

\* IA;

\* usuario confirmado.



Debemos llevar el mismo principio al resto de Host AI.



\### Estados conceptuales



`REAL`



`CALCULADO`



`IA\_PROPUESTA`



`CONFIRMADO`



\### Prioridad



🔥🔥🔥🔥



\---



\# 28. FOTOS Y DOCUMENTOS



\## Estado: 🔴 GENERALIZACIÓN PENDIENTE



Debe existir una forma estándar de adjuntar:



\* albarán;

\* factura;

\* foto;

\* evidencia;

\* documento.



No necesitamos un gestor documental complejo.



Solo un contrato reutilizable.



\### Prioridad



🔥🔥



\---



\# 29. MÓVIL / TABLET



\## Estado: 🟡 WEB EXISTENTE / EXPERIENCIA POR VALIDAR



Host AI ya tiene frontend React considerable.



Pero Mi Jornada, recepción, stock y tareas deben probarse específicamente en:



\* teléfono;

\* tablet;

\* cocina.



\### Regla V1



Las operaciones de trabajador se diseñan \*\*mobile-first\*\*.



\### Prioridad



🔥🔥🔥🔥



\---



\# 30. BACKUP / ROLLBACK / ARRANQUE LIMPIO



\## Estado: 🟡



Hay tradición de escritura segura y se ha creado una política de inicialización de repositorios.



\### Debemos certificar



`git clone`

→

instalación

→

repositorios vacíos

→

Host AI arranca.



No puede depender de los `DATOS/` privados del ordenador de desarrollo.



\### Prioridad



🔥🔥🔥🔥🔥



\---



\# 31. MCP



\## Estado: 🟢 AVANZADO



Existen:



\* adapter;

\* auth;

\* tenants;

\* remote server;

\* tests de seguridad.



\### Decisión



No invertir mucho más ahora.



No es cuello de botella de la V1.



\### Prioridad



⚪



\---



\# 32. MAPA RESUMIDO



| Área                   | Estado | Próxima acción            |

| ---------------------- | ------ | ------------------------- |

| Importación IA         | 🟢     | \*\*Cerrar Fase 1\*\*         |

| Biblioteca/recetas     | 🟢     | Consolidar contrato       |

| Agente Host            | 🟢     | Reutilizar                |

| Permisos               | 🟡     | Crear modelo universal    |

| Multi-restaurante      | 🟡     | Asegurar IDs/aislamiento  |

| Tareas                 | 🟡     | Unificar contrato         |

| Mi Jornada             | 🟡     | Profesionalizar después   |

| Producción             | 🟡     | Motor profesional         |

| Stock                  | 🟢/🟡  | Cerrar trazabilidad       |

| Compras                | 🟢     | Integrar necesidades      |

| Recepción              | 🟢/🟡  | Mejorar flujo             |

| Reservas/Eventos       | 🟢     | No expandir ahora         |

| Economía               | 🟡     | Crear libro operativo     |

| TPV                    | 🔴     | Integración               |

| Rentabilidad           | 🟡     | Completar con ventas      |

| Ingeniería menú        | 🔴     | Después TPV               |

| Alertas                | 🔴     | Motor universal           |

| Objetivos              | 🔴     | Configuración             |

| Hoy                    | 🟡     | Evolucionar               |

| Qué ha cambiado        | 🔴/🟡  | Construir sobre auditoría |

| Entrega turno          | 🔴     | Después tareas            |

| Incidencias            | 🟡     | Universalizar             |

| Fotos/docs             | 🔴     | Contrato sencillo         |

| Mobile                 | 🟡     | Validación real           |

| Backup/arranque limpio | 🟡     | Certificar                |

| MCP                    | 🟢     | Congelar                  |



\---



\# 33. CUATRO CIMIENTOS QUE NO DEBEMOS OLVIDAR



Antes de desarrollar masivamente las fases económicas y de producción, debemos asegurarnos de que existen cuatro contratos transversales.



\## CIMIENTO A — IDENTIDAD



Toda entidad importante debe tener ID estable.



Y pertenecer al restaurante correspondiente.



\---



\## CIMIENTO B — PERMISOS



Cada acción debe saber:



`usuario`

\+

`permiso`

\+

`restaurante`.



\---



\## CIMIENTO C — TAREAS



Todo trabajo operativo debe poder representarse mediante el sistema común de tareas.



\---



\## CIMIENTO D — AUDITORÍA / PROCEDENCIA



Toda acción importante debe saber:



qué ocurrió y de dónde salió el dato.



Estos cuatro cimientos evitan rehacer Host AI más adelante.



\---



\# 34. ROADMAP REAL DESDE HOY



\## FASE 1 — IMPORTACIÓN INTELIGENTE



\### Objetivo



Cerrar completamente:



Excel

→

análisis

→

IA

→

revisión

→

confirmación

→

escritura segura.



\### Resultado



Host AI puede absorber de forma eficiente los datos existentes de un restaurante.



\### Estado



\*\*CERTIFICADA TÉCNICAMENTE. VALIDACIÓN MANUAL/CULINARIA PENDIENTE.\*\*



\---



\# FASE 1.5 — CIMIENTOS V1



Antes de crecer:



\* tenant/restaurante;

\* usuarios;

\* permisos;

\* tarea universal;

\* auditoría;

\* procedencia;

\* contrato de adjuntos básico.



No desarrollar interfaces enormes.



Solo dejar los contratos centrales correctos.



\---



\# FASE 2 — ECONOMÍA OPERATIVA



Crear:



`LibroEconomicoHostAI`



Unificar:



\* ingresos;

\* ventas;

\* compras;

\* gastos;

\* coste laboral;

\* eventos.



Sin contabilidad fiscal.



\---



\# FASE 3 — TPV



Crear:



`VentaHostAI`



Primero:



\### Importador universal CSV/Excel



Después:



\### Primer conector TPV real



No crear TPV propio.



\---



\# FASE 4 — PRODUCCIÓN PROFESIONAL



Construir:



\* procesos de receta;

\* tiempos;

\* dependencias;

\* maquinaria;

\* capacidades;

\* trabajadores;

\* horarios;

\* habilidades;

\* stock;

\* planificación;

\* regeneración;

\* replanificación.



Resultado:



`PlanProduccion`.



\---



\# FASE 5 — MI JORNADA PROFESIONAL



El plan genera tareas personales.



Cada trabajador ve:



\* qué hacer;

\* cuándo;

\* cuánto;

\* receta;

\* ingredientes escalados;

\* maquinaria;

\* pasos;

\* siguiente tarea;

\* incidencias.



Incluye:



`NECESITO ALGO`.



\---



\# FASE 6 — RENTABILIDAD



Combinar:



TPV

\+

escandallos

\+

compras

\+

gastos

\+

producción.



Calcular:



\* plato;

\* menú;

\* evento;

\* día;

\* turno;

\* canal;

\* restaurante.



Añadir ingeniería de menú.



\---



\# FASE 7 — INTELIGENCIA OPERATIVA



Crear:



`AlertEngine`



\*



objetivos.



Host AI empieza a detectar automáticamente:



\* margen bajo;

\* subida proveedores;

\* mermas;

\* stocks;

\* retrasos;

\* desviaciones;

\* oportunidades.



\---



\# FASE 8 — HOY / QUÉ HA CAMBIADO



Convertir el dashboard en la experiencia principal del propietario.



Debe responder:



\*\*¿Qué pasa?\*\*



\*\*¿Qué cambió?\*\*



\*\*¿Qué tengo que hacer?\*\*



\---



\# FASE 9 — PILOTO REAL



Probar durante actividad real.



Evaluar:



\* velocidad;

\* comprensión;

\* errores;

\* móvil;

\* cocina;

\* recepción;

\* stock;

\* producción;

\* alertas;

\* permisos.



La prueba real decidirá qué pulir antes de vender.



\---



\# 35. REGLA A PARTIR DE AHORA



Antes de pedir un nuevo sprint a Codex:



1\. identificar la fase;

2\. identificar el contrato de dominio afectado;

3\. comprobar qué existe;

4\. reutilizar;

5\. implementar verticalmente;

6\. probar end-to-end;

7\. certificar;

8\. cerrar la fase;

9\. pasar a la siguiente.



NO abrir simultáneamente diez módulos.



\---



\# 36. OBJETIVO INMEDIATO



Aunque este roadmap sea grande, la única prioridad inmediata sigue siendo:



\# FASE 1 — IMPORTACIÓN INTELIGENTE



No empezar TPV.



No empezar alertas.



No empezar contabilidad.



No rehacer producción todavía.



Terminar primero la entrada de datos.



Porque las siguientes fases necesitan:



\* artículos correctos;

\* recetas correctas;

\* costes;

\* proveedores;

\* menús;

\* relaciones;

\* rendimientos.



La importación es la puerta de entrada de todo el sistema.



\---



\# 37. PRODUCTO FINAL



Cuando las fases anteriores estén conectadas:



\### PROPIETARIO



Abre Host AI y sabe:



\* cómo va el restaurante;

\* cuánto vende;

\* cuánto gana;

\* dónde pierde;

\* qué está mal;

\* qué puede mejorar.



\### TRABAJADOR



Abre Mi Jornada y sabe:



\* qué hacer;

\* cómo hacerlo;

\* qué receta utilizar;

\* cuándo terminar;

\* qué hacer después.



\### HOST AI



Observa todo el sistema autorizado y puede responder:



\*\*“Esto es lo que está ocurriendo y estas son las acciones que más te convienen ahora.”\*\*



Ese es el objetivo técnico y comercial de Host AI V1.
