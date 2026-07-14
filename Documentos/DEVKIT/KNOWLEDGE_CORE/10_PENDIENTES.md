# HOST AI — 10_PENDIENTES

> Backlog maestro oficial del proyecto  
> Estado: Oficial  
> Ámbito: DEVKIT / Memoria viva  
> Versión: 1.0  
> Fecha: 13 de julio de 2026  
> Relacionado con: `01_IDENTIDAD.md`, `03_REGLAS.md`, `04_ROADMAP.md`, `05_SPRINTS.md`, `08_CERTIFICACIONES.md`, `09_ESTADO_ACTUAL.md`

---

# 1. PROPÓSITO

Este documento define cómo Host AI registra, clasifica, prioriza, revisa y cierra sus pendientes.

No es una lista informal de tareas. Es el backlog maestro oficial del proyecto.

Debe evitar que:

- las ideas se pierdan;
- los bugs queden olvidados;
- la deuda técnica crezca sin control;
- varios pendientes describan lo mismo;
- cualquier idea se convierta directamente en sprint;
- se mezclen urgencias reales con ideas futuras;
- el proyecto dependa de la memoria de un chat.

---

# 2. PRINCIPIO FUNDAMENTAL

> Todo pendiente debe conservar suficiente contexto para que pueda entenderse y retomarse meses después sin depender de la conversación en la que apareció.

Un pendiente debe explicar:

- qué ocurrió;
- por qué importa;
- dónde afecta;
- qué evidencia existe;
- qué prioridad tiene;
- qué dependencias presenta;
- qué sprint podría resolverlo;
- cómo se sabrá que está resuelto.

---

# 3. QUÉ ES UN PENDIENTE

Un pendiente es una necesidad, problema, riesgo, mejora, deuda o investigación todavía no resuelta que merece seguimiento.

Debe cumplir al menos una condición:

- afecta al uso real;
- puede generar errores;
- bloquea otro desarrollo;
- reduce fiabilidad;
- mejora significativamente la experiencia;
- representa deuda técnica;
- necesita investigación;
- requiere certificación;
- pertenece a una fase futura del roadmap.

---

# 4. QUÉ NO ES UN PENDIENTE

No es:

- una idea sin contexto;
- una frase suelta;
- una preferencia momentánea;
- una tarea ya resuelta;
- un sprint ya abierto;
- una conversación repetida;
- una mejora sin valor operativo;
- un recordatorio personal sin impacto en Host AI.

---

# 5. TIPOS OFICIALES

## 5.1 BUG

Comportamiento incorrecto respecto al esperado.

## 5.2 BLOQUEO

Impide continuar un flujo, sprint o validación.

## 5.3 MEJORA

Aumenta utilidad o eficiencia sin corregir un fallo.

## 5.4 UX

Mejora específica de experiencia de usuario.

## 5.5 DEUDA_TECNICA

Problema estructural que aumenta el coste futuro.

## 5.6 REFACTOR

Reorganización técnica sin cambio funcional esperado.

## 5.7 ARQUITECTURA

Cambio o revisión de responsabilidades, contratos o dependencias.

## 5.8 DATOS

Calidad, migración, duplicidad o integridad.

## 5.9 DOCUMENTACION

Creación o corrección de memoria oficial.

## 5.10 CERTIFICACION

Prueba, recertificación o evidencia pendiente.

## 5.11 INVESTIGACION

Pregunta técnica u operativa que necesita evidencia.

## 5.12 IA

Mejora, riesgo o desarrollo relacionado con inteligencia artificial.

## 5.13 SEGURIDAD

Permisos, secretos, backups, trazabilidad o pérdida de datos.

## 5.14 RENDIMIENTO

Tiempo, memoria, volumen o carga.

## 5.15 OPERATIVA

Necesidad detectada en cocina real.

## 5.16 NEGOCIO

Precio, soporte, modelo comercial o estrategia futura.

---

# 6. ESTADOS

```text
NUEVO
REGISTRADO
ANALIZADO
PRIORIZADO
LISTO_PARA_SPRINT
EN_SPRINT
EN_VALIDACION
RESUELTO
CERRADO
ARCHIVADO
```

