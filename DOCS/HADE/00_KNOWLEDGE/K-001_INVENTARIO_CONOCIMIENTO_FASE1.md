# HOST AI — K-001 Consolidación del conocimiento

## Fase 1 — Inventario y diagnóstico inicial

**Fuente auditada:** `Host AI 6.0 (5).zip`  
**Fecha de la copia:** 16/07/2026  
**Rama incluida:** `develop-6.1`

## 1. Resultado inicial

El ZIP contiene el proyecto completo: código, repositorio Git, datos, tests, auditorías, certificaciones y documentación histórica.

Inventario documental detectado:

- 466 archivos Markdown (`.md`).
- 143 archivos de texto (`.txt`).
- 2 documentos Word (`.docx`).
- 1 PDF.
- 3 archivos reStructuredText (`.rst`), procedentes principalmente de dependencias.

La documentación útil no está concentrada en una sola carpeta. Está repartida entre:

- raíz del proyecto;
- `DEVKIT/`;
- `Documentos/DEVKIT/`;
- `DOCS/`;
- `ROC/`;
- `Auditoria/`;
- `CERTIFICACION/`;
- `Informe/`;
- `CHANGELOG/`;
- carpetas de versiones y entregables históricos.

## 2. Hallazgo principal

El proyecto **ya contiene gran parte de la filosofía que pretendíamos llevar a HADE**. No hay que reconstruirla desde cero.

Los documentos más importantes detectados son:

1. `AGENTS.md`
2. `MASTER_PLAN.md`
3. `DEVKIT/KNOWLEDGE_CORE/01_IDENTIDAD.md`
4. `DEVKIT/KNOWLEDGE_CORE/03_REGLAS.md`
5. `DEVKIT/KNOWLEDGE_CORE/04_ROADMAP.md`
6. `DEVKIT/KNOWLEDGE_CORE/09_ESTADO_ACTUAL.md`
7. `DEVKIT/KNOWLEDGE_CORE/10_PENDIENTES.md`
8. `DEVKIT/KNOWLEDGE_CORE/11.1A_FILOSOFIA_Y_MODELO_DE_COMPONENTES.md`
9. `DEVKIT/KNOWLEDGE_CORE/11.1B_FILOSOFIA_Y_MODELO_DE_COMPONENTES.md`
10. `DEVKIT/KNOWLEDGE_CORE/11.2_REGISTRO_OFICIAL_DE_COMPONENTES.md`
11. `ROC/ROC-01A_NUCLEO.md` a `ROC/ROC-04B_COCINA.md`
12. Auditorías de arquitectura y funcionalidad de `Auditoria/`.
13. Certificaciones técnicas de `CERTIFICACION/`.

## 3. Duplicación confirmada

`DEVKIT/` y `Documentos/DEVKIT/` son copias idénticas en el ZIP auditado.

Esto significa que actualmente existen dos ubicaciones físicas con la misma fuente documental. No se debe eliminar ninguna todavía, pero solo una debe mantenerse como fuente activa en el futuro.

**Propuesta preliminar:**

- Fuente oficial activa: `DEVKIT/KNOWLEDGE_CORE/`.
- `Documentos/DEVKIT/`: copia histórica o exportación, pendiente de confirmar antes de archivar.

## 4. Clasificación preliminar de fuentes

| Fuente | Estado inicial | Papel futuro |
|---|---|---|
| `AGENTS.md` | Vigente y crítico | Contrato operativo para agentes y desarrolladores |
| `MASTER_PLAN.md` | Vigente, pero resumido | Dirección, estado y sprint activo; no debe absorber HADE |
| `DEVKIT/KNOWLEDGE_CORE/01_IDENTIDAD.md` | Muy vigente | Base de visión, misión, personalidad y límites de HADE |
| `DEVKIT/KNOWLEDGE_CORE/03_REGLAS.md` | Muy vigente | Fuente principal de leyes y reglas existentes |
| `DEVKIT/KNOWLEDGE_CORE/04_ROADMAP.md` | Vigente con posible desfase temporal | Roadmap histórico/operativo; debe actualizarse, no duplicarse en HADE |
| `DEVKIT/KNOWLEDGE_CORE/09_ESTADO_ACTUAL.md` | Valioso pero temporal | Estado histórico; necesita contraste con código y commits actuales |
| `DEVKIT/KNOWLEDGE_CORE/10_PENDIENTES.md` | Vigente como sistema | Taxonomía oficial de pendientes |
| `11.1A/11.1B` | Vigentes y técnicos | Arquitectura de componentes; no deben reescribirse como filosofía HADE |
| `ROC/` | Vigente como registro técnico | Fuente de autoridad de componentes reales |
| `Auditoria/` | Evidencia histórica | Sirve para comprobar evolución y arquitectura real |
| `CERTIFICACION/` | Evidencia técnica | No se fusiona en HADE; se referencia desde estado/certificación |
| `DOCS/` | Mixto | Requiere clasificación individual por antigüedad y validez |
| `CHANGELOG/` y carpetas de versión | Histórico | Evidencia de evolución, no fuente normativa principal |

