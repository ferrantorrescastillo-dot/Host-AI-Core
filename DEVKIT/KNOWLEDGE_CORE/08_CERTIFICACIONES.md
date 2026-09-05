# HOST AI — 08_CERTIFICACIONES

> Sistema oficial de calidad y certificación  
> Estado: Oficial  
> Ámbito: DEVKIT / Memoria viva  
> Versión del documento: 1.0  
> Fecha de creación: 13 de julio de 2026  
> Documentos relacionados: `01_IDENTIDAD.md`, `03_REGLAS.md`, `04_ROADMAP.md`, `05_SPRINTS.md`, `09_ESTADO_ACTUAL.md`

---

---

# 1. PROPÓSITO

Este documento define cómo se certifican las funcionalidades, sprints, motores, servicios, flujos, documentos y versiones de Host AI.

Su objetivo es evitar que el proyecto confunda código creado, entregado, ejecutado, probado, validado manualmente, usado en cocina y realmente fiable.

Certificar significa aportar evidencia suficiente, vinculada a una versión concreta, para sostener una afirmación de calidad.

---

# 2. PRINCIPIO FUNDAMENTAL

> Ninguna certificación puede ser más fuerte que la evidencia que la sostiene.

Un archivo llamado `CERTIFICACION.md` no certifica por sí solo.  
Un test aislado no certifica todo un flujo.  
Una prueba manual no sustituye la regresión.  
Una ruta validada no certifica todas las rutas.

---

# 3. QUÉ SIGNIFICA CERTIFICAR

Certificar una parte de Host AI significa declarar, con evidencia, que:

- cumple un objetivo definido;
- funciona sobre una versión identificada;
- ha pasado las pruebas exigidas;
- no rompe componentes protegidos dentro del alcance revisado;
- sus limitaciones son conocidas;
- su estado puede auditarse;
- existe una base razonable para confiar en ella.

Toda certificación debe especificar alcance y fuera de alcance.

---

# 4. QUÉ NO ES UNA CERTIFICACIÓN

No es:

- una promesa;
- una opinión;
- una captura aislada;
- una ausencia de errores visibles;
- un documento sin ejecución;
- un test feliz;
- una garantía absoluta;
- una frase como “funciona perfecto”.

---

# 5. TIPOS OFICIALES DE CERTIFICACIÓN

## 5.1 Documental

Valida documentos oficiales, coherencia, versión y alineación.

## 5.2 Técnica

Valida código, tests, integración, regresión y diagnóstico.

## 5.3 Manual

Confirma que un usuario recorrió el flujo.

## 5.4 Operativa

Confirma que el flujo es útil y comprensible.

## 5.5 Cocina real

Confirma uso durante trabajo real.

## 5.6 Datos

Valida estructura, integridad, migración y calidad.

## 5.7 Arquitectura

Valida responsabilidades, dependencias y contratos.

## 5.8 Seguridad

Valida permisos, secretos, backups, rollback y trazabilidad.

## 5.9 Rendimiento

Valida comportamiento con volumen y entorno definidos.

## 5.10 IA

Valida intención, incertidumbre, coste, fallback, privacidad y ausencia de invención operativa.

---

# 6. NIVELES DE CONFIANZA

```text
C0 — No evaluado
C1 — Creado
C2 — Entregado
C3 — Ejecutado
C4 — Probado
C5 — Diagnosticado
C6 — Validado manualmente
C7 — Certificado técnicamente
C8 — Validado operativamente
C9 — Validado en cocina real
C10 — Cerrado y estable
```

El nivel debe corresponder a evidencia real, no al nombre del sprint.

---

# 7. REGLA DE ALCANCE

Toda certificación debe indicar:

- qué certifica;
- qué no certifica;
- versión;
- entorno;
- datos;
- pruebas;
- limitaciones;
- dependencias.

Ejemplo correcto:

> PILOTO-1.4 certificado manualmente para la ruta de stock insuficiente y bloqueo seguro.

