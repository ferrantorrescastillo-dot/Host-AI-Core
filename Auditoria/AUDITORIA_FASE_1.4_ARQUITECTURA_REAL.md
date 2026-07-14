# HOST AI — FASE 1.4: AUDITORÍA DE ARQUITECTURA REAL

> Artefacto auditado: `Host AI 6.0 (4).zip`  
> Fecha: 14 de julio de 2026  
> Modo: Solo lectura  
> Archivos del proyecto modificados: Ninguno  
> Alcance: entradas, capas, dependencias, componentes activos, legado, duplicidades, huérfanos, tests y propuesta de consolidación

---

# 1. OBJETIVO

Esta auditoría cierra la Fase 1 mediante un mapa técnico basado en el código real.

No pretende rediseñar Host AI.

Pretende identificar:

1. qué arquitectura está activa;
2. qué componentes gobiernan cada dominio;
3. qué dependencias existen;
4. qué partes son legado, parches o copias históricas;
5. qué módulos parecen no estar conectados;
6. qué duplicidades deben auditarse;
7. qué impide considerar la versión completamente consolidada;
8. qué debe hacer Codex primero.

---

# 2. RESUMEN EJECUTIVO

La arquitectura activa de Host AI tiene una estructura reconocible:

```text
main.py
↓
Lanzador
↓
HostAICore
↓
APP / Consolas
↓
Servicios y orquestadores
↓
Motores de dominio
↓
Modelos
↓
Persistencia JSON
```

El núcleo reciente del piloto es coherente.

El problema arquitectónico principal no es que falten capas.

Es que conviven en el mismo ZIP:

- arquitectura activa;
- líneas históricas completas;
- parches;
- wrappers APP;
- servicios de generaciones anteriores;
- tests que esperan contratos antiguos;
- pruebas dependientes de archivos externos;
- documentación de varias etapas.

Conclusión:

> El proyecto es funcional, pero el repositorio todavía mezcla producto activo, histórico, laboratorio y paquetes de entrega.

Antes de permitir refactors grandes a Codex debe crearse una clasificación oficial de vigencia.

---

# 3. INVENTARIO PYTHON

Archivos Python auditados:

```text
1030
```

Distribución principal:

```text
APP:        156
CORE:        18
MODELOS:     68
MOTORES:     13
PIPELINES:   92
SERVICIOS:  312
TESTS:      346
```

Además existen archivos Python dentro de:

```text
HOST_AI_6.0.2_LINEA_BASE_VERDE
HOST_AI_6.0.3_MODO_MANUAL_OPERATIVO
HOST_AI_RR11_PULIDO_PRODUCCION
HOST_AI_RR12_PULIDO_EVENTOS
HOST_AI_RR13_PULIDO_STOCK_COMPRAS
HOST_AI_RR14_PULIDO_ESCANDALLOS_COSTES
PILOTO-1.2.1_Humanizacion_Mi_Jornada
```

Estos paquetes no deberían considerarse automáticamente parte de la arquitectura activa.

---

# 4. ALCANZABILIDAD DESDE `main.py`

El análisis estático de imports encontró:

```text
Módulos alcanzables desde main.py: 325
```

Distribución:

```text
CORE:       10
APP:         6
SERVICIOS: 146
PIPELINES:  90
MOTORES:    12
MODELOS:    60
ROOT:        1
```

Interpretación:

- aproximadamente 325 módulos forman parte directa o indirecta del grafo estático de arranque;
- el resto puede ser tests, herramientas, entradas alternativas, legado, plugins dinámicos o código no conectado;
- el número es una cota mínima porque existen imports dinámicos dentro de métodos.

No debe eliminarse ningún módulo solo porque no aparezca en este grafo.

---

# 5. ENTRADAS REALES DEL SISTEMA

## 5.1 Entrada oficial

```text
main.py
```

Lanza:

```text
SERVICIOS/lanzador_piloto_01.py
```

## 5.2 Entradas auxiliares

Existen:

- scripts `COMPROBAR_*`;
- ejecutores de certificación;
- demos;
- herramientas;
- entradas históricas dentro de carpetas empaquetadas;
- consolas individuales APP;
- tests ejecutables.

## 5.3 Regla recomendada

Clasificar entradas como:

```text
OFICIAL
DIAGNÓSTICO
DESARROLLO
HISTÓRICA
PAQUETE
EXPERIMENTAL
```

Solo `main.py` debe figurar como entrada oficial del producto actual.

---

# 6. COMPOSITION ROOT

Componente:

```text
CORE/host_ai_core.py
```

Es el centro de composición.

