# HOST AI — FASE 1: AUDITORÍA COMPLETA DEL PROYECTO

> Segunda pasada técnica: arranque, producción, stock, persistencia, bloqueos y escrituras  
> Artefacto auditado: `Host AI 6.0 (4).zip`  
> Fecha: 14 de julio de 2026  
> Modo: Solo lectura  
> Archivos del proyecto modificados: Ninguno

---

# 1. OBJETIVO DE ESTA PASADA

Esta segunda pasada se ha centrado en responder con código real a estas preguntas:

1. ¿Cómo arranca Host AI?
2. ¿Qué menú abre el piloto?
3. ¿Cuál es el motor real de producción?
4. ¿Cuál es el motor real de stock?
5. ¿Dónde persisten los datos activos del piloto?
6. ¿Cómo se representa y resuelve un bloqueo?
7. ¿Qué ocurre exactamente al terminar una producción?
8. ¿Qué escrituras se realizan?
9. ¿Qué rollback existe?
10. ¿Qué capas parecen activas, paralelas o históricas?

---

# 2. RESUMEN EJECUTIVO

El flujo activo del piloto está bien definido y es coherente:

```text
main.py
↓
SERVICIOS/lanzador_piloto_01.py
↓
CORE/host_ai_core.py
↓
APP/consola_piloto_01.py
↓
APP/consola_produccion_guiada_piloto_13.py
↓
SERVICIOS/produccion_guiada_piloto_13.py
↓
MOTORES/motor_produccion_real.py
```

Para terminar una producción con actualización de stock:

```text
Consola de Producción Guiada
↓
SERVICIOS/produccion_stock_piloto_14.py
↓
MOTORES/motor_stock.py
+
MOTORES/motor_produccion_real.py
↓
SERVICIOS/base_datos_local.py
↓
DATOS/db/*.json
+
DATOS/piloto/produccion_stock_registros.json
```

Hallazgo principal:

> La línea piloto activa no usa SQLite como persistencia principal. Usa una base local basada en archivos JSON mediante `BaseDatosLocal`.

Existe además una capa SQLite histórica o paralela:

```text
SERVICIOS/gestor_base_datos_definitiva_451.py
```

pero no forma parte del `HostAICore` activo del piloto auditado.

---

# 3. MAPA DE ARRANQUE

## 3.1 Entrada oficial

Archivo:

```text
main.py
```

Responsabilidad:

- resolver `BASE_DIR`;
- añadir la raíz a `sys.path`;
- importar el lanzador;
- ejecutar el piloto.

Flujo:

```text
main()
→ ejecutar_piloto_01(BASE_DIR)
```

## 3.2 Lanzador

Archivo:

```text
SERVICIOS/lanzador_piloto_01.py
```

Clase:

```text
LanzadorPiloto01
```

Opciones:

```text
1. Modo Piloto privado
2. Modo Desarrollo y herramientas técnicas
8. Auditoría de arranque
9. Certificar PILOTO-0.1
0. Salir
```

Antes de abrir el piloto ejecuta:

```text
AuditorArranquePiloto01(...).ejecutar(importar_modulos=False)
```

Si la auditoría falla:

```text
raise RuntimeError
```

Esto protege el arranque del piloto.

## 3.3 Composition root

Archivo:

```text
CORE/host_ai_core.py
```

Clase:

```text
HostAICore
```

Responsabilidad real:

- crear la base local;
- inicializar motores;
- inicializar servicios;
- registrar pipelines;
- exponer director y orquestador.

Componentes críticos inicializados:

```text
self.db = BaseDatosLocal(self.base_dir)
self.compras = MotorCompras(self.db)
self.stock = MotorStock(self.db)
self.eventos = MotorEventos(self.db)
self.escandallos_inteligente = MotorEscandallosInteligente(self.db)
self.costes_inteligente = MotorCostesInteligente(self)
self.produccion_real = MotorProduccionReal(self)
self.persistencia = MotorPersistencia(self, self.db)
```

Conclusión:

> `HostAICore` es el contenedor central de dependencias del piloto actual.

---

# 4. MENÚ DEL PILOTO

Archivo:

```text
APP/consola_piloto_01.py
```

Clase:

```text
ConsolaPiloto01
```

Menú:

```text
1. Mi jornada
2. Recepción inteligente de mercancía
3. Eventos
4. Producción
5. Compras
6. Stock
7. Costes y rentabilidad
8. Hablar con Host AI
0. Volver
```

La consola reutiliza:

```text
APP.consola.AppConsolaHostAI
```

y no duplica las áreas ya existentes.

Producción abre:

```text
APP/consola_produccion_guiada_piloto_13.py
```

---

# 5. MOTOR REAL DE PRODUCCIÓN

Archivo:

```text
MOTORES/motor_produccion_real.py
```

Clase:

```text
MotorProduccionReal
```

Versión declarada en docstring:

```text
v2.0.7
```

## 5.1 Persistencia

Carga:

```python
self.core.db.cargar("planes_produccion")
```

Guarda:

```python
self.core.db.guardar(
    "planes_produccion",
    [p.to_dict() for p in self.planes.values()]
)
```

Archivo físico:

```text
DATOS/db/planes_produccion.json
```

## 5.2 Operaciones operativas

Métodos relevantes:

```text
iniciar_tarea
pausar_tarea
reanudar_tarea
finalizar_tarea
actualizar_progreso_tarea
registrar_incidencia_tarea
resolver_bloqueo_tarea
actualizar_observaciones_ejecucion
```

## 5.3 Finalización simple

`finalizar_tarea()`:

- comprueba que no esté finalizada;
- acumula tiempo real;
- cambia estado a `finalizada`;
- pone avance al 100 %;
- marca fecha de finalización;
- actualiza estado del plan;
- persiste el plan.

Importante:

> `MotorProduccionReal.finalizar_tarea()` por sí solo no modifica stock.

La integración con stock se realiza en el servicio PILOTO-1.4.

---

# 6. MODELO REAL DE PRODUCCIÓN

Archivo:

```text
MODELOS/produccion_real.py
```

Modelos:

```text
FaseProduccionReal
TareaProduccionReal
BloqueProduccionReal
PlanProduccionReal
```

## 6.1 Estado de una tarea

Campos principales:

```text
estado_ejecucion
iniciado_en
pausado_en
finalizado_en
cronometro_iniciado_en
segundos_acumulados
progreso_manual
retraso_min
bloqueo
observaciones_ejecucion
incidencias
checklist
```

## 6.2 Bloqueo

El bloqueo operativo no es una entidad independiente.

Actualmente se representa como:

```text
TareaProduccionReal.bloqueo: str
```

y se complementa con:

```text
TareaProduccionReal.incidencias: list
```

Conclusión:

> El modelo de bloqueo activo es simple y está embebido dentro de la tarea.

Esto es suficiente para PILOTO-1.3, pero limita un futuro asistente de resolución avanzada.

---

# 7. SERVICIO DE PRODUCCIÓN GUIADA

Archivo:

```text
SERVICIOS/produccion_guiada_piloto_13.py
```

Clase:

```text
ProduccionGuiadaPiloto13
```

Responsabilidad:

- leer del motor real;
- humanizar;
- ordenar tareas;
- seleccionar siguiente acción;
- delegar escrituras.

Delegación confirmada:

```text
iniciar       → MotorProduccionReal.iniciar_tarea
pausar        → MotorProduccionReal.pausar_tarea
reanudar      → MotorProduccionReal.reanudar_tarea
finalizar     → MotorProduccionReal.finalizar_tarea
avance        → MotorProduccionReal.actualizar_progreso_tarea
incidencia    → MotorProduccionReal.registrar_incidencia_tarea
resolver      → MotorProduccionReal.resolver_bloqueo_tarea
```

No duplica el motor.

---

# 8. INTERFAZ DE PRODUCCIÓN GUIADA

Archivo:

```text
APP/consola_produccion_guiada_piloto_13.py
```

Clase:

```text
ConsolaProduccionGuiadaPiloto13
```

Opciones:

```text
1. Voy a empezar una tarea
2. He terminado una tarea
3. Necesito pausar o reanudar
4. Quiero indicar cuánto llevo
5. Ha surgido un problema
6. He resuelto un bloqueo
7. Actualizar la pantalla
0. Volver
```

## 8.1 Separación correcta

La consola:

- muestra;
- pregunta;
- confirma;
- delega.

No aplica directamente movimientos de stock.

## 8.2 Fricción detectada

Al mostrar faltantes utiliza:

```python
{f['faltante']:g}
```

Esto produce números como:

```text
4.70448 kg
```

Confirma el pendiente UX previamente registrado.

---

# 9. MOTOR REAL DE STOCK

Archivo:

```text
MOTORES/motor_stock.py
```

Clase:

```text
MotorStock
```

## 9.1 Estado en memoria

```text
self.lotes
self.movimientos
self.stock_minimos
```

## 9.2 Carga

Colecciones:

```text
stock_lotes
stock_movimientos
```

Archivos físicos:

```text
DATOS/db/stock_lotes.json
DATOS/db/stock_movimientos.json
```

## 9.3 Escritura

Método:

```text
_guardar_automatico()
```

Escribe ambas colecciones completas mediante `BaseDatosLocal`.

## 9.4 Operaciones críticas

```text
registrar_entrada
consumir
_descontar_stock
_cantidad_disponible
_lotes_compatibles
```

## 9.5 Selección de lotes

El consumo ordena lotes según:

```text
caducidad
fecha de entrada
creado_en
id
```

La intención es FEFO/FIFO híbrido.

---

# 10. PERSISTENCIA ACTIVA

Archivo:

```text
SERVICIOS/base_datos_local.py
```

Clase:

```text
BaseDatosLocal
```

Persistencia:

```text
JSON
```

Ruta:

```text
DATOS/db/
```

Colecciones oficiales de `BaseDatosLocal`:

```text
eventos
stock_lotes
stock_movimientos
compras_necesidades
compras_pedidos
escandallos
precios
planes_produccion
ideas_culinarias
historial_chat
historial_escandallos_costes
historial_costes_eventos
historial_rentabilidad
```

## 10.1 Comportamiento de guardado

`guardar()`:

- valida nombre de colección;
- exige lista;
- sobrescribe el JSON completo;
- actualiza `_metadata.json`.

## 10.2 Snapshots

Existe:

```text
BaseDatosLocal.snapshot()
```

pero el flujo PILOTO-1.4 no lo invoca automáticamente.

## 10.3 Base actual encontrada

Conteos relevantes:

```text
articulos.json:              359
compras_necesidades.json:      2
compras_pedidos.json:          2
escandallos.json:             16
eventos.json:                  4
planes_produccion.json:        1
precios.json:                  1
proveedores.json:             24
stock_lotes.json:              5
stock_movimientos.json:        6
```

Algunos archivos de `DATOS/db` no pertenecen a `BaseDatosLocal.COLECCIONES`.

Son gestionados por servicios históricos o especializados.

---

# 11. SQLITE: CAPA PARALELA O HISTÓRICA

Archivo:

```text
SERVICIOS/gestor_base_datos_definitiva_451.py
```

Utiliza:

```text
sqlite3
DATOS/db/host_ai.db
```

Sin embargo:

- no existe `host_ai.db` dentro del ZIP auditado;
- `HostAICore` no instancia `GestorBaseDatosDefinitiva451`;
- la línea piloto activa usa `BaseDatosLocal`.

Conclusión:

```text
Persistencia activa del piloto: JSON
Persistencia SQLite 4.5.1: paralela, histórica o no integrada en el arranque actual
```

Esto debe quedar claro en la futura arquitectura.

---

# 12. FLUJO EXACTO AL TERMINAR PRODUCCIÓN

## 12.1 Paso 1 — Selección

La consola recibe:

```text
He terminado una tarea
```

## 12.2 Paso 2 — Confirmación

Pregunta:

```text
¿Confirmas que la tarea está terminada?
```

## 12.3 Paso 3 — Vista previa

Llama:

```text
ProduccionStockPiloto14.preparar_cierre(plan_id, tarea_id)
```

## 12.4 Paso 4 — Protección de duplicado

Busca en:

```text
DATOS/piloto/produccion_stock_registros.json
```

Clave:

```text
plan_id::tarea_id
```

Si existe una operación registrada:

```text
YA_REGISTRADA
```

## 12.5 Paso 5 — Protección de tarea ya finalizada

Si la tarea ya estaba finalizada antes del registro:

```text
FINALIZADA_SIN_REGISTRO
```

No toca stock automáticamente.

## 12.6 Paso 6 — Escandallo

Busca primero por:

```text
receta_id
```

y después por nombre exacto normalizado.

Colección:

```text
DATOS/db/escandallos.json
```

## 12.7 Paso 7 — Escalado

Calcula:

```text
factor = cantidad_tarea / raciones_base
```

y obtiene consumos.

## 12.8 Paso 8 — Disponibilidad

Usa:

```text
MotorStock._cantidad_disponible()
```

## 12.9 Paso 9 — Falta de stock

Si falta:

```text
STOCK_INSUFICIENTE
```

La consola puede registrar una incidencia:

```text
Stock insuficiente para cerrar la producción
```

No se modifica stock.

## 12.10 Paso 10 — Vista previa humana

Muestra:

- salidas previstas;
- entrada del producto terminado.

## 12.11 Paso 11 — Confirmación final

Pregunta:

```text
¿Registrar producción y actualizar stock?
```

## 12.12 Paso 12 — Ejecución

Llama:

```text
ProduccionStockPiloto14.cerrar_y_actualizar_stock()
```

---

# 13. ESCRITURAS DEL CIERRE

El cierre normal realiza, en este orden:

## 13.1 Consumos

Por cada ingrediente:

```text
MotorStock.consumir()
```

Cada llamada:

- reduce lotes en memoria;
- crea movimiento;
- guarda `stock_lotes.json`;
- guarda `stock_movimientos.json`.

## 13.2 Entrada de elaboración

```text
MotorStock.registrar_entrada()
```

Crea:

- nuevo lote;
- movimiento de entrada;
- guardado automático.

## 13.3 Cierre de tarea

```text
MotorProduccionReal.finalizar_tarea()
```

Actualiza:

```text
DATOS/db/planes_produccion.json
```

## 13.4 Trazabilidad de PILOTO-1.4

Guarda:

```text
DATOS/piloto/produccion_stock_registros.json
```

Incluye:

- plan;
- tarea;
- receta;
- operario;
- lote;
- consumos;
- producción generada;
- movimientos;
- estado.

---

# 14. TRANSACCIÓN Y ROLLBACK

Antes de escribir, el servicio crea copias en memoria:

```text
stock.lotes
stock.movimientos
produccion.planes
```

Si ocurre una excepción:

1. restaura las copias en memoria;
2. vuelve a guardar stock;
3. vuelve a guardar producción;
4. devuelve:

```text
ERROR_REVERTIDO
```

## 14.1 Fortaleza

Existe rollback funcional de los tres estados principales:

- lotes;
- movimientos;
- planes.

## 14.2 Limitación crítica

El rollback no usa una transacción atómica del sistema de archivos.

Cada `consumir()` guarda inmediatamente.

Por tanto, durante la operación existen escrituras parciales temporales.

Si el proceso de Python o el equipo se interrumpe de forma abrupta antes del `except`, el rollback no puede ejecutarse.

## 14.3 Otra limitación

La trazabilidad se guarda al final.

Si el guardado de trazabilidad falla:

- el `except` revierte stock y producción;
- el registro no queda escrito.

Esto es coherente.

## 14.4 Riesgo de archivo corrupto

`BaseDatosLocal` escribe directamente sobre el JSON final.

No utiliza:

- archivo temporal;
- `fsync`;
- reemplazo atómico;
- journal.

Riesgo:

```text
Pérdida o corrupción por interrupción durante escritura.
```

No significa que ocurra normalmente, pero debe registrarse como deuda de persistencia.

---

# 15. MODELO DE BLOQUEOS

## 15.1 Registro

Para un bloqueo:

```text
MotorProduccionReal.registrar_incidencia_tarea(
    tipo="bloqueo"
)
```

Guarda:

- incidencia completa en `tarea.incidencias`;
- texto en `tarea.bloqueo`;
- retraso acumulado;
- plan actualizado.

## 15.2 Visualización

`ProduccionGuiadaPiloto13`:

- cuenta tareas con `bloqueo`;
- las muestra como `🔴 Bloqueada`;
- les da máxima prioridad visual;
- propone `RESOLVER_BLOQUEO`.

## 15.3 Resolución

```text
MotorProduccionReal.resolver_bloqueo_tarea()
```

Hace:

- copia el texto anterior;
- vacía `tarea.bloqueo`;
- opcionalmente actualiza observaciones;
- persiste.

## 15.4 Limitaciones del modelo actual

El bloqueo no tiene campos propios para:

- categoría;
- causa estructurada;
- origen;
- componente afectado;
- alternativas;
- acción recomendada;
- responsable;
- fecha objetivo;
- estado de resolución;
- relación con compras o recepción;
- evidencia de cierre.

## 15.5 Consecuencia para PILOTO-1.4.1

El futuro asistente no debería basarse solo en el texto libre.

Primero debe decidirse si:

1. amplía la estructura de incidencia existente; o
2. introduce un modelo común de bloqueo compatible.

No debe duplicar un segundo sistema de bloqueos sin auditar bandeja, menús e importaciones.

---

# 16. BANDEJA Y BLOQUEOS

Archivo de datos:

```text
DATOS/piloto/bandeja_trabajo/bandeja.json
```

Existe un sistema de bandeja separado.

En esta pasada no se ha encontrado una conexión directa automática entre:

```text
bloqueo de TareaProduccionReal
```

y:

```text
bandeja de trabajo
```

La integración debe auditarse en la siguiente pasada.

Posible riesgo:

> El bloqueo puede existir dentro del plan sin convertirse en una tarea transversal de Mi Jornada o Bandeja.

---

# 17. DATOS DE TRAZABILIDAD EN EL ZIP

La ruta prevista:

```text
DATOS/piloto/produccion_stock_registros.json
```

no aparece actualmente en el ZIP auditado.

Esto puede significar:

- aún no se ha ejecutado una ruta exitosa sobre esta copia;
- el diagnóstico usa entorno temporal;
- el archivo se excluyó;
- la validación manual solo recorrió falta de stock.

Esto explica por qué el diagnóstico técnico puede estar verde mientras la evidencia real persistida del ZIP sigue incompleta.

---

# 18. COMPONENTES CRÍTICOS IDENTIFICADOS

## CMP-CORE-001 — HostAICore

Tipo:

```text
Composition root
```

Criticidad:

```text
CRÍTICA
```

Riesgo:

- constructor extremadamente grande;
- alto número de imports;
- gran coste de inicialización;
- acoplamiento central.

## CMP-PROD-001 — MotorProduccionReal

Criticidad:

```text
CRÍTICA
```

Autoridad sobre:

- planes;
- tareas;
- ejecución;
- incidencias;
- bloqueos.

## CMP-STOCK-001 — MotorStock

Criticidad:

```text
CRÍTICA
```

Autoridad sobre:

- lotes;
- movimientos;
- disponibilidad.

## CMP-PROD-002 — ProduccionGuiadaPiloto13

Criticidad:

```text
ALTA
```

Responsabilidad:

- humanización;
- priorización;
- delegación.

## CMP-PROD-STOCK-001 — ProduccionStockPiloto14

Criticidad:

```text
CRÍTICA
```

Responsabilidad:

- cierre integrado;
- idempotencia;
- rollback;
- trazabilidad.

## CMP-DAT-001 — BaseDatosLocal

Criticidad:

```text
CRÍTICA
```

Responsabilidad:

- persistencia JSON activa.

---

# 19. RIESGOS Y DEUDA DETECTADOS

## P1 — Persistencia no atómica

Los JSON se sobrescriben directamente.

## P1 — Rollback solo dentro del proceso

No protege contra caída abrupta.

## P1 — Versión y persistencia documentadas de forma inconsistente

La memoria previa hablaba de SQLite como base local principal.

El piloto actual usa JSON.

## P1 — Modelo de bloqueo demasiado simple para 1.4.1

Debe ampliarse o adaptarse sin duplicar.

## P2 — Uso de métodos privados de stock

`ProduccionStockPiloto14` llama:

```text
MotorStock._cantidad_disponible
```

Esto crea acoplamiento con API privada.

Debe existir un método público como:

```text
cantidad_disponible()
```

o un contrato equivalente.

## P2 — `HostAICore` como contenedor gigante

Tiene cientos de imports e inicializaciones.

No debe refactorizarse todavía sin mapa de impacto.

## P2 — Persistencias paralelas

Conviven:

- `BaseDatosLocal` JSON activa;
- SQLite 4.5.1;
- múltiples JSON especializados;
- Excel legado.

Debe definirse autoridad por dominio.

## P2 — Falta de evidencia persistida de cierre exitoso

No existe `produccion_stock_registros.json` en el ZIP.

## P3 — Cantidades no humanizadas

