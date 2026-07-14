# HOST AI — 05_SPRINTS

> Estándar oficial del ciclo de desarrollo  
> Estado: Oficial  
> Ámbito: DEVKIT / Memoria viva  
> Versión del documento: 1.0  
> Fecha de creación: 13 de julio de 2026  
> Documentos relacionados: `01_IDENTIDAD.md`, `03_REGLAS.md`, `04_ROADMAP.md`, `09_ESTADO_ACTUAL.md`

---

# 1. PROPÓSITO

Este documento define cómo debe evolucionar Host AI mediante sprints controlados, verificables y trazables.

Su objetivo es que cualquier desarrollo responda siempre a estas preguntas:

- ¿Qué problema real resuelve?
- ¿Por qué se hace ahora?
- ¿Qué puede tocar?
- ¿Qué no puede tocar?
- ¿Qué dependencias tiene?
- ¿Cómo se prueba?
- ¿Qué evidencia demuestra que funciona?
- ¿Cuándo se considera cerrado?
- ¿Qué memoria debe actualizar?
- ¿Qué sprints futuros dependen de él?

Un sprint no es únicamente un bloque de código.

Es una unidad completa de trabajo con:

- propósito;
- alcance;
- límites;
- diseño;
- implementación;
- pruebas;
- diagnóstico;
- validación;
- certificación;
- memoria;
- cierre.

---

# 2. PRINCIPIO GENERAL

Host AI trabaja por sprints porque el proyecto es grande, acumulativo y sensible a regresiones.

La metodología debe evitar:

- cambios descontrolados;
- sprints que crecen sin límite;
- funciones sin pruebas;
- documentación separada del código;
- certificaciones sin evidencia;
- duplicidad;
- reabrir líneas cerradas sin motivo;
- perder el contexto entre chats;
- confundir “entregado” con “terminado”.

Regla principal:

> Un sprint solo está cerrado cuando el problema real está resuelto, el código está probado, la evidencia existe y la memoria viva ha sido actualizada.

---

# 3. QUÉ ES UN SPRINT

Un sprint es una unidad de evolución del proyecto con un objetivo principal verificable.

Debe poder expresarse así:

```text
Cuando ocurre [situación real],
Host AI debe [comportamiento esperado],
sin romper [funciones protegidas],
y se considerará correcto cuando [evidencia].
```

Ejemplo:

```text
Cuando un cocinero termina una producción,
Host AI debe calcular consumos, validar stock,
registrar movimientos y trazabilidad,
sin descontar dos veces,
y se considerará correcto cuando la ruta normal,
la falta de stock y el rollback hayan sido probados.
```

---

# 4. QUÉ NO ES UN SPRINT

No es:

- una idea abierta;
- una lista de deseos;
- una conversación;
- un parche sin objetivo;
- una acumulación de mejoras;
- un documento sin código cuando el objetivo es funcional;
- código sin tests;
- una certificación escrita antes de ejecutar;
- una refactorización masiva sin necesidad;
- una entrega que depende de supuestos no verificados.

---

# 5. TIPOS OFICIALES DE SPRINT

## 5.1 PILOTO

Resuelve un flujo real de cocina.

Ejemplos:

```text
PILOTO-1.3
PILOTO-1.4
PILOTO-1.5
```

Debe incluir validación manual.

## 5.2 DEVKIT

Mejora la forma de desarrollar Host AI.

Ejemplos:

```text
DEVKIT-0.1
DEVKIT-0.2
```

Puede consistir en documentación, herramientas, comandos, auditoría o automatización.

## 5.3 ARQUITECTURA

Modifica estructura, responsabilidades o contratos.

Requiere análisis de impacto ampliado.

## 5.4 INFRAESTRUCTURA

Afecta:

- entorno;
- configuración;
- despliegue;
- persistencia;
- backups;
- logging;
- CI.

## 5.5 IA

Añade o modifica:

- interpretación;
- prompts;
- clasificación;
- recomendaciones;
- modelos;
- costes;
- límites.

Nunca puede ocultar reglas críticas dentro de prompts.

## 5.6 DATOS

Afecta:

- migraciones;
- esquemas;
- importaciones;
- normalización;
- relaciones;
- calidad.

## 5.7 MIGRACIÓN

Transforma versiones de datos o estructuras.

Debe ser repetible, trazable y segura.

## 5.8 REFACTOR

Mejora código sin cambiar comportamiento esperado.

Debe demostrar compatibilidad.

## 5.9 HOTFIX

Corrige un fallo crítico y acotado.

Debe minimizar cambios.

## 5.10 INVESTIGACIÓN