Importa o inicializa un número muy alto de componentes.

Métricas estáticas:

```text
Dependencias internas directas aproximadas: 189
Módulos que lo importan: 144
```

Esto lo convierte en el componente de mayor centralidad del proyecto.

## Fortaleza

- existe una ubicación clara para construir el sistema;
- permite compartir motores;
- facilita reutilización.

## Riesgo

- constructor de gran tamaño;
- arranque costoso;
- acoplamiento global;
- cualquier cambio puede afectar muchas áreas;
- difícil aislamiento de tests.

## Recomendación

No refactorizarlo todavía.

Primero:

1. registrar componentes;
2. separar inicialización por dominios;
3. crear pruebas de composición;
4. medir impacto.

---

# 7. CAPAS OBSERVADAS

## 7.1 APP

Responsabilidad esperada:

- interacción;
- presentación;
- comandos;
- navegación.

Dependencias observadas:

```text
APP → SERVICIOS: 207 imports
APP → CORE:        1 import
APP → APP:         5 imports
```

Esto es coherente en términos generales.

## 7.2 SERVICIOS

Responsabilidad:

- coordinación;
- integración;
- adaptadores;
- orquestación.

Dependencias:

```text
SERVICIOS → SERVICIOS: 201
SERVICIOS → MODELOS:    76
SERVICIOS → CORE:       39
SERVICIOS → MOTORES:     1
SERVICIOS → APP:         3
```

Los tres imports Servicio → APP corresponden principalmente a lanzadores.

Son excepciones comprensibles, pero deberían registrarse como adaptadores de entrada.

## 7.3 MOTORES

Dependencias:

```text
MOTORES → MODELOS:   8
MOTORES → SERVICIOS: 5
```

Los imports Motor → Servicio son una inversión de capa relevante.

Casos encontrados:

```text
motor_asistente_conversacional
→ clasificador_intenciones
→ interprete_recepcion
→ validador_recepcion

motor_persistencia
→ base_datos_local

motor_stock
→ base_datos_local
```

No todos son errores.

Sin embargo, `BaseDatosLocal` funciona como infraestructura y está ubicada en `SERVICIOS`, lo que provoca la inversión.

Recomendación futura:

```text
INFRAESTRUCTURA/
o
REPOSITORIOS/
```

No moverlo todavía sin migración.

## 7.4 PIPELINES

Dependencias:

```text
PIPELINES → MODELOS:   91
PIPELINES → PIPELINES: 90
```

Hay una estructura homogénea basada en:

```text
PIPELINES/base_pipeline.py
```

Este patrón parece deliberado y reutilizado.

## 7.5 MODELOS

No se detectaron imports desde MODELOS hacia APP o SERVICIOS.

Esto es una fortaleza arquitectónica.

---

# 8. COMPONENTES DE ALTA CENTRALIDAD

## 8.1 `CORE.host_ai_core`

Entradas aproximadas:

```text
144 consumidores
```

## 8.2 `CORE.orquestador`

```text
120 consumidores
```

## 8.3 `MODELOS.api_interna`

```text
94 consumidores
```

## 8.4 `PIPELINES.base_pipeline`

```text
90 consumidores
```

Estos componentes deben tratarse como infraestructura crítica.

Cualquier modificación requiere:

- mapa de impacto;
- regresión amplia;
- versión;
- certificación.

---

# 9. AUTORIDAD POR DOMINIO

## Artículos

Fuentes:

```text
DATOS/db/articulos.json
```

Servicios y componentes históricos adicionales gestionan importación, clasificación y edición.

## Recetas y escandallos

Autoridad activa repartida entre:

- `escandallos.json`;
- entidades de CORE;
- servicios de importación;
- conectores reales.

Debe consolidarse documentalmente.

## Stock

Autoridad principal:

```text
MOTORES/motor_stock.py
```

Persistencia:

```text
stock_lotes.json
stock_movimientos.json
```

## Producción

Autoridad:

```text
MOTORES/motor_produccion_real.py
```

## Compras

Autoridad:

```text
MOTORES/motor_compras.py
```

## Eventos

Autoridad:

```text
MOTORES/motor_eventos.py
```

## Costes

Autoridad de cálculo:

```text
MOTORES/motor_costes_inteligente.py
```

## Jornada

Agregador:

```text
SERVICIOS/jornada_piloto_12.py
```

## Bandeja

Autoridad sobre tareas de bandeja:

```text
SERVICIOS/bandeja_trabajo_piloto_11.py
```

---

# 10. PERSISTENCIA

La arquitectura activa utiliza:

```text
SERVICIOS/base_datos_local.py
```