Ejemplo incorrecto:

> Stock certificado.

---

# 8. EVIDENCIAS ADMITIDAS

- salida de tests;
- informe de regresión;
- diagnóstico;
- logs;
- prueba manual;
- prueba en cocina;
- capturas contextualizadas;
- commit;
- tag;
- hash;
- manifest;
- backup;
- comparación antes/después;
- auditoría.

La evidencia debe ser identificable, comprensible y vinculada a versión.

---

# 9. EVIDENCIAS INSUFICIENTES POR SÍ SOLAS

- “parece que funciona”;
- ausencia de error visible;
- un documento sin ejecución;
- código revisado sin ejecutar;
- una única ruta feliz;
- test modificado para pasar;
- captura sin contexto;
- resultado sin versión.

---

# 10. PASAPORTE DE CALIDAD

Cada componente importante podrá tener un Pasaporte de Calidad.

Ruta recomendada:

```text
DEVKIT/
└── CALIDAD/
    └── PASAPORTES/
        └── <COMPONENTE>.md
```

Campos mínimos:

```text
COMPONENTE:
TIPO:
VERSIÓN:
NIVEL:
ALCANCE:
EVIDENCIAS:
TESTS:
DIAGNÓSTICO:
VALIDACIÓN MANUAL:
VALIDACIÓN REAL:
LIMITACIONES:
RIESGOS:
DEPENDENCIAS:
ÚLTIMA REVISIÓN:
RESPONSABLE:
```

---

# 11. EJEMPLO DE PASAPORTE

```markdown
# PASAPORTE — PILOTO-1.3

## Nivel
C7 — Certificado técnicamente

## Alcance
Producción guiada sobre el motor existente.

## Evidencias
- Diagnóstico OK.
- Planes y tareas detectados.
- Siguiente acción calculada.
- Escrituras delegadas.

## Validación manual
Sí.

## Validación en cocina
Pendiente.

## Limitaciones
No validado durante varias jornadas reales.
```

---

# 12. MATRIZ GENERAL

Formato:

```text
COMPONENTE | CÓDIGO | TESTS | DIAG | MANUAL | COCINA | NIVEL | ESTADO
```

Ejemplo:

```text
PILOTO-1.3 | Sí | Sí | Sí | Sí | No | C7 | Certificado técnicamente
PILOTO-1.4 | Sí | Sí | Sí | Parcial | No | C6 parcial | Validación parcial
DEVKIT-0.1 | Parcial | N/A | N/A | Sí | N/A | C2 | En desarrollo
```

---

# 13. CERTIFICACIÓN DE SPRINTS

Un sprint puede certificarse cuando:

- tiene contrato;
- existe código o entregable;
- los tests pasan;
- el diagnóstico es correcto;
- la regresión es aceptable;
- la versión está identificada;
- la documentación coincide;
- las limitaciones están registradas;
- la memoria viva está actualizada.

---

# 14. CERTIFICACIÓN TÉCNICA

Requisitos mínimos:

- versión base;
- archivos modificados;
- tests específicos;
- regresión;
- diagnóstico;
- manifest;
- changelog;
- limitaciones;
- resultado.

---

# 15. CERTIFICACIÓN MANUAL

Debe registrar:

- usuario;
- fecha;
- pasos;
- resultado esperado;
- resultado observado;
- incidencias;
- decisión.

---

# 16. CERTIFICACIÓN EN COCINA

Debe registrar:

- contexto real;
- servicio o evento;
- duración;
- usuarios;
- problemas;
- utilidad;
- fricciones;
- impacto;
- conclusión.

---

# 17. CERTIFICACIÓN DOCUMENTAL

Un documento del Knowledge Core se certifica si:

- está en ruta oficial;
- tiene versión y fecha;
- tiene propósito;
- no contradice identidad ni reglas;
- distingue hechos y planes;
- está revisado;
- se incorpora al repositorio.

