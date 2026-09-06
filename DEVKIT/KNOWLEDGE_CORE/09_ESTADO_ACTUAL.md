# HOST AI — 09_ESTADO_ACTUAL

> Cabina de control oficial del proyecto  
> Estado del documento: Oficial  
> Ámbito: DEVKIT / Memoria viva  
> Versión del documento: 1.0  
> Fecha de actualización: 13 de julio de 2026  
> Proyecto de referencia: Host AI 6.0  
> Documentos superiores: `01_IDENTIDAD.md`, `03_REGLAS.md`

# 0. INSTRUCCIÓN DE LECTURA PRIORITARIA

Este es el primer documento que debe leer cualquier:

- nuevo chat;
- desarrollador;
- arquitecto;
- auditor;
- agente de inteligencia artificial;
- colaborador técnico;

antes de modificar Host AI.

Su objetivo es responder inmediatamente:

1. ¿Qué proyecto tengo delante?
2. ¿En qué punto exacto está?
3. ¿Qué está realmente terminado?
4. ¿Qué está entregado, pero aún requiere validación?
5. ¿Qué sprint está activo?
6. ¿Cuál es el siguiente paso?
7. ¿Qué no debe tocarse?
8. ¿Qué archivos y decisiones son referencia?
9. ¿Qué riesgos existen?
10. ¿Cómo debe continuarse sin empezar desde cero?

Este documento no sustituye al código real.

El orden correcto de autoridad es:

1. Código real de la versión de trabajo.
2. Datos y configuración reales.
3. Diagnósticos y tests ejecutados.
4. Certificaciones asociadas a esa versión.
5. Este estado actual.
6. Roadmap y documentación histórica.

Si el código contradice este documento, debe detenerse el desarrollo, investigar la diferencia y actualizar la memoria viva.

---

# 1. RESUMEN EJECUTIVO

## 1.1 Estado general

Host AI es actualmente un proyecto local avanzado en Python orientado a convertirse en un **segundo de cocina digital**.

No está en fase inicial.

Dispone de una base amplia de:

- artículos;
- recetas;
- escandallos;
- menús;
- eventos;
- compras;
- stock;
- producción;
- recepción de mercancía;
- planificación;
- inteligencia artificial;
- importadores;
- diagnósticos;
- tests;
- documentación.

La estrategia activa ya no consiste en añadir motores aislados.

La estrategia vigente es construir y validar **flujos completos de trabajo real**, centrados en `Mi Jornada`.

## 1.2 Momento actual del proyecto

El desarrollo funcional del piloto ha llegado hasta:

- `PILOTO-1.4 — Producción → Stock`, entregado y parcialmente validado manualmente.

Después se propuso:

- `PILOTO-1.4.1 — Asistente de resolución de bloqueos`.

Ese sub-sprint **no está desarrollado**.

Antes de continuarlo se tomó una decisión estratégica:

> Crear primero un DEVKIT y una memoria viva para que el proyecto deje de depender del contexto de los chats y de intercambios manuales poco trazables.

## 1.3 Sprint activo real

El sprint activo es:

> **DEVKIT-0.1 — Memoria viva / Knowledge Core**

Estado:

- `01_IDENTIDAD.md`: creado.
- `03_REGLAS.md`: creado.
- `09_ESTADO_ACTUAL.md`: creado mediante esta versión.
- Resto del Knowledge Core: pendiente.

## 1.4 Próxima acción recomendada

Después de incorporar este documento al proyecto, el siguiente documento recomendado es:

> **`02_ARQUITECTURA.md`**

Debe construirse auditando el código real completo, no únicamente a partir de la memoria.

Después:

1. `04_ROADMAP.md`
2. `05_SPRINTS.md`
3. `06_MEMORIA_TECNICA.md`
4. `07_MEMORIA_OPERATIVA.md`
5. `08_CERTIFICACIONES.md`
6. `10_PENDIENTES.md`

Solo después de tener una memoria mínima fiable debe iniciarse la automatización del DEVKIT.

---

# 2. IDENTIFICACIÓN DEL PROYECTO

## 2.1 Nombre

**Host AI**

## 2.2 Versión de referencia

**Host AI 6.0**

## 2.3 Tipo de producto

Plataforma operativa inteligente para cocinas profesionales.

Definición oficial:

> Un segundo de cocina digital que reúne la información operativa de un negocio gastronómico, la convierte en decisiones comprensibles y guía el trabajo diario respetando la forma real de trabajar de un equipo de cocina.

## 2.4 Fase comercial

No comercial.

La prioridad actual es:

- uso propio;
- piloto privado;
- validación diaria;
- corrección;
- fiabilidad;
- aprendizaje operativo.

## 2.5 Usuario inicial

El propio creador del proyecto, con experiencia real en cocina y catering.

El sistema debe probarse primero en su operativa cotidiana.

## 2.6 Entorno principal conocido

- Sistema operativo: Windows.
- Editor: Visual Studio Code.
- Lenguaje: Python.
- Versión conocida: Python 3.13.x.
- Librerías principales conocidas: pandas, openpyxl.
- Persistencia: combinación de legado Excel y SQLite.
- Repositorio: GitHub privado.
- Uso actual: aplicación local por consola.

## 2.7 Idioma funcional

Español como idioma principal del sistema.

El lenguaje debe ser natural y orientado a cocina.

---

# 3. FUENTES DE VERDAD DISPONIBLES EN ESTE ESTADO

## 3.1 ZIP base auditado

Archivo de referencia recibido:

```text
Host AI 6.0 (3).zip
```

Contenido observado:

- 2.615 archivos reales.
- 1.020 archivos Python.
- 169 archivos dentro de `APP`.
- 616 archivos dentro de `SERVICIOS`.
- 677 archivos dentro de `TESTS`.
- 349 archivos Python de tests.
- 223 archivos dentro de `DATOS`.
- 286 archivos dentro de `DOCS`.

Estas cifras describen el ZIP auditado y pueden cambiar al incorporar parches posteriores.

## 3.2 Parches posteriores disponibles

### PILOTO-1.2.1

```text
PILOTO-1.2.1_Humanizacion_Mi_Jornada.zip
```

Archivos incluidos:

```text
APP/consola_jornada_piloto_12.py
SERVICIOS/jornada_piloto_12.py
TESTS/test_piloto_121_humanizacion_jornada.py
CHANGELOG_PILOTO-1.2.1.md
CERTIFICACION_PILOTO-1.2.1.md
```

### PILOTO-1.3

```text
PILOTO-1.3_Produccion_Guiada.zip
```

Archivos incluidos:

```text
SERVICIOS/produccion_guiada_piloto_13.py
APP/consola_produccion_guiada_piloto_13.py
APP/consola_piloto_01.py
TESTS/test_piloto_13_produccion_guiada.py
COMPROBAR_PILOTO_1.3.py
CHANGELOG_PILOTO-1.3.md
CERTIFICACION_PILOTO-1.3.md
COMPROBACION_PILOTO-1.3.txt
```

### PILOTO-1.4

```text
PILOTO-1.4_Produccion_a_Stock.zip
```

Archivos incluidos:

```text
APP/consola_produccion_guiada_piloto_13.py
SERVICIOS/produccion_stock_piloto_14.py
TESTS/test_piloto_14_produccion_stock.py
COMPROBAR_PILOTO_1.4.py
CHANGELOG_PILOTO-1.4.md
CERTIFICACION_PILOTO-1.4.md
COMPROBACION_PILOTO-1.4.txt
```

## 3.3 Documentos DEVKIT creados

Ruta oficial:

```text
DEVKIT/
└── KNOWLEDGE_CORE/
```

Documentos existentes:

```text
01_IDENTIDAD.md
03_REGLAS.md
09_ESTADO_ACTUAL.md
```

## 3.4 Regla para reconstruir la versión actual

La versión de trabajo más reciente no debe reconstruirse usando únicamente el ZIP base.

Orden correcto:

1. Extraer `Host AI 6.0 (3).zip`.
2. Aplicar `PILOTO-1.2.1`.
3. Aplicar `PILOTO-1.3`.
4. Aplicar `PILOTO-1.4`.
5. Incorporar `DEVKIT/KNOWLEDGE_CORE`.
6. Ejecutar los diagnósticos.
7. Confirmar con Git qué archivos cambian.

Cuando exista un nuevo ZIP completo consolidado, ese ZIP deberá sustituir esta secuencia como fuente de verdad.

---

# 4. FILOSOFÍA ACTIVA

## 4.1 Principio central

> Host AI debe adaptarse al cocinero. Nunca el cocinero al programa.

## 4.2 Pregunta obligatoria

Toda decisión debe responder:

> ¿Así trabajaría un jefe de cocina real?

## 4.3 Cambio de enfoque ya acordado

En etapas anteriores se desarrollaban motores y funciones independientes.

El enfoque vigente es:

> Desarrollar flujos operativos completos.

## 4.4 Centro operativo

`Mi Jornada` es el centro de la aplicación.

Todo debe terminar reflejado allí:

- producción;
- eventos;
- compras;
- recepciones;
- stock;
- incidencias;
- tareas;
- bloqueos.

## 4.5 Lenguaje de la aplicación

Los flujos deben empezar por lo que ha sucedido:

- Ha llegado un proveedor.
- He terminado una tarea.
- Falta producto.
- Ha cambiado un evento.
- Quiero saber qué hacer hoy.

No por nombres técnicos de módulos.

## 4.6 Relación IA–motores

- Los motores calculan.
- Los servicios coordinan.
- Los datos conservan.
- La IA interpreta y explica.
- La interfaz guía.

La IA no debe sustituir lógica crítica ni inventar datos operativos.

---

# 5. ESTADO DEL PILOTO

## 5.1 Escala de estados utilizada

Para evitar falsas certificaciones se utilizan estos estados:

### CREADO

Existe el código o documento.

### ENTREGADO

Se ha preparado un paquete para incorporarlo.

### DIAGNOSTICADO

Su script de diagnóstico ha sido ejecutado correctamente.

### VALIDADO MANUALMENTE

El usuario ha recorrido el flujo en su instalación.

### VALIDADO EN COCINA

Se ha usado en una situación real de trabajo.

### CERTIFICADO TÉCNICAMENTE

Tests, diagnóstico, regresión y documentación aportan evidencia suficiente sobre una versión concreta.

### CERRADO

No se prevén cambios salvo bug real o requisito nuevo.

Una misma funcionalidad puede tener varios de estos estados a la vez.

---

## 5.2 PILOTO-0.1 — Estabilización

Objetivo:

- entrada única;
- modo piloto;
- modo desarrollo;
- configuración central;
- inventario;
- auditoría;
- certificación.

Estado documental heredado:

```text
CERTIFICADO / CERRADO
```

Precaución:

Debe verificarse contra el código consolidado antes de una nueva certificación global.

---

## 5.3 PILOTO-1.0 — Recepción inteligente

Objetivo:

- facturas;
- albaranes;
- recepciones;
- lectura;
- relación con artículos;
- vista previa;
- confirmación;
- escritura segura.

Estado documental heredado:

```text
CERTIFICADO
```

Validación real futura necesaria:

- uso repetido con documentos reales;
- recepción parcial;
- incidencias;
- actualización diferida de stock.

---

## 5.4 PILOTO-1.1 — Bandeja de trabajo

Objetivo:

Centralizar:

- producciones;
- recepciones;
- eventos;
- compras;
- stock;
- incidencias;
- tareas manuales.

Estados definidos:

- pendiente;
- en curso;
- aplazada;
- bloqueada;
- terminada;
- cancelada.

Estado documental heredado:

```text
CERTIFICADO
```

Debe conservarse como corazón de pendientes operativos.

---

## 5.5 PILOTO-1.2 — Mi Jornada

Objetivo:

Organizar el día mediante:

- prioridades;
- recomendaciones;
- tiempos;
- trabajo paralelo;
- agrupación de fuentes operativas.

Estado documental heredado:

```text
CERTIFICADO
```

Regla:

`Mi Jornada` no debe transformarse en un módulo técnico o en un simple dashboard de datos.

---

## 5.6 PILOTO-1.2.1 — Humanización de Mi Jornada

Objetivo:

- saludo natural;
- resumen;
- prioridades humanas;
- duraciones legibles;
- eventos interpretados;
- explicaciones;
- cronograma;
- lenguaje de segundo de cocina.

Estado disponible:

```text
CREADO
ENTREGADO
CON TEST Y CERTIFICACIÓN EN EL PARCHE
```

No consta en esta memoria una prueba manual completa documentada por el usuario.

Estado recomendado:

```text
CERTIFICADO TÉCNICAMENTE DE FORMA PROVISIONAL
VALIDACIÓN MANUAL COMPLETA PENDIENTE
```

---

## 5.7 PILOTO-1.3 — Producción guiada

Objetivo:

- seleccionar plan;
- mostrar siguiente tarea;
- explicar prioridad;
- iniciar;
- pausar;
- reanudar;
- finalizar;
- registrar progreso;
- bloquear;
- resolver bloqueo;
- delegar escrituras al motor existente.

Evidencia manual recibida:

```text
PILOTO-1.3 — PRODUCCIÓN GUIADA
Diagnóstico: OK
Planes: 1
Tareas: 2
Siguiente acción: CONTINUAR
Escrituras delegadas al motor existente: SÍ
```

También se visualizó correctamente el plan:

```text
Boda prueba RR1
```

y sus tareas.

Estado:

```text
ENTREGADO
DIAGNOSTICADO
VALIDADO MANUALMENTE
CERTIFICADO TÉCNICAMENTE
```

No consta todavía validación prolongada en una jornada real de cocina.

---

## 5.8 PILOTO-1.4 — Producción → Stock

Objetivo:

- localizar receta;
- escalar consumos;
- validar stock;
- mostrar vista previa;
- descontar materias primas;
- añadir producto terminado;
- finalizar tarea;
- registrar trazabilidad;
- evitar duplicados;
- revertir fallos.

Evidencia manual recibida:

Al cerrar:

```text
Producir / preparar Carrillera de ternera
```

el sistema detectó:

```text
Carrillera de ternera: faltan 4.70448 kg
Demi-glace: faltan 1.9008 L
```

Después permitió registrar incidencia y dejó la tarea:

```text
Bloqueada
```

con motivo:

```text
Stock insuficiente para cerrar la producción
```

La pantalla se replanteó correctamente:

```text
AHORA: Resuelve el bloqueo...
```

Garantías manualmente observadas:

- el cierre normal se detuvo;
- la tarea no se marcó como terminada;
- se registró un bloqueo;
- la planificación priorizó resolverlo.

No existe todavía evidencia manual documentada de:

- cierre con stock suficiente;
- consumos reales aplicados;
- entrada del producto terminado;
- trazabilidad visible;
- protección contra duplicado en instalación del usuario;
- rollback provocado manualmente.

Estado preciso:

```text
CREADO
ENTREGADO
FLUJO DE STOCK INSUFICIENTE VALIDADO MANUALMENTE
CIERRE EXITOSO PENDIENTE DE VALIDACIÓN MANUAL
CERTIFICACIÓN TÉCNICA DEL PARCHE DISPONIBLE
VALIDACIÓN EN COCINA PENDIENTE
```

No debe declararse completamente cerrado hasta probar la ruta de éxito.

---

## 5.9 PILOTO-1.4.1 — Asistente de resolución de bloqueos

Objetivo propuesto:

- clasificar bloqueos;
- explicar causa;
- proponer acciones;
- detectar recepción pendiente;
- revisar stock;
- conservar contexto;
- volver a producción;
- integrarse con Mi Jornada.

Estado real:

```text
PROPUESTO
NO DESARROLLADO
```

Se propusieron archivos como:

```text
MODELOS/bloqueo.py
SERVICIOS/asistente_bloqueos.py
APP/consola_resolver_bloqueo.py
```

Pero no deben considerarse existentes hasta verificar el código.

No se creó un ZIP funcional del 1.4.1.

No existen tests reales aportados para este sprint.

Decisión vigente:

> Pausar este desarrollo hasta establecer el DEVKIT y la memoria viva mínima.

---

# 6. ROADMAP FUNCIONAL VIGENTE

```text
✅ PILOTO-0.1    Estabilización
✅ PILOTO-1.0    Recepción inteligente
✅ PILOTO-1.1    Bandeja de trabajo
✅ PILOTO-1.2    Mi Jornada
🟡 PILOTO-1.2.1 Humanización de Mi Jornada
✅ PILOTO-1.3    Producción guiada
🟡 PILOTO-1.4    Producción → Stock
⬜ PILOTO-1.4.1 Asistente de resolución de bloqueos
⬜ PILOTO-1.5    Recepción → Stock
⬜ PILOTO-1.6    Compras inteligentes
⬜ PILOTO-1.7    Eventos inteligentes
⬜ PILOTO-1.8    Coste real del evento
```

Leyenda:

```text
✅ Evidencia técnica y manual suficiente para continuar
🟡 Existe, pero queda validación pendiente
⬜ Pendiente
```

El roadmap completo se trasladará a `04_ROADMAP.md`.

---

# 7. ROADMAP DEL DEVKIT

## 7.1 DEVKIT-0.1 — Memoria viva

Estado:

```text
EN DESARROLLO
```

### Knowledge Core previsto

```text
01_IDENTIDAD.md
02_ARQUITECTURA.md
03_REGLAS.md
04_ROADMAP.md
05_SPRINTS.md
06_MEMORIA_TECNICA.md
07_MEMORIA_OPERATIVA.md
08_CERTIFICACIONES.md
09_ESTADO_ACTUAL.md
10_PENDIENTES.md
```

### Estado actual

```text
✅ 01_IDENTIDAD.md
⬜ 02_ARQUITECTURA.md
✅ 03_REGLAS.md
⬜ 04_ROADMAP.md
⬜ 05_SPRINTS.md
⬜ 06_MEMORIA_TECNICA.md
⬜ 07_MEMORIA_OPERATIVA.md
⬜ 08_CERTIFICACIONES.md
✅ 09_ESTADO_ACTUAL.md
⬜ 10_PENDIENTES.md
```

## 7.2 DEVKIT-0.2 — Comandos básicos

Pendiente.

Comandos previstos:

```text
host estado
host roadmap
host test
host diagnostico
host certificar
```

No deben implementarse todavía de forma improvisada.

Primero debe definirse:

- interfaz;
- fuentes;
- formato;
- seguridad;
- salida;
- alcance.

## 7.3 DEVKIT-0.3 — Inventario y arquitectura

Pendiente.

Objetivo:

- indexar proyecto;
- identificar módulos;
- detectar dependencias;
- mapear entradas;
- localizar duplicados;
- construir arquitectura viva.

## 7.4 DEVKIT-0.4 — Ejecutor de pruebas

Pendiente.

## 7.5 DEVKIT-0.5 — Certificador

Pendiente.

## 7.6 DEVKIT-0.6 — Actualización automática de memoria

Pendiente.

## 7.7 Integración MCP

Idea futura.

No está diseñada ni implementada.

No debe asumirse que ChatGPT tiene acceso directo al repositorio por MCP.

El flujo actual continúa siendo:

- ZIP completo;
- parches;
- inspección en entorno disponible;
- entrega de archivos.

---

# 8. ARQUITECTURA CONOCIDA

## 8.1 Carpetas principales observadas

```text
APP/
CORE/
SERVICIOS/
TESTS/
DATOS/
DOCS/
```

También existen otras estructuras heredadas o auxiliares que deberán auditarse en `02_ARQUITECTURA.md`.

## 8.2 Responsabilidades esperadas

### APP

Interacción y consolas.

No debe concentrar lógica crítica.

### CORE

Motores deterministas y lógica de negocio central.

### SERVICIOS

Coordinación entre motores, datos e interfaz.

### TESTS

Pruebas unitarias, integración, regresión y diagnósticos.

### DATOS

Persistencia local, configuraciones operativas, JSON, SQLite y otros datos.

### DOCS

Documentación histórica, certificaciones, changelogs y auditorías.

### DEVKIT

Herramientas de desarrollo y memoria viva.

## 8.3 Arquitectura pendiente de verificar

No debe darse por hecho que todos los archivos respetan esta separación.

El proyecto tiene más de mil módulos Python y una historia larga de sprints.

Debe auditarse:

- duplicidad;
- módulos numerados antiguos;
- rutas activas;
- entradas reales;
- servicios superseded;
- imports;
- archivos muertos;
- tests vigentes;
- documentación obsoleta.

---

# 9. ENTRADAS Y FLUJOS PRINCIPALES CONOCIDOS

## 9.1 Entrada principal

Existe un `main.py` único según PILOTO-0.1.

Debe verificarse en el proyecto consolidado.

## 9.2 Menú piloto observado

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

## 9.3 Producción guiada

Ruta observada:

```text
Modo Piloto
→ Producción
→ Seleccionar plan
→ ¿Qué acaba de pasar?
```

Acciones:

```text
Voy a empezar una tarea
He terminado una tarea
Necesito pausar o reanudar
Quiero indicar cuánto llevo
Ha surgido un problema
He resuelto un bloqueo
Actualizar la pantalla
```

Este patrón debe conservarse.

---

# 10. DATOS Y REGLAS DE DOMINIO CRÍTICAS

## 10.1 Artículos

Búsqueda preferida:

1. nombre;
2. parecidos;
3. revisión del usuario;
4. proveedor como segunda vía;
5. código como apoyo.

## 10.2 Prefijos

```text
M.P = Materia Prima
A.P = Aperitivo
```

Regla crítica:

Un `A.P` no debe interpretarse automáticamente como ingrediente base.

Debe tratarse según su ficha como:

- aperitivo;
- elaboración;
- producto compuesto;
- producto terminado o intermedio.

## 10.3 Unidades

Operativas:

- kg;
- L;
- unidades;
- cajas;
- equivalencias registradas.

No deben inventarse conversiones.

## 10.4 Stock

Debe distinguirse:

- stock físico;
- stock registrado;
- stock pendiente de actualizar;
- recepción pendiente;
- consumo previsto;
- movimiento real.

## 10.5 Producción

Reglas conocidas:

- jornada de referencia: 08:00–15:30;
- 7,5 horas activas;
- 0,5 horas de comida;
- tiempos pasivos liberan huecos;
- quien empieza, preferentemente termina;
- multi-día si no cabe;
- recursos: horno, brasa, abatidor y otros;
- checklist final;
- coste activo y pasivo.

## 10.6 Recepción

Flujo real:

1. llega proveedor;
2. descargar;
3. comparar pedido;
4. comprobar;
5. pesar;
6. anotar incidencias;
7. firmar;
8. guardar;
9. archivar;
10. actualizar stock más tarde.

No obligar a stock inmediato.

---

# 11. FUNCIONALIDADES CRÍTICAS QUE NO DEBEN ROMPERSE

## 11.1 Importador de menús I1.3

La línea se considera cerrada.

Incluye:

- MUR;
- resolución;
- validación culinaria;
- interpretación;
- conocimiento gastronómico;
- escritura segura;
- importación;
- auditoría;
- corrección;
- certificación.

No reabrir salvo bug real.

## 11.2 Búsqueda de artículos

Debe conservar:

- nombre primero;
- coincidencias parecidas;
- proveedor después;
- edición por nombre.

## 11.3 Escritura segura

Debe conservar:

- vista previa;
- confirmación;
- backup;
- trazabilidad;
- no duplicidad;
- rollback cuando aplica.

## 11.4 Mi Jornada

Debe seguir siendo el centro.

No convertirla en un listado técnico.

## 11.5 Producción guiada

Debe delegar en motores existentes.

No duplicar `MotorProduccionReal`.

## 11.6 Producción → Stock

Debe evitar:

- doble descuento;
- cierre sin stock;
- estados parciales;
- entrada sin consumo;
- consumo sin trazabilidad.

---

# 12. TESTS Y EVIDENCIAS CONOCIDAS

## 12.1 Históricos relevantes

Se han documentado anteriormente resultados como:

### Inteligencia de compras

```text
Análisis: 16
Recomendaciones: 12
Anomalías: 238
Predicciones: 5
Proveedores comparados: 7
Roturas de stock: 5
Decisiones de pedidos: 5
Cierre: 7/7
```