sobre archivos JSON.

SQLite existe en una línea paralela:

```text
SERVICIOS/gestor_base_datos_definitiva_451.py
```

No está integrado en el `HostAICore` activo.

## Conclusión arquitectónica

Actualmente no existe una única abstracción formal de repositorio compartida por todos los dominios.

Conviven:

- `BaseDatosLocal`;
- JSON especializados;
- Excel;
- SQLite histórico;
- archivos de piloto.

Esto debe registrarse como:

```text
Persistencia múltiple con autoridad por dominio.
```

No debe describirse todavía como una arquitectura SQLite unificada.

---

# 11. DUPLICIDAD DE NOMBRES

Se identificaron:

```text
99 nombres de archivo repetidos
```

Muchos corresponden al patrón:

```text
APP/<nombre>.py
SERVICIOS/<nombre>.py
```

Ejemplos:

```text
APP/analizador_situacion_541.py
SERVICIOS/analizador_situacion_541.py

APP/clasificador_intenciones_503.py
SERVICIOS/clasificador_intenciones_503.py

APP/confirmaciones_inteligentes_5412.py
SERVICIOS/confirmaciones_inteligentes_5412.py
```

Esto no demuestra duplicación lógica.

Puede representar:

- wrapper APP;
- servicio real;
- compatibilidad histórica;
- reexportación.

Pero dificulta la navegación y debe auditarse por lotes.

---

# 12. DUPLICADOS EXACTOS

El análisis por hash encontró un duplicado Python exacto no vacío relevante:

```text
SERVICIOS/lanzador_host_ai_base_603.py
HOST_AI_6.0.3_MODO_MANUAL_OPERATIVO/SERVICIOS/lanzador_host_ai_base_603.py
```

Esto confirma que las carpetas `HOST_AI_*` contienen copias empaquetadas de entregas anteriores.

No deben estar en el namespace activo ni analizarse como módulos actuales.

---

# 13. CARPETAS HISTÓRICAS Y PAQUETES

Clasificación recomendada:

## HISTÓRICAS / ARTEFACTOS DE ENTREGA

```text
HOST_AI_6.0.2_LINEA_BASE_VERDE
HOST_AI_6.0.3_MODO_MANUAL_OPERATIVO
HOST_AI_RR11_PULIDO_PRODUCCION
HOST_AI_RR12_PULIDO_EVENTOS
HOST_AI_RR13_PULIDO_STOCK_COMPRAS
HOST_AI_RR14_PULIDO_ESCANDALLOS_COSTES
PILOTO-1.2.1_Humanizacion_Mi_Jornada
```

## ACTIVAS

```text
APP
CORE
DATOS
DEVKIT
MODELOS
MOTORES
PIPELINES
SERVICIOS
TESTS
QA
```

## DOCUMENTACIÓN

```text
CERTIFICACION
CHANGELOG
DOCS
Documentos
LEEME
```

## HERRAMIENTAS

```text
HERRAMIENTAS
COMPROBAR_*
ejecutar_certificacion_*
```

## Acción recomendada

No borrar.

Mover en una futura consolidación a:

```text
ARCHIVO_HISTORICO/
ARTEFACTOS/
```

y excluirlos de Pytest y del análisis activo.

---

# 14. CANDIDATOS A HUÉRFANOS

El análisis estático identificó:

```text
175 candidatos
```

Muchos son entradas APP individuales que no son importadas desde `main.py`.

Ejemplos:

```text
APP/alta_articulo_416.py
APP/chat_host_ai_504.py
APP/chat_host_ai_505.py
APP/base_datos_definitiva_451.py
APP/planificador_diario_produccion_461.py
```

No deben llamarse huérfanos confirmados.

Pueden ser:

- comandos independientes;
- módulos históricos;
- pantallas accesibles dinámicamente;
- herramientas técnicas.

Clasificación correcta:

```text
CANDIDATO_NO_ALCANZABLE_POR_IMPORT_ESTATICO
```

Se necesita:

- buscar llamadas dinámicas;
- revisar menús;
- revisar documentación;
- ejecutar cobertura.

---

# 15. SUITE GLOBAL — RESULTADO COMPLETO

## 15.1 Colección normal

```text
306 tests recogidos
3 errores de colección
```

## 15.2 Ejecución excluyendo los tres bloqueos

Resultado:

```text
282 passed
24 failed
```

## 15.3 Clasificación de los 24 fallos

### Grupo A — Contrato conversacional antiguo

```text
5 fallos/errores relacionados con gestor_contexto_5410
```

La clase:

```text
OrquestadorInteligente52
```

