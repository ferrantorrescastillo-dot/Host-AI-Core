# HOST AI — 09_ESTADO_ACTUAL

> Cabina de control oficial del proyecto  
> Estado del documento: Oficial  
> Ámbito: DEVKIT / Memoria viva  
> Versión del documento: 1.0  
> Fecha de actualización: 13 de julio de 2026  
> Proyecto de referencia: Host AI 6.0  
> Documentos superiores: `01_IDENTIDAD.md`, `03_REGLAS.md`

---

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

**Fin del documento oficial `09_ESTADO_ACTUAL.md`.**