---

# 18. CERTIFICACIÓN DE MOTORES

Debe validar:

- entradas;
- salidas;
- errores;
- límites;
- duplicados;
- persistencia;
- transacciones;
- contratos;
- idempotencia cuando aplique;
- rendimiento cuando aplique.

---

# 19. CERTIFICACIÓN DE SERVICIOS

Debe validar:

- coordinación correcta;
- delegación;
- no duplicidad;
- manejo de errores;
- trazabilidad;
- compatibilidad;
- integración con motores.

---

# 20. CERTIFICACIÓN DE APP Y CONSOLA

Debe validar:

- claridad;
- flujo;
- cancelación;
- mensajes;
- errores;
- acciones;
- ausencia de lógica crítica;
- comprensión por el usuario.

---

# 21. CERTIFICACIÓN DE DATOS

Debe revisar:

- número de registros;
- duplicados;
- nulos;
- unidades;
- relaciones;
- origen;
- errores;
- integridad;
- migración.

---

# 22. CERTIFICACIÓN DE IMPORTADORES

Debe validar:

- lectura;
- normalización;
- coincidencias;
- ambigüedades;
- vista previa;
- escritura segura;
- backup;
- auditoría;
- repetición sin duplicados.

---

# 23. CERTIFICACIÓN DE IA

Debe validar:

- intención;
- casos correctos;
- ambigüedad;
- rechazo;
- incertidumbre;
- coste;
- seguridad;
- fallback;
- no invención;
- confirmación antes de escribir.

---

# 24. CERTIFICACIÓN DE MIGRACIONES

Requisitos:

- backup;
- dry-run;
- conteos;
- integridad;
- idempotencia;
- rollback;
- logs;
- reconciliación.

---

# 25. PROCEDIMIENTO OFICIAL

```text
1. Identificar versión
2. Revisar contrato
3. Ejecutar tests
4. Ejecutar regresión
5. Ejecutar diagnóstico
6. Revisar escrituras
7. Validar manualmente
8. Registrar limitaciones
9. Emitir informe
10. Actualizar Pasaporte
11. Actualizar 08_CERTIFICACIONES.md
12. Actualizar 09_ESTADO_ACTUAL.md
13. Etiquetar versión cuando proceda
```

---

# 26. INFORME DE CERTIFICACIÓN

Debe contener:

```text
ID:
COMPONENTE:
VERSIÓN:
TIPO:
ALCANCE:
FUERA DE ALCANCE:
ENTORNO:
EVIDENCIAS:
TESTS:
REGRESIÓN:
DIAGNÓSTICO:
VALIDACIÓN:
LIMITACIONES:
RIESGOS:
RESULTADO:
NIVEL:
FECHA:
RESPONSABLE:
```

---

# 27. RESULTADOS POSIBLES

- APROBADO
- APROBADO CON LIMITACIONES
- VALIDACIÓN PARCIAL
- BLOQUEADO
- RECHAZADO
- REVOCADO

---

# 28. LIMITACIONES

Toda certificación debe registrar limitaciones.

Ejemplos:

- solo probado en Windows;
- solo con SQLite;
- no probado con múltiples usuarios;
- no validado en cocina;
- no incluye lotes;
- solo datos sintéticos.

---

# 29. REVOCACIÓN

Debe revocarse si:

- aparece pérdida de datos;
- la evidencia era incorrecta;
- cambia una dependencia;
- falla regresión;
- se modifica el componente;
- aparece un bug crítico;
- la versión certificada deja de ser la activa.

---

# 30. PROCEDIMIENTO DE REVOCACIÓN

```text
1. Registrar incidencia
2. Identificar certificación afectada
3. Cambiar estado a REVOCADA
4. Explicar motivo
5. Identificar versiones afectadas
6. Actualizar estado
7. Abrir hotfix o sprint
8. Recertificar después
```

---

# 31. RECERTIFICACIÓN

Se realiza cuando cambia:

- código;
- datos;
- configuración;
- entorno;
- contrato;
- dependencia;
- alcance.

Debe indicar qué evidencia anterior se reutiliza y qué evidencia nueva se genera.

---

# 32. VIGENCIA

Estados posibles:

```text
VIGENTE
EN REVISIÓN
OBSOLETA
REVOCADA
```

Una certificación puede quedar obsoleta por antigüedad, cambio de versión, migración, refactor o cambio de entorno.

---

# 33. VINCULACIÓN A GIT

Toda certificación técnica debería vincularse a:

- commit;
- tag;
- hash;
- manifest;
- fecha.

Sin esta vinculación, debe considerarse una certificación más débil.

---

# 34. VINCULACIÓN A ZIP

Si se entrega mediante ZIP debe indicar:

- archivos;
- hash;
- versión base;
- orden de aplicación;
- dependencias;
- diagnóstico;
- manifest.

---

# 35. VINCULACIÓN A TESTS

Debe conservar:

- comando;
- fecha;
- entorno;
- número de tests;
- fallos;
- resultado;
- duración cuando importe.

---

# 36. VINCULACIÓN A MEMORIA VIVA

Al certificar debe actualizarse:

- `08_CERTIFICACIONES.md`;
- `09_ESTADO_ACTUAL.md`;
- `04_ROADMAP.md` si cambia de fase;
- `05_SPRINTS.md` si cambia metodología;
- `10_PENDIENTES.md`.

---

# 37. REGISTRO MAESTRO

Formato:

```text
ID | COMPONENTE | VERSIÓN | TIPO | NIVEL | ESTADO | FECHA | EVIDENCIA
```

---

# 38. ESTADO ACTUAL — PILOTO-0.1

Estado:

```text
CERTIFICADO HISTÓRICAMENTE
```

Nivel estimado:

```text
C7 histórico
```

Acción:

- recertificar sobre una versión consolidada.

---

# 39. ESTADO ACTUAL — PILOTO-1.0

Estado:

```text
CERTIFICADO HISTÓRICAMENTE
```

Pendiente:

- validación prolongada con recepciones reales.

---

# 40. ESTADO ACTUAL — PILOTO-1.1

Estado:

```text
CERTIFICADO HISTÓRICAMENTE
```

Nivel estimado:

```text
C7 histórico
```

---

# 41. ESTADO ACTUAL — PILOTO-1.2

Estado:

```text
CERTIFICADO HISTÓRICAMENTE
```

Nivel estimado:

```text
C7 histórico
```

---

# 42. ESTADO ACTUAL — PILOTO-1.2.1

Estado:

```text
ENTREGADO
CERTIFICACIÓN TÉCNICA DISPONIBLE
VALIDACIÓN MANUAL COMPLETA PENDIENTE
```

Nivel:

```text
C5–C7 provisional
```

---

# 43. ESTADO ACTUAL — PILOTO-1.3

Estado:

```text
DIAGNOSTICADO
VALIDADO MANUALMENTE
CERTIFICADO TÉCNICAMENTE
```

Nivel:

```text
C7
```

---

# 44. ESTADO ACTUAL — PILOTO-1.4

Estado:

```text
VALIDACIÓN PARCIAL
```

Validado:

- stock insuficiente;
- bloqueo;
- replanificación.

Pendiente:

- ruta de éxito;
- entrada del producto terminado;
- duplicado;
- rollback;
- trazabilidad visible.

Nivel:

```text
C6 parcial
```

---

# 45. ESTADO ACTUAL — PILOTO-1.4.1

Estado:

```text
NO DESARROLLADO
```

Nivel:

```text
C0
```

---

# 46. ESTADO ACTUAL — DEVKIT

```text
01_IDENTIDAD.md       | C2 documental
03_REGLAS.md          | C2 documental
04_ROADMAP.md         | C2 documental
05_SPRINTS.md         | C2 documental
08_CERTIFICACIONES.md | C2 documental
09_ESTADO_ACTUAL.md   | C2 documental
```