Estados alternativos:

```text
BLOQUEADO
APLAZADO
DUPLICADO
DESCARTADO
SUSTITUIDO
REABIERTO
```

---

# 7. DEFINICIÓN DE ESTADOS

## NUEVO

Detectado, aún sin ficha completa.

## REGISTRADO

Tiene contexto mínimo y evidencia.

## ANALIZADO

Se conoce impacto, causa probable y dependencias.

## PRIORIZADO

Tiene prioridad y puntuación.

## LISTO_PARA_SPRINT

Dispone de definición suficiente para convertirse en sprint.

## EN_SPRINT

Está siendo resuelto.

## EN_VALIDACION

Existe solución y se está comprobando.

## RESUELTO

La solución cumple el criterio de resolución.

## CERRADO

Además está documentado y no quedan acciones abiertas.

## ARCHIVADO

Se conserva históricamente.

## BLOQUEADO

No puede avanzar por una dependencia.

## APLAZADO

Se revisará en otra fase o fecha.

## DUPLICADO

Está representado por otro pendiente.

## DESCARTADO

No se realizará, con motivo documentado.

## SUSTITUIDO

Otra solución reemplaza la necesidad.

## REABIERTO

Vuelve a activarse por nueva evidencia.

---

# 8. PRIORIDADES

```text
P0 — CRÍTICA
P1 — MUY ALTA
P2 — ALTA
P3 — MEDIA
P4 — BAJA
P5 — FUTURA
```

## P0 — CRÍTICA

- pérdida de datos;
- corrupción;
- operación peligrosa;
- seguridad grave;
- bloqueo total.

## P1 — MUY ALTA

- flujo diario bloqueado;
- cálculo crítico incorrecto;
- dependencia del siguiente sprint;
- regresión importante.

## P2 — ALTA

- afecta uso frecuente;
- reduce fiabilidad;
- validación importante pendiente;
- deuda con impacto cercano.

## P3 — MEDIA

- mejora útil;
- fricción no bloqueante;
- limpieza necesaria.

## P4 — BAJA

- mejora menor;
- refinamiento;
- documentación secundaria.

## P5 — FUTURA

- idea válida fuera de fase;
- comercial;
- plataforma;
- investigación a largo plazo.

---

# 9. SISTEMA DE PUNTUACIÓN

Puntuar de 0 a 5:

- impacto operativo;
- riesgo de datos;
- frecuencia;
- dependencia;
- urgencia;
- valor de validación;
- coste de no hacerlo;
- esfuerzo.

Fórmula orientativa:

```text
PUNTUACIÓN =
impacto × 3
+ riesgo × 3
+ frecuencia × 2
+ dependencia × 2
+ urgencia × 2
+ valor_validación
+ coste_no_hacer
- esfuerzo
```

La puntuación ayuda a ordenar, pero no sustituye el criterio profesional.

---

# 10. FICHA OFICIAL

```text
ID:
TÍTULO:
TIPO:
SUBTIPO:
ESTADO:
PRIORIDAD:
PUNTUACIÓN:
FECHA:
ORIGEN:

DESCRIPCIÓN:
SITUACIÓN REAL:
RESULTADO ACTUAL:
RESULTADO ESPERADO:

ÁREA:
ARCHIVOS O MÓDULOS:
VERSIÓN:
EVIDENCIA:

IMPACTO:
RIESGO:
FRECUENCIA:
URGENCIA:
ESFUERZO:

DEPENDENCIAS:
BLOQUEA:
BLOQUEADO_POR:

SOLUCIÓN PROPUESTA:
ALTERNATIVAS:
SPRINT PROPUESTO:

CRITERIO DE RESOLUCIÓN:
CRITERIO DE CIERRE:

RESPONSABLE:
ÚLTIMA REVISIÓN:
```

---

# 11. IDENTIFICADORES

Formato recomendado:

```text
PEND-0001
BUG-0001
DEUDA-0001
UX-0001
CERT-0001
FUT-0001
```

Los identificadores no deben reutilizarse.

---

# 12. TÍTULOS

