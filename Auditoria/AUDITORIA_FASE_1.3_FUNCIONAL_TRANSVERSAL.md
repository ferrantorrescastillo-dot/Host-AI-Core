# HOST AI — FASE 1.3: AUDITORÍA FUNCIONAL TRANSVERSAL

> Artefacto auditado: `Host AI 6.0 (4).zip`  
> Fecha: 14 de julio de 2026  
> Modo: Solo lectura  
> Archivos del proyecto modificados: Ninguno  
> Alcance: Mi Jornada, Bandeja, Producción, Recepción, Compras, Stock, Eventos, Costes y Bloqueos

---

# 1. OBJETIVO

Esta auditoría analiza cómo se relacionan las áreas principales de Host AI durante la operativa diaria.

No estudia únicamente si cada módulo funciona por separado.

Estudia si el dato puede recorrer correctamente el sistema:

```text
Evento
↓
Producción
↓
Compras
↓
Recepción
↓
Stock
↓
Mi Jornada
↓
Bandeja
↓
Bloqueos
↓
Costes
```

Preguntas principales:

1. ¿Dónde nace cada dato?
2. ¿Qué componente es su fuente de verdad?
3. ¿Quién puede modificarlo?
4. ¿Quién solo lo consulta?
5. ¿Qué integraciones son automáticas?
6. ¿Qué integraciones son manuales?
7. ¿Dónde existen sincronizaciones de una sola dirección?
8. ¿Qué puede quedar desactualizado?
9. ¿Qué debe corregirse antes de PILOTO-1.4.1?

---

# 2. RESUMEN EJECUTIVO

La arquitectura funcional del piloto está bien separada por dominios:

- Eventos gobierna eventos.
- Producción gobierna planes y tareas.
- Compras gobierna necesidades y pedidos.
- Stock gobierna lotes y movimientos.
- Recepción incorpora artículos, precios, facturas y stock.
- Bandeja conserva trabajo pendiente.
- Mi Jornada agrega y prioriza.
- Costes consulta eventos, recetas, precios e históricos.

La fortaleza principal es:

> Cada motor mantiene una autoridad bastante clara sobre sus datos.

La debilidad principal es:

> La integración transversal se apoya en sincronizaciones periódicas y referencias, pero varias de ellas son de una sola dirección.

En especial:

- la Bandeja crea tareas desde Producción, Eventos, Pedidos y Recepciones;
- los cambios hechos dentro de la Bandeja no actualizan automáticamente el módulo de origen;
- completar el dato de origen no siempre completa la tarea ya existente en la Bandeja;
- Mi Jornada confía en la Bandeja como fuente agregada;
- por tanto, una tarea de la Bandeja puede quedar desalineada con el estado real del origen.

Este es el principal problema funcional encontrado en esta pasada.

---

# 3. PRUEBAS EJECUTADAS

Se ejecutaron los diagnósticos aislados:

```text
PILOTO-1.1 — Bandeja: OK
PILOTO-1.2 — Mi Jornada: OK
PILOTO-1.0 — Recepción: OK
```

Se ejecutaron los tests:

```text
TESTS/test_piloto_11_bandeja_trabajo.py
TESTS/test_piloto_12_jornada.py
TESTS/test_piloto_1_recepcion.py
TESTS/test_604_c1_gestion_compras.py
TESTS/test_604_e1_gestion_eventos.py
TESTS/test_604_e3_flujo_eventos.py
```

Resultado real:

```text
15 passed in 0.95s
```

Conclusión:

> Los componentes funcionan correctamente dentro de los casos probados, pero los tests actuales no cubren todas las desincronizaciones transversales detectadas.

---

# 4. FUENTES DE VERDAD POR DOMINIO

## 4.1 Eventos

Componente:

```text
MOTORES/motor_eventos.py
```

Fuente de verdad:

```text
DATOS/db/eventos.json
```

Autoridad sobre:

- evento;
- fecha;
- pax;
- servicios;
- pases;
- recetas;
- estado;
- datos de cliente;
- ubicación.

Consumidores:

- Producción;
- Mi Jornada;
- Bandeja;
- Costes;
- conversación;
- herramientas históricas.

---

## 4.2 Producción

Componente:

```text
MOTORES/motor_produccion_real.py
```

Fuente de verdad:

```text
DATOS/db/planes_produccion.json
```