Pendiente para todos:

- revisión consolidada;
- incorporación al repositorio;
- commit;
- revisión cruzada.

---

# 47. MATRIZ RESUMIDA

```text
PILOTO-0.1   | C7 histórico | Recertificar
PILOTO-1.0   | C7 histórico | Validación real pendiente
PILOTO-1.1   | C7 histórico | Vigente provisional
PILOTO-1.2   | C7 histórico | Vigente provisional
PILOTO-1.2.1 | C5–C7        | Manual pendiente
PILOTO-1.3   | C7            | Validado manualmente
PILOTO-1.4   | C6 parcial    | Ruta exitosa pendiente
PILOTO-1.4.1 | C0            | No desarrollado
DEVKIT-0.1   | C2 parcial    | En desarrollo
```

---

# 48. CERTIFICACIONES HISTÓRICAS

Toda certificación previa debe clasificarse como:

- vigente;
- histórica;
- provisional;
- obsoleta;
- revocada.

No deben eliminarse los documentos históricos.

---

# 49. CERTIFICACIONES PROVISIONALES

Se usan cuando:

- existe evidencia técnica;
- falta validación real;
- la versión no está consolidada;
- faltan pruebas de entorno.

Deben tener fecha de revisión.

---

# 50. CERTIFICACIONES PARCIALES

Deben indicar rutas concretas.

Ejemplo:

```text
PILOTO-1.4:
- Falta de stock: validada.
- Cierre exitoso: pendiente.
- Duplicado: pendiente.
```

---

# 51. PASAPORTES PRIORITARIOS

1. PILOTO-1.3
2. PILOTO-1.4
3. Mi Jornada
4. MotorProduccionReal
5. MotorStock
6. Recepción inteligente
7. Importador I1.3
8. DEVKIT-0.1

---

# 52. CHECKLIST TÉCNICO

- [ ] Versión identificada.
- [ ] Contrato revisado.
- [ ] Código integrado.
- [ ] Tests específicos.
- [ ] Regresión.
- [ ] Diagnóstico.
- [ ] Datos aislados.
- [ ] Escrituras revisadas.
- [ ] Duplicados controlados.
- [ ] Rollback validado.
- [ ] Limitaciones.
- [ ] Manifest.
- [ ] Changelog.
- [ ] Informe.
- [ ] Memoria actualizada.

---

# 53. CHECKLIST MANUAL

- [ ] Flujo completo.
- [ ] Cancelación.
- [ ] Error.
- [ ] Mensajes.
- [ ] Resultado.
- [ ] Persistencia.
- [ ] Reapertura.
- [ ] Evidencia.
- [ ] Incidencias.

---

# 54. CHECKLIST COCINA REAL

- [ ] Situación real.
- [ ] Usuario real.
- [ ] Datos reales controlados.
- [ ] Jornada o evento.
- [ ] Fricciones.
- [ ] Tiempo.
- [ ] Errores.
- [ ] Utilidad.
- [ ] Confianza.
- [ ] Decisión.

---

# 55. CHECKLIST DOCUMENTAL

- [ ] Ruta oficial.
- [ ] Versión.
- [ ] Fecha.
- [ ] Propósito.
- [ ] Coherencia.
- [ ] Sin contradicciones.
- [ ] Hechos y planes separados.
- [ ] Referencias.
- [ ] Revisión.
- [ ] Commit.

---

# 56. PLANTILLA DE PASAPORTE

```markdown
# PASAPORTE DE CALIDAD — <COMPONENTE>

## Identidad
- Tipo:
- Versión:
- Estado:
- Nivel:

## Alcance
## Fuera de alcance
## Evidencias
## Tests
## Diagnóstico
## Validación manual
## Validación en cocina
## Limitaciones
## Riesgos
## Dependencias
## Historial
## Última revisión
```

---