### IA conversacional

```text
Intención: consulta_stock
Pipeline: analizador_inteligente_stock
Acción: crear_pedido
Cierre: True
```

### Generador de códigos

```text
Artículos: 354
Generados: 354
Duplicados: 0
```

Estos datos son históricos.

Deben reejecutarse antes de utilizarlos como certificación de la versión actual.

## 12.2 PILOTO-1.3

Diagnóstico manual confirmado por el usuario.

## 12.3 PILOTO-1.4

Validación manual confirmada únicamente para la ruta de stock insuficiente.

## 12.4 Estado global de tests

No existe todavía un único comando certificado que ejecute toda la suite de forma fiable y produzca un informe consolidado.

Esto es uno de los objetivos del DEVKIT.

---

# 13. PROBLEMAS ABIERTOS

## 13.1 Validación incompleta del 1.4

Prioridad:

```text
ALTA
```

Falta probar en la instalación real:

- stock suficiente;
- cierre;
- consumos;
- entrada;
- duplicado;
- trazabilidad;
- rollback.

## 13.2 Experiencia de bloqueos

Prioridad:

```text
ALTA
```

El mensaje actual muestra cantidades con demasiados decimales:

```text
4.70448 kg
1.9008 L
```

Debe humanizarse:

```text
4,70 kg
1,90 L
```

Además, el bloqueo debe ofrecer acciones guiadas.

## 13.3 Versión consolidada inexistente

Prioridad:

```text
ALTA
```

Actualmente existe:

- ZIP base;
- parches;
- documentos DEVKIT.

Debe crearse un nuevo ZIP completo o una rama Git que consolide todo.

## 13.4 Memoria viva incompleta

Prioridad:

```text
ALTA
```

Faltan siete documentos del Knowledge Core.

## 13.5 Arquitectura no mapeada completamente

Prioridad:

```text
ALTA
```

Más de 1.000 módulos Python hacen necesario identificar:

- activos;
- duplicados;
- obsoletos;
- entradas;
- dependencias.

## 13.6 Documentación histórica dispersa

Prioridad:

```text
MEDIA
```

Debe clasificarse:

- vigente;
- histórica;
- sustituida;
- certificación;
- diagnóstico.

## 13.7 Certificaciones heterogéneas

Prioridad:

```text
MEDIA
```

No existe todavía un formato único ni vínculo automático con versión Git.

## 13.8 Nomenclatura histórica

Prioridad:

```text
MEDIA
```

Hay numerosos archivos numerados por sprint.

No deben renombrarse masivamente sin auditoría.

---

# 14. RIESGOS ACTUALES

## 14.1 Falsa sensación de certificación

Un ZIP con `CERTIFICACION.md` no demuestra por sí solo que se ejecutó sobre la instalación final.

Mitigación:

- hash o commit;
- logs;
- comando único;
- evidencia;
- prueba manual.

## 14.2 Divergencia entre ZIP base y parches

Mitigación:

- consolidar;
- Git;
- inventario de archivos;
- manifest.

## 14.3 Duplicidad de lógica

El tamaño y la historia del proyecto aumentan este riesgo.

Mitigación:

- `02_ARQUITECTURA.md`;
- búsqueda previa;
- auditoría;
- mapa de motores.

## 14.4 Datos de prueba mezclados con datos reales

Mitigación:

- entornos;
- copias;
- rutas temporales;
- solo lectura;
- fixtures.

## 14.5 Automatización prematura del DEVKIT

Crear comandos antes de definir fuentes puede automatizar errores.

Mitigación:

- terminar memoria mínima;
- diseñar contratos;
- probar sobre copia.

## 14.6 Dependencia del chat

Mitigación activa:

- Knowledge Core;
- estado;
- decisiones;
- arquitectura;
- roadmap.

---

# 15. DEUDA TÉCNICA CONOCIDA

## 15.1 Inventario de módulos

Pendiente de clasificar.

## 15.2 Tests consolidados

Pendiente crear un runner estable.

## 15.3 Versionado de datos

Pendiente formalizar migraciones.

## 15.4 Contratos entre servicios

Pendiente documentar modelos y entradas/salidas.

## 15.5 Logs estructurados

Pendiente comprobar cobertura real.

## 15.6 Manejo centralizado de errores

Pendiente auditar.

## 15.7 Configuración

Pendiente verificar si todos los valores están centralizados.

## 15.8 Archivos antiguos

Pendiente marcar como:

- vigente;
- legado;
- sustituido;
- archivo histórico.

---

# 16. DECISIONES YA TOMADAS

## D-001

Host AI no es un ERP tradicional.

## D-002

Host AI es un segundo de cocina digital.

## D-003

Mi Jornada es el centro operativo.

## D-004

Los flujos empiezan por “qué acaba de pasar”.

## D-005

La IA es interfaz y asistencia; los motores conservan autoridad.

## D-006

No se duplica lógica.

## D-007

No se toca lo certificado sin motivo real.

## D-008

La búsqueda de artículos prioriza nombre.

## D-009

Proveedor es segunda vía.

## D-010

`M.P` y `A.P` tienen significado operativo obligatorio.

## D-011

No se obliga a actualizar stock al recibir mercancía.

## D-012

La producción debe distinguir tiempos activos y pasivos.

## D-013

Quien empieza una elaboración, preferentemente la termina.

## D-014

Los sprints deben incluir código, tests, diagnóstico, changelog y certificación.

## D-015

El proyecto debe tener una memoria viva dentro del repositorio.

## D-016

Antes de continuar el 1.4.1 se construye el DEVKIT mínimo.

---

# 17. LO QUE NO DEBE HACER EL SIGUIENTE DESARROLLADOR

No debe:

- empezar Host AI desde cero;
- rediseñar toda la arquitectura sin auditoría;
- crear otro motor de stock;
- crear otro motor de producción;
- reabrir I1.3 sin bug;
- considerar 1.4.1 implementado;
- declarar 1.4 completamente validado;
- obligar a stock inmediato;
- interpretar `A.P` como materia prima;
- usar proveedor como búsqueda principal;
- modificar datos reales durante diagnósticos;
- confiar únicamente en documentación;
- generar una certificación sin ejecutar;
- hacer refactor masivo mientras desarrolla una función;
- crear comandos DEVKIT sin contrato;
- asumir acceso MCP inexistente;
- depender del contexto de un chat.

---

# 18. INSTRUCCIONES PARA UN NUEVO CHAT

Un nuevo chat debe actuar así:

## Paso 1

Leer:

```text
01_IDENTIDAD.md
03_REGLAS.md
09_ESTADO_ACTUAL.md
```

## Paso 2

Pedir el ZIP completo consolidado más reciente.

Si no existe, pedir:

- ZIP base;
- parches posteriores;
- carpeta DEVKIT.

## Paso 3

Auditar el árbol real.

## Paso 4

Comparar el código con este estado.

## Paso 5

Informar diferencias.

## Paso 6

No desarrollar hasta identificar:

- fuente de verdad;
- sprint;
- archivos;
- tests;
- riesgos.

## Paso 7

Continuar el sprint activo, no inventar otro roadmap.

Sprint activo actual:

```text
DEVKIT-0.1 — Memoria viva
```

Siguiente documento:

```text
02_ARQUITECTURA.md
```

---

# 19. PROCEDIMIENTO RECOMENDADO DE TRABAJO

## 19.1 Preparar rama o copia

Ejemplo:

```text
feature/devkit-0.1
```

## 19.2 Consolidar versión

Aplicar parches en orden.

## 19.3 Ejecutar smoke tests

- arranque;
- modo piloto;
- Mi Jornada;
- Producción;
- diagnóstico 1.3;
- diagnóstico 1.4.

## 19.4 Añadir DEVKIT

Copiar:

```text
DEVKIT/KNOWLEDGE_CORE/
```

## 19.5 Crear arquitectura

Auditar:

- árbol;
- entradas;
- motores;
- servicios;
- persistencia;
- tests;
- documentación.

## 19.6 Commit

Mensaje sugerido:

```text
DEVKIT-0.1: add project identity, rules and current state
```

---

# 20. CRITERIO PARA CERRAR DEVKIT-0.1

DEVKIT-0.1 podrá cerrarse cuando existan:

```text
01_IDENTIDAD.md
02_ARQUITECTURA.md
03_REGLAS.md
04_ROADMAP.md
05_SPRINTS.md
06_MEMORIA_TECNICA.md
07_MEMORIA_OPERATIVA.md
08_CERTIFICACIONES.md
09_ESTADO_ACTUAL.md
10_PENDIENTES.md
```

Y además:

- estén revisados;
- no se contradigan;
- distingan hechos de planes;
- indiquen fecha;
- estén dentro del repositorio;
- exista una guía de actualización;
- haya un índice principal;
- se haya realizado commit.

---

# 21. CRITERIO PARA RETOMAR PILOTO-1.4.1

Antes de retomar:

1. cerrar DEVKIT-0.1;
2. crear versión consolidada;
3. validar ruta exitosa del 1.4;
4. auditar bloqueos existentes;
5. localizar modelos similares;
6. comprobar recepción y stock;
7. definir contrato común.

Después, desarrollar por orden:

1. modelo de bloqueo;
2. servicio clasificador;
3. tests;
4. diagnóstico;
5. integración con producción;
6. consola;
7. integración con Mi Jornada;
8. integración con recepción;
9. regresión;
10. certificación.

---

# 22. SIGUIENTES PASOS INMEDIATOS

## Paso inmediato 1

Copiar este documento en:

```text
DEVKIT/KNOWLEDGE_CORE/09_ESTADO_ACTUAL.md
```

## Paso inmediato 2

Crear un ZIP completo consolidado de la versión real instalada.

## Paso inmediato 3

Ejecutar:

```text
python COMPROBAR_PILOTO_1.3.py
python COMPROBAR_PILOTO_1.4.py
```

Guardar las salidas.

## Paso inmediato 4

Desarrollar:

```text
02_ARQUITECTURA.md
```

## Paso inmediato 5

Crear:

```text
04_ROADMAP.md
```

## Paso inmediato 6

Actualizar este documento si la auditoría descubre diferencias.

---

# 23. PANEL DE CONTROL

```text
PROYECTO: Host AI
VERSIÓN BASE: 6.0
FASE: Piloto privado + construcción DEVKIT
CENTRO OPERATIVO: Mi Jornada

SPRINT FUNCIONAL MÁS AVANZADO:
PILOTO-1.4 — Producción → Stock

VALIDACIÓN 1.4:
Parcial; ruta de stock insuficiente confirmada

SPRINT FUNCIONAL PENDIENTE:
PILOTO-1.4.1 — Asistente de bloqueos

SPRINT ACTIVO:
DEVKIT-0.1 — Memoria viva

DOCUMENTOS KNOWLEDGE CORE:
3/10 creados

SIGUIENTE DOCUMENTO:
02_ARQUITECTURA.md

RIESGO PRINCIPAL:
No existe todavía una versión completa consolidada y trazada

PRIORIDAD:
Consolidar, documentar y auditar antes de añadir lógica
```

---

# 24. SEMÁFORO ACTUAL

## Verde

- Identidad definida.
- Reglas definidas.
- Mi Jornada como centro.
- Producción guiada validada.
- Bloqueo por stock observado.
- Knowledge Core iniciado.

## Amarillo

- PILOTO-1.2.1 pendiente de validación manual completa.
- PILOTO-1.4 pendiente de ruta exitosa.
- Certificaciones históricas por vincular a versión.
- Arquitectura por mapear.
- Tests por consolidar.
- Documentación por clasificar.

## Rojo

- No existe un único paquete consolidado confirmado.
- PILOTO-1.4.1 no está desarrollado.
- No existe comando global de tests.
- No existe actualización automática de memoria.
- No existe MCP operativo.

---

# 25. DEFINICIÓN DEL ESTADO ACTUAL EN UNA FRASE

> Host AI dispone de una base funcional muy amplia y ha alcanzado el flujo Producción → Stock dentro del piloto; ahora se ha pausado la expansión funcional para construir una memoria viva, consolidar la versión real y profesionalizar el proceso de desarrollo antes de continuar con la resolución inteligente de bloqueos.