Autoridad sobre:

- planes;
- tareas;
- fases;
- ejecución;
- progreso;
- bloqueos;
- incidencias;
- cronograma.

Consumidores:

- Producción Guiada;
- Producción → Stock;
- Bandeja;
- Mi Jornada;
- planificación;
- informes.

---

## 4.3 Compras

Componente:

```text
MOTORES/motor_compras.py
```

Fuentes de verdad:

```text
DATOS/db/compras_necesidades.json
DATOS/db/compras_pedidos.json
```

Autoridad sobre:

- necesidades;
- pedidos;
- líneas;
- estados;
- proveedor;
- recepción de pedido;
- relación necesidad-pedido.

Consumidores:

- Bandeja;
- Mi Jornada;
- producción completa;
- stock;
- recepción de pedidos;
- conversación.

---

## 4.4 Stock

Componente:

```text
MOTORES/motor_stock.py
```

Fuentes de verdad:

```text
DATOS/db/stock_lotes.json
DATOS/db/stock_movimientos.json
```

Autoridad sobre:

- lotes;
- cantidades;
- movimientos;
- disponibilidad;
- consumos;
- entradas;
- mermas.

Consumidores:

- Producción;
- Compras;
- Recepción;
- Costes;
- alertas;
- planificación.

---

## 4.5 Recepción

Componente:

```text
SERVICIOS/recepcion_inteligente_piloto_1.py
```

Fuentes:

```text
DATOS/piloto/recepciones/
DATOS/db/articulos.json
DATOS/db/proveedores.json
DATOS/db/precios.json
DATOS/db/facturas_piloto.json
DATOS/db/stock_lotes.json
DATOS/db/stock_movimientos.json
```

Autoridad sobre:

- plan de recepción;
- documento recibido;
- relación con artículos;
- altas;
- actualización de precios;
- factura registrada;
- entradas de stock generadas por recepción.

---

## 4.6 Bandeja

Componente:

```text
SERVICIOS/bandeja_trabajo_piloto_11.py
```

Fuente de verdad:

```text
DATOS/piloto/bandeja_trabajo/bandeja.json
```

Autoridad sobre:

- tareas de trabajo;
- estado manual de la tarea;
- notas;
- historial;
- aplazamiento;
- prioridad de la tarea en la bandeja.

No es autoridad sobre:

- estado real de producción;
- estado real del evento;
- estado real del pedido;
- aplicación real de una recepción;
- stock.

---

## 4.7 Mi Jornada

Componente:

```text
SERVICIOS/jornada_piloto_12.py
```

Fuente:

```text
BandejaTrabajoPiloto11
```

Autoridad:

```text
Ninguna sobre datos operativos.
```

Responsabilidad:

- sincronizar;
- agregar;
- calcular prioridad;
- humanizar;
- recomendar;
- mostrar tiempos.

---

## 4.8 Costes

Componente:

```text
MOTORES/motor_costes_inteligente.py
```

Fuentes:

- eventos;
- escandallos;
- precios;
- extras;
- históricos.

Autoridad sobre:

- cálculos de coste;
- históricos de costes;
- históricos de rentabilidad.

No es autoridad sobre:

- receta;
- precio de origen;
- evento;
- stock.

---

# 5. FLUJO EVENTO → PRODUCCIÓN

Un evento nace en:

```text
MotorEventos.crear_evento()
```

Se guarda en:

```text
eventos.json
```

La producción puede generarse mediante:

```text
MotorProduccionReal.planificar_evento()
```

Este método:

1. obtiene el evento;
2. crea tareas;
3. diagnostica tareas;
4. añade logística si se solicita;
5. construye cronograma;
6. guarda el plan.

Resultado:

```text
eventos.json
↓
MotorProduccionReal
↓
planes_produccion.json
```

## Hallazgo

La relación existe mediante:

```text
evento_id
```

pero no existe actualización automática completa en sentido inverso.

Ejemplos:

- cambiar pax de un evento no recalcula automáticamente el plan existente;
- cambiar recetas no regenera automáticamente producción;
- cancelar evento no cancela automáticamente el plan;
- cerrar plan no cambia automáticamente el evento.

Conclusión:

> Evento y Producción están vinculados, pero no sincronizados bidireccionalmente.

Esto es correcto para un sistema controlado, pero requiere avisos claros de desactualización.

