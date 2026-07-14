# AGENTS.md — HOST AI

> Punto de entrada obligatorio para cualquier agente de programación que trabaje en este repositorio.  
> Aplicable a Codex y a cualquier otro agente compatible con instrucciones de repositorio.  
> Versión: 1.0  
> Fecha: 14 de julio de 2026

---

## 1. MISIÓN

Tu función es colaborar en el desarrollo de Host AI sin perder su identidad, sin duplicar lógica, sin romper componentes certificados y sin modificar datos reales durante pruebas o diagnósticos.

Host AI es un segundo de cocina digital para restaurantes, caterings, hoteles y colectividades.

No es un ERP tradicional.

No es un chatbot independiente.

La interfaz puede ser conversacional, pero la autoridad operativa pertenece a los motores, servicios, datos y reglas del proyecto.

Antes de tomar una decisión de diseño, aplica esta pregunta:

> ¿Así trabajaría un jefe de cocina real?

Si la respuesta es no, detén el diseño y revisa el flujo.

---

## 2. ALCANCE DE ESTE ARCHIVO

Este archivo no sustituye al DEVKIT.

Su función es:

1. indicar qué documentos leer;
2. establecer el proceso obligatorio;
3. definir límites de seguridad;
4. explicar cómo desarrollar y entregar cambios;
5. mantener sincronizados código, tests y memoria viva.

No copies aquí el contenido completo de los documentos enlazados.

Consulta siempre la versión existente en el repositorio.

---

## 3. ORDEN OBLIGATORIO DE LECTURA

Antes de modificar código, lee en este orden:

1. `DEVKIT/KNOWLEDGE_CORE/01_IDENTIDAD.md`
2. `DEVKIT/KNOWLEDGE_CORE/03_REGLAS.md`
3. `DEVKIT/KNOWLEDGE_CORE/09_ESTADO_ACTUAL.md`
4. `DEVKIT/KNOWLEDGE_CORE/04_ROADMAP.md`
5. `DEVKIT/KNOWLEDGE_CORE/05_SPRINTS.md`
6. `DEVKIT/KNOWLEDGE_CORE/08_CERTIFICACIONES.md`
7. `DEVKIT/KNOWLEDGE_CORE/10_PENDIENTES.md`
8. `DEVKIT/KNOWLEDGE_CORE/11.1A_FILOSOFIA_Y_MODELO_DE_COMPONENTES.md`
9. `DEVKIT/KNOWLEDGE_CORE/11.1B_FILOSOFIA_Y_MODELO_DE_COMPONENTES.md`
10. `DEVKIT/KNOWLEDGE_CORE/11.2_REGISTRO_OFICIAL_DE_COMPONENTES.md`

Lee también, cuando existan:

- `DEVKIT/KNOWLEDGE_CORE/02_ARQUITECTURA.md`
- `DEVKIT/KNOWLEDGE_CORE/06_MEMORIA_TECNICA.md`
- `DEVKIT/KNOWLEDGE_CORE/07_MEMORIA_OPERATIVA.md`
- `MASTER_PLAN.md`
- el contrato del sprint activo;
- el expediente del sprint;
- certificaciones de los componentes afectados.

---

## 4. JERARQUÍA DE AUTORIDAD

En caso de conflicto, utiliza este orden:

1. datos y código reales de la versión abierta;
2. tests y diagnósticos ejecutados sobre esa versión;
3. contratos y certificaciones vinculados a esa versión;
4. `03_REGLAS.md`;
5. `01_IDENTIDAD.md`;
6. `09_ESTADO_ACTUAL.md`;
7. arquitectura, roadmap y memoria;
8. documentación histórica;
9. mensajes o instrucciones no incorporados al repositorio.

No ocultes contradicciones.

Si el código contradice la memoria viva:

- no decidas silenciosamente;
- documenta la diferencia;
- identifica la fuente probable;
- propone la corrección;
- actualiza el documento correcto solo con evidencia.

---

## 5. PROCESO OBLIGATORIO ANTES DE PROGRAMAR

Antes de escribir una línea:

1. confirma la raíz del repositorio;
2. identifica la versión base;
3. revisa el estado de Git;
4. localiza el sprint activo;
5. lee su contrato;
6. audita los componentes afectados;
7. busca lógica equivalente;
8. identifica motores y servicios existentes;
9. revisa tests relacionados;
10. revisa certificaciones;
11. identifica datos que podrían verse afectados;
12. define cómo probar sin usar datos reales;
13. indica los archivos previstos;
14. confirma el criterio de aceptación.

No crees archivos nuevos solo porque su nombre parece adecuado.

Primero comprueba que no existe un componente que ya tenga esa responsabilidad.