Explora una solución sin comprometer código estable.

Resultados posibles:

- viable;
- no viable;
- requiere prueba;
- aplazado.

## 5.11 CERTIFICACIÓN

Revalida una línea existente frente a una versión concreta.

## 5.12 DOCUMENTACIÓN

Crea o corrige memoria oficial.

No sustituye pruebas funcionales.

---

# 6. CONVENCIÓN DE NOMBRES

Formato:

```text
TIPO-X.Y
TIPO-X.Y.Z
```

Ejemplos:

```text
PILOTO-1.4
PILOTO-1.4.1
DEVKIT-0.1
IA-2.3
HOTFIX-1.4.1-H1
```

Reglas:

- mayúsculas para familia;
- guion antes de versión;
- puntos para jerarquía;
- nombre descriptivo adicional;
- no reutilizar identificadores;
- no renumerar sprints históricos.

Ejemplo completo:

```text
PILOTO-1.4 — Producción → Stock
```

---

# 7. CUÁNDO CREAR UN SUB-SPRINT

Debe crearse un sub-sprint cuando:

- el objetivo principal sigue siendo el mismo;
- aparece una mejora acotada;
- no se justifica abrir una línea nueva;
- la funcionalidad base ya existe;
- el cambio puede certificarse por separado.

Ejemplo:

```text
PILOTO-1.4
└── PILOTO-1.4.1 — Asistente de resolución de bloqueos
```

No debe usarse un sub-sprint para esconder un cambio arquitectónico grande.

---

# 8. CICLO DE VIDA OFICIAL

```text
IDEA
↓
PROPUESTO
↓
DEFINIDO
↓
AUDITADO
↓
DISEÑADO
↓
EN DESARROLLO
↓
EN PRUEBAS
↓
ENTREGADO
↓
DIAGNOSTICADO
↓
VALIDADO MANUALMENTE
↓
CERTIFICADO TÉCNICAMENTE
↓
VALIDADO EN COCINA
↓
CERRADO
↓
ARCHIVADO
```

No todos los sprints necesitan llegar a “validado en cocina”, pero los sprints PILOTO sí.

---

# 9. ESTADOS OFICIALES

## 9.1 IDEA

Existe una necesidad no analizada.

## 9.2 PROPUESTO

Se ha registrado y tiene una intención clara.

## 9.3 DEFINIDO

Dispone de objetivo, alcance y criterio de éxito.

## 9.4 AUDITADO

Se ha revisado el código real y las dependencias.

## 9.5 DISEÑADO

Existe contrato técnico y operativo.

## 9.6 EN DESARROLLO

Hay cambios activos.

## 9.7 EN PRUEBAS

El código está implementado y se valida.

## 9.8 ENTREGADO

Existe paquete o commit disponible.

No significa que funcione en la instalación final.

## 9.9 DIAGNOSTICADO

El diagnóstico específico da resultado correcto.

## 9.10 VALIDADO MANUALMENTE

El usuario ha recorrido el flujo.

## 9.11 CERTIFICADO TÉCNICAMENTE

Existen tests, regresión, diagnóstico y documentación sobre una versión concreta.

## 9.12 VALIDADO EN COCINA

Se ha usado en una situación real.

## 9.13 CERRADO

Cumple criterios de salida y la memoria está actualizada.

## 9.14 ARCHIVADO

No recibe cambios salvo hotfix o reactivación oficial.

## 9.15 BLOQUEADO

No puede avanzar por una dependencia o riesgo.

## 9.16 RECHAZADO

Se descarta con motivo documentado.

## 9.17 SUSTITUIDO

Otro sprint absorbe su objetivo.

---

# 10. CONTRATO DEL SPRINT

Todo sprint debe tener un contrato antes de desarrollar.

Plantilla:

```text
IDENTIFICADOR:
NOMBRE:
TIPO:
ESTADO:
RESPONSABLE:
FECHA DE APERTURA:

PROBLEMA REAL:
OBJETIVO:
USUARIO:
MOMENTO OPERATIVO:

ALCANCE:
FUERA DE ALCANCE:

ARCHIVOS O ÁREAS PERMITIDAS:
ÁREAS PROTEGIDAS:

DEPENDENCIAS:
MOTORES REUTILIZADOS:
DATOS NECESARIOS:

RIESGOS:
ESCRITURAS:
ROLLBACK:
TRAZABILIDAD:

TESTS OBLIGATORIOS:
DIAGNÓSTICO:
VALIDACIÓN MANUAL:

CRITERIOS DE ACEPTACIÓN:
CRITERIOS DE CIERRE:
```