ya no instancia:

```text
GestorContextoPermanente5410
```

pero los tests 5.4.10–5.4.13 siguen esperando ese atributo.

Esto es una incompatibilidad real entre:

- contrato histórico;
- implementación actual.

Debe decidirse si:

1. restaurar compatibilidad;
2. migrar tests;
3. archivar esa línea.

No corregir automáticamente.

### Grupo B — Paralelización rota

```text
motor_paralelizacion_produccion_556e4
```

importa:

```text
_hora
_minutos_hora
```

desde:

```text
motor_reparto_cocineros_556e3
```

pero esas funciones ya no existen.

Además, el motor 556e3 actual devuelve una estructura distinta y limita el reparto a una sola producción.

Conclusión:

> No es un simple import roto; existe una divergencia de contrato entre 5.5.6E.3.1 y 5.5.6E.4.

### Grupo C — Paquete histórico 6.0.3

Un test dentro de:

```text
HOST_AI_6.0.3_MODO_MANUAL_OPERATIVO/TESTS
```

falla porque esa carpeta empaquetada no contiene toda la raíz requerida.

Este test no debería formar parte de la suite activa del repositorio principal.

### Grupo D — Paquete de entrega PILOTO-1.2.1

Cinco tests internos fallan por probar la copia local del parche en lugar de la implementación integrada.

La implementación activa de PILOTO-1.2 sí pasa sus tests.

Estos tests deben clasificarse como tests del artefacto histórico, no de la raíz activa.

### Grupo E — Fixtures Excel externas

Catorce fallos dependen de rutas absolutas o externas:

```text
/mnt/data/esc_test/Escandallos Boronat.xlsx
/mnt/data/esc_i133/Escandallos Boronat.xlsx
```

No son fallos funcionales demostrados.

Son tests no autocontenidos.

Debe incorporarse fixture o marcarse requisito externo.

---

# 16. ESTADO REAL DE TESTS

No es correcto resumir el repositorio como:

```text
Suite rota completamente
```

Tampoco como:

```text
Todos los tests pasan
```

Estado preciso:

```text
Núcleo reciente del piloto: VERDE
282 tests globales: PASAN
3 errores de colección: ABIERTOS
24 fallos restantes:
- contratos antiguos;
- artefactos históricos;
- fixture Excel ausente;
- una línea de paralelización incompatible.
```

---

# 17. ARQUITECTURA ACTIVA VS HISTÓRICA

## Activa y confirmada

- main piloto;
- HostAICore;
- consola piloto;
- BaseDatosLocal;
- Motores de Producción, Stock, Compras, Eventos y Costes;
- Bandeja;
- Mi Jornada;
- Recepción Inteligente;
- Producción Guiada;
- Producción → Stock.

## Activa pero con deuda

- Orquestador conversacional 5.5.6;
- paralelización 5.5.6E.4;
- importador I1.3 con tests no autocontenidos;
- HostAICore centralizado.

## Histórica o pendiente de clasificación

- paquetes HOST_AI_*;
- RR11–RR14;
- parche PILOTO-1.2.1 empaquetado;
- APP individuales no alcanzables;
- SQLite 4.5.1.

---

# 18. MAPA PRELIMINAR DE COMPONENTES CRÍTICOS

```text
CMP-CORE-001       HostAICore
CMP-ENTRY-001      LanzadorPiloto01
CMP-UI-001         ConsolaPiloto01
CMP-DAT-001        BaseDatosLocal
CMP-STOCK-001      MotorStock
CMP-PROD-001       MotorProduccionReal
CMP-COMP-001       MotorCompras
CMP-EVT-001        MotorEventos
CMP-COST-001       MotorCostesInteligente
CMP-BANDEJA-001    BandejaTrabajoPiloto11
CMP-JORNADA-001    JornadaPiloto12
CMP-RCP-001        RecepcionInteligentePiloto1
CMP-PROD-002       ProduccionGuiadaPiloto13
CMP-PROD-STOCK-001 ProduccionStockPiloto14
CMP-IA-001         OrquestadorInteligente52
CMP-PIPE-001       BasePipeline
```

Estos deben ser los primeros pasaportes reales.

---

# 19. RIESGOS ARQUITECTÓNICOS

## P1 — Mezcla de producto e histórico

Pytest y las búsquedas atraviesan paquetes de entrega antiguos.

## P1 — Contratos incompatibles no clasificados

Líneas 5.4.10–5.4.13 y 5.5.6E.3–E.4.

## P1 — Persistencia JSON no atómica

Ya identificada en Fase 1.2.