Uso de formato `:g`.

---

# 20. CONTRADICCIONES CON LA MEMORIA VIVA

## 20.1 Persistencia

Documentación previa:

```text
SQLite / base de datos local
```

Código activo:

```text
BaseDatosLocal sobre JSON
```

Corrección recomendada:

```text
Base local activa del piloto: JSON
SQLite 4.5.1: línea paralela/no conectada al arranque actual
```

## 20.2 PILOTO-1.4

Documentación previa:

```text
validación parcial
```

Diagnóstico actual:

```text
consumos, entrada, trazabilidad, duplicados y rollback: OK
```

ZIP actual:

```text
sin archivo real de trazabilidad de cierre
```

Estado reconciliado recomendado:

```text
Certificado técnicamente mediante diagnóstico y tests.
Ruta real persistida sobre esta copia: no demostrada.
Validación manual de stock insuficiente: demostrada históricamente.
```

---

# 21. DIAGRAMA DE ESCRITURAS

```text
Usuario confirma cierre
        │
        ▼
ProduccionStockPiloto14
        │
        ├── consumir ingrediente 1
        │       └── stock_lotes.json
        │       └── stock_movimientos.json
        │
        ├── consumir ingrediente N
        │       └── stock_lotes.json
        │       └── stock_movimientos.json
        │
        ├── registrar producto terminado
        │       └── stock_lotes.json
        │       └── stock_movimientos.json
        │
        ├── finalizar tarea
        │       └── planes_produccion.json
        │
        └── guardar trazabilidad
                └── produccion_stock_registros.json
```

---

# 22. GARANTÍAS ACTUALES DEL CIERRE

## Garantizado por código

- vista previa;
- validación de escandallo;
- validación de stock;
- confirmación doble;
- protección lógica frente a duplicados;
- consumo por lotes;
- entrada de producto terminado;
- cierre de tarea;
- trazabilidad;
- rollback por excepción controlada.

## No garantizado ante fallo abrupto

- atomicidad de archivos;
- recuperación si el proceso muere;
- bloqueo concurrente;
- escritura multiusuario;
- journal de transacción.

---

# 23. RECOMENDACIÓN PARA PILOTO-1.4.1

Antes de desarrollar el asistente de bloqueos:

1. registrar formalmente los componentes críticos;
2. auditar la bandeja y Mi Jornada;
3. definir un contrato común de bloqueo;
4. mantener compatibilidad con `tarea.bloqueo`;
5. evitar que el asistente escriba stock;
6. permitir propuestas:
   - producir faltante;
   - crear necesidad de compra;
   - vincular recepción;
   - aplazar;
   - cambiar prioridad;
7. requerir confirmación;
8. registrar decisión y resolución.

---

# 24. ESTADO DE ESTA PASADA

## Completado

- arranque completo;
- menú piloto;
- composition root;
- producción real;
- stock real;
- persistencia activa;
- capa SQLite paralela;
- flujo de cierre;
- escrituras;
- rollback;
- bloqueos;
- componentes críticos;
- contradicciones principales.

## Pendiente para cerrar Fase 1

- auditar Mi Jornada;
- auditar Bandeja;
- auditar Recepción;
- auditar Compras;
- revisar propagación de bloqueos;
- clasificar carpetas históricas;
- analizar los tres errores de colección;
- crear mapa preliminar de componentes;
- emitir informe final consolidado.

---

# 25. CONCLUSIÓN

La arquitectura del piloto reciente es más coherente de lo que su tamaño sugiere:

- la interfaz delega;
- el servicio 1.3 humaniza;
- el motor de producción gobierna tareas;
- el servicio 1.4 orquesta;
- el motor de stock gobierna lotes;
- la base JSON persiste.

El mayor problema inmediato no está en la lógica de PILOTO-1.4.

Está en:

1. la falta de atomicidad de persistencia;
2. la mezcla de capas históricas;
3. la documentación desalineada;
4. el modelo simple de bloqueos;
5. la suite global bloqueada.

No se recomienda todavía un refactor grande.

La siguiente auditoría debe seguir el flujo transversal:

```text
Mi Jornada
↔ Bandeja
↔ Producción
↔ Recepción
↔ Compras
↔ Bloqueos
```

para diseñar PILOTO-1.4.1 sobre componentes reales y no sobre supuestos.