## 5. Qué debe ser HADE después de la consolidación

HADE no debe sustituir todos los documentos existentes.

Debe convertirse en la fuente oficial de verdad únicamente para:

- cómo razona Host AI;
- jerarquía de decisiones;
- anticipación;
- atención y tiempos pasivos;
- relación entre servicio, calidad, producción, recursos y personal;
- recomendaciones explicables;
- control humano;
- aprendizaje con aprobación;
- comportamiento de segundo de cocina.

No debe duplicar:

- el roadmap completo;
- el estado actual de cada sprint;
- el registro de componentes;
- las certificaciones;
- los contratos técnicos detallados de cada módulo;
- el historial del proyecto.

## 6. Primer mapa de absorción hacia HADE

| Contenido existente | Fuente principal | Destino HADE previsto |
|---|---|---|
| Misión, visión y definición del producto | `01_IDENTIDAD.md` | HADE-00 Visión |
| Qué no es Host AI | `01_IDENTIDAD.md`, `AGENTS.md` | HADE-00 / HADE-01 |
| Lenguaje natural y personalidad | `01_IDENTIDAD.md`, `03_REGLAS.md` | HADE-01 Filosofía / HADE-11 Conversación |
| Control humano y no inventar | `AGENTS.md`, `03_REGLAS.md` | HADE-02 Leyes fundamentales |
| Pensar por trabajo real, no por módulos | `03_REGLAS.md` | HADE-02 / HADE-03 Modelo mental |
| Tiempos pasivos liberan capacidad | `03_REGLAS.md` | HADE-05 Producción |
| Bloqueos deben proponer salidas | `03_REGLAS.md` | HADE-04 Motor de decisiones |
| Arquitectura de motores/servicios/modelos | `11.1A`, `11.1B`, ROC | HADE-13 Arquitectura (referencias, no copia completa) |
| Árbol decisional de producción creado en conversación | Conversación de diseño | HADE-04 y HADE-05 |
| Estado y roadmap | `MASTER_PLAN.md`, `04_ROADMAP.md`, `09_ESTADO_ACTUAL.md` | No absorber; solo referenciar |

## 7. Conclusión de la fase inicial

No es necesario cambiar todo porque haya aparecido HADE.

La base documental existente es sólida y ya contiene muchas decisiones correctas. El problema real es la dispersión y la duplicación, no la ausencia de conocimiento.

La estrategia correcta es:

1. identificar las fuentes de autoridad existentes;
2. eliminar contradicciones mediante clasificación, no mediante borrado inmediato;
3. absorber en HADE solo el conocimiento decisional;
4. mantener roadmap, ROC, certificaciones y estado como sistemas separados;
5. evitar crear documentos nuevos que repitan contenido ya oficial.

## 8. Siguiente trabajo de K-001

La siguiente fase debe revisar individualmente las fuentes prioritarias y producir una matriz de consolidación con estas decisiones:

- **CONSERVAR COMO AUTORIDAD**
- **ABSORBER EN HADE**
- **REFERENCIAR DESDE HADE**
- **ACTUALIZAR**
- **ARCHIVAR COMO HISTÓRICO**
- **DUPLICADO**
- **OBSOLETO**

El primer lote recomendado es:

1. `AGENTS.md`
2. `MASTER_PLAN.md`
3. `01_IDENTIDAD.md`
4. `03_REGLAS.md`
5. `04_ROADMAP.md`
6. `09_ESTADO_ACTUAL.md`
7. `10_PENDIENTES.md`
8. `11.1A` y `11.1B`
9. `ROC-01A` a `ROC-04B`