Correcto:

> Redondear cantidades faltantes en bloqueo de stock.

Incorrecto:

> Mejorar cosas del stock.

---

# 13. EVIDENCIAS

Pueden ser:

- salida de consola;
- captura;
- log;
- test fallido;
- diagnóstico;
- archivo;
- consulta;
- pasos de reproducción;
- fecha y usuario.

---

# 14. EVITAR DUPLICADOS

Antes de crear:

1. buscar palabras clave;
2. revisar el área;
3. revisar tipo;
4. revisar cerrados;
5. revisar roadmap;
6. revisar deuda;
7. revisar certificaciones.

Si es duplicado:

- marcar `DUPLICADO`;
- enlazar al original;
- conservar evidencia adicional si aporta valor.

---

# 15. FUSIÓN Y DIVISIÓN

Fusionar si:

- comparten causa;
- requieren la misma solución;
- tienen alcance equivalente.

Dividir si:

- contiene varios problemas;
- mezcla UX y arquitectura;
- mezcla bug y mejora;
- tiene rutas independientes;
- no puede cerrarse con un único criterio.

---

# 16. CONVERSIÓN EN SPRINT

Puede convertirse si:

- el problema está entendido;
- pertenece a la fase activa;
- las dependencias están disponibles;
- el alcance puede definirse;
- puede probarse;
- aporta valor real.

Al convertirlo:

- conservar ID;
- enlazar sprint;
- cambiar a `EN_SPRINT`;
- crear contrato de sprint.

---

# 17. CUÁNDO NO CONVERTIRLO

No convertir si:

- es una idea sin evidencia;
- no pertenece a la fase activa;
- depende de algo inexistente;
- puede resolverse dentro de otro sprint;
- no tiene criterio de éxito;
- contradice identidad o reglas.

---

# 18. DESCARTE Y APLAZAMIENTO

Puede descartarse si:

- no aporta valor;
- contradice estrategia;
- el problema ya no existe;
- otra función lo sustituye;
- el coste supera el impacto.

Aplazar debe indicar:

- motivo;
- fase futura;
- condición de reactivación;
- fecha o evento de revisión;
- riesgo de esperar.

---

# 19. REVISIÓN PERIÓDICA

Recomendación:

- semanal durante desarrollo activo;
- al cerrar cada sprint;
- mensual para deuda técnica;
- trimestral para ideas futuras;
- al cambiar de fase.

La revisión debe:

- cerrar resueltos;
- detectar duplicados;
- recalcular prioridades;
- revisar bloqueos;
- actualizar dependencias;
- eliminar ruido.

---

# 20. RELACIÓN CON OTROS DOCUMENTOS

## Roadmap

Si altera el orden estratégico, actualizar `04_ROADMAP.md`.

## Sprints

Cada pendiente debe enlazar el sprint que lo resuelve.

## Certificaciones

Puede bloquear, reducir nivel o revocar una certificación.

## Estado actual

Los P0, P1 y bloqueos estratégicos deben aparecer en `09_ESTADO_ACTUAL.md`.

## Memoria técnica

La deuda y decisiones se trasladarán a `06_MEMORIA_TECNICA.md`.

## Memoria operativa

Los aprendizajes de cocina se trasladarán a `07_MEMORIA_OPERATIVA.md`.

---

# 21. GESTIÓN DE BUGS

Todo bug debe incluir:

- pasos para reproducir;
- resultado actual;
- resultado esperado;
- versión;
- severidad;
- datos afectados;
- workaround;
- evidencia.

Severidades:

```text
S0 — Pérdida de datos o seguridad
S1 — Flujo principal bloqueado
S2 — Resultado incorrecto importante
S3 — Error con alternativa
S4 — Visual o menor
```

---

# 22. GESTIÓN DE DEUDA TÉCNICA

Debe registrar:

- origen;
- motivo;
- riesgo;
- coste futuro;
- área;
- sprint propuesto.

Se prioriza si:

- bloquea nuevos sprints;
- genera bugs;
- duplica lógica;
- impide pruebas;
- aumenta riesgo de datos.

---

# 23. GESTIÓN DE UX