---

# 11. PROBLEMA REAL

Debe describirse desde cocina.

Incorrecto:

> Mejorar módulo de stock.

Correcto:

> Cuando se termina una elaboración, el stock no refleja automáticamente los ingredientes consumidos ni el producto generado.

---

# 12. OBJETIVO

Debe ser concreto y comprobable.

Incorrecto:

> Hacer stock inteligente.

Correcto:

> Al finalizar una producción válida, descontar materias primas, añadir la elaboración, registrar trazabilidad y evitar duplicados.

---

# 13. ALCANCE

Debe indicar qué incluye.

Ejemplo:

- vista previa;
- validación;
- consumo;
- entrada;
- cierre;
- trazabilidad.

---

# 14. FUERA DE ALCANCE

Debe impedir crecimiento descontrolado.

Ejemplo:

- no modifica recetas;
- no recalcula costes históricos;
- no crea compras;
- no añade permisos avanzados;
- no cambia interfaz web.

---

# 15. ÁREAS PERMITIDAS Y PROTEGIDAS

Ejemplo:

```text
Permitidas:
SERVICIOS/produccion_stock_piloto_14.py
APP/consola_produccion_guiada_piloto_13.py
TESTS/test_piloto_14_produccion_stock.py

Protegidas:
Importador I1.3
Motor de compras
Datos reales
```

Si durante el sprint hace falta tocar un área protegida, debe ampliarse el contrato.

---

# 16. AUDITORÍA PREVIA

Antes de programar:

1. revisar ZIP o rama real;
2. localizar entradas;
3. localizar motores;
4. buscar lógica equivalente;
5. revisar tests;
6. revisar datos;
7. revisar certificaciones;
8. identificar riesgos;
9. confirmar rutas;
10. registrar diferencias con memoria.

No se debe desarrollar basándose solo en el nombre de un archivo o en conversaciones anteriores.

---

# 17. DISEÑO DEL SPRINT

Debe definir:

- flujo;
- contratos;
- modelos;
- entradas;
- salidas;
- errores;
- estados;
- escrituras;
- trazabilidad;
- interfaz;
- pruebas.

Diagrama mínimo:

```text
Situación real
↓
APP
↓
Servicio coordinador
↓
Motor existente
↓
Persistencia
↓
Resultado
↓
Mi Jornada
```

---

# 18. DESARROLLO

Reglas:

- cambios mínimos;
- commits pequeños;
- no duplicar;
- no mezclar refactors;
- no tocar datos reales;
- no esconder errores;
- no modificar tests para ocultar fallos;
- documentar decisiones;
- mantener compatibilidad.

---

# 19. GESTIÓN DEL ALCANCE

Un cambio entra en el sprint si:

- es necesario para el objetivo;
- no crea una línea distinta;
- no aumenta significativamente el riesgo.

Un cambio sale a pendientes si:

- es mejora;
- no bloquea;
- añade complejidad;
- requiere otro motor;
- cambia arquitectura;
- pertenece a otra fase.

---

# 20. CAMBIO DE ALCANCE

Debe registrarse:

```text
CAMBIO:
MOTIVO:
IMPACTO:
ARCHIVOS NUEVOS:
RIESGOS:
TESTS ADICIONALES:
APROBACIÓN:
```

Si el alcance aumenta más de forma sustancial, dividir el sprint.

---

# 21. EXPEDIENTE DEL SPRINT

Cada sprint debe dejar un expediente.

Ruta recomendada:

```text
DEVKIT/
└── SPRINTS/
    └── PILOTO-1.4/
        ├── CONTRATO.md
        ├── CAMBIOS.md
        ├── TESTS.md
        ├── DIAGNOSTICO.md
        ├── VALIDACION.md
        ├── CERTIFICACION.md
        ├── LECCIONES.md
        └── MANIFEST.json
```

---

# 22. CONTENIDO DEL EXPEDIENTE

## 22.1 CONTRATO.md

Definición inicial.

## 22.2 CAMBIOS.md

Archivos y decisiones.

## 22.3 TESTS.md

Comandos, resultados y entorno.

## 22.4 DIAGNOSTICO.md

Qué valida el diagnóstico.

## 22.5 VALIDACION.md

Prueba manual y real.

## 22.6 CERTIFICACION.md

Conclusión técnica.

## 22.7 LECCIONES.md

Qué se aprendió.

## 22.8 MANIFEST.json

Metadatos estructurados.

---

# 23. MANIFEST DEL SPRINT

Ejemplo:

```json
{
  "id": "PILOTO-1.4",
  "nombre": "Producción a Stock",
  "estado": "validacion_parcial",
  "version_base": "Host AI 6.0",
  "archivos_modificados": [],
  "tests": [],
  "diagnostico": "",
  "commit": "",
  "fecha": "2026-07-13"
}
```

No debe incluir secretos.

---

# 24. TESTS OBLIGATORIOS

Todo sprint funcional debe incluir:

- caso normal;
- caso límite;
- error;
- duplicado cuando aplique;
- rollback cuando aplique;
- compatibilidad;
- regresión;
- solo lectura en diagnóstico.

---

# 25. PIRÁMIDE DE PRUEBAS

```text
Unitarias
↓
Servicios
↓
Integración
↓
Regresión
↓
Diagnóstico
↓
Validación manual
↓
Validación real
```

No sustituir una capa por otra.

---

# 26. TEST UNITARIO

Valida una función o clase aislada.

Debe ser:

- rápido;
- reproducible;
- independiente;
- claro.

---

# 27. TEST DE SERVICIO

Valida coordinación entre componentes con dependencias controladas.

---

# 28. TEST DE INTEGRACIÓN

Valida componentes reales conectados.

Debe usar datos de prueba.

---

# 29. REGRESIÓN

Debe incluir:

- sprint anterior;
- motores reutilizados;
- entradas afectadas;
- flujos protegidos.

---

# 30. DIAGNÓSTICO

Cada sprint relevante debe incluir:

```text
COMPROBAR_<SPRINT>.py
```

Debe:

- ser ejecutable;
- no dañar datos;
- resumir garantías;
- distinguir error y aviso;
- devolver estado claro.

---

# 31. VALIDACIÓN MANUAL

Debe indicar:

- pasos;
- datos;
- resultado esperado;
- resultado real;
- capturas o texto;
- incidencias;
- decisión.

---

# 32. VALIDACIÓN EN COCINA

Debe registrar:

- fecha;
- contexto;
- usuarios;
- evento o servicio;
- comportamiento;
- problemas;
- utilidad;
- cambios necesarios.

---

# 33. CERTIFICACIÓN TÉCNICA

Debe contener:

- sprint;
- versión;
- entorno;
- archivos;
- tests;
- regresión;
- diagnóstico;
- limitaciones;
- resultado;
- firma o responsable;
- fecha.

No debe afirmar más de lo probado.

---

# 34. CERTIFICACIÓN OPERATIVA

Solo después de uso real.

Debe responder:

- ¿ayuda?
- ¿frena?
- ¿se entiende?
- ¿es fiable?
- ¿qué falta?
- ¿puede usarse diariamente?

---

# 35. CRITERIOS DE CIERRE

Un sprint puede cerrarse cuando:

- objetivo cumplido;
- alcance estable;
- tests pasan;
- diagnóstico correcto;
- regresión correcta;
- validación necesaria realizada;
- documentación completa;
- memoria actualizada;
- pendientes separados;
- versión identificada;
- no hay riesgo crítico abierto.

---

# 36. CIERRE PARCIAL

Puede cerrarse técnicamente y quedar pendiente de validación operativa.

Debe indicarse como:

```text
CERTIFICADO TÉCNICAMENTE
VALIDACIÓN EN COCINA PENDIENTE
```

Nunca usar únicamente:

```text
TERMINADO
```

---

# 37. REAPERTURA

Puede reabrirse por:

- bug;
- incompatibilidad;
- datos;
- requisito real;
- certificación revocada.

Debe registrar:

- motivo;
- versión;
- impacto;
- nuevo estado.

---

# 38. HOTFIX

Proceso:

1. reproducir;
2. aislar;
3. corregir mínimo;
4. test específico;
5. regresión;
6. documentar;
7. actualizar certificación.

No introducir mejoras no relacionadas.

---

# 39. DEUDA TÉCNICA

Debe registrarse si:

- existe duplicidad;
- falta test;
- hay código legado;
- aparece acoplamiento;
- hay configuración dispersa;
- una solución es provisional.

Formato:

```text
ID:
ORIGEN:
DESCRIPCIÓN:
RIESGO:
PRIORIDAD:
SPRINT PROPUESTO:
```

---

# 40. PENDIENTES DESCUBIERTOS

Durante un sprint:

- bloqueante → resolver;
- crítico no relacionado → hotfix;
- mejora → `10_PENDIENTES.md`;
- deuda → memoria técnica;
- idea futura → roadmap.

---

# 41. DECISIONES TÉCNICAS

Toda decisión importante debe registrar:

- contexto;
- decisión;
- alternativas;
- motivo;
- impacto;
- reversibilidad.

Después se traslada a `06_MEMORIA_TECNICA.md`.

---

# 42. LECCIONES APRENDIDAS

Al cerrar:

- qué funcionó;
- qué falló;
- qué supuestos eran incorrectos;
- qué test faltó;
- qué regla nueva se necesita;
- qué debe evitarse.

---

# 43. RELACIÓN CON ROADMAP

Un sprint debe pertenecer a una fase.

Si no pertenece:

- revisar roadmap;
- justificar urgencia;
- registrar cambio.

No abrir sprints por impulso.

---

# 44. RELACIÓN CON ESTADO ACTUAL

Al cerrar o cambiar de estado, actualizar:

```text
09_ESTADO_ACTUAL.md
```

Debe indicar:

- evidencia;
- limitaciones;
- siguiente paso.

---

# 45. RELACIÓN CON CERTIFICACIONES

Actualizar:

```text
08_CERTIFICACIONES.md
```

cuando se certifique, revoque o sustituya.

---

# 46. RELACIÓN CON PENDIENTES

Actualizar:

```text
10_PENDIENTES.md
```

para:

- añadir;
- resolver;
- aplazar;
- descartar.

---

# 47. RELACIÓN CON ARQUITECTURA

Si cambia:

- capa;
- contrato;
- dependencia;
- entrada;
- persistencia;

actualizar `02_ARQUITECTURA.md`.

---

# 48. RELACIÓN CON REGLAS

Si el sprint descubre una regla permanente:

- proponer modificación;
- justificar;
- versionar `03_REGLAS.md`.

No convertir soluciones temporales en reglas sin revisión.

---

# 49. GIT

Rama sugerida:

```text
feature/piloto-1.4
feature/devkit-0.1
hotfix/piloto-1.4-stock
```

Commits:

```text
PILOTO-1.4: add stock preview
PILOTO-1.4: add transactional rollback
PILOTO-1.4: add regression tests
```

---

# 50. REGLAS DE COMMIT

- un propósito;
- mensaje claro;
- sin secretos;
- sin datos reales;
- sin archivos accidentales;
- tests relacionados;
- documentación cuando corresponda.

---

# 51. TAGS

Una versión certificada puede etiquetarse:

```text
piloto-1.4-tech-certified
devkit-0.1
```

El tag debe vincularse a evidencia.

---

# 52. ZIP DE ENTREGA

El ZIP es un artefacto de distribución.

Debe incluir:

- solo archivos necesarios;
- estructura correcta;
- comprobación;
- changelog;
- certificación;
- guía.

No debe sustituir el repositorio.

---

# 53. MANIFEST DE ENTREGA

El ZIP debería incluir:

```text
MANIFEST_SPRINT.json
```

con:

- sprint;
- versión;
- archivos;
- hash;
- fecha;
- dependencias.

---

# 54. EVIDENCIAS

Evidencias aceptadas:

- salida de tests;
- logs;
- diagnóstico;
- prueba manual;
- captura;
- commit;
- hash;
- archivo generado;
- base de prueba.

Una afirmación sin evidencia no certifica.

---

# 55. MÉTRICAS DE CALIDAD

## 55.1 Claridad

¿Se entiende?

## 55.2 Seguridad

¿Puede dañar datos?

## 55.3 Reutilización

¿Duplica?

## 55.4 Cobertura

¿Prueba rutas importantes?

## 55.5 Compatibilidad

¿Rompe?

## 55.6 Operatividad

¿Ayuda en cocina?

## 55.7 Trazabilidad

¿Se puede reconstruir?

## 55.8 Mantenibilidad

¿Puede modificarse?

---

# 56. SEMÁFORO DE CALIDAD

```text
VERDE:
Listo para continuar.

AMARILLO:
Puede continuar con limitaciones documentadas.

ROJO:
No debe integrarse.
```

---

# 57. REGLAS PARA SPRINTS PILOTO

Además de lo general:

- lenguaje humano;
- flujo real;
- Mi Jornada;
- validación manual;
- validación en cocina;
- no imponer burocracia;
- medir utilidad.

---

# 58. REGLAS PARA SPRINTS DEVKIT

Debe:

- no afectar operativa salvo necesidad;
- trabajar sobre copia;
- explicar fuentes;
- ser reproducible;
- reducir dependencia del chat;
- mejorar trazabilidad.

---

# 59. REGLAS PARA SPRINTS IA

Debe incluir:

- modelo;
- prompt;
- coste;
- incertidumbre;
- fallback;
- pruebas;
- límites;
- confirmación;
- privacidad.