---

## 6. REGLAS INNEGOCIABLES

### 6.1 Reutilizar antes que crear

Busca motores, servicios, modelos, repositorios y utilidades existentes.

No copies lógica para acelerar una entrega.

### 6.2 No duplicar autoridad

No pueden existir dos componentes activos que calculen o gobiernen el mismo concepto sin una regla explícita.

### 6.3 No modificar componentes certificados sin necesidad

Si debes modificarlos:

- explica el motivo;
- analiza impacto;
- amplía regresión;
- revisa la certificación;
- registra la modificación.

### 6.4 No asumir arquitectura

La estructura real debe comprobarse en el código abierto.

### 6.5 No inventar datos

No inventes:

- stock;
- recetas;
- precios;
- eventos;
- proveedores;
- estados;
- rutas;
- unidades;
- identificadores.

### 6.6 No esconder incertidumbre

Distingue:

- hecho observado;
- inferencia;
- propuesta;
- dato no verificado.

### 6.7 No afirmar ejecución inexistente

No declares:

- tests OK;
- diagnóstico OK;
- integrado;
- certificado;
- validado;

si no existe evidencia real de esa acción.

---

## 7. REGLAS DE DOMINIO CRÍTICAS

### 7.1 Búsqueda de artículos

Prioridad:

1. nombre exacto;
2. coincidencias parecidas;
3. revisión del usuario;
4. proveedor como segunda vía;
5. código como apoyo.

### 7.2 Prefijos

- `M.P` significa Materia Prima.
- `A.P` significa Aperitivo.

Un `A.P` no debe interpretarse automáticamente como ingrediente base.

Debe tratarse según su ficha como elaboración, aperitivo, producto compuesto, intermedio o terminado.

### 7.3 Recepción

El flujo real puede separar recepción física y actualización de stock.

No obligues a actualizar stock inmediatamente al recibir mercancía.

### 7.4 Mi Jornada

Es el centro operativo.

Debe agregar y explicar.

No debe convertirse en la fuente de verdad de todos los datos.

### 7.5 Producción

Distingue tiempos activos y pasivos.

Respeta responsables, recursos, dependencias y trabajo paralelo.

### 7.6 Escritura segura

Toda escritura crítica debe contemplar, cuando aplique:

- vista previa;
- confirmación;
- backup;
- transacción;
- idempotencia;
- trazabilidad;
- rollback o compensación.

---

## 8. SEPARACIÓN DE RESPONSABILIDADES

### APP / interfaces

Pueden:

- mostrar;
- preguntar;
- confirmar;
- navegar;
- formatear.

No deben contener lógica crítica.

### SERVICIOS

Pueden:

- coordinar;
- orquestar;
- traducir errores;
- preparar vistas previas;
- controlar transacciones.

No deben duplicar motores.

### CORE / motores

Deben:

- calcular;
- validar;
- aplicar reglas;
- conservar invariantes.

No deben depender de consolas.

### MODELOS

Representan conceptos de dominio.

### REPOSITORIOS / persistencia

Leen y escriben.

No deciden política culinaria.

### IA

Interpreta, resume, explica o propone.

No escribe directamente en datos críticos sin servicio autorizado, validación y confirmación.

---

## 9. SEGURIDAD DE DATOS

Durante auditorías, pruebas y diagnósticos:

- usa copias;
- usa fixtures;
- usa bases temporales;
- usa modo solo lectura siempre que sea posible;
- no sobrescribas Excel real;
- no borres datos reales;
- no migres datos sin backup;
- no ejecutes scripts destructivos sin autorización explícita.

Antes de una escritura relevante:

1. identifica el origen;
2. crea backup cuando proceda;
3. valida datos;
4. muestra vista previa;
5. pide confirmación si afecta operativa;
6. registra trazabilidad;
7. verifica el resultado.

---

## 10. GIT

Antes de cambios:

- ejecuta `git status`;
- identifica cambios preexistentes;
- no sobrescribas trabajo ajeno;
- no mezcles cambios no relacionados.

Buenas prácticas:

- una rama por sprint o cambio;
- commits pequeños y comprensibles;
- no incluir secretos;
- no incluir datos reales;
- no incluir archivos temporales;
- no hacer refactor masivo dentro de un sprint funcional.

No hagas `push`, merges, rebase destructivo, reset duro ni borrado de ramas sin autorización explícita.

---

## 11. CICLO DE DESARROLLO

Utiliza este ciclo:

```text
AUDITAR
↓
DEFINIR
↓
DISEÑAR
↓
IMPLEMENTAR
↓
PROBAR
↓
DIAGNOSTICAR
↓
VALIDAR
↓
DOCUMENTAR
↓
ENTREGAR
↓
CERTIFICAR
```