---

# 26. CONTROL DE CAMBIOS DE ESTE DOCUMENTO

## Versión 1.0 — 13 de julio de 2026

Creación inicial.

Incluye:

- estado funcional;
- estado DEVKIT;
- evidencia manual;
- roadmap;
- riesgos;
- deuda;
- decisiones;
- instrucciones de continuidad;
- panel de control.

Próxima actualización obligatoria:

- al completar `02_ARQUITECTURA.md`;
- al consolidar el ZIP;
- al validar completamente PILOTO-1.4;
- al cerrar DEVKIT-0.1;
- al abrir PILOTO-1.4.1.

---

# 26.1 ACTUALIZACIÓN RESERVAS R1 — 20 de agosto de 2026

Reservas R1 incorpora modelo canónico, repositorio JSON aislado por `base_dir`, servicio READ y API GET.
No incluye frontend, Chat, UI_ACTION ni WRITE público. R2, R3 y R4 permanecen pendientes.
La persistencia real `DATOS/db/reservas.json` no se crea ni se puebla durante la implementación.
Validación técnica focal: 20 tests R1 y 28 regresiones API/Eventos correctos; sin certificación ni validación manual.
Reservas R2 añade frontend READ, navegación, filtros y detalle. Chat y WRITE siguen pendientes.
Validación R2: 15 tests frontend focales/regresión, typecheck y build correctos; validación manual pendiente.

Reservas R3 integra el dominio con el General Agent mediante `consultar_reservas` READ y las UI_ACTION cerradas `abrir_reservas`/`abrir_reserva`. Mantiene contexto `RESERVA`, admite follow-up y candidatos ambiguos, y no publica ninguna capacidad WRITE de Reservas. La navegación de Chat queda limitada a `/reservas` y `/reservas/RES-...` canónico.
Evidencia R3 del 20 de agosto de 2026: 73 tests backend focales/regresión, 56 tests frontend focales/regresión, typecheck y build correctos; validación manual pendiente. No se escribieron datos reales.

Corrección runtime R3 del 20 de agosto de 2026: la selección inválida de una tool conocida ya no se confunde con una tool desconocida ni provoca fallback terminal inmediato. El agente recibe el motivo de validación y puede reintentar con `consultar_reservas`; `abrir_reserva` exige patrón canónico también en policy. Evidencia local con provider simulado: 39 tests focales correctos. La repetición manual con OpenAI real queda pendiente.

Reservas R4 incorpora WRITE seguro separado del READ para crear, modificar, confirmar, cancelar y marcar no-show. Toda operación sigue preview con token opaco y confirmación humana explícita; aplica control stale, replay idempotente, máquina de estados centralizada y auditoría sin observaciones ni PII. El estado inicial por defecto es `PENDIENTE`; `CONFIRMADA` solo se admite si se solicita explícitamente. Frontend y General Agent reutilizan el mismo servicio y no escriben directamente.
Evidencia R4 del 20 de agosto de 2026: 72 tests backend focales/regresión, 57 tests frontend focales/regresión, typecheck, build y compilación Python correctos. No se creó `DATOS/db/reservas.json` ni auditoría real. Estado: implementado y probado técnicamente; validación manual y certificación pendientes.

---

Extensión R4 del 20 de agosto de 2026: el General Agent publica `completar_reserva` como PREVIEW para la transición canónica `CONFIRMADA → COMPLETADA`. Chat expone acciones estructuradas cerradas `APPLY_PENDING_RESERVATION` y `DISCARD_PENDING_RESERVATION`; el navegador no recibe ni construye token, reserva u operación, y el backend conserva la autoridad sobre sesión, expiración, stale e idempotencia. La confirmación textual sigue disponible. Evidencia focal: 73 tests backend y 55 frontend correctos, además de typecheck y build; validación manual pendiente.

---

UX contextual R4 del 20 de agosto de 2026: Chat publica acciones estructuradas según el estado real de la reserva activa. `PENDIENTE` ofrece confirmar, modificar, cancelar y abrir; `CONFIRMADA` ofrece modificar, cancelar, no-show, completar y abrir; los estados terminales solo permiten abrir. Cada transición contextual prepara un PREVIEW y mantiene separada la confirmación humana. Los botones llevan un contexto opaco rotatorio ligado al mensaje, mientras el backend resuelve y revalida sesión, reserva y estado; no se exponen IDs operativos, tokens ni payload WRITE. El texto libre continúa soportado como fallback y los previews usan una respuesta natural sin instrucciones tipo consola. Evidencia focal: 86 tests backend y 67 frontend correctos, typecheck y build correctos. Validación manual de esta extensión UX pendiente.

---

Consistencia Receta/Escandallo en Chat del 20 de agosto de 2026: la elaboración/receta continúa siendo la entidad culinaria canónica y el escandallo una asociación opcional. La lectura conversacional ya localiza recetas `SIN_ESCANDALLO`; `OPEN_VIEW ELABORACION/RECETA` puede abrirlas, mientras `ELABORACION/ESCANDALLO` se rechaza si no existe estructura económica. La sesión conserva `tipo=RECETA` al abrir la ficha culinaria. Evidencia local: 45 tests Chat/UI_ACTION y 20 tests de Biblioteca correctos, compilación Python y `git diff --check` correctos. Sin cambios frontend ni datos reales; validación manual con OpenAI real pendiente y sin certificación.

Fix focal de navegación del 20 de agosto de 2026: una petición explícita de vista `ESCANDALLO` ya no admite `RECETA` como fallback. Si la receta existe pero `tiene_escandallo=false`, el resultado estructurado es `ESCANDALLO_NO_ENCONTRADO`, no se emite `OPEN_VIEW`, no cambia la entidad activa y la respuesta final se limita a informar que no hay escandallo. El catálogo actual del General Agent no publica PREVIEW, CONFIRM ni WRITE para crear/preparar escandallos, por lo que tampoco se ofrece esa operación. Evidencia local: 47 tests focales correctos, incluida regresión adversarial; compilación Python y `git diff --check` correctos. Validación manual con OpenAI real pendiente y sin certificación.

Acciones económicas contextuales del 20 de agosto de 2026: el detalle de coste incompleto conserva incidencias estructuradas y Chat ofrece, solo cuando existe un artículo canónico, `RESOLVE_MISSING_PRICE` o `RESOLVE_MISSING_CONVERSION`. Ambas acciones usan contexto opaco ligado a sesión, revalidan el artículo en servidor y abren su ficha canónica mediante `OPEN_VIEW ARTICULO/FICHA`. No aceptan IDs ni rutas aportados por el navegador y no realizan WRITE. La autoridad de precio, unidad y formato continúa en la ficha maestra del artículo; el General Agent no publica hoy PREVIEW/CONFIRM/WRITE para corregirlos desde Chat. Evidencia local: 2 tests backend focales y 17 tests frontend correctos, además de typecheck, build, compilación Python y `git diff --check`. La regresión backend amplia quedó limitada por permisos del directorio temporal de pytest; validación manual y certificación pendientes. No se escribieron datos reales ni se llamó a OpenAI real.

Fix focal posterior del 20 de agosto de 2026: el materializador de acciones económicas normaliza la taxonomía real del motor (`CONVERSION_INEXISTENTE`, `UNIDAD_INCOMPATIBLE` y `UNIDADES_INCOMPATIBLES`) a `CONVERSION_NO_DISPONIBLE`, y `PRODUCTO_SIN_PRECIO` a `SIN_PRECIO`, antes de decidir la acción cerrada. El fixture de APERITIVO CALÇOTADA con `ART000285` genera `RESOLVE_MISSING_CONVERSION` y el click abre exclusivamente `OPEN_VIEW ARTICULO/FICHA ART000285`, sin WRITE. Evidencia focal: 3 tests backend y 17 frontend correctos, typecheck, build y compilación Python correctos. Prueba manual con OpenAI y UI reales pendiente; sin certificación.

Edición segura de artículos desde Chat del 20 de agosto de 2026: `ConfirmacionFormatoArticuloService` amplía su autoridad existente con previews parciales cerrados para precio y relación de formato/conversión, confirmación humana, expiración, fingerprint stale, aislamiento por actor/tenant/sesión, replay idempotente, compensación y auditoría mínima. Chat captura únicamente el importe o factor que falta; conserva artículo y unidades en servidor, no expone el token y ofrece `APPLY_PENDING_ARTICLE_CHANGE`/`DISCARD_PENDING_ARTICLE_CHANGE`. El formato comercial se persiste mediante `unidad_compra`, `cantidad_formato`, `unidad_formato` y `unidad_base`; las relaciones físicas explícitas se conservan estructuradas en `conversion_unidades`. Solo se ofrecen acciones con scope `articulos:preview`; confirmar exige `articulos:write`. No se recalculan escandallos automáticamente ni se afirma que queden completos. Evidencia focal: 60 tests backend y 17 frontend correctos, typecheck, build y compilación Python correctos. Todos los WRITE de prueba usaron fixtures aislados; prueba manual y certificación pendientes.

Fix semántico de formato del 20 de agosto de 2026: la captura distingue `FORMATO_ENVASE` de `CONVERSION_FISICA`. Expresiones como “paquete de 200 unidades” se representan como precio del paquete más `unidad_compra=paquete`, `cantidad_formato=200`, `unidad_formato=u` y `unidad_base=u`; el coste unitario se deriva con Decimal y no se crea ninguna relación `u→kg`. Si falta el tipo de envase se solicita esa única aclaración. Las relaciones físicas explícitas, como “1 unidad pesa 0,005 kg”, conservan su flujo separado. El caso fixture `ART000285`, precio 6,89 €, deriva exactamente 0,03445 €/u y no declara resuelto el escandallo sin recalcular. Evidencia focal acumulada: 62 tests backend correctos; todos los WRITE se ejecutaron sobre fixtures aislados. Prueba manual pendiente y sin certificación.

Preview auditable de cambios de artículo en Chat del 20 de agosto de 2026: el backend publica el contrato cerrado `ARTICLE_CHANGE_PREVIEW_V1` con identidad del artículo, operación, valores antes/después, valores relevantes sin cambios, cálculos derivados y aviso explícito de que aún no se han modificado datos. El token, actor, tenant, scopes y propuesta interna permanecen exclusivamente en servidor. La web valida el esquema y representa el DTO sin recalcular precios, IVA ni conversiones; un preview desconocido o inválido no se muestra. Evidencia focal: 62 tests backend y 18 frontend correctos, typecheck, build, compilación Python y `git diff --check` correctos. Los WRITE de tests usaron fixtures aislados; no se llamó a OpenAI real. Validación manual y certificación pendientes.

Grounding de nombres aislados de elaboración del 21 de agosto de 2026: un mensaje nominal breve de dos a ocho palabras que coincide de forma única con la Biblioteca canónica ya no acepta un `FINAL_RESPONSE` creativo sin datos internos. El runtime ejecuta la resolución READ autorizada, activa la receta y responde con identidad canónica; si hay varias coincidencias pide elección y, si no existe ninguna, conserva el comportamiento general. La selección mantiene candidatos e incidencias económicas inmediatas para el siguiente turno. Evidencia focal: 57 tests de agente/Chat/escandallos/UI_ACTION y 3 tests específicos de Biblioteca correctos, compilación Python y `git diff --check` correctos. La regresión culinaria ampliada conserva dos expectativas históricas incompatibles con las capacidades PREVIEW/CONFIRM de artículos ya publicadas; no pertenecen a este fix. Sin OpenAI ni datos reales; prueba manual y certificación pendientes.

Normalización focal de detalle económico del 21 de agosto de 2026: cuando el mensaje actual pregunta causalmente por un coste incompleto, `consultar_escandallos` con `consulta=detalle` y una receta concreta se transforma antes de policy/executor en `agregacion=DETAIL_COSTE_INCOMPLETO`. El DTO económico materializa `motivos[]` como `economic_incidents`, permitiendo las acciones contextuales de precio o conversión; las peticiones explícitas de ingredientes, receta completa, ficha o procedimiento conservan el detalle culinario general. El caso reconstruido `9bd05421-e89d-4621-a6a7-662bff3fd859` con `REC-EXCEL-6B4B251F8E` y `ART000285` genera `RESOLVE_MISSING_CONVERSION`. Evidencia focal: 68 tests correctos, compilación Python y `git diff --check` correctos. Sin frontend, OpenAI ni datos reales; validación manual y certificación pendientes.