---

# 60. REGLAS PARA MIGRACIONES

Debe:

- detectar versión;
- backup;
- dry-run;
- idempotencia;
- logs;
- rollback;
- validación;
- no perder origen.

---

# 61. REGLAS PARA REFACTORS

Debe demostrar:

- mismo comportamiento;
- mejor estructura;
- tests previos;
- tests posteriores;
- sin cambios ocultos.

---

# 62. REGLAS PARA HOTFIX

Debe priorizar:

- rapidez controlada;
- alcance mínimo;
- reproducción;
- evidencia;
- regresión.

---

# 63. ERRORES HISTÓRICOS A EVITAR

## 63.1 Explicar muchas veces sin ejecutar

La metodología debe pasar a acción cuando el objetivo está claro.

## 63.2 Prometer trabajo futuro

No afirmar que se hará después.

Debe ejecutarse en la respuesta actual cuando sea posible.

## 63.3 Certificar sin ejecutar

Nunca.

## 63.4 Crear arquitectura ideal sin código real

Auditar primero.

## 63.5 Confundir parche con versión consolidada

Registrar base y orden de aplicación.

## 63.6 Decir “perfecto” sin evidencia

Usar estados concretos.

## 63.7 Abrir demasiadas ideas

Pasarlas a pendientes.

## 63.8 Diseñar desde módulos

Diseñar desde la situación real.

---

# 64. EJEMPLO — PILOTO-1.3

Problema:

La producción existía, pero el usuario debía entrar en gestión técnica.

Objetivo:

Guiar qué hacer ahora.

Evidencia:

- diagnóstico;
- planes;
- tareas;
- siguiente acción;
- delegación al motor.

Estado:

```text
CERTIFICADO TÉCNICAMENTE
VALIDADO MANUALMENTE
```

Lección:

La interfaz puede humanizarse sin duplicar motor.

---

# 65. EJEMPLO — PILOTO-1.4

Problema:

Finalizar producción no actualizaba inventario de forma coordinada.

Objetivo:

Conectar producción y stock transaccionalmente.

Validado:

- falta de stock;
- bloqueo.

Pendiente:

- ruta exitosa;
- duplicado;
- rollback;
- trazabilidad visible.

Estado correcto:

```text
VALIDACIÓN PARCIAL
```

Lección:

No declarar cierre completo por validar una única ruta.

---

# 66. EJEMPLO — DEVKIT-0.1

Objetivo:

Crear memoria viva.

Entregables:

- identidad;
- reglas;
- roadmap;
- estado;
- sprints;
- arquitectura;
- memoria técnica;
- memoria operativa;
- certificaciones;
- pendientes.

Estado actual:

```text
EN DESARROLLO
```

Cierre:

Solo cuando todos estén revisados y consolidados.

---

# 67. PLANTILLA DE APERTURA

```markdown
# SPRINT <ID> — <NOMBRE>

## Estado
PROPUESTO

## Problema real

## Objetivo

## Usuario

## Alcance

## Fuera de alcance

## Dependencias

## Áreas permitidas

## Áreas protegidas

## Riesgos

## Pruebas

## Diagnóstico

## Validación

## Criterios de cierre
```

---

# 68. PLANTILLA DE CAMBIOS

```markdown
# CAMBIOS

## Archivos creados

## Archivos modificados

## Archivos eliminados

## Contratos modificados

## Migraciones

## Compatibilidad

## Decisiones
```

---

# 69. PLANTILLA DE TESTS

```markdown
# TESTS

## Entorno

## Comandos

## Unitarios

## Integración

## Regresión

## Fallos

## Resultado
```

---

# 70. PLANTILLA DE VALIDACIÓN

```markdown
# VALIDACIÓN

## Fecha

## Usuario

## Contexto

## Pasos

## Resultado esperado

## Resultado observado

## Incidencias

## Decisión
```

---

# 71. PLANTILLA DE CERTIFICACIÓN

```markdown
# CERTIFICACIÓN

## Sprint

## Versión

## Evidencia

## Tests

## Diagnóstico

## Regresión

## Limitaciones

## Resultado

## Estado otorgado

## Fecha
```

---

# 72. PLANTILLA DE CIERRE

```markdown
# CIERRE

## Objetivo cumplido

## Evidencias

## Pendientes derivados

## Deuda técnica

## Memoria actualizada

## Siguiente sprint

## Estado final
```

---

# 73. CHECKLIST DE APERTURA