### Auditar

Comprueba código, datos, entradas, dependencias y pruebas.

### Definir

Confirma problema, objetivo, alcance y fuera de alcance.

### Diseñar

Define componentes, contratos, errores, efectos y pruebas.

### Implementar

Realiza cambios mínimos y coherentes.

### Probar

Ejecuta pruebas específicas y regresión.

### Diagnosticar

Ejecuta o crea un diagnóstico aislado cuando el sprint lo requiera.

### Validar

Distingue validación técnica, manual y en cocina real.

### Documentar

Actualiza únicamente los documentos afectados.

### Entregar

Expón cambios, evidencia, riesgos y limitaciones.

### Certificar

Solo cuando la evidencia lo permita.

---

## 12. REGLAS DE TESTS

Todo cambio funcional debe probar:

- caso normal;
- caso límite;
- error esperado;
- duplicado cuando aplique;
- rollback o compensación cuando aplique;
- compatibilidad;
- regresión de los componentes afectados.

Los tests deben:

- ser reproducibles;
- usar datos aislados;
- no depender del orden;
- no ocultar fallos;
- describir la garantía comprobada.

No modifiques un test solo para hacer que pase sin explicar por qué el comportamiento esperado cambia.

---

## 13. DIAGNÓSTICOS

Un diagnóstico debe:

- ser ejecutable;
- tener alcance definido;
- ser solo lectura por defecto;
- diferenciar error, aviso y éxito;
- producir una salida comprensible;
- no sustituir tests;
- indicar qué garantías valida.

Formato recomendado:

```text
COMPROBAR_<SPRINT>.py
```

---

## 14. CERTIFICACIONES

Aplica los niveles definidos en `08_CERTIFICACIONES.md`.

No confundas:

- creado;
- entregado;
- ejecutado;
- probado;
- diagnosticado;
- validado manualmente;
- certificado técnicamente;
- validado en cocina;
- cerrado.

Toda certificación debe estar vinculada a una versión, commit o artefacto identificable.

---

## 15. ACTUALIZACIÓN DEL DEVKIT

Actualiza solo los documentos afectados.

### Si cambia el estado del proyecto

Actualiza `09_ESTADO_ACTUAL.md`.

### Si cambia el roadmap

Actualiza `04_ROADMAP.md`.

### Si aparece un pendiente

Actualiza `10_PENDIENTES.md`.

### Si cambia metodología de sprint

Actualiza `05_SPRINTS.md`.

### Si cambia certificación

Actualiza `08_CERTIFICACIONES.md`.

### Si cambia una regla permanente

Actualiza `03_REGLAS.md`.

### Si cambia arquitectura o componentes

Actualiza:

- registro de componentes;
- pasaportes;
- `02_ARQUITECTURA.md` cuando exista.

No reescribas documentos completos para añadir una modificación menor.

Conserva control de cambios.

---

## 16. COMPONENTES

Antes de crear o modificar un componente:

1. consulta `11.1A`;
2. consulta `11.1B`;
3. consulta `11.2`;
4. busca su registro;
5. revisa dependencias y consumidores;
6. revisa tests y certificación;
7. calcula impacto.

Todo sprint debe indicar componentes:

- creados;
- modificados;
- deprecados;
- retirados;
- recertificados.

---

## 17. TRABAJO CON IA Y AGENTES

Un agente de programación puede:

- leer;
- buscar;
- proponer;
- editar;
- ejecutar pruebas;
- generar diagnósticos;
- actualizar documentación;
- preparar commits.

Debe solicitar o respetar aprobación antes de:

- ejecutar comandos destructivos;
- modificar datos reales;
- instalar dependencias no acordadas;
- cambiar arquitectura crítica;
- hacer operaciones remotas;
- eliminar componentes;
- revocar certificaciones;
- ampliar significativamente el alcance.

No uses acceso a Internet, servicios externos o credenciales salvo que la tarea lo requiera y esté autorizado.

---

## 18. QUÉ HACER ANTE AMBIGÜEDAD

Primero intenta resolverla mediante:

1. código real;
2. tests;
3. DEVKIT;
4. Git;
5. datos de prueba;
6. documentación histórica.

Si aún existen varias interpretaciones:

- explica las opciones;
- identifica la opción más segura;
- no escribas datos;
- no inventes una decisión de negocio.

Cuando sea posible, avanza con una solución reversible y acotada.

---

## 19. QUÉ HACER SI ENCUENTRAS UN PROBLEMA NO RELACIONADO

Clasifícalo:

- bloqueante;
- bug crítico;
- deuda;
- mejora;
- idea futura.

Actuación:

- bloqueante: detén la parte afectada y documenta;
- crítico: propone hotfix;
- deuda: registra pendiente;
- mejora: no amplíes el sprint;
- idea futura: envíala al backlog.

No conviertas un sprint concreto en una reforma general.

---

## 20. FORMATO OBLIGATORIO DE ENTREGA

Toda entrega debe incluir:

### Resumen

Qué problema se resolvió y cómo.

### Archivos

- creados;
- modificados;
- eliminados.

### Componentes

- creados;
- modificados;
- afectados.

### Tests ejecutados

Comandos y resultado real.

### Diagnósticos

Comandos y resultado real.

### Datos

Indica si se escribieron datos y sobre qué entorno.

### Riesgos

Riesgos introducidos o pendientes.

### Limitaciones

Qué no se ha validado.

### DEVKIT

Documentos actualizados.

### Estado final

Usa un estado preciso:

- implementado;
- probado;
- diagnosticado;
- validado;
- certificado;
- pendiente.

### Siguiente paso

Solo uno, claramente justificado.

---

## 21. REVISIÓN DEL DIFF

Antes de finalizar:

- revisa el diff;
- elimina cambios accidentales;
- revisa archivos generados;
- confirma que no hay secretos;
- confirma que no hay datos reales;
- confirma que los cambios pertenecen al sprint.

Cuando el entorno lo permita, muestra o resume el diff antes de operaciones críticas.

---

## 22. CRITERIOS PARA DETENER EL TRABAJO

Detente si:

- hay riesgo de pérdida de datos;
- la versión base es incierta;
- faltan dependencias críticas;
- el objetivo contradice reglas;
- la operación requiere credenciales no disponibles;
- existe una migración no respaldada;
- la tarea exige modificar un componente certificado sin poder probar regresión;
- el código real contradice gravemente el contrato.

No te detengas únicamente porque la tarea sea grande.

Divide el trabajo y entrega una parte coherente cuando sea seguro.

---

## 23. CRITERIOS PARA CONSIDERAR UN SPRINT COMPLETO

- objetivo cumplido;
- alcance respetado;
- código integrado;
- tests específicos correctos;
- regresión correcta;
- diagnóstico correcto cuando aplique;
- datos protegidos;
- documentación actualizada;
- pendientes derivados registrados;
- limitaciones declaradas;
- versión identificada;
- entrega reproducible.

Los sprints PILOTO requieren además validación manual y, para cierre definitivo, validación en cocina cuando corresponda.

---

## 24. PRIMERA TAREA RECOMENDADA PARA UN AGENTE NUEVO

No modifiques nada.

Realiza una auditoría de solo lectura y entrega:

1. raíz y versión;
2. entradas principales;
3. motor real de producción;
4. motor real de stock;
5. lógica actual de bloqueos;
6. consola de Producción Guiada;
7. tests de PILOTO-1.3 y PILOTO-1.4;
8. escrituras al cerrar producción;
9. posibles duplicados;
10. contradicciones entre código y DEVKIT;
11. riesgos;
12. propuesta acotada para el siguiente sprint.

Esta auditoría será la prueba inicial de comprensión del proyecto.

---

## 25. PRIMER CAMBIO RECOMENDADO

Después de aprobar la auditoría, realizar un cambio pequeño y reversible:

> Humanizar el formato de cantidades mostrado en bloqueos sin cambiar precisión interna.

Requisitos:

- localizar el formateador correcto;
- no duplicar lógica;
- añadir pruebas;
- ejecutar regresión relacionada;
- mostrar archivos modificados;
- no tocar datos reales.

Solo después debe encargarse un sprint funcional grande.

---

## 26. CHECKLIST FINAL DEL AGENTE

Antes de entregar:

- [ ] Leí `AGENTS.md`.
- [ ] Leí los documentos obligatorios.
- [ ] Identifiqué versión y estado de Git.
- [ ] Audité antes de crear.
- [ ] Reutilicé componentes.
- [ ] No dupliqué lógica.
- [ ] Respeté el alcance.
- [ ] Protegí datos reales.
- [ ] Añadí o actualicé tests.
- [ ] Ejecuté pruebas reales.
- [ ] Ejecuté diagnóstico cuando correspondía.
- [ ] Revisé regresión.
- [ ] Revisé el diff.
- [ ] Actualicé el DEVKIT necesario.
- [ ] Registré pendientes derivados.
- [ ] Declaré limitaciones.
- [ ] No exageré el estado.
- [ ] Dejé un siguiente paso claro.

---

## 27. REGLA FINAL

> Comprender primero. Reutilizar después. Modificar lo mínimo. Probar de verdad. Documentar con evidencia. No declarar más de lo demostrado.