---

# 6. FLUJO EVENTO → STOCK → COMPRAS

Existe un motor transversal:

```text
MOTORES/motor_produccion_completa.py
```

Flujo:

```text
Evento
↓
Escandallos
↓
Necesidades
↓
Predicción de stock
↓
Faltantes
↓
Necesidades de compra
```

Método:

```text
MotorProduccionCompleta.analizar_evento()
```

Puede generar compras automáticamente si:

```text
generar_compras=True
```

Usa:

```text
core.stock.predecir_necesidad()
core.compras.registrar_necesidad()
```

## Fortaleza

Existe una conexión funcional real entre:

- evento;
- receta;
- stock;
- compras.

## Riesgo

La generación de necesidades puede repetirse si se ejecuta varias veces y no existe una clave de idempotencia suficientemente fuerte para el mismo evento, artículo y revisión.

El motor guarda informes en memoria:

```text
self.informes
```

No se observó persistencia directa de estos informes en esta ruta.

Conclusión:

> Debe auditarse la duplicación de necesidades antes de automatizar esta acción mediante IA o bloqueos.

---

# 7. FLUJO COMPRAS → STOCK

Método:

```text
MotorCompras.recibir_pedido()
```

Flujo:

```text
Pedido
↓
MotorStock.registrar_entrada()
↓
Lote
↓
Movimiento
↓
Pedido recibido
↓
Necesidad comprada
```

Garantías:

- no permite recibir dos veces un pedido ya recibido;
- no permite recibir un pedido cancelado;
- no permite pedido vacío;
- marca necesidades asociadas como compradas;
- registra lotes y movimientos.

## Limitación

Cada línea de pedido se registra una por una en stock.

No existe una transacción global visible que englobe:

- todas las líneas;
- estado del pedido;
- estado de necesidades.

Si falla una línea intermedia:

- las anteriores pueden haber quedado registradas;
- el pedido puede no quedar recibido;
- puede existir recepción parcial no formalizada.

Conclusión:

> Compras → Stock necesita una revisión transaccional antes de considerarse robusto para automatización completa.

---

# 8. FLUJO RECEPCIÓN → STOCK

La Recepción Inteligente aplica una transacción lógica propia.

Flujo:

```text
Documento
↓
Plan
↓
Resolución de artículos
↓
Vista previa
↓
Confirmación RECEPCIONAR
↓
Artículos
↓
Precios
↓
Lotes
↓
Movimientos
↓
Factura
```

Fortalezas:

- backup;
- escritura atómica por archivo;
- rollback mediante restauración;
- idempotencia por hash;
- proveedor como segunda vía;
- no escribe con líneas pendientes.

Esta ruta es más segura transversalmente que la recepción directa de pedidos de `MotorCompras`.

## Hallazgo estratégico

Existen dos formas de recibir mercancía:

### Ruta A

```text
Recepción Inteligente
```

### Ruta B

```text
MotorCompras.recibir_pedido()
```

Ambas pueden actualizar stock.

No son equivalentes:

- Recepción Inteligente registra factura, precios, backup e idempotencia documental.
- Recibir pedido actualiza pedido, necesidades y stock.

Conclusión:

> Existen dos rutas legítimas, pero falta un contrato común de recepción que evite duplicar entradas cuando se usan juntas.

Este punto es crítico para PILOTO-1.5.

---

# 9. RECEPCIÓN → BANDEJA

Si el usuario decide no aplicar la recepción inmediatamente:

```text
ConsolaRecepcionPiloto1
↓
BandejaTrabajoPiloto11.registrar_recepcion_pendiente()
```

La tarea queda en:

```text
bandeja.json
```

La referencia apunta al archivo de recepción.

Esto respeta correctamente la operativa real:

> recibir ahora y actualizar stock más tarde.

## Problema detectado

Cuando después se aplica la recepción, no existe una llamada automática que complete la tarea correspondiente de la Bandeja.

La sincronización de recepciones:

```text
_sync_recepciones()
```

evita crear nuevas tareas si ya existe un resultado.

Pero no completa ni cancela una tarea anterior ya creada.

Consecuencia:

- la recepción puede estar aplicada;
- la tarea puede seguir abierta en la Bandeja;
- Mi Jornada puede continuar mostrándola.

Prioridad:

```text
P1 funcional
```

---

# 10. PRODUCCIÓN → BANDEJA

La Bandeja lee:

```text
planes_produccion.json
```

y crea una tarea por cada tarea de producción no finalizada.

Clave:

```text
produccion:<tarea_id>
```

Fortaleza:

- no duplica la tarea si ya existe;
- conserva referencia al plan;
- conserva `plan_id`, `tarea_id` y `evento_id`.

## Problema detectado

La sincronización solo crea.

No actualiza el estado de la tarea ya existente.

Caso:

1. una tarea de producción crea una tarea de Bandeja;
2. la tarea real se finaliza desde Producción Guiada;
3. `_sync_produccion()` ya no la considera abierta;
4. pero la tarea previa de Bandeja sigue con estado `PENDIENTE`.

La función:

```text
_crear_si_no_existe()
```

no reconcilia ni completa tareas existentes.

Consecuencia:

- Mi Jornada puede mostrar producción ya terminada;
- la Bandeja puede acumular tareas obsoletas.

Prioridad:

```text
P1 funcional
```

---

# 11. EVENTOS → BANDEJA

La Bandeja crea una tarea por cada evento cuyo estado no sea:

```text
cerrado
completado
cancelado
```

Clave:

```text
evento:<evento_id>
```

## Problemas detectados

### 11.1 Evento cerrado después

Si un evento se cierra en `eventos.json`, la tarea ya existente de la Bandeja no se completa automáticamente.

### 11.2 Evento editado

Cambiar:

- fecha;
- pax;
- nombre;

no actualiza automáticamente título y descripción de la tarea ya creada.

### 11.3 Evento eliminado

Eliminar un evento no elimina ni marca huérfana su tarea de Bandeja.

Conclusión:

> La Bandeja conserva una fotografía inicial del evento, no una proyección sincronizada.

---

# 12. PEDIDOS → BANDEJA

La Bandeja crea tareas para pedidos cuyo estado no sea:

```text
recibido
cancelado
cerrado
```

Clave:

```text
pedido:<pedido_id>
```

## Problema

Si el pedido pasa posteriormente a `recibido`, la tarea ya creada no se completa automáticamente.

Consecuencia:

- pedido recibido;
- tarea de Bandeja pendiente;
- Mi Jornada desactualizada.

---

# 13. BANDEJA → ORÍGENES

La Bandeja permite:

- iniciar;
- completar;
- aplazar;
- bloquear;
- cancelar;
- eliminar.

Pero estas acciones solo modifican:

```text
bandeja.json
```

No modifican:

- producción;
- evento;
- pedido;
- recepción;
- stock.

Ejemplo:

> Completar una tarea de producción desde la Bandeja no finaliza la tarea en `planes_produccion.json`.

Esto evita escrituras peligrosas, pero puede confundir al usuario.

Conclusión:

> La Bandeja es un gestor paralelo de trabajo, no un panel de mando transaccional.

La interfaz debería dejarlo explícito o delegar acciones al componente de origen.

---

# 14. MI JORNADA → BANDEJA

`JornadaPiloto12.construir()` ejecuta:

```text
self.bandeja.sincronizar_fuentes()
self.bandeja.listar()
```

Mi Jornada depende completamente de la calidad de la Bandeja.

No consulta directamente:

- necesidades de compras;
- alertas de stock;
- recepciones ya aplicadas;
- eventos modificados;
- estados actuales de tareas si la Bandeja quedó desactualizada.

## Hallazgo principal

> Mi Jornada hereda cualquier desincronización de la Bandeja.

La lógica de priorización es correcta.

La calidad del dato de entrada puede no serlo.

---

# 15. COMPRAS EN MI JORNADA

Mi Jornada muestra pedidos mediante tareas `PEDIDO`.

No crea tareas desde:

```text
compras_necesidades.json
```

Consecuencia:

- puede existir una necesidad urgente sin pedido;
- Mi Jornada no la muestra;
- solo aparecerá cuando se genere un pedido.

Esto es una carencia funcional importante.

Ejemplo:

```text
Necesidad urgente:
Carrillera 10 kg
Estado: pendiente
Sin pedido generado
```

No aparece en Mi Jornada.

Recomendación:

> La Bandeja debe sincronizar también necesidades de compra pendientes, diferenciándolas de pedidos.