- [ ] Identidad leída.
- [ ] Reglas leídas.
- [ ] Estado actual revisado.
- [ ] Roadmap revisado.
- [ ] Código real auditado.
- [ ] Problema definido.
- [ ] Objetivo verificable.
- [ ] Alcance definido.
- [ ] Fuera de alcance definido.
- [ ] Dependencias identificadas.
- [ ] Motores reutilizados identificados.
- [ ] Áreas protegidas definidas.
- [ ] Riesgos identificados.
- [ ] Tests definidos.
- [ ] Criterios de cierre definidos.

---

# 74. CHECKLIST DE DESARROLLO

- [ ] Rama o copia.
- [ ] Cambios mínimos.
- [ ] Sin datos reales.
- [ ] Sin duplicidad.
- [ ] Configuración central.
- [ ] Errores controlados.
- [ ] Trazabilidad.
- [ ] Compatibilidad.
- [ ] Commits claros.
- [ ] Decisiones registradas.

---

# 75. CHECKLIST DE PRUEBAS

- [ ] Caso normal.
- [ ] Caso límite.
- [ ] Error.
- [ ] Duplicado.
- [ ] Rollback.
- [ ] Regresión.
- [ ] Diagnóstico.
- [ ] Datos aislados.
- [ ] Resultado reproducible.

---

# 76. CHECKLIST DE ENTREGA

- [ ] Código.
- [ ] Tests.
- [ ] Diagnóstico.
- [ ] Changelog.
- [ ] Certificación.
- [ ] Guía.
- [ ] Manifest.
- [ ] Estructura correcta.
- [ ] ZIP comprobado.
- [ ] Versión indicada.

---

# 77. CHECKLIST DE CIERRE

- [ ] Objetivo cumplido.
- [ ] Evidencia suficiente.
- [ ] Limitaciones registradas.
- [ ] Validación manual.
- [ ] Validación real si aplica.
- [ ] Roadmap actualizado.
- [ ] Estado actualizado.
- [ ] Certificaciones actualizadas.
- [ ] Pendientes actualizados.
- [ ] Lecciones registradas.
- [ ] Commit o tag.
- [ ] Siguiente paso claro.

---

# 78. AUTOMATIZACIÓN FUTURA

Comandos previstos:

```text
host sprint abrir
host sprint estado
host sprint comprobar
host sprint certificar
host sprint cerrar
```

No deben implementarse hasta definir:

- formatos;
- manifest;
- fuentes;
- permisos;
- integración Git.

---

# 79. REGLA DE HONESTIDAD

Nunca debe afirmarse:

- “tests OK” si no se ejecutaron;
- “certificado” si solo existe el documento;
- “integrado” si solo existe el ZIP;
- “validado” si no se probó;
- “sin errores” si no se conoce.

La confianza del proyecto depende de esta regla.

---

# 80. REGLA DE CONTINUIDAD

Cada sprint debe dejar suficiente contexto para que otra persona continúe sin depender del chat anterior.

Debe indicar:

- punto exacto;
- archivos;
- estado;
- evidencia;
- pendientes;
- siguiente acción.

---

# 81. REGLA DE NO REPETICIÓN

Una vez definido y aprobado un contrato, no debe repetirse indefinidamente la explicación.

Se pasa a:

- auditar;
- desarrollar;
- probar;
- entregar.

---

# 82. REGLA DE PARCIALIDAD HONESTA

Si no puede completarse todo:

- entregar lo completado;
- indicar lo pendiente;
- no simular;
- no bloquear el proyecto innecesariamente.

---

# 83. REGLA DE TRAZABILIDAD TOTAL

Todo cambio significativo debe poder responder:

- quién;
- qué;
- cuándo;
- por qué;
- dónde;
- cómo;
- con qué prueba;
- con qué resultado;
- qué depende después.

---

# 84. DEFINICIÓN DE SPRINT EXITOSO

Un sprint es exitoso cuando:

- resuelve el problema;
- no rompe;
- puede demostrarse;
- se entiende;
- se puede mantener;
- queda documentado;
- ayuda al usuario real.

---

# 85. PANEL DE CONTROL DE UN SPRINT

Formato recomendado:

```text
SPRINT:
ESTADO:
OBJETIVO:
VERSIÓN BASE:
ARCHIVOS:
TESTS:
DIAGNÓSTICO:
VALIDACIÓN:
LIMITACIONES:
RIESGOS:
SIGUIENTE PASO:
```

---

# 86. MATRIZ DE MADUREZ

```text
NIVEL 0 — Idea
NIVEL 1 — Definido
NIVEL 2 — Implementado
NIVEL 3 — Probado
NIVEL 4 — Diagnosticado
NIVEL 5 — Validado manualmente
NIVEL 6 — Certificado técnicamente
NIVEL 7 — Validado en cocina
NIVEL 8 — Cerrado
```