Debe explicar:

- situación;
- confusión;
- número de pasos;
- lenguaje actual;
- propuesta;
- impacto;
- evidencia del usuario.

No convertir preferencias estéticas en prioridad alta sin impacto operativo.

---

# 24. GESTIÓN DE INVESTIGACIONES

Debe formular una pregunta concreta.

Ejemplo:

> ¿Existe ya un modelo común de bloqueo reutilizable?

Resultados posibles:

- encontrado;
- no encontrado;
- parcial;
- requiere prototipo;
- descartado.

---

# 25. GESTIÓN DE BLOQUEOS

Debe indicar:

- qué está detenido;
- causa;
- responsable;
- solución temporal;
- condición de resolución;
- próxima revisión.

No dejar bloqueos sin dueño ni condición.

---

# 26. GESTIÓN DE IDEAS FUTURAS

Categorías:

- web;
- móvil;
- SaaS;
- multiempresa;
- marketplace;
- hardware;
- IA predictiva;
- integraciones externas.

Estado recomendado:

```text
APLAZADO — FASE FUTURA
```

---

# 27. PENDIENTES CRÍTICOS Y ALTOS ACTUALES

## PEND-0001 — Consolidar versión completa

Tipo:

```text
BLOQUEO / ARQUITECTURA
```

Prioridad:

```text
P1
```

Situación:

Existe ZIP base y varios parches.

Objetivo:

Crear una versión completa consolidada y trazada.

Bloquea:

- arquitectura real;
- recertificación global;
- desarrollo seguro del 1.4.1.

---

## PEND-0002 — Validar ruta exitosa de PILOTO-1.4

Tipo:

```text
CERTIFICACION / OPERATIVA
```

Prioridad:

```text
P1
```

Pendiente:

- stock suficiente;
- consumos;
- entrada del producto terminado;
- trazabilidad;
- duplicado;
- rollback.

---

## PEND-0003 — Terminar Knowledge Core

Tipo:

```text
DOCUMENTACION
```

Prioridad:

```text
P1
```

Pendientes:

- `02_ARQUITECTURA.md`;
- `06_MEMORIA_TECNICA.md`;
- `07_MEMORIA_OPERATIVA.md`.

---

## PEND-0004 — Auditar arquitectura real

Tipo:

```text
ARQUITECTURA
```

Prioridad:

```text
P1
```

Condición:

Versión consolidada disponible.

---

## PEND-0005 — Humanizar cantidades de bloqueos

Tipo:

```text
UX
```

Prioridad:

```text
P2
```

Situación:

Se muestran cantidades como `4.70448 kg`.

Resultado esperado:

Mostrar `4,70 kg`, manteniendo precisión interna.

---

## PEND-0006 — Desarrollar PILOTO-1.4.1

Tipo:

```text
OPERATIVA / UX / INTEGRACIÓN
```

Prioridad:

```text
P2
```

Bloqueado por:

- DEVKIT mínimo;
- validación completa de 1.4;
- auditoría de modelos y servicios existentes.

---

## PEND-0007 — Crear Pasaporte de Calidad de PILOTO-1.3

Prioridad:

```text
P2
```

---

## PEND-0008 — Crear Pasaporte de Calidad de PILOTO-1.4

Prioridad:

```text
P2
```

---

## PEND-0009 — Crear runner global de tests

Prioridad:

```text
P2
```

Objetivo futuro:

```text
host test
```

---

# 28. PENDIENTES MEDIOS ACTUALES

## PEND-0010

Clasificar documentación histórica como vigente, histórica, sustituida, certificación o auditoría.

## PEND-0011

Crear formato único de certificación.

## PEND-0012

Crear manifest de sprint.

## PEND-0013

Inventariar módulos activos.

## PEND-0014

Detectar módulos duplicados.

## PEND-0015

Revisar configuración dispersa.

## PEND-0016

Revisar cobertura de logs estructurados.

## PEND-0017

Revisar manejo central de errores.

---

# 29. IDEAS FUTURAS REGISTRADAS

## FUT-0001 — MCP

Estado:

```text
APLAZADO
```