Conflicto entre precio canónico y precio aportado al configurar formato del 21 de agosto de 2026: la captura distingue el número de unidades de un precio explícito asociado a `precio` o `€` y lo compara con Decimal. Si difiere del precio maestro, conserva formato, precio actual y precio aportado en un pending de sesión con caducidad, no prepara preview aplicable y solicita elegir. Mantener genera el preview de formato con precio sin cambios; cambiar genera un único `UPDATE_FORMAT` combinado con precio y formato, cuyo unitario es solo derivado. La confirmación reutiliza la actualización transaccional y compensación existentes. No se calcula IVA ni se extrae precio desde el nombre del artículo. Evidencia: 15 tests focales, 70 tests backend de regresión y 18 frontend correctos; compilación Python y `git diff --check` correctos. Todos los WRITE usaron fixtures aislados. Sin OpenAI ni datos reales; validación manual y certificación pendientes.

---

Autorización interna local de artículos del 21 de agosto de 2026: el fallback de desarrollo, aplicable exclusivamente cuando las cuatro variables `HOST_AI_INTERNAL_*` están completamente ausentes, incorpora `articulos:write` junto a los scopes locales ya existentes. Cualquier configuración presente pero parcial, incluso solo roles o una variable vacía, impide el fallback y conserva el resultado no autorizado. El navegador no aporta scopes y preview, confirmación, aislamiento de sesión, stale y replay mantienen sus validaciones. Evidencia focal y de regresión: 129 tests backend y 18 frontend correctos; todos los WRITE usaron fixtures aislados. Sin OpenAI ni datos reales; validación manual y certificación pendientes.

---

Comprobación económica post-WRITE de artículo del 21 de agosto de 2026: la tool histórica `recalcular_escandallo` continúa deshabilitada porque es una WRITE sobre `biblioteca_escandallos_601.json`, con timestamps, versión e historial, y no corresponde a la proyección canónica consultada por Chat. Tras confirmar una corrección de artículo asociada a una incidencia, Chat ofrece `CHECK_ESCANDALLO_COST` con contexto opaco de sesión. La acción reutiliza `DETAIL_COSTE_INCOMPLETO` y el motor económico canónico en modo READ/PURE_CALC, refresca estado, costes e incidencias de sesión y elimina causas resueltas sin persistir escandallos. El fixture equivalente a la conversión resuelta pasa a `DISPONIBLE`, coste total y por ración `0.24115`, sin modificar el escandallo canónico. Evidencia: 88 tests backend y 19 frontend correctos; replay y payload frontend protegidos. Sin OpenAI ni datos reales; validación manual y certificación pendientes.

---

Corrección de respuesta económica completa del 21 de agosto de 2026: ante `DETAIL_COSTE_INCOMPLETO`, la respuesta grounded prioriza ahora `coste_completo=true` o `estado_coste=DISPONIBLE` antes de evaluar `motivos`. Un resultado completo sin incidencias informa coste disponible y presenta `coste_total` y `coste_por_racion`; `PARCIAL` con causas, `PARCIAL` sin causas y `SIN_ESCANDALLO` conservan sus respuestas anteriores. El DTO real reconstruido para `REC-EXCEL-6B4B251F8E` produce “El coste está completo y disponible” con `5,59435 €` total y por ración. Sin cambios en motor, cálculo, artículo ni datos reales; validación con provider simulado correcta y repetición manual con OpenAI pendiente.

---

Cierre UX del ciclo económico post-artículo del 21 de agosto de 2026: después de un WRITE originado por una incidencia con receta identificada, Chat conserva en servidor receta, artículo, incidencia, sesión y timestamp, y publica únicamente `CHECK_ESCANDALLO_COST`, contexto opaco y etiqueta. El click relee el estado actual y ejecuta cálculo canónico puro; `DISPONIBLE` muestra coste total y por ración sin acciones, `PARCIAL` reemplaza incidencias antiguas por causas actuales y vuelve a materializar reparaciones válidas, y `SIN_ESCANDALLO` usa la respuesta mínima. Una edición genérica no ofrece la acción; sesión ajena, replay y doble click quedan protegidos. Se mantiene el botón explícito y no se implementa auto-check. Evidencia: 91 tests backend y 19 frontend correctos. Sin WRITE de escandallo, OpenAI ni datos reales; prueba manual UI pendiente.

---

## 26.1 Modelo económico canónico de artículo (21 de agosto de 2026)

La autoridad económica queda definida así: `precio` es el precio de una unidad de compra y conserva `precio_incluye_iva`; `unidad_compra` identifica el envase o unidad adquirida; `cantidad_formato` y `unidad_formato` describen exclusivamente el contenido de ese envase; `unidad_base` es la unidad de consumo y coste. El precio unitario de contenido es derivado y no se persiste como segundo precio.

Las relaciones físicas explícitas que no son un formato comercial se conservan en `conversion_unidades` como registros `CONVERSION_FISICA` con cantidad y unidad de origen/destino. `articulo_economico_canonico.py` es la autoridad compartida para alias, aritmética Decimal, conversiones métricas, conversiones físicas bidireccionales y taxonomía pública de incidencias. El motor económico consume esa capa; Chat solo captura y normaliza la expresión y el frontend no calcula.

Compatibilidad: no se migran datos automáticamente. La lectura admite ausencia, JSON estructurado y JSON serializado; los campos comerciales existentes mantienen su semántica. Auditoría de solo lectura: 359 artículos, 5 con datos de formato, ninguno con conversión explícita informada y 2 formatos incompletos que deben revisarse en una migración futura, no corregirse por inferencia. La validación técnica y manual completa se registra en la entrega del bloque; no se han modificado datos reales.

## 26.2 Navegación al escandallo tras comprobación económica (21 de agosto de 2026)

`CHECK_ESCANDALLO_COST` ofrece, para resultados `DISPONIBLE` o `PARCIAL`, la navegación canónica `OPEN_VIEW / ELABORACION / ESCANDALLO` en modo `OFFER`. El identificador procede exclusivamente del contexto económico server-side consumido por la comprobación. React muestra `Ver escandallo` y navega internamente a la ficha existente con la pestaña de escandallo; no ejecuta otro POST ni adquiere permisos WRITE. `SIN_ESCANDALLO` no ofrece destino. Prueba manual pendiente.

## 26.3 Coherencia económica y rendimiento físico (21 de agosto de 2026)

El estado económico y el rendimiento físico son indicadores independientes: un coste puede ser `DISPONIBLE` aunque la proyección física sea `PARCIAL`. El calculador físico reutiliza ahora la autoridad canónica de conversiones explícitas de artículo y no deriva equivalencias desde formatos comerciales. En `REC-EXCEL-CAF1B25D3D`, `ART000230` aporta correctamente `1 u = 0,050 kg`; permanece excluido únicamente `ART000173`, cuyo formato `paquete = 6 u` no demuestra masa física. La ficha distingue expresamente ambos estados. Sin migración ni escritura sobre datos reales; validación manual pendiente.

---

## 26.4 Pipeline híbrido de importaciones con IA opt-in (28 de agosto de 2026)

El importador conserva el parser determinista para perfiles conocidos y ofrece análisis documental IA únicamente por acción explícita cuando la lectura inicial clasifica el documento como complejo. `AIImportDocumentInterpreter` reutiliza `HostAIEngine`, recibe regiones estructurales acotadas y solo acepta `hostai.import.package 0.1`; después se ejecutan el adaptador, matching canónico, revisión, PREVIEW y CONFIRM existentes.

Las sesiones de ANALYZE/PREVIEW del servicio web son ahora efímeras en memoria y ya no crean `DATOS/db/biblioteca_importaciones_web.json`. La política READ del importador evita también la inicialización eager de directorios y repositorios JSON: sobre una base totalmente vacía, ANALYZE básico, ANALYZE con engine fake y PREVIEW producen delta de filesystem vacío. Los repositorios existentes conservan sus bytes. CONFIRM mantiene la inicialización y escritura persistente normal.

Validación local sin OpenAI: 84 pruebas backend y 19 frontend correctas; incluye schema, salidas inseguras, TAPA, MENU, duplicados, variantes, ambigüedad, matching de artículos/recetas/legacy, opt-in, fallback y ausencia de escritura ante confirmación inválida. Prueba productiva manual pendiente.

---

# 27. ESTATUS OFICIAL

Este documento es la fotografía oficial del estado del proyecto en la fecha indicada.

No debe modificarse para hacer que el proyecto parezca más avanzado.

Debe reflejar:

- hechos;
- evidencias;
- dudas;
- límites;
- pendientes.

Ruta oficial:

```text
DEVKIT/
└── KNOWLEDGE_CORE/
    └── 09_ESTADO_ACTUAL.md
```

Cualquier nuevo chat debe pedir una actualización si la fecha o el código disponible son posteriores a este documento.

---

## Actualización — Fase 1 Importación Inteligente (31 de agosto de 2026)

La Fase 1 alcanza certificación técnica sobre la rama `feature/compras-web`, base `af3642d2`, con fixtures y repositorios temporales. Quedan diferenciados el pipeline oficial, el fallback sin IA, la deduplicación medida, la revisión humana, la confirmación segura y la procedencia. Evidencia: `DEVKIT/CERTIFICACION_TECNICA_FASE1_IMPORTACION.md`.

Estado preciso: `CERTIFICADA TÉCNICAMENTE + VALIDACIÓN MANUAL EN CURSO`.

La primera validación real originó correcciones de menús, exclusión A.P por sesión, relaciones proveedor y claridad de acciones. Único siguiente paso: repetir el mismo Excel y comparar resultados antes/después. No iniciar Fase 1.5.

---

## Actualizacion - cierre tecnico Fase 1 (1 de septiembre de 2026)

Estado preciso: `FASE 1 - LISTA PARA CIERRE FORMAL`. El Excel real fue reanalizado sin IA y sin escritura sobre un repositorio temporal limpio. La regresion final acredita 122 pruebas backend y 31 frontend, con typecheck correcto. Los contenedores de menu ya no se proyectan como recetas; las fichas `M.P` conservan autoridad de receta; plantillas y documentos multicolumna quedan documentales o pendientes explicitos. El usuario conserva la autoridad para cerrar y realizar el commit. Fase 1.5 no iniciada.

## Actualizacion - completado masivo de recetas (1 de septiembre de 2026)

Se corrigio el falso HTTP 500 del batch, la frontera de `recipe_ids` y el contador contextual de importacion. Sobre la copia temporal Boronat, 30 de las 46 recetas disponian de identidad canonica utilizable: la UI muestra 30 y el batch recibe exactamente esos 30 IDs, sin recetas ajenas. `start`, `summary` y cancelacion no invocan IA ni escriben datos. Evidencia: 126 pruebas backend, 33 frontend, typecheck y diff check correctos. Estado: `LISTA PARA VALIDACION HUMANA FINAL DE FASE 1`; cierre formal, commit y push pendientes del usuario. Fase 1.5 no iniciada.

## Actualizacion - tolerancia a timeout y propuestas criticas (1 de septiembre de 2026)

El completado masivo conserva los exitos y continua la cola cuando una receta falla por provider. Expone `PENDIENTE`, `CON_PROPUESTAS`, `NECESITA_USUARIO`, `ERROR_PROVIDER` y `YA_COMPLETA`, con contadores de exitosas, fallidas, pendientes y propuestas; admite retry unitario/global con limite y backoff. La seleccion masiva solo admite descripcion, elaboracion y observaciones filtradas. Alergenos, vida util, conservacion, temperaturas de seguridad, HACCP, tiempos y rendimiento quedan en validacion individual; el contenido critico embebido en texto libre se bloquea para revision.

Evidencia: 129 pruebas backend de Fase 1 y 268 frontend correctas, mas typecheck y diff check. IA exclusivamente fake/mock; cero confirmaciones y cero escrituras sobre datos reales. Estado: `LISTA PARA REPETIR VALIDACION HUMANA FINAL DE FASE 1`; Fase 1.5, commit y push no iniciados.