# 57. PLANTILLA DE CERTIFICACIÓN

```markdown
# CERTIFICACIÓN — <ID>

## Componente
## Versión
## Tipo
## Alcance
## Entorno
## Evidencias
## Tests
## Regresión
## Diagnóstico
## Validación
## Limitaciones
## Resultado
## Nivel
## Estado
## Fecha
```

---

# 58. PLANTILLA DE REVOCACIÓN

```markdown
# REVOCACIÓN

## Certificación afectada
## Motivo
## Fecha
## Versiones afectadas
## Riesgo
## Medida inmediata
## Sprint correctivo
## Estado
```

---

# 59. REGLA DE HONESTIDAD

No escribir:

- “100 %”;
- “sin fallos”;
- “perfecto”;
- “totalmente seguro”;

sin evidencia extraordinaria.

Usar:

- dentro del alcance;
- con las limitaciones indicadas;
- validado para estas rutas;
- pendiente de estas comprobaciones.

---

# 60. REGLA DE VERSIONADO

Una certificación sin versión es una opinión.

Debe indicar:

- commit o ZIP;
- hash;
- fecha;
- versión base;
- parches;
- entorno.

---

# 61. REGLA DE REPRODUCIBILIDAD

Otra persona debe poder repetir la certificación.

Debe disponer de:

- comandos;
- datos;
- entorno;
- pasos;
- resultado esperado.

---

# 62. REGLA DE NO HERENCIA AUTOMÁTICA

Certificar un servicio no certifica toda la aplicación.

Certificar un motor no certifica toda la interfaz.

Certificar una ruta no certifica todas las rutas.

---

# 63. REGLA DE DEPENDENCIAS

Si cambia una dependencia crítica deben revisarse las certificaciones relacionadas.

Ejemplo:

Cambiar `MotorStock` obliga a revisar:

- Producción → Stock;
- Recepción → Stock;
- Compras;
- Eventos;
- Costes.

---

# 64. REGLA DE DATOS

Una certificación con datos sintéticos debe indicarlo.

La validación con datos reales debe realizarse sobre copia o entorno controlado.

---

# 65. REGLA DE SEGURIDAD

No certificar escrituras críticas sin:

- backup;
- validación;
- rollback o compensación;
- trazabilidad;
- prueba de error.

---

# 66. REGLA DE UX

Un flujo puede funcionar técnicamente y no estar certificado operativamente si:

- no se entiende;
- genera dudas;
- tiene demasiados pasos;
- usa lenguaje técnico;
- no propone salida.

---

# 67. AUTOMATIZACIÓN FUTURA

Comandos previstos:

```text
host certificar
host certificar <sprint>
host pasaporte <componente>
host revocar <certificacion>
host recertificar <componente>
```

---

# 68. ESTRUCTURA FUTURA

```text
DEVKIT/
├── CALIDAD/
│   ├── CERTIFICACIONES/
│   ├── PASAPORTES/
│   ├── EVIDENCIAS/
│   ├── REVOCACIONES/
│   └── MATRICES/
```

---

# 69. INDICADORES GLOBALES

- sprints C7 o superior;
- flujos C9;
- certificaciones obsoletas;
- regresiones fallidas;
- bugs post-certificación;
- componentes sin pasaporte;
- dependencias sin cobertura;
- tiempo de recertificación.

---

# 70. SEMÁFORO

## Verde

Versión, evidencia, tests, diagnóstico y validación suficientes.

## Amarillo

Validación parcial, limitaciones o versión no consolidada.

## Rojo

Pérdida de datos, regresión, evidencia falsa o versión desconocida.

---

# 71. PANEL ACTUAL

```text
PROYECTO:
Host AI 6.0

SITUACIÓN:
Certificaciones históricas dispersas.

FORTALEZA:
Existen tests, diagnósticos y certificados por sprint.

DEBILIDAD:
No están vinculados todavía a una versión consolidada única.

MEJOR EVIDENCIA ACTUAL:
PILOTO-1.3 diagnosticado y validado manualmente.

RIESGO PRINCIPAL:
Confundir documento de certificación con ejecución real.

PRIORIDAD:
Consolidar versión y recertificar líneas críticas.
```