---

# 16. STOCK EN MI JORNADA

La Bandeja admite tipo:

```text
STOCK
```

pero la sincronización automática no crea tareas desde:

- stock bajo;
- roturas;
- caducidades;
- lotes sin ubicar;
- conciliaciones pendientes.

Las tareas STOCK actuales deben crearse manualmente o por otro flujo.

Consecuencia:

> Mi Jornada dice integrar Stock, pero no existe una fuente automática activa equivalente a Producción, Eventos, Pedidos o Recepciones.

Debe considerarse integración parcial.

---

# 17. BLOQUEOS EN PRODUCCIÓN

El bloqueo vive en:

```text
TareaProduccionReal.bloqueo
```

Producción Guiada lo muestra y prioriza.

Pero la Bandeja no sincroniza el estado de bloqueo.

Cuando crea la tarea, siempre usa estado inicial:

```text
PENDIENTE
```

No comprueba:

```text
tarea.bloqueo
```

Consecuencia:

- Producción Guiada muestra `Bloqueada`;
- Bandeja puede mostrar `Pendiente`;
- Mi Jornada puede priorizarla sin explicar correctamente el bloqueo.

Este es el hallazgo más importante para PILOTO-1.4.1.

Prioridad:

```text
P1
```

---

# 18. BLOQUEOS TRANSVERSALES

Actualmente existen varias representaciones potenciales:

- `TareaProduccionReal.bloqueo`;
- estado `BLOQUEADA` en Bandeja;
- incidencias de producción;
- bloqueos de importación;
- revisiones pendientes;
- incidencias de proveedor;
- stock insuficiente;
- pedidos pendientes.

No existe un contrato común transversal.

Conclusión:

> PILOTO-1.4.1 no debe añadir otra estructura aislada de bloqueos.

Debe crear un adaptador común o una representación canónica compatible con las estructuras actuales.

---

# 19. EVENTOS → COSTES

`MotorCostesInteligente` obtiene el evento desde:

```text
core.eventos.obtener(evento_id)
```

Después:

- recorre servicios;
- recorre pases;
- recoge recetas;
- calcula coste por receta;
- añade extras;
- calcula coste por pax;
- food cost;
- margen.

Fortaleza:

- Costes consulta fuentes reales;
- no duplica el evento;
- no altera el evento.

## Riesgo

Los históricos de costes pueden quedar obsoletos si:

- cambia el evento;
- cambia una receta;
- cambia un precio;
- cambia pax.

El histórico conserva la fotografía calculada, lo cual es correcto.

Pero la interfaz debe distinguir:

- coste actual;
- histórico;
- simulación;
- cálculo desactualizado.

---

# 20. PRODUCCIÓN → COSTES

El coste real de producción no está integrado todavía como fuente completa del coste real del evento.

Los costes actuales se basan principalmente en:

- escandallos;
- precios;
- extras;
- mano de obra introducida;
- indirectos.

PILOTO-1.8 sigue siendo necesario para integrar:

- consumo real;
- mermas;
- horas reales;
- compras específicas;
- transporte;
- desviaciones.

---

# 21. RUTAS DE RECEPCIÓN DUPLICABLES

Caso posible:

1. se recibe un pedido desde Compras;
2. se actualiza stock;
3. después se importa la factura con Recepción Inteligente;
4. se vuelve a actualizar stock.

La Recepción Inteligente detecta duplicado por hash del documento.

Pero no detecta que el pedido ya fue recibido si no existe vinculación entre:

```text
pedido_id
factura
plan_id
```

Conclusión:

> Falta una clave transversal de recepción.

Propuesta futura:

```text
RECEPCION_ID
pedido_id
documento_hash
proveedor
fecha
líneas
estado_stock
```

---

# 22. IDENTIDAD Y REFERENCIAS

Las relaciones actuales usan:

- `evento_id`;
- `plan_id`;
- `tarea_id`;
- `pedido_id`;
- `necesidad_id`;
- `articulo_id`;
- `plan_id` de recepción;
- claves de origen de Bandeja.

Fortaleza:

> Existe bastante identidad estructurada.

Debilidad:

> No existe un identificador transversal común para incidencias, bloqueos y recepciones.

---

# 23. DATOS REALES ENCONTRADOS

## Eventos

```text
4 eventos
```

## Producción