---

# 87. USO DE LA MATRIZ

Ejemplo:

```text
PILOTO-1.3 — Nivel 6
PILOTO-1.4 — Nivel 5 parcial
DEVKIT-0.1 — Nivel 2 documental en progreso
```

La matriz no reemplaza el estado, lo complementa.

---

# 88. RESPONSABILIDADES

## Arquitecto

- coherencia;
- dependencias;
- reglas;
- alcance.

## Desarrollador

- implementación;
- tests;
- documentación técnica.

## Tester

- casos;
- regresión;
- evidencia.

## Usuario piloto

- validación manual;
- validación real;
- feedback.

## Certificador

- revisar evidencia;
- otorgar estado.

Una persona puede asumir varios roles, pero las responsabilidades deben diferenciarse.

---

# 89. CRITERIOS DE PRIORIZACIÓN

Orden:

1. seguridad;
2. pérdida de datos;
3. bloqueo operativo;
4. flujo diario;
5. dependencia;
6. fiabilidad;
7. UX;
8. automatización;
9. IA;
10. comercial.

---

# 90. SPRINT BLOQUEADO

Debe indicar:

- bloqueo;
- causa;
- dependencia;
- responsable;
- próxima revisión;
- trabajo alternativo permitido.

No debe quedar simplemente abandonado.

---

# 91. SPRINT CANCELADO

Debe conservar expediente.

Motivos:

- ya no aporta valor;
- solución absorbida;
- riesgo;
- dependencia;
- cambio de estrategia.

---

# 92. SPRINT SUSTITUIDO

Debe apuntar al nuevo identificador.

Ejemplo:

```text
SUSTITUIDO POR: PILOTO-2.1
```

---

# 93. SPRINT EXPERIMENTAL

Debe ejecutarse fuera de estable.

No debe escribir datos reales.

Debe tener fecha de caducidad.

---

# 94. GESTIÓN DE VERSIONES

Cada entrega debe indicar:

- versión base;
- versión del sprint;
- fecha;
- commit o hash;
- compatibilidad.

---

# 95. COMPATIBILIDAD

Tipos:

- compatible;
- requiere parche anterior;
- requiere migración;
- incompatible;
- experimental.

---

# 96. REVOCACIÓN DE CERTIFICACIÓN

Puede ocurrir por:

- bug crítico;
- pérdida de datos;
- evidencia falsa;
- incompatibilidad;
- test incorrecto.

Debe actualizar:

- estado;
- certificación;
- pendientes;
- roadmap.

---

# 97. ARCHIVO HISTÓRICO

Los sprints cerrados deben conservarse.

No eliminar:

- contratos;
- certificaciones;
- decisiones;
- lecciones;
- manifests.

---

# 98. REVISIÓN PERIÓDICA

Cada cierto número de sprints:

- revisar roadmap;
- deuda;
- arquitectura;
- duplicidad;
- pruebas;
- documentación.

Recomendación:

```text
cada 5–10 sprints
```

---

# 99. CRITERIO PARA PASAR AL SIGUIENTE SPRINT

No basta con que el ZIP exista.

Debe quedar claro:

- qué estado alcanzó;
- qué queda pendiente;
- si la dependencia es suficiente;
- si el riesgo es aceptable.

---

# 100. ORDEN ACTUAL

Según el estado vigente:

1. terminar Knowledge Core;
2. consolidar versión;
3. validar completamente PILOTO-1.4;
4. abrir PILOTO-1.4.1;
5. continuar PILOTO-1.5.

---

# 101. CONTROL DE CAMBIOS

## Versión 1.0 — 13 de julio de 2026

Creación inicial del estándar.

Incluye:

- tipos;
- estados;
- contrato;
- expediente;
- pruebas;
- certificación;
- Git;
- plantillas;
- checklists;
- ejemplos;
- madurez;
- cierre.

Próxima revisión:

- al automatizar gestión de sprints;
- al cerrar DEVKIT-0.1;
- al aplicar el estándar al primer sprint nuevo.

---

# 102. ESTATUS OFICIAL

Ruta oficial:

```text
DEVKIT/
└── KNOWLEDGE_CORE/
    └── 05_SPRINTS.md
```

Debe leerse junto con:

```text
01_IDENTIDAD.md
03_REGLAS.md
04_ROADMAP.md
09_ESTADO_ACTUAL.md
```

---

**Fin del documento oficial `05_SPRINTS.md`.**