## Actualización - completado externo provider-agnostic (1 de septiembre de 2026)

Biblioteca dispone ahora de dos fuentes compatibles de propuestas: IA integrada de Host AI y XLSX externo `HOSTAI_RECIPE_COMPLETION_PACKAGE 0.1`. El nuevo adaptador exporta únicamente IDs canónicos contextuales incompletos y reimporta como propuesta, con fingerprint, validación por fila/campo, rechazo de fórmulas y límites de seguridad. No escribe: delega la política de campos, preview, autorización, confirmación, idempotencia, procedencia y lectura posterior en los servicios existentes.

La validación real aislada de Boronat reprodujo 21 hojas, 1029 filas, 46 recetas, 30 canónicas aptas, 316 artículos efectivos, 300 reutilizados, 16 en revisión, 10 menús y 36 A.P excluidos solo de la sesión. El batch controlado continuó después de un timeout, resolvió el retry, conservó cancelación y separó 30 campos seguros, 30 críticos individuales y 30 textos críticos bloqueados. El flujo externo exportó 30, reimportó una propuesta sintética y generó preview sin confirmar ni escribir dominio. Evidencia: 142 pruebas backend relevantes, 270 frontend completas y typecheck correctos; cero llamadas IA reales y coste cero.

Estado preciso: `LISTA PARA REPETIR VALIDACION HUMANA FINAL DE FASE 1`. La Fase 1 no se declara cerrada; validación humana final, commit y push siguen pendientes. Fase 1.5 no iniciada.

## Actualización - corrección del round-trip XLSX físico (1 de septiembre de 2026)

La reimportación externa ya no depende de que el editor conserve la dimensión calculada de `RECETAS`. La validación expone simultáneamente filas/campos seguros y filas/campos críticos para revisión, mantiene ambos grupos de una receta mixta en el batch y devuelve traza por campo junto al nombre, tamaño y SHA-256 del archivo procesado. La UI identifica de forma explícita una plantilla sin valores `*_propuesto`.

Sobre copia temporal, el XLSX real completado de 30 recetas produjo 30 filas con propuestas, 30 útiles, 30 con revisión, 0 rechazadas, 83 campos seguros, 257 críticos individuales, 29 descartados y 7 textos bloqueados; el batch alcanzó 30/30 con 340 propuestas. La plantilla física vacía disponible reprodujo exactamente 30 recibidas, cero propuestas y batch 0/0. Evidencia: 153 pruebas backend de Fase 1 y 271 frontend completas, además de typecheck; sin IA real, confirmación ni escritura en `DATOS`.

Estado preciso: `LISTA PARA REPETIR ROUND-TRIP XLSX REAL`. La validación humana debe repetirse usando el archivo completado que la pantalla identificará por nombre y huella. Fase 1.5, commit y push no iniciados.

## Actualización - selección masiva a preview en UI (1 de septiembre de 2026)

`/seleccion` conserva su contrato sin escritura y devuelve `preview=null` porque toda selección invalida el preview anterior. El bloqueo estaba en la orquestación React: guardaba la selección pero no invocaba `/preview`, mantenía los botones originales y solo ofrecía un `Continuar` ambiguo. La UI ejecuta ahora la secuencia explícita selección → preview, informa cuántos campos seguros/críticos están seleccionados y ofrece un CTA de recuperación si la generación del preview falla después de haber guardado la selección.

El preview masivo reutiliza `RecetaDocumentacionWriteService.preview` y añade detalle de valor actual/propuesto, procedencia, clasificación y tipo de cambio. Solo contiene los campos seleccionados; los críticos pendientes quedan fuera. Evidencia: 154 pruebas backend de Fase 1 y 271 frontend completas, además de typecheck; sin IA real, confirmación ni escritura en `DATOS`.

Estado preciso: `LISTA PARA REPETIR SELECCIÓN → PREVIEW EN UI`. Fase 1 no cerrada; Fase 1.5, commit y push no iniciados.

## Actualización - selección segura por receta y regreso a propuestas externas (1 de septiembre de 2026)

La contaminación del preview por receta procedía de una diferencia contractual real: omitir `individual_selections` conserva las selecciones críticas previas, mientras enviarlo como `{}` las reemplaza por ninguna. La UI omitía el miembro al aceptar solo las propuestas seguras, de modo que dos campos seguros podían reunirse con nueve críticos residuales. Las acciones seguras global y por receta reemplazan ahora toda la selección con su conjunto seguro exacto; solo la aceptación individual de un campo crítico acumula sobre ella.

El resumen mantiene además la referencia al batch externo activo y muestra `Revisar propuestas externas · 30 recetas`. El identificador se conserva por importación y se rehidrata desde el endpoint canónico del batch, por lo que volver al resumen y entrar de nuevo no exige reimportar el XLSX. Preview ofrece `Volver a propuestas` y conserva una ruta inequívoca en ambos sentidos.

Evidencia: caso controlado 2 seguras/9 críticas con previews exactos 2 → 3 → 2, dataset 30 recetas con 83 seguras/257 críticas, 37 pruebas backend focales, 156 backend de Fase 1, 38 frontend focales, 271 frontend completas y typecheck correctos. Sin IA real, confirmación ni escritura en `DATOS`.

Estado preciso: `LISTA PARA REPETIR: SELECCIÓN SEGURA DE 1 RECETA → PREVIEW EXACTO → VOLVER A PROPUESTAS`. Fase 1 no cerrada; Fase 1.5, commit y push no iniciados.

## Actualización - persistencia del flujo externo y E2E de reconstrucción (1 de septiembre de 2026)

La sesión de importación usada por la API de producto y el workflow de completado de recetas se conservan ahora en repositorios persistentes seguros. El detalle de la importación incorpora el batch externo activo, por lo que React reconstruye propuestas, selección y preview desde backend tras remount, navegación, F5 o cierre y reapertura del navegador. `sessionStorage` y `localStorage` sólo conservan una pista de identidad; no son autoridad ni contienen las propuestas. El reinicio del backend también recupera la sesión y el batch persistidos.

Estado durable A: sesión normalizada, batch, propuestas, selecciones, preview e idempotencia. Estado reconstruible B: pantalla y contadores React, y preview regenerable por su autoridad cuando una selección lo invalida. Estado temporal C: binario XLSX, que no se conserva tras validar e incorporar sus propuestas normalizadas. Sólo confirmación conserva autoridad WRITE sobre Biblioteca.

El E2E con Chrome y XLSX físico valida 30/30/30/0, 83 seguras, 257 críticas y 340 propuestas; recorre previews 83 → 2 → 3 → 2, resumen, reload y reapertura con el mismo batch, sin reimportación ni duplicado. Evidencia: 157 pruebas backend, 38 frontend focales, 271 frontend completas, 1 E2E real, typecheck y build correctos. `datos_reales_modificados=false`, cero confirmaciones y fixtures fuera de `DATOS`. La creación de artículos nuevos desde ingredientes sigue pendiente de Fase 1. Estado preciso: `LISTA PARA SMOKE TEST HUMANO`; Fase 1 no cerrada, Fase 1.5 no iniciada, sin commit ni push.

## Actualización - smoke POST-FIX durable sin reconstrucción manual (1 de septiembre de 2026)

El primer smoke intentó recuperar el único registro existente en el storage real: `IMPWEB-477EE3DB31E1`, confirmado y sin `schema_version`, `created_at` ni `updated_at`. No existe allí un store de batches. La evidencia lo clasifica como PRE-PERSISTENCE; no demuestra un fallo de la persistencia nueva y no es reconstruible retrospectivamente.

El contrato POST-FIX incorpora `GET /api/v1/biblioteca/importaciones`, ordena sesiones activas por actualización y permite a React descubrir la sesión aunque el navegador no tenga puntero local. Los stores de importaciones y batches usan esquema 2 con timestamps de envelope y registro; el detalle de importación sigue siendo la autoridad que adjunta el batch externo activo. Las rutas productivas efectivas son `DATOS/db/biblioteca_importaciones_web.json` y `DATOS/db/biblioteca_completado_recetas_batches.json`, resueltas respecto de `HOST_AI_BASE_DIR` o de la raíz del proyecto.

El E2E aislado crea mediante las autoridades reales una importación Boronat equivalente de 30 recetas, un XLSX físico y un batch externo de 340 propuestas (83 seguras y 257 críticas). Cierra el primer contexto Chrome, reinicia de verdad frontend y backend, verifica el mismo `import_id`, `batch_id`, selección y preview por GET, y abre un contexto Chrome limpio sin storage. La UI muestra `Revisar propuestas externas · 30 recetas` sin subir ni reimportar ningún fichero; F5 conserva el acceso y el preview exacto.

Evidencia: 3 backend focales, 158 backend de Fase 1, 39 frontend focales, 272 frontend completas, 1 E2E Playwright real, typecheck y build correctos. Runtime y persistencia del smoke: `.test-runs/fase1-e2e`; cero confirmaciones y cero escrituras sobre `DATOS`. Estado preciso: `LISTA PARA SMOKE HUMANO SIN REIMPORTAR`; Fase 1 no cerrada, Fase 1.5 no iniciada, sin commit, push ni staging.

## Actualización - ingredientes nuevos a artículos y referencias externas (1 de septiembre de 2026)

El pendiente final conocido de Fase 1 ya dispone de un recorrido único y automatizado: ingrediente nuevo importado → candidato consolidado → preview/alta autorizada mediante la autoridad de catálogo → enlace versionado en el borrador → artículo incompleto → exportación y reimportación de referencia externa → preview → confirmación aislada. Las apariciones repetidas se consolidan por nombre normalizado y unidad compatible, de modo que un ingrediente presente en dos recetas produce un artículo y enlaza ambas recetas sin duplicados.

La creación no inventa precio ni proveedor y deja el artículo `PENDIENTE_DE_COMPLETAR`. El enriquecimiento externo conserva la separación entre referencia y dato operativo: `proveedor_referencia` se almacena como `tienda_referencia` dentro de `precios_referencia`; nunca reemplaza `precio` ni `proveedor` reales. El frontend expone valor real actual y valor externo propuesto antes de confirmar. La confirmación de referencias y la confirmación de la importación de Biblioteca siguen siendo operaciones distintas.

Evidencia: 37 pruebas backend focales, 183 backend de Fase 1, 54 frontend focales, 274 frontend completas y 2 E2E Playwright en Chrome; typecheck, build y `git diff --check` correctos. Los E2E usaron `.test-runs/fase1-articles-e2e`, confirmaron únicamente contra ese runtime aislado y verificaron por lectura posterior que precio/proveedor reales seguían vacíos. No se escribió ni restauró `DATOS`, no se llamó a IA externa y no hubo commit, push ni staging.

Estado preciso: `FASE 1 ABIERTA; ÚLTIMO FLUJO FUNCIONAL CONOCIDO IMPLEMENTADO, PROBADO Y VALIDADO E2E EN AISLAMIENTO`. El smoke humano previo de persistencia/rehidratación/selección/preview está aprobado. Fase 1.5 no iniciada.

## Actualización - auditoría final y runtime de smoke (1 de septiembre de 2026)

La matriz completa de Fase 1 queda técnicamente cubierta desde fuente hasta post-read y desde receta hasta artículo y referencia externa. El único E2E continuo usa el Excel físico Boronat, reinicia backend y frontend dos veces y demuestra persistencia de importación, batch, selección, preview, candidato, enlace y enriquecimiento. La referencia externa confirmada en el runtime aislado es durable e idempotente tras reinicio; precio y proveedor operativos no se alteran.

La auditoría detectó y corrigió persistencia incompleta del preview de referencias, idempotencia solo en memoria, recuperación insuficiente ante respuesta perdida del alta, cobertura de fronteras XLSX y tres falsos rótulos `TAPA` en `M.P CALÇOTADA`. El diagnóstico físico final devuelve 47 recetas, 32 canónicas aptas, 10 menús, 1 exclusión A.P y cero rótulos genéricos como receta. Evidencia: 189 backend Fase 1, 50 frontend focales, suite frontend completa, 3 E2E Chrome, typecheck y build correctos. IA real y confirmaciones de dominio sobre `DATOS`: cero.