```text
1 plan
4 tareas visibles en Bandeja
```

## Compras

```text
2 necesidades
2 pedidos
ambos recibidos
```

## Stock

```text
5 lotes
6 movimientos
```

## Bandeja

```text
8 tareas
```

Se observaron tareas de Bandeja cuya referencia contiene una ruta absoluta antigua de Windows:

```text
C:\PROYECTO HOST IA\...
```

Esto no impide listar.

Sí puede impedir abrir la referencia en otra ubicación.

Prioridad:

```text
P2 portabilidad
```

---

# 24. PROBLEMAS DE PORTABILIDAD

La Bandeja guarda:

```text
referencia absoluta
```

Ejemplo:

```text
C:\PROYECTO HOST IA\Proyecto Host AI 6.0\...
```

Al mover el proyecto:

- la referencia queda inválida;
- el metadato sigue existiendo;
- la clave funcional sigue siendo válida.

Recomendación:

> Guardar rutas relativas a `base_dir`.

---

# 25. MATRIZ DE INTEGRACIÓN ACTUAL

```text
ORIGEN       DESTINO       ESTADO
Evento       Producción    Integrado manualmente
Evento       Bandeja       Creación automática
Evento       Costes        Consulta directa
Producción   Bandeja       Creación automática
Producción   Stock         Integrado por PILOTO-1.4
Producción   Compras       Mediante Producción Completa
Recepción    Stock         Integrado
Recepción    Bandeja       Integrado si queda pendiente
Compras      Stock         Integrado al recibir pedido
Compras      Bandeja       Pedidos abiertos
Stock        Mi Jornada    Parcial / no automático
Bandeja      Mi Jornada    Integrado
Bandeja      Orígenes      No integrado
Bloqueos     Bandeja       No integrado
Bloqueos     Mi Jornada    Parcial
Costes       Eventos       Consulta directa
Costes       Producción    Parcial
```

---

# 26. CLASIFICACIÓN DE SINCRONIZACIONES

## Bidireccional real

No se ha identificado una integración completamente bidireccional automática entre dominios principales.

## Unidireccional segura

- Evento → Producción.
- Producción → Stock.
- Recepción → Stock.
- Compras → Stock.
- Orígenes → Bandeja.
- Bandeja → Mi Jornada.
- Eventos/Recetas/Precios → Costes.

## Manual o bajo confirmación

- creación de producción desde evento;
- generación de compras;
- recepción;
- cierre de producción;
- actualización de stock.

## Ausente

- Bandeja → Producción;
- Bandeja → Eventos;
- Bandeja → Compras;
- Bloqueo de Producción → Bandeja;
- Necesidades de compra → Mi Jornada;
- Alertas de stock → Mi Jornada;
- recepción aplicada → completar tarea de Bandeja.

---

# 27. FORTALEZAS FUNCIONALES

1. Mi Jornada es de solo lectura.
2. Bandeja conserva contexto.
3. Recepción permite aplazar stock.
4. Producción → Stock exige confirmación.
5. Eventos tienen identidad estable.
6. Compras vincula necesidades y pedidos.
7. Costes usa motores existentes.
8. Diagnósticos están aislados.
9. Las integraciones críticas no dependen de IA.
10. Los motores de dominio tienen autoridad razonablemente clara.

---

# 28. DEBILIDADES FUNCIONALES

1. Bandeja no reconcilia estados.
2. Mi Jornada hereda tareas obsoletas.
3. Bloqueos no llegan estructurados a Bandeja.
4. Necesidades sin pedido no aparecen en Mi Jornada.
5. Stock no genera tareas automáticas.
6. Dos rutas de recepción pueden duplicar stock.
7. Compras → Stock no es transaccional globalmente.
8. Eventos y producción pueden quedar desalineados.
9. Rutas absolutas reducen portabilidad.
10. No existe contrato transversal de bloqueo.

---

# 29. PENDIENTES RECOMENDADOS

## P1 — Reconciliación Bandeja-Origen

Al sincronizar:

- actualizar título;
- actualizar descripción;
- actualizar estado;
- completar tareas cuyo origen ya terminó;
- marcar huérfanas.

## P1 — Propagar bloqueos de Producción

Mapear:

```text
tarea.bloqueo
→ tarea de Bandeja BLOQUEADA
→ Mi Jornada
```