## P1 — Reconciliación transversal incompleta

Identificada en Fase 1.3.

## P2 — Composition root sobredimensionado

`HostAICore`.

## P2 — Nomenclatura APP/SERVICIOS repetida

99 stems repetidos.

## P2 — Tests dependientes del entorno

Fixtures externas.

## P2 — Infraestructura colocada en SERVICIOS

`BaseDatosLocal`.

## P2 — Versionado contradictorio

Host AI 6.0 frente a VERSION 3.0 RC3.

---

# 20. QUÉ NO DEBE HACER CODEX AL ENTRAR

No debe:

- mover carpetas masivamente;
- borrar APP no alcanzables;
- migrar a SQLite;
- dividir HostAICore;
- corregir 24 tests de golpe;
- actualizar todos los contratos históricos;
- renombrar cientos de módulos;
- eliminar paquetes RR.

Estas acciones tienen demasiado impacto para una primera tarea.

---

# 21. PLAN DE CONSOLIDACIÓN RECOMENDADO

## CONS-0.1 — Clasificación del repositorio

Crear:

```text
pytest.ini
```

y exclusiones oficiales para:

```text
ARCHIVO_HISTORICO
ARTEFACTOS
paquetes de entrega
```

Sin mover aún archivos.

## CONS-0.2 — Versión única

Crear fuente de versión oficial.

## CONS-0.3 — Suite activa

Definir qué tests pertenecen al producto actual.

## CONS-0.4 — Fixtures autocontenidas

Incorporar Excel de prueba o generarlo en tests.

## CONS-0.5 — Contratos rotos

Resolver por separado:

- contexto 5410;
- paralelización 556e4.

## CONS-0.6 — Registro de componentes

Crear pasaportes de los 16 componentes críticos.

## CONS-0.7 — Reconciliación de Bandeja

Sprint funcional identificado en Fase 1.3.

---

# 22. PRIMERA TAREA IDEAL PARA CODEX

No debe ser PILOTO-1.4.1 todavía.

Debe ser:

```text
DEVKIT-CODEX-0.1 — Clasificar la suite activa sin modificar lógica de negocio
```

Objetivo:

1. identificar carpetas históricas;
2. configurar Pytest para excluir artefactos;
3. separar fallos de fixture;
4. no corregir lógica;
5. producir informe reproducible;
6. dejar la suite activa claramente definida.

Criterio de éxito:

```text
pytest de la raíz activa no recoge tests de paquetes históricos.
Los errores restantes están clasificados por componente real.
```

---

# 23. SEGUNDA TAREA PARA CODEX

```text
DEVKIT-CODEX-0.2 — Autocontener fixtures de importador I1.3
```

Sin tocar datos reales.

---

# 24. TERCERA TAREA PARA CODEX

```text
HOTFIX-IA-5410 — Decidir y corregir compatibilidad de contexto
```

Requiere contrato previo.

---

# 25. CUARTA TAREA PARA CODEX

```text
HOTFIX-PROD-556E4 — Reconciliar paralelización con reparto real
```

No debe limitarse a reintroducir helpers privados sin revisar estructuras.

---

# 26. DESPUÉS DE LA CONSOLIDACIÓN

Entonces sí:

```text
PILOTO-1.4.0-R
Reconciliación de Bandeja y fuentes
```

y después:

```text
PILOTO-1.4.1
Asistente de resolución de bloqueos
```

---

# 27. ESTADO FINAL DE FASE 1

## Arquitectura conocida

```text
SUFICIENTE PARA DIRIGIR CODEX
```

## Repositorio consolidado

```text
NO
```

## Núcleo piloto

```text
FUNCIONAL Y PROBADO
```

## Suite global

```text
PARCIALMENTE VERDE
```

## Históricos clasificados físicamente

```text
NO
```

## Componentes críticos identificados

```text
SÍ
```

## Riesgos principales conocidos

```text
SÍ
```

---

# 28. CONCLUSIÓN

Host AI ya puede empezar a trabajar con Codex.

Pero Codex debe entrar primero como:

```text
auditor
clasificador
mantenedor de tests
```

y no todavía como autor de un gran sprint funcional.

La arquitectura activa tiene sentido.

El repositorio, en cambio, todavía conserva demasiadas capas históricas juntas.

El orden profesional es:

```text
Clasificar
↓
Consolidar
↓
Registrar componentes
↓
Reconciliar Bandeja
↓
Construir Asistente de Bloqueos
```

Esta auditoría cierra la Fase 1 y proporciona la base necesaria para crear un `MASTER_PLAN.md` realista y una primera tarea segura para Codex.