Una regresión adicional de toda la suite histórica, fuera de la suite Fase 1, añadió tres eventos a `DATOS/logs/host_ai_general_agent.jsonl` al instanciar un shell con la raíz real. La huella agregada de `DATOS` dejó de ser idéntica aunque no cambió ningún objeto operativo. El log no se restaura por la prohibición expresa de tocar/restaurar `DATOS`.

Estado preciso: `NO LISTA PARA CERRAR FASE 1` por incumplimiento de la garantía estricta de inmutabilidad de `DATOS`. La Fase 1 sigue abierta; no hay commit, push, staging ni Fase 1.5.

## Actualización - aislamiento y escandallo/ficha antes del smoke (1 de septiembre de 2026)

La causa de la telemetría real está corregida y pytest dispone de una raíz temporal global, bloqueo inmediato de operaciones de escritura hacia `DATOS` real y verificación final del manifiesto completo. La suite histórica adicional terminó con 1.753 pruebas correctas, 1 omitida y 48 fallos legacy no relacionados; no hubo fallos del guard. Antes y después se conservaron exactamente 376 archivos y el hash agregado `B7C5917CC518D331E6D8F0F41E78ADEF2C00CC95DFA9BCD319DC25FB77440E14`.

La derivación existente receta→escandallo→ficha conserva ahora en API/UI la diferencia entre precio real, confirmado y referencia externa provisional, expone completitud e ingredientes pendientes y recalcula desde el catálogo en cada lectura. La ficha reutiliza receta, escandallo y procedencia canónicos y muestra ausencias como pendientes. Evidencia: casos A-E y suite contractual backend 218/218, focales frontend 74/74, suite frontend completa 276/276 y 3/3 E2E Chrome correctos.

Estado preciso: `LISTA PARA SMOKE FINAL DE CIERRE DE FASE 1`. La Fase 1 sigue abierta; no se ejecutó el smoke humano y no hay commit, push, staging ni Fase 1.5.

## Actualización - completado operativo y proyección provisional (2 de septiembre de 2026)

El flujo de completado de recetas cubre ahora la triple completitud documental, propuesta y confirmada. Además de los tres textos seguros para selección masiva, puede proponer con revisión individual rendimiento, unidad, raciones, cantidad por ración, tiempos, conservación, regeneración, capacidad, personal, recursos e ingredientes estructurados. Se conserva la información documental, la procedencia por campo y la precedencia `DOCUMENTO > CALCULADO > CONTEXTO_INTERNO > IA_PROPUESTA > REFERENCIA_EXTERNA > PENDIENTE`; vacío continúa siendo el último recurso.

La autoridad de lectura proyecta ficha y escandallo provisionales sobre copia en memoria y reutiliza el motor económico existente. No persiste propuestas ni costes, no introduce ingredientes nuevos y no convierte referencias externas en precios reales. El paquete XLSX de completado avanza a `0.2`, manteniendo lectura de `0.1`, y transporta los nuevos campos, contexto y metadatos de origen/confianza/motivo. Confirmación e idempotencia continúan en el workflow seguro existente.

Evidencia: backend Fase 1 ampliado 248/248, frontend focal 41/41, frontend completo 276/276, E2E Chrome 3/3, typecheck, compilación Python y build correctos. El recorrido continuo sobre copia Boronat acredita `Agua de jamaica`, persistencia tras reinicios, artículo nuevo, referencia precio/proveedor, ficha y escandallo, sin escribir en `DATOS` real. Su manifiesto sigue en 376 archivos y hash `B7C5917CC518D331E6D8F0F41E78ADEF2C00CC95DFA9BCD319DC25FB77440E14`.

Estado preciso: `LISTA PARA REANUDAR SMOKE FINAL DE FASE 1`. La fase no se cierra, Fase 1.5 no se inicia y no hay commit, push ni staging.

## Actualización - round-trip operativo XLSX 0.3 (5 de septiembre de 2026)

El paquete de completado de recetas exporta versión `0.3`, importa de forma compatible `0.1`/`0.2` y añade instrucciones físicas, identidad de importación por fila y contexto suficiente para que un completador externo proponga con procedencia, confianza y motivo sin adquirir autoridad sobre datos. El fixture GPT permanece determinista y local: no ejecuta IA ni incurre en coste.

Los campos de descongelación, vida útil congelado y regeneración admiten `NO_APLICA` como estado operativo expreso. La UI y el preview lo distinguen de vacío; la confirmación persiste el estado separado del escalar. Selección, preview, confirmación y WRITE continúan siendo fronteras distintas, y todo campo crítico no seleccionado queda fuera.

Evidencia final automática: backend ampliado 250/250, frontend focal 41/41, frontend completo 276/276 y E2E continuo Boronat 1/1 en Chrome; typecheck, compilación Python y build correctos. El E2E cubre el recorrido Host AI → XLSX → fixture GPT → XLSX → Host AI, ficha/escandallo provisional y confirmado en copia aislada, artículo nuevo, referencia de precio/proveedor, persistencia tras reinicios e idempotencia. No hubo IA externa ni escritura sobre `DATOS` real.

Estado preciso: `LISTA PARA SMOKE FINAL DEL ROUND-TRIP HOST AI → GPT → HOST AI`. Fase 1 sigue abierta; no hay commit, push, staging ni Fase 1.5.

Punto de continuación:

- Hecho: contrato XLSX 0.3, `NO_APLICA`, round-trip físico, post-read, artículo/referencia, regresión y runtime aislado durable.
- Pendiente: únicamente el smoke humano final; no requiere subir, exportar ni reimportar archivos.
- Último comando funcional: `npm.cmd run test:e2e -- e2e/fase1-closing-audit.spec.ts`.
- Resultado: `1 passed (2.4m)` en Chrome; runtime final comprobado en `http://127.0.0.1:55478/biblioteca/importaciones`.

## Actualización - rehidratación del batch externo completado (5 de septiembre de 2026)

La validación humana detectó que el batch externo post-confirmación no aparecía en la UI. El store conservaba el batch original, pero `active_external` descartaba los estados terminales y el detalle publicaba `completado_recetas_activo=null`. Se mantiene ahora revisable el último batch externo `COMPLETADO` o `COMPLETADO_PARCIAL`, sin repetir confirmación ni escritura; `CANCELADO` sigue excluido.

Evidencia: mismo `IMPWEB-9CFB9A4EC21E` y `RECIPE-BATCH-CBF31653B5A5`, HTTP 34/392, backend focal 40/40, backend Fase 1 250/250, frontend focal 41/41, frontend completo 276/276, Chrome limpio con storage vacío y F5 1/1, typecheck y build correctos. `DATOS` real permanece intacto.

Estado preciso: `LISTA PARA REANUDAR SMOKE FINAL`. Fase 1 sigue abierta.

## Actualización - completado masivo production-ready provisional (5 de septiembre de 2026)

El completado externo de recetas queda preparado como operación de lote. El contrato XLSX continúa en `HOSTAI_RECIPE_COMPLETION_PACKAGE 0.3`, conserva lectura de `0.1` y `0.2` y transporta los campos estructurales de identidad, rendimiento, ingredientes, tiempos, tanda, personal, recursos y conservación. `RecetaDocumentacionWriteService` calcula por separado completitud documental/con propuestas/confirmada y `production_ready_provisional`/`production_ready_confirmed`; una propuesta suficiente puede habilitar planificación provisional sin convertirse en dato real ni confirmado.

El batch publica estado operativo y un resumen masivo con recetas procesadas, production-ready provisional/confirmada, críticos, artículos/precios pendientes, baja confianza, errores, imposibles con motivo y `NO_APLICA`. La UI permite revisar únicamente excepciones. Una fila stale o un campo inválido quedan aislados en su receta y no eliminan el resto del lote. `NO_APLICA` y `PENDIENTE_IMPOSIBLE_DE_ESTIMAR: motivo` son estados distintos de vacío; el segundo nunca entra en WRITE.

Evidencia automática: backend Fase 1 233/233, frontend focal de importaciones 42/42, frontend completo 277/277, E2E Chrome masivo 1/1 y continuo Boronat 1/1, typecheck, compilación Python y build correctos. El E2E masivo utiliza un único XLSX físico de 52 recetas, una única reimportación, 1.195 propuestas y 49 recetas production-ready provisionales; incluye `Agua de jamaica`, una stale, un booleano inválido, un imposible con motivo, `NO_APLICA`, campo crítico, artículo nuevo y referencia externa. La confirmación E2E ocurre únicamente en `.test-runs`; el runtime de smoke se deja sin confirmar. `DATOS` conserva 376 archivos y la huella agregada `B7C5917CC518D331E6D8F0F41E78ADEF2C00CC95DFA9BCD319DC25FB77440E14` antes y después.

Estado preciso: `LISTA PARA SMOKE FINAL PRODUCTION-READY MASIVO DE FASE 1`. Esto no cierra la Fase 1, no inicia Fase 1.5 y no implica validación de calidad culinaria de los textos del fixture.

## Actualización - descarga directa del paquete XLSX externo (5 de septiembre de 2026)

El smoke humano detectó que `Completar externamente con XLSX` solo cambiaba el paso React. La llamada de exportación y la descarga física estaban ligadas a un segundo botón interno; cuando ya existía un batch externo, esa rama ni siquiera se renderizaba. El clic no emitía request, no generaba descarga y tampoco mostraba progreso o error.

El CTA principal reutiliza ahora la única autoridad `RecipeCompletionExchangeService.export`: muestra `Preparando XLSX…`, impide un segundo clic concurrente, ejecuta `POST /api/v1/biblioteca/recetas/completado-externo/exportar`, inicia la descarga física del navegador y publica nombre y número de recetas. Un error queda visible y permite reintentar. Exportar no crea, sustituye ni confirma batches; si existe uno, conserva exactamente su identificador y el CTA separado de revisión. Si no existe, el batch solo se creará al reimportar propuestas.

Evidencia: reproducción Chrome pre-fix sin POST y con timeout de descarga; 30/30 pruebas backend focales, 233/233 backend Fase 1, 44/44 frontend focales y 279/279 frontend completas. Playwright valida descarga física, parseo del XLSX con hojas `METADATA`, `INSTRUCCIONES` y `RECETAS`, contrato 0.3, 52 recetas, `import_id` y contexto en escenarios con y sin batch; el runtime de smoke conserva F5 y el mismo batch. Typecheck, build y compilación Python correctos. `DATOS` real no se escribió.

Estado preciso: `LISTA PARA SMOKE DE DESCARGA XLSX`. Fase 1 permanece abierta; no hay commit, push, staging ni Fase 1.5.

## Actualización - proyección visual de NO_APLICA (5 de septiembre de 2026)

La ficha técnica provisional distingue ahora un campo operativo realmente ausente de un campo resuelto estructuralmente como `NO_APLICA`. En el segundo caso presenta «No aplica» y conserva procedencia, motivo, confianza y estado de revisión; el escalar canónico continúa vacío y el estado sigue viajando por `estados_campos_operativos`. La corrección se limita al adaptador de presentación de `BibliotecaImportPage`: no altera readiness, selección, preview, confirmación, XLSX, batches ni escandallo.

La garantía focal cubre regeneración y tiempo de descongelación con `NO_APLICA`, además de un campo realmente ausente que sigue mostrando «Sin dato». La comprobación Playwright sobre el runtime aislado valida Agua de jamaica y persistencia tras F5 sin confirmar cambios. Fase 1 permanece abierta por instrucción expresa del usuario.

Estado preciso: `LISTA PARA CIERRE FORMAL DE FASE 1`; no equivale al cierre formal de la fase.

## Actualización - nombres humanos en el runtime masivo (5 de septiembre de 2026)

El último smoke humano no reveló una pérdida productiva de nombres: el generador sintético de 52 recetas asignaba literalmente `Receta N` tanto a la fuente de importación como a la receta canónica. Exportación XLSX, reimportación, persistencia del batch, HTTP y React conservaban fielmente ese valor. El fixture dispone ahora de 52 nombres humanos explícitos y falla durante la preparación si falta alguno o reaparece el patrón numérico silencioso.