## P1 — Contrato común de recepción

Evitar duplicidad entre:

- recibir pedido;
- aplicar factura.

## P1 — Necesidades de compra en Bandeja

Sincronizar necesidades pendientes aunque no exista pedido.

## P2 — Alertas de stock

Crear tareas desde:

- rotura;
- stock mínimo;
- caducidad;
- lote sin ubicar.

## P2 — Rutas relativas

Migrar referencias absolutas.

## P2 — Invalidación de producción

Avisar si cambia:

- evento;
- pax;
- recetas;
- fecha.

---

# 30. IMPACTO EN PILOTO-1.4.1

El asistente de bloqueos debería actuar sobre un contrato transversal.

Modelo mínimo propuesto:

```text
bloqueo_id
tipo
origen_tipo
origen_id
titulo
descripcion
causa
estado
prioridad
acciones_posibles
accion_elegida
responsable
creado_en
resuelto_en
evidencia
```

Debe adaptarse a:

- bloqueo de producción;
- falta de stock;
- necesidad de compra;
- recepción pendiente;
- incidencia de proveedor;
- tarea de Bandeja.

No debe escribir directamente.

Debe:

1. detectar;
2. explicar;
3. proponer;
4. pedir confirmación;
5. delegar;
6. recalcular;
7. cerrar o mantener bloqueo.

---

# 31. DISEÑO RECOMENDADO PARA EL ASISTENTE

```text
Origen
↓
Adaptador de bloqueo
↓
Bloqueo canónico
↓
Asistente de resolución
↓
Opciones
↓
Confirmación
↓
Servicio del dominio
↓
Reconciliación
↓
Bandeja
↓
Mi Jornada
```

Esto evita:

- duplicar motores;
- modificar stock desde IA;
- resolver solo mediante texto;
- crear una segunda Bandeja.

---

# 32. QUÉ NO DEBE HACERSE TODAVÍA

No se recomienda:

- refactor completo de Bandeja;
- eliminar sistemas históricos;
- migrar toda la persistencia;
- conectar IA directamente;
- hacer sincronización bidireccional automática completa;
- hacer que completar una tarea de Bandeja ejecute operaciones críticas sin confirmación.

---

# 33. ORDEN DE CORRECCIÓN RECOMENDADO

Antes de PILOTO-1.4.1 completo:

```text
1. Reconciliar Bandeja con orígenes
2. Propagar bloqueos de Producción
3. Añadir necesidades de compra
4. Definir contrato común de bloqueo
5. Definir vínculo de recepción
6. Desarrollar asistente
```

Puede agruparse en dos sprints:

## Sprint A

```text
PILOTO-1.4.0-R
Reconciliación de Bandeja y fuentes
```

## Sprint B

```text
PILOTO-1.4.1
Asistente de resolución de bloqueos
```

---

# 34. ESTADO DE LA AUDITORÍA FUNCIONAL

## Completado

- Mi Jornada;
- Bandeja;
- Producción;
- Recepción;
- Compras;
- Stock;
- Eventos;
- Costes;
- bloqueos;
- referencias;
- pruebas específicas;
- mapa transversal.

## No incluido todavía

- auditoría semántica de los 620 servicios;
- clasificación de módulos históricos;
- errores globales de pytest;
- mapa completo de imports;
- huérfanos;
- duplicados lógicos amplios.

Eso pertenece a la Fase 1.4 de arquitectura.

---

# 35. CONCLUSIÓN

Host AI ya dispone de los dominios necesarios para funcionar como sistema operativo de cocina.

El problema transversal principal no es la falta de módulos.

Es la reconciliación entre ellos.

La arquitectura actual sigue este patrón:

```text
Motores de dominio
↓
Bandeja crea representaciones
↓
Mi Jornada las prioriza
```

Pero falta:

```text
Origen cambia
↓
Bandeja se reconcilia
↓
Mi Jornada refleja el nuevo estado
```

Por tanto, la siguiente prioridad técnica no debería ser añadir más inteligencia.

Debería ser garantizar que:

> Mi Jornada y la Bandeja muestran siempre el estado real de Producción, Eventos, Compras y Recepciones.

Una vez resuelto esto, PILOTO-1.4.1 podrá construirse sobre una base fiable y podrá convertir bloqueos reales en acciones coordinadas sin duplicar lógica.