---

# 72. ORDEN DE RECERTIFICACIÓN

1. Arranque y modo piloto.
2. Mi Jornada.
3. Producción guiada.
4. Producción → Stock.
5. Recepción inteligente.
6. Bandeja.
7. Importador I1.3.
8. Stock.
9. Compras.
10. Eventos.

---

# 73. DIFERENCIAS CLAVE

## Certificado vs cerrado

Certificado: cumple evidencia actual.  
Cerrado: además está integrado, validado y sin pendientes críticos.

## Probado vs validado

Probado: tests.  
Validado: comportamiento observado en contexto.

## Operativo vs usable

Operativo: ejecuta.  
Usable: ayuda y se entiende.

---

# 74. ERRORES A EVITAR

- certificar por nombre de archivo;
- certificar sin versión;
- certificar solo ruta feliz;
- olvidar regresión;
- ocultar limitaciones;
- no registrar revocación;
- heredar certificaciones automáticamente;
- mezclar histórico y vigente;
- declarar cocina real sin uso real.

---

# 75. DECISIONES OFICIALES

1. Las certificaciones tendrán nivel.
2. El nivel depende de evidencia.
3. PILOTO exige validación manual.
4. Cocina real es un nivel separado.
5. Las certificaciones pueden revocarse.
6. Toda certificación se vincula a versión.
7. Existirá Pasaporte de Calidad.
8. Habrá matriz general.
9. Se conserva el histórico.
10. No se exagerará el estado del proyecto.

---

# 76. PRÓXIMOS PASOS

1. Incorporar este documento.
2. Crear `10_PENDIENTES.md`.
3. Consolidar el ZIP completo.
4. Crear `02_ARQUITECTURA.md`.
5. Crear pasaporte de PILOTO-1.3.
6. Crear pasaporte de PILOTO-1.4.
7. Recertificar versión consolidada.
8. Automatizar después.

---

# 77. CONTROL DE CAMBIOS

## Versión 1.0 — 13 de julio de 2026

Creación inicial.

Incluye:

- tipos;
- niveles;
- evidencias;
- pasaportes;
- matrices;
- revocación;
- recertificación;
- plantillas;
- estado actual.

Próxima revisión:

- al consolidar versión;
- al crear el primer pasaporte;
- al automatizar `host certificar`.

---

# 78. ESTATUS OFICIAL

Ruta oficial:

```text
DEVKIT/
└── KNOWLEDGE_CORE/
    └── 08_CERTIFICACIONES.md
```

Debe mantenerse alineado con:

```text
01_IDENTIDAD.md
03_REGLAS.md
04_ROADMAP.md
05_SPRINTS.md
09_ESTADO_ACTUAL.md
```

---

## Registro — Fase 1 Importación Inteligente

- Versión base histórica: `86e1f1a0`; el cierre definitivo corresponde al commit posterior al smoke humano final.
- Tipo: certificación técnica y validación humana del flujo de importación inteligente.
- Nivel: C7 dentro del alcance técnico y funcional validado.
- Evidencia: `DEVKIT/CERTIFICACION_TECNICA_FASE1_IMPORTACION.md`, tests focales, regresión frontend, E2E Chrome y smoke humano final aprobado.
- Datos: fixtures y runtimes temporales; ninguna confirmación ni WRITE sobre `DATOS/` real durante la validación de cierre.
- Estado: `CERRADA / CERTIFICADA` el 5 de septiembre de 2026.
- Alcance excluido: Fase 1.5 no iniciada y calidad culinaria de propuestas automáticas sujeta a validación operativa posterior.

---

**Fin del documento oficial `08_CERTIFICACIONES.md`.**