La preparación compara por `recipe_id` los nombres canónicos, los escritos físicamente en `RECETAS` y los persistidos en el batch. Chrome valida las 52 tarjetas, F5 y reinicio de backend con el mismo batch. Si una respuesta carece objetivamente de nombre, la UI muestra «Receta sin nombre» junto al identificador técnico, sin fabricar un nombre culinario. La corrección previa de `NO_APLICA` permanece cubierta.

Estado preciso: `LISTA PARA CIERRE FORMAL DE FASE 1`; la fase sigue abierta.

## Cierre formal - Fase 1 Importación Inteligente (5 de septiembre de 2026)

Estado oficial: `CERRADA / CERTIFICADA`. El smoke humano final aprobó descarga XLSX, persistencia tras F5, lote de 52 recetas con nombres humanos, Agua de jamaica production-ready provisional y presentación estructurada de regeneración/descongelación como «No aplica». No se aceptaron ni confirmaron cambios reales.

El alcance cerrado conserva pipeline determinista primero, IA opcional limitada a propuestas, XLSX 0.3, round-trip externo, selección, preview, confirmación humana, persistencia/rehidratación, ficha y escandallo provisionales, y candidatos de artículo con referencias externas separadas de precio/proveedor reales. `1070` cuenta propuestas críticas individuales; `1071` incluye además el único campo imposible de estimar de `REC601-000003` (`unidad_tanda`), que no es propuesta ni entra en WRITE.

`DATOS` permanece en 376 archivos y hash `B7C5917CC518D331E6D8F0F41E78ADEF2C00CC95DFA9BCD319DC25FB77440E14`. Fase 1.5 no iniciada.

## Hotfix post-cierre - reimportación XLSX visible (5 de septiembre de 2026)

Tras el cierre formal, un smoke comercial detectó que el importador específico de `HOSTAI_RECIPE_COMPLETION_PACKAGE 0.3` quedaba oculto cuando la importación ya tenía un batch externo activo. El endpoint y el servicio de validación seguían operativos; el bloqueo estaba limitado a la rama de render de React.

La revisión del batch muestra ahora siempre la acción inequívoca `Importar XLSX completado`, separada del importador genérico JSON. La acción acepta únicamente `.xlsx`, reutiliza el endpoint y servicio existentes, reemplaza en pantalla el batch por el identificador devuelto y muestra archivo, validación, propuestas y ausencia de cambios reales. No ejecuta selección, preview, confirmación ni WRITE de forma automática.

Evidencia técnica previa al smoke humano: backend focal 30/30, frontend focal 47/47, suite frontend completa 282/282, Playwright Chrome de upload físico 1/1, descarga física 1/1 y smoke de nombres/`NO_APLICA`/readiness/ficha/escandallo/F5/reinicio 1/1; typecheck y build correctos. `DATOS` real permanece protegido por el baseline de 376 archivos y hash `B7C5917CC518D331E6D8F0F41E78ADEF2C00CC95DFA9BCD319DC25FB77440E14`.

Estado: `HOTFIX IMPLEMENTADO Y VALIDADO TÉCNICAMENTE; PENDIENTE SMOKE HUMANO`. Fase 1 continúa cerrada/certificada y Fase 1.5 no se ha iniciado.

## Hotfix post-cierre - contrato ChatGPT/XLSX autocontenido (5 de septiembre de 2026)

La primera prueba comercial con el XLSX completado por ChatGPT sí atravesó la subida, pero expuso tres insuficiencias del contrato: el JSON global de metadatos podía superar el límite genérico de texto y ocultar los motivos de `NO_APLICA`; el libro no publicaba de forma machine-readable tipos, shapes, enums, unidades y claves canónicas pendientes; y el normalizador de ingredientes exigía cantidad/orden idénticos, impidiendo proponer candidatos nuevos. Además, dos patrones genéricos de texto clasificaban falsamente como críticos avisos sobre alérgenos y lotes.

La exportación 0.3 incorpora ahora `SCHEMA`, ejemplos estructurados y reglas completas dentro del propio libro. El parser acepta la representación escalar histórica inequívoca y el objeto documentado, pero normaliza siempre a `{estado: "NO_APLICA"}`. Conserva cada ingrediente documental por identidad normalizada y proyecta líneas adicionales como candidatos pendientes de alta autorizada, sin crear artículos ni precio/proveedor reales. Los rechazos exponen mensajes accionables. La importación histórica 0.1/0.2/0.3 sigue soportada.

Evidencia final: archivo humano auditado por SHA-256 `0624F4C00FF2560CB5BF411A5F4E170A33EAEFC69475311BB0BA641DAC81E22C`; backend focal 38/38 y regresión Fase 1 235/235; frontend focal 47/47 y completa 282/282; Playwright físico descarga+subida 2/2 y contrato público realista 1/1. El último escenario deja 52/52 recetas `production_ready_provisional`, 1.820 propuestas, 52 con `NO_APLICA`, 0 rechazadas/bloqueadas/erróneas y 0 confirmadas; valida Agua de jamaica, candidato de artículo, ficha, escandallo parcial, F5, reinicio y navegador limpio. `DATOS` real no se escribió.

Estado: `LISTA PARA ÚLTIMO SMOKE HUMANO DEL CIRCUITO REAL`; no constituye commit ni inicio de Fase 1.5.

## Cierre autónomo del hotfix con artefacto GPT real (5 de septiembre de 2026)

La validación sintética 52/52 demuestra el contrato, pero no representa el resultado del primer fichero GPT comercial. El runtime de smoke contiene ahora el artefacto real exacto (SHA-256 `0624F4C00FF2560CB5BF411A5F4E170A33EAEFC69475311BB0BA641DAC81E22C`) en el mismo `IMPWEB-6F402EBB0868`, con batch durable `RECIPE-BATCH-7B15EDEEADBC` y recibo de origen rehidratable.

El resultado real es 52 filas útiles, 1.736 propuestas aceptadas (156 seguras y 1.580 individuales), 136 rechazos trazables, 1 receta provisionalmente lista, 0 confirmadas, 13 con error y 34 con `NO_APLICA`. Agua de jamaica queda lista provisionalmente, con Agua como candidato nuevo y ficha/escandallo de solo lectura `SIN_COSTE`; no se inventan precios o proveedores. La UI recupera el nombre y SHA del archivo, batch, validación y propuestas desde servidor después de F5, navegador limpio y reinicio, sin depender de storage local.

Evidencia final: backend Fase 1 273/273, frontend 282/282, typecheck, compilación Python y build correctos; E2E de fronteras, rehidratación, persistencia, flujo continuo y smoke final GPT real correctos. `DATOS` permanece en 376 archivos y hash `B7C5917CC518D331E6D8F0F41E78ADEF2C00CC95DFA9BCD319DC25FB77440E14`. No hubo confirmación, WRITE real, staging, commit, push ni inicio de Fase 1.5.

Estado vigente: `FASE 1 LISTA PARA SMOKE HUMANO FINAL`.

## Corrección del snapshot económico del preview (6 de septiembre de 2026)

El batch real `RECIPE-BATCH-27AD1C3C567B` conservaba dos derivados incoherentes: la proyección integral de `resultados` calculaba Agua de jamaica como `PARCIAL` con 11,63 EUR, 75 % y tres referencias, mientras el snapshot persistido en `preview.items` decía `SIN_COSTE`. La causa era que el preview se había calculado solo con los campos agrupados seleccionados; `ingredientes_estructurados`, correctamente crítico y no confirmable sin revisión individual, no participaba en ese cálculo aunque sus referencias se mostraban.

El preview reutiliza y rehidrata ahora la proyección integral solo-lectura, sin ampliar su conjunto de cambios confirmables. La UI distingue coste total parcial conocido de un total completo, muestra cobertura y Agua pendiente. F5, reinicio completo y Chrome limpio conservan el mismo batch, 52/52 recetas listas provisionalmente, 1.807 propuestas, 1.144 agrupadas, 507 críticas, 11 escandallos parciales y cero modificaciones reales.

Evidencia: backend focal 83/83, backend Fase 1 227/227, frontend focal 49/49, frontend completo 284/284, E2E económico/buscador post-reinicio 1/1, typecheck, build y compilación Python correctos.

Estado vigente: `ESCANDALLO CORREGIDO — LISTO PARA SMOKE HUMANO FINAL`; Fase 1 sigue abierta y Fase 1.5 no se ha iniciado.

**Fin del documento oficial `09_ESTADO_ACTUAL.md`.**

## Actualización — contrato maestro autosuficiente de Fase 1 (5 de septiembre de 2026)

El objetivo durable queda fijado como importación masiva + completado masivo con IA + ficha técnica + escandallo + revisión por excepciones. `recipe_completion_contract.py` centraliza el contrato versionado y el XLSX 0.3 incorpora un único `PROMPT_IA`, schema explicativo de 36 campos y hojas públicas de artículos/precios consolidados. La importación valida referencias externas sin elevarlas a precio/proveedor real ni escribir datos.

Evidencia: backend focal 66/66, backend Fase 1 245/245, frontend focal 47/47 y suite frontend completa correcta; Playwright valida descarga/subida física, contrato público >50, referencia externa, `NO_APLICA`, candidato, ficha, escandallo, readiness, F5, reinicio, navegador limpio, persistencia e aislamiento. Typecheck, build y compilación Python correctos.

Estado preciso: `ESPERANDO XLSX GPT REAL`. Se generó un paquete nuevo de 52 recetas desde `IMPWEB-6F402EBB0868`; no se reutiliza el XLSX GPT anterior. Fase 1 permanece abierta, sin commit, push, staging ni Fase 1.5.

## Cierre del circuito económico y revisión por excepciones (6 de septiembre de 2026)

El XLSX GPT real nuevo `hostai-completado-recetas-IMPWEB-6F402EBB0868_COMPLETADO_GPT_NUEVO.xlsx` (SHA-256 `72CF33170BB034A9C389DE1639669D7B7E22E27E4BF5BBBE08683EFF61988274`) reveló que las referencias de `PRECIOS_REFERENCIA` se validaban pero no se transferían al batch ni a la proyección. El batch schema 3 persiste ahora referencias consolidadas y selecciones operativas agrupadas. La proyección reutiliza una referencia por identidad exacta nombre+familia de unidad, admite candidatos nuevos declarados en el mismo libro y conserva la prioridad `REAL/CONFIRMADO > REFERENCIA_EXTERNA > SIN_PRECIO`; nunca crea precio, proveedor o artículo real.

Resultado real aislado: 52/52 recetas, 1.807 propuestas, 156 seguras, 1.144 operativas agrupables, 507 críticas individuales, 0 rechazadas y 0 bloqueadas. Las seis filas de precio válidas se consolidan en tres identidades; producen 11 escandallos `PARCIAL` y 41 `SIN_COSTE`. Agua de jamaica usa tres referencias, calcula 11,63 EUR parciales y conserva Agua sin coste. Las 52 recetas siguen production-ready provisionales y 0 confirmadas; la baja confianza relevante baja de un falso 52/52 a 0 sin alterar las confianzas originales.

La UI presenta un resumen de excepciones, permite incorporar los 1.144 campos operativos a un único preview y mantiene vida útil, conservación, refrigeración/congelación, regeneración/descongelación, alérgenos e ingredientes/artículos en revisión individual. Seleccionar agrupados no confirma ni escribe. Chrome limpio verificó selección, preview, exclusión de ingredientes no seleccionados, F5 y reinicio sobre `RECIPE-BATCH-27AD1C3C567B`.

Evidencia final: regresión Fase 1 206/206, frontend focal 48/48 y completo 283/283. Playwright cubre contrato adversarial 4/4, persistencia/artículo/referencia 2/2, rehidratación 1/1, lote masivo 1/1, recorrido Boronat 1/1 y XLSX GPT real económico 1/1. Typecheck, compilación Python y build correctos. No hubo confirmación ni escritura sobre `DATOS` real, staging, commit, push o Fase 1.5.

Estado: `FASE 1 LISTA PARA SMOKE HUMANO FINAL DE ESCANDALLO Y EXCEPCIONES`.