Condiciones:

- seguridad;
- repositorio limpio;
- DEVKIT;
- permisos;
- arquitectura.

## FUT-0002 — Web

## FUT-0003 — Aplicación móvil

## FUT-0004 — SaaS multiempresa

## FUT-0005 — IA predictiva

## FUT-0006 — Multiestablecimiento

## FUT-0007 — API pública

Todas permanecen fuera de la fase activa.

---

# 30. PANEL DEL BACKLOG

```text
CRÍTICOS P0:
0 conocidos

MUY ALTOS P1:
4

ALTOS P2:
5

MEDIOS P3:
8 identificados

FUTUROS P5:
7 principales

BLOQUEO PRINCIPAL:
No existe versión consolidada

SIGUIENTE ACCIÓN:
Completar gobierno documental y consolidar código
```

---

# 31. MÉTRICAS

- pendientes abiertos;
- bugs por severidad;
- deuda por área;
- bloqueos;
- pendientes sin responsable;
- pendientes sin revisión;
- duplicados;
- tiempo medio abierto;
- pendientes convertidos en sprint;
- certificaciones bloqueadas.

---

# 32. BACKLOG SALUDABLE

Un backlog saludable:

- tiene títulos claros;
- no tiene duplicados;
- distingue fases;
- tiene prioridades;
- conserva evidencia;
- se revisa;
- cierra pendientes;
- descarta ideas sin valor;
- no es una lista infinita.

---

# 33. SEÑALES DE BACKLOG ENFERMO

- cientos de ideas sin prioridad;
- bugs sin versión;
- tareas antiguas sin revisión;
- duplicados;
- todo marcado urgente;
- nada se descarta;
- pendientes sin criterio de cierre;
- sprints abiertos directamente desde conversaciones.

---

# 34. CHECKLIST DE ALTA

- [ ] ID.
- [ ] Título.
- [ ] Tipo.
- [ ] Situación real.
- [ ] Resultado esperado.
- [ ] Evidencia.
- [ ] Área.
- [ ] Impacto.
- [ ] Prioridad inicial.
- [ ] Dependencias.
- [ ] Criterio de resolución.

---

# 35. CHECKLIST DE ANÁLISIS

- [ ] Reproducido o verificado.
- [ ] No es duplicado.
- [ ] Causa probable.
- [ ] Riesgo.
- [ ] Frecuencia.
- [ ] Esfuerzo.
- [ ] Bloqueos.
- [ ] Fase.
- [ ] Sprint posible.
- [ ] Puntuación.

---

# 36. CHECKLIST DE CIERRE

- [ ] Solución integrada.
- [ ] Evidencia.
- [ ] Tests.
- [ ] Validación.
- [ ] Certificación actualizada.
- [ ] Estado actualizado.
- [ ] Pendientes derivados.
- [ ] Memoria actualizada.
- [ ] Fecha.
- [ ] Responsable.

---

# 37. PLANTILLA MARKDOWN

```markdown
# <ID> — <TÍTULO>

## Clasificación
- Tipo:
- Estado:
- Prioridad:
- Puntuación:

## Situación real

## Resultado actual

## Resultado esperado

## Evidencia

## Impacto

## Riesgo

## Dependencias

## Solución propuesta

## Sprint propuesto

## Criterio de resolución

## Historial
```

---

# 38. HISTORIAL

Cada pendiente debe registrar:

```text
FECHA | CAMBIO | ESTADO | RESPONSABLE | MOTIVO
```

No sobrescribir el historial.

---

# 39. RESPONSABILIDAD

Todo P0, P1 o bloqueo debe tener responsable.

Responsable significa garantizar seguimiento, no necesariamente programarlo personalmente.

---

# 40. FECHA DE REVISIÓN

Todo aplazado debe indicar fecha o condición.

Ejemplo:

```text
Revisar al cerrar DEVKIT-0.1.
```

---

# 41. WORKAROUND

Si existe solución temporal debe registrarse.

No debe confundirse workaround con resolución definitiva.

---

# 42. CRITERIO DE RESOLUCIÓN

Debe ser verificable.

Ejemplo:

> Se considera resuelto cuando el ZIP consolidado arranca, ejecuta los diagnósticos 1.3 y 1.4 y Git muestra únicamente los cambios esperados.

---

# 43. REAPERTURA

Puede reabrirse si:

- reaparece;
- la solución era incompleta;
- cambia el entorno;
- una regresión lo reactiva;
- nueva evidencia amplía el alcance.

Debe conservar historial.

---

# 44. AUTOMATIZACIÓN FUTURA

Comandos previstos:

```text
host pendientes
host pendiente crear
host pendiente priorizar
host pendiente cerrar
host backlog revisar
```

No deben implementarse antes de definir el formato estructurado.

---

# 45. FORMATO ESTRUCTURADO FUTURO

Además del Markdown podrá existir:

```text
DEVKIT/BACKLOG/pendientes.json
```

o una tabla SQLite.

Los campos deberán alinearse con este documento.

---

# 46. REGLAS DE HONESTIDAD Y FOCO

No marcar como resuelto:

- porque existe código;
- porque se creó un ZIP;
- porque se escribió documentación;
- porque no volvió a verse;
- porque se aplazó.

La existencia de un pendiente no obliga a resolverlo ahora.

La prioridad debe respetar:

- fase;
- dependencias;
- valor;
- riesgo;
- capacidad.

---

# 47. REGLA DE COCINA REAL

Los pendientes surgidos en cocina deben registrar:

- qué hacía el usuario;
- qué esperaba;
- qué le frenó;
- qué hizo para continuar;
- cuánto impacto tuvo.

---

# 48. REGLA DE IA

Un pendiente de IA debe separar:

- fallo de modelo;
- fallo de prompt;
- dato faltante;
- motor incorrecto;
- interfaz;
- coste;
- seguridad.

No atribuir automáticamente a IA un fallo de datos o lógica.

---

# 49. REGLA DE CERTIFICACIÓN

Un bug posterior a una certificación debe:

- afectar al Pasaporte;
- revisar el nivel;
- valorar revocación;
- abrir pendiente o hotfix;
- registrar alcance.

---

# 50. DECISIONES OFICIALES

1. Existirá un backlog maestro.
2. Todo pendiente tendrá tipo y estado.
3. P0 y P1 tendrán responsable.
4. Se distinguirá prioridad, severidad y urgencia.
5. Se evitarán duplicados.
6. No toda idea se convertirá en sprint.
7. Los pendientes se vincularán a roadmap y certificaciones.
8. Se conservará historial.
9. El backlog se revisará periódicamente.
10. La evidencia prevalece sobre la percepción.

---

# 51. ORDEN RECOMENDADO

1. Incorporar `10_PENDIENTES.md`.
2. Consolidar todos los documentos.
3. Crear ZIP completo consolidado.
4. Validar PILOTO-1.4.
5. Crear `02_ARQUITECTURA.md`.
6. Crear `06_MEMORIA_TECNICA.md`.
7. Crear `07_MEMORIA_OPERATIVA.md`.
8. Cerrar DEVKIT-0.1.
9. Retomar PILOTO-1.4.1.

---

# 52. CONTROL DE CAMBIOS

## Versión 1.0 — 13 de julio de 2026

Creación inicial.

Incluye:

- tipos;
- estados;
- prioridades;
- puntuación;
- ficha;
- reglas;
- pendientes actuales;
- ideas futuras;
- métricas;
- plantillas;
- checklists.

Próxima revisión:

- al crear backlog estructurado;
- al consolidar versión;
- al cerrar DEVKIT-0.1;
- al abrir PILOTO-1.4.1.

---

# 53. ESTATUS OFICIAL

Ruta oficial:

```text
DEVKIT/
└── KNOWLEDGE_CORE/
    └── 10_PENDIENTES.md
```

Debe mantenerse alineado con:

```text
01_IDENTIDAD.md
03_REGLAS.md
04_ROADMAP.md
05_SPRINTS.md
08_CERTIFICACIONES.md
09_ESTADO_ACTUAL.md
```

---

**Fin del documento oficial `10_PENDIENTES.md`.**
