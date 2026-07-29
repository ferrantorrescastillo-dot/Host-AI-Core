# PLAN DE SUSTITUCION DEL LEGADO EXCEL IMPORTACIONES

Fecha: 2026-07-23
Estado del documento: diseño funcional, sin cambios de comportamiento
Ruta documental real del proyecto: DOCS/PLAN_SUSTITUCION_LEGADO_EXCEL_IMPORTACIONES.md

## 1. Resumen ejecutivo
El legado Excel Importaciones no puede retirarse hoy. La auditoría previa confirmó que solo la importación de escandallos Excel ya tiene sustitución funcional suficiente en el stack 601. Siguen siendo capacidades únicas o incompletamente sustituidas: análisis estructural multihoja, detector general de tipo de Excel, importación de artículos, vista previa/comparación/importación de inventario y toda la cadena avanzada de menús I1.2-I1.3.5.

La arquitectura actual sí permite una sustitución ordenada, pero no como un único reemplazo. El patrón correcto es:
- un núcleo determinista común dentro del Centro de Importación 601;
- servicios de dominio en Catálogo, Stock, Recetas, Escandallos y Menús;
- Asistente de Incidencias para revisión y confirmaciones;
- Host AI Engine y Director IA solo en casos ambiguos, para proponer y explicar, nunca para decidir en solitario ni escribir datos.

Recomendación final: 3. EJECUTAR UNA MIGRACION HIBRIDA POR SPRINTS.

Motivo:
- hay capacidades que deben reimplementarse de forma determinista en el nuevo core;
- hay otras que conviene apoyar con Host AI Engine para interpretación y propuestas;
- y varias deben mantenerse temporalmente como legado hasta tener sustitución segura y pruebas equivalentes.

## 2. Base del análisis
Documento base reutilizado:
- DOCS/AUDITORIA_LEGADO_EXCEL_IMPORTACIONES.md

Código real auditado para el plan:
- APP/consola.py
- PIPELINES/pipeline_excel.py
- SERVICIOS/asistente_importacion_excel.py
- SERVICIOS/detector_documentos_excel.py
- SERVICIOS/mapeador_columnas_excel.py
- SERVICIOS/resolutor_conflictos_excel.py
- SERVICIOS/importador_articulos_excel.py
- SERVICIOS/importador_inventario_excel.py
- SERVICIOS/importador_seguro_escandallos_i12.py
- SERVICIOS/detector_limpio_menus_i131.py
- SERVICIOS/motor_reconocimiento_menus_i1321.py
- SERVICIOS/constructor_arbol_semantico_menus_i1322.py
- SERVICIOS/vista_previa_resolucion_asistida_menus_i1323.py
- SERVICIOS/motor_aprendizaje_culinario_i1324.py
- SERVICIOS/preimportador_definitivo_menus_i133.py
- SERVICIOS/resolutor_bloqueos_preimportacion_i1331.py
- SERVICIOS/simulador_importacion_menus_i13411.py
- SERVICIOS/simulador_importacion_menus_i13412.py
- SERVICIOS/bandeja_revision_i13413.py
- SERVICIOS/bandeja_revision_i13414.py
- SERVICIOS/bandeja_revision_i13415.py
- SERVICIOS/diagnostico_escritura_segura_i1342.py
- SERVICIOS/importador_definitivo_menus_i1343.py
- SERVICIOS/diagnostico_auditoria_postimportacion_i1344.py
- SERVICIOS/auditor_integridad_postimportacion_i1344.py
- SERVICIOS/bandeja_correccion_postimportacion_i13441.py
- SERVICIOS/bandeja_correccion_inteligente_i13442.py
- SERVICIOS/certificador_final_importador_i135.py
- SERVICIOS/centro_importacion_601.py
- SERVICIOS/catalogo_maestro_productos_601.py
- SERVICIOS/biblioteca_recetas_601.py
- SERVICIOS/biblioteca_escandallos_601.py
- SERVICIOS/biblioteca_menus_601.py
- SERVICIOS/asistente_resolucion_incidencias_601.py
- SERVICIOS/host_ai_engine/__init__.py

## 3. Inventario detallado de capacidades B y C

### 3.1 Analizar archivo Excel
- Nombre funcional: análisis estructural de libro Excel.
- Legado: PIPELINES/pipeline_excel.py + lector_excel a través de APP/consola.py.
- Flujo actual: consola -> orquestador -> pipeline excel -> lector_excel.analizar_archivo.
- Entradas: ruta_archivo, filas_preview, exportar_json.
- Salidas: hojas, filas, columnas, columnas detectadas, vista previa y resumen textual.
- Persistencias: export JSON del análisis; no toca negocio.
- Dependencias: lector Excel, orquestador.
- Reglas: solo lectura; no infiere negocio todavía.
- Validaciones: existencia/formato del archivo en lector.
- Incidencias: errores de lectura, hojas vacías, metadatos incompletos.
- Pruebas existentes: test_lector_excel.py, test_detector_documentos_excel.py.
- Nivel de uso real: alto como primer paso del menú legado.
- Riesgo de sustitución: medio. La lógica es transversal y no debe duplicarse.
- Estrategia propuesta: B. REIMPLEMENTAR EN EL NUEVO CORE.
- Componente destino: Centro de Importación 601 como analizador común de libro.

### 3.2 Detector general de tipo de Excel
- Nombre funcional: clasificación de documento/hoja.
- Legado: SERVICIOS/detector_documentos_excel.py.
- Flujo actual: detector sobre análisis previo; devuelve tipo, confianza, motivos y ambigüedad.
- Entradas: análisis del libro o ruta.
- Salidas: tipo_principal, confianza, hojas, candidatos, avisos.
- Persistencias: ninguna.
- Dependencias: lector_excel, MODELOS/deteccion_excel.
- Reglas: heurísticas por columnas fuertes/medias y bonus por combinaciones.
- Validaciones: confianza mínima, detección ambigua si diferencia < 12.
- Incidencias: desconocido, ambigüedad.
- Pruebas existentes: test_detector_documentos_excel.py.
- Nivel de uso real: alto, alimenta importadores clásicos.
- Riesgo de sustitución: alto; es una dependencia estructural del resto del flujo.
- Estrategia propuesta: B ahora, C solo para ambigüedad.
- Componente destino: Centro de Importación + IMPORTACION_IA para casos dudosos.

### 3.3 Mapeo de columnas y aprendizaje
- Nombre funcional: normalización de encabezados a campos canónicos.
- Legado: SERVICIOS/mapeador_columnas_excel.py.
- Flujo actual: detector -> reanálisis -> mapeo por hoja -> aprendizaje opcional.
- Entradas: análisis/detección, diccionario aprendido.
- Salidas: campos mapeados, desconocidas, faltantes obligatorias, confianza media.
- Persistencias: DATOS/diccionarios/diccionario_columnas_excel.json.
- Dependencias: detector, MODELOS/mapeo_columnas_excel.
- Reglas: score léxico; obligatorias por tipo; soporte de campos personalizados.
- Validaciones: umbral mínimo 55 para aceptar coincidencia automática.
- Incidencias: columnas desconocidas, obligatorias faltantes.
- Pruebas existentes: cobertura indirecta por detector/importadores y resolutor de conflictos.
- Nivel de uso real: alto.
- Riesgo de sustitución: alto por su papel transversal.
- Estrategia propuesta: A. MIGRAR TAL CUAL a un servicio común del Centro 601.
- Componente destino: Centro de Importación común + Asistente de Incidencias para corrección manual.

### 3.4 Resolución previa de conflictos Excel
- Nombre funcional: análisis preventivo de conflictos antes de importar.
- Legado: SERVICIOS/resolutor_conflictos_excel.py.
- Flujo actual: analiza mapeo, duplicados crudos, preview de artículos, escandallos e inventario.
- Entradas: ruta_archivo, resultados de detectores/importadores preview.
- Salidas: informe con conflictos, nivel, recomendación y opciones.
- Persistencias: solo último informe en memoria del servicio.
- Dependencias: detector, mapeador, importadores clásicos, costes.
- Reglas: duplicados, cambios fuertes de precio, artículos parecidos, faltantes obligatorios.
- Validaciones: clasificación crítica/aviso.
- Incidencias: error_lectura, duplicado_excel, articulo_parecido, cambio_precio_fuerte, etc.
- Pruebas existentes: test_resolucion_conflictos_excel.py.
- Nivel de uso real: medio-alto.
- Riesgo de sustitución: alto porque hoy concentra explicabilidad previa.
- Estrategia propuesta: B.
- Componente destino: Asistente de Incidencias 601 + Centro de Importación común.

### 3.5 Vista previa e importación de artículos Excel
- Nombre funcional: importación de catálogo maestro desde Excel.
- Legado: SERVICIOS/importador_articulos_excel.py.
- Flujo actual: detector -> mapeo -> preview -> alta/actualización -> histórico de precios vía costes_inteligente -> persistencia.
- Entradas: artículo, código, unidad, familia, proveedor, precio, stock mínimo, ubicación, alérgenos.
- Salidas: artículos detectados/importados/actualizados, precios registrados, duplicados, errores.
- Persistencias: memoria interna del importador, costes_inteligente, persistencia general del core.
- Dependencias: detector, mapeador, lector, costes, persistencia.
- Reglas: exige nombre; avisa por unidad ausente; actualiza existentes según flag.
- Validaciones: nombre obligatorio; normalización de floats; slug de IDs.
- Incidencias: faltas de nombre/unidad, duplicados, cambios de precio vía resolutor.
- Pruebas existentes: test_importador_articulos_excel.py.
- Nivel de uso real: crítico.
- Riesgo de sustitución: muy alto porque afecta autoridad de catálogo y precios.
- Estrategia propuesta: B.
- Componente destino: Centro de Importación común + Catálogo Maestro 601 + RepositorioProductosMaestro601.

### 3.6 Vista previa, comparación e importación de inventario Excel
- Nombre funcional: conciliación masiva de inventario con stock real.
- Legado: SERVICIOS/importador_inventario_excel.py + pipeline_importador_inventario_excel.py.
- Flujo actual: detector -> mapeo -> cálculo de diferencias -> preview/comparación -> alta opcional de artículos básicos -> ajuste de stock.
- Entradas: artículo, cantidad, unidad, ubicación, caducidad, lote, proveedor, precio, código.
- Salidas: lineas, cambios, errores, artículos creados, stock actualizado.
- Persistencias: stock real, costes_inteligente, memoria del importador de artículos, persistencia general.
- Dependencias: detector, mapeador, stock, importador artículos, costes.
- Reglas: no acepta cantidad negativa; permite preview y comparación; ajusta diferencia positiva/negativa.
- Validaciones: nombre obligatorio, cantidad no negativa, unidad recomendada, parsing de fecha.
- Incidencias: errores de ajuste negativo, datos incompletos.
- Pruebas existentes: test_importador_inventario_excel.py.
- Nivel de uso real: crítico.
- Riesgo de sustitución: muy alto; afecta stock real.
- Estrategia propuesta: B.
- Componente destino: Centro de Importación + Stock + Catálogo + Auditoría + Incidencias.

### 3.7 I1.1 Detector de escandallos antiguos
- Nombre funcional: detección de formatos heredados de escandallos.
- Legado: SERVICIOS/detector_escandallos_antiguos_i11.py.
- Flujo actual: analiza hojas legacy y genera resumen sin importar.
- Entradas: Excel legacy.
- Salidas: vista previa, tipos de hoja y datos detectados.
- Persistencias: ninguna salvo export si se pide.
- Pruebas existentes: test_i11_detector_escandallos_antiguos.py.
- Nivel de uso real: técnico.
- Riesgo de sustitución: medio.
- Estrategia propuesta: D. MANTENER COMO LEGADO TEMPORAL.
- Componente destino futuro: detector común del Centro 601, si realmente hay necesidad recurrente.

### 3.8 I1.2 Importación segura de recetas
- Nombre funcional: importación segura de recetas con vinculación culinaria y memoria.
- Legado: SERVICIOS/importador_seguro_escandallos_i12.py.
- Flujo actual: detecta recetas antiguas -> vincula ingredientes a catálogo -> permite decisiones manuales -> recuerda equivalencias -> importa solo seguras.
- Entradas: Excel de recetas, catálogo de artículos, escandallos/recetas existentes, memoria de vinculaciones.
- Salidas: previa, pendientes de revisión, decisiones aplicadas, importación segura.
- Persistencias: DATOS/db/memoria_vinculaciones_i122.json, datos legacy de escandallos/recetas.
- Dependencias: detector I1.1, similitud léxica, catálogo real.
- Reglas: umbral exacto/probable, no inventa ingredientes, no crea catálogo sin decisión explícita.
- Validaciones: ingrediente vacío no se recuerda; importación cancelable; solo recetas seguras.
- Incidencias: dudosos, sin resolver, duplicados, unidades/cantidades incompletas.
- Pruebas existentes: test_i12_importador_seguro_escandallos.py, test_i122_revision_aprendizaje.py.
- Nivel de uso real: alto en migración de recetas antiguas.
- Riesgo de sustitución: alto.
- Estrategia propuesta: A para heurística de vinculación y memoria; B para persistencia y escritura; C solo para propuestas ambiguas.
- Componente destino: Centro de Importación 601 + Biblioteca de Recetas 601 + Asistente de Incidencias 601 + Host AI Engine IMPORTACION_IA/RECETAS_IA.

### 3.9 Cadena avanzada de menús I1.3.1-I1.3.5
Se separa por valor funcional real:

#### I1.3.1 Detector limpio de menús
- Qué hace: clasifica filas, secciones, platos, artículos directos, complementos y economía; no escribe.
- Persistencias: ninguna.
- Pruebas: test_i131_detector_limpio_menus.py.
- Riesgo: alto, es la base estructural.
- Estrategia: A para reglas de clasificación de filas; B para integrar en estructura intermedia común.
- Destino: Centro de Importación + Biblioteca de Menús.

#### I1.3.2.1.1 Reconocimiento corregido
- Qué hace: reconoce candidatos de recetas/artículos/roles a partir del menú limpio.
- Persistencias: ninguna.
- Pruebas: test_i1321_motor_reconocimiento.py.
- Riesgo: alto.
- Estrategia: B para motor determinista de matching; C para enriquecer ambigüedades.
- Destino: Biblioteca de Menús + IMPORTACION_IA + MENUS_IA.

#### I1.3.2.2 Árbol semántico
- Qué hace: separa receta principal, guarniciones, salsas y artículos directos; preserva parciales sin inventar.
- Persistencias: ninguna.
- Pruebas: test_i1322_constructor_arbol_semantico.py.
- Riesgo: alto.
- Estrategia: B.
- Destino: estructura intermedia de menús + Motor de Menús 601.

#### I1.3.2.3 Vista previa y resolución asistida
- Qué hace: presenta pendientes de revisión y permite decisiones sobre vínculos/propuestas, con memoria opcional.
- Persistencias: memoria local cuando se confirma recordar.
- Pruebas: test_i1323_vista_previa_resolucion_asistida.py.
- Riesgo: alto.
- Estrategia: B para interfaz de revisión/estado; C para sugerencias; A parcial para memoria de decisiones.
- Destino: Asistente de Incidencias 601 + IMPORTACION_IA/MENUS_IA.

#### I1.3.2.4 Aprendizaje culinario
- Qué hace: guarda decisiones reutilizables, migra memoria antigua y aplica aprendizajes automáticamente.
- Persistencias: DATOS/db/aprendizaje_culinario_i1324.json.
- Pruebas: test_i1324_motor_aprendizaje_culinario.py.
- Riesgo: medio-alto.
- Estrategia: A parcial para modelo/persistencia; B para integración; C para futuras sugerencias explicadas.
- Destino: Asistente de Incidencias 601 + historial de importación + posible memoria del Engine.

#### I1.3.3 Preimportación definitiva
- Qué hace: genera contrato de menús, economía y componentes; deja estado LISTA o BLOQUEADA sin importar.
- Persistencias: lectura de aprendizaje; no escribe menú.
- Pruebas: test_i133_preimportacion_definitiva_menus.py.
- Riesgo: alto.
- Estrategia: B.
- Destino: Centro de Importación 601 con modo SIMULAR.

#### I1.3.3.1 Resolución de bloqueos
- Qué hace: crea o vincula recetas para desbloquear la preimportación, con backup y recalculo.
- Persistencias: escandallos/recetas legacy + backups.
- Pruebas: test_i1331_resolucion_bloqueos.py.
- Riesgo: muy alto.
- Estrategia: B para flujo y escritura segura; C solo para propuesta de resolución.
- Destino: Asistente de Incidencias 601 + Biblioteca Recetas/Escandallos + confirmación explícita.

#### I1.3.4.1.1 / I1.3.4.1.2 Simulación y clasificador gastronómico
- Qué hace: simula importación multimenu, detecta relaciones y clasificación culinaria antes de escribir.
- Persistencias: ninguna de negocio.
- Pruebas: test_i13411_deteccion_simulacion_multimenu.py, test_i13412_clasificador_gastronomico.py.
- Riesgo: medio-alto.
- Estrategia: B para motor de simulación; C solo si hay ambigüedad semántica.
- Destino: Centro de Importación 601 + Motor de Menús 601 en modo SIMULAR.

#### I1.3.4.1.3 / 1.4 / 1.5 Bandejas y motores de interpretación
- Qué hace: revisión masiva, renombrado, clasificación, vinculación y conocimiento gastronómico.
- Persistencias: sesiones y memorias auxiliares.
- Pruebas: test_i13413_bandeja_revision.py, test_i13414_motor_interpretacion.py, test_i13415_motor_conocimiento.py.
- Riesgo: alto.
- Estrategia: B para flujo de revisión agrupada; C para sugerencia y explicación.
- Destino: Asistente de Incidencias 601 + Director IA + confirmaciones agrupadas.

#### I1.3.4.2 Escritura segura
- Qué hace: diagnostica garantías de escritura segura del flujo legacy.
- Persistencias: diagnósticos solamente.
- Pruebas: test_i1342_motor_escritura_segura.py.
- Riesgo: medio.
- Estrategia: E como módulo separado, pero sus garantías deben absorberse en repositorios 601 y tests.
- Destino: reglas de escritura segura en repositorios/servicios 601 + tests.

#### I1.3.4.3 Importación definitiva de menús
- Qué hace: importa sesión revisada lista, con confirmación, idempotencia e integridad.
- Persistencias: DATOS/db/menus.json + backups.
- Pruebas: test_i1343_importacion_definitiva_menus.py.
- Riesgo: muy alto.
- Estrategia: B.
- Destino: Centro de Importación 601 + Biblioteca de Menús 601 + confirmaciones del Director IA.

#### I1.3.4.4 Auditoría postimportación
- Qué hace: revisa menús reales ya escritos y detecta incoherencias estructurales/económicas.
- Pruebas: test_i1344_auditoria_integridad_postimportacion.py.
- Riesgo: alto.
- Estrategia: B.
- Destino: Auditoría de importación dentro del Centro 601 + historial + Biblioteca de Menús.

#### I1.3.4.4.1 / 4.2 Corrección postimportación y masiva
- Qué hace: corrige incidencias sobre menú real, individual o agrupada, con guardado confirmado.
- Pruebas: test_i13441_bandeja_correccion_postimportacion.py, test_i13442_correccion_inteligente_masiva.py.
- Riesgo: muy alto.
- Estrategia: B para herramientas de corrección; C para sugerir lote/agrupación.
- Destino: Asistente de Incidencias 601 + confirmación agrupada + Biblioteca de Menús.

#### I1.3.5 Certificación final del importador
- Qué hace: certifica la cadena legacy de menús y sus dependencias.
- Pruebas: test_i135_refactor_certificacion.py.
- Riesgo: medio-alto.
- Estrategia: E como módulo separado legacy; B para trasladar sus garantías a suites de integración R6.x del nuevo core.
- Destino: certificación por tests del nuevo stack, no un servicio runtime específico.

## 4. Mapa de equivalencias objetivo

### Excel común
- análisis estructural multihoja -> Centro de Importación común
- detector de tipo -> Centro de Importación común + IMPORTACION_IA en dudas
- mapeo de columnas -> Centro de Importación común
- conflictos previos -> Asistente de Incidencias 601 + Centro de Importación

### Artículos
- preview/importación de artículos -> Catálogo Maestro + Centro de Importación
- detección de duplicados y precios anómalos -> Catálogo Maestro + Asistente de Incidencias + IMPORTACION_IA opcional para explicación
- histórico de precios/proveedores -> RepositorioProductosMaestro601

### Inventario
- preview/comparación -> Centro de Importación + Stock
- importación confirmada -> Stock + Catálogo + Auditoría
- conciliación de lotes y ubicaciones -> Stock

### Recetas
- importación segura de recetas -> Centro de Importación + Biblioteca de Recetas + Asistente de Incidencias
- resolución de ingredientes ambiguos -> IMPORTACION_IA/RECETAS_IA solo como propuesta

### Escandallos
- ya cubiertos en 601, mantener como referencia de diseño para otros flujos.

### Menús
- detector limpio / reconocimiento / árbol -> Centro de Importación + Biblioteca de Menús + Motor de Menús
- preimportación / simulación -> Centro de Importación en modo SIMULAR
- bloqueos / corrección / postimportación -> Asistente de Incidencias + Biblioteca de Menús + confirmación
- importación final -> Centro de Importación + Biblioteca de Menús + escritura segura + auditoría
- certificación -> batería de tests del nuevo core, no en runtime

### Host AI Engine y Director IA
- papel: interpretar ambigüedad, proponer correspondencias, explicar incidencias, preparar confirmaciones y registrar auditoría.
- no sustituye cálculos, persistencias ni reglas de validación.

## 5. Tabla de decisión función por función

| Función legado | Archivo | Categoría actual | Estrategia | Componente destino | Partes reutilizables | Partes a descartar | IA real | GUI | Riesgo | Prioridad | Esfuerzo | Criterio de retirada |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Analizar Excel | PIPELINES/pipeline_excel.py | C | B | Centro de Importación | contrato de análisis y lectura_host_ai | pipeline legacy aislado | no | no | medio | alta | media | nuevo analizador cubre mismas métricas y tests |
| Detectar tipo de Excel | detector_documentos_excel.py | C | B/C | Centro de Importación + IMPORTACION_IA | reglas, motivos, confianza | tipos legacy no usados | opcional | no | alto | alta | media | detector común clasifica igual o mejor |
| Mapear columnas | mapeador_columnas_excel.py | C implícita | A | Centro de Importación | diccionario y scoring | acoplamiento al detector legacy | no | no | alto | alta | baja | nuevo mapeador usa mismo diccionario |
| Resolver conflictos Excel | resolutor_conflictos_excel.py | C | B | Asistente de Incidencias | taxonomía de conflictos | último informe solo memoria local | opcional | no | alto | alta | media | incidencias 601 cubren mismos casos |
| Vista previa artículos | importador_articulos_excel.py | C | B | Catálogo Maestro + Centro | parsing y normalización | memoria interna temporal | no | no | alto | alta | media | preview 601 equivalente |
| Importar artículos | importador_articulos_excel.py | C | B | Catálogo Maestro + Centro | validaciones, slug, precios | escritura via costes_inteligente ad hoc | no | no | muy alto | muy alta | alta | importación 601 confirmada con histórico y duplicados |
| Vista previa inventario | importador_inventario_excel.py | C | B | Centro + Stock | cálculo de cambios | acoplamiento a importador de artículos legacy | no | no | alto | alta | media | preview 601 muestra diferencias equivalentes |
| Comparar inventario | importador_inventario_excel.py | C | B | Centro + Stock | contrato de cambios | formato legacy de salida | no | no | alto | alta | media | comparación 601 con mismas diferencias |
| Importar inventario | importador_inventario_excel.py | C | B | Stock + Centro + Auditoría | conciliación por diferencia | altas básicas implícitas sin workflow 601 | no | no | muy alto | muy alta | alta | escritura confirmada y trazable en 601 |
| I1.1 detector escandallos antiguos | detector_escandallos_antiguos_i11.py | C | D | legado temporal | heurísticas si reaprovechan | UI separada si no hay uso real | no | no | medio | baja | baja | detector común absorbe formatos antiguos o uso cae a cero |
| I1.2 importación segura recetas | importador_seguro_escandallos_i12.py | B | A/B/C | Centro + Recetas + Incidencias + Engine | memoria, matching, umbrales | escritura sobre escandallos legacy | opcional | no | alto | alta | alta | flujo 601 importa recetas seguras con memoria |
| I1.3.1 detector limpio menús | detector_limpio_menus_i131.py | B | A/B | Centro + Menús | reglas de filas y economía | acoplamiento a menú legado | no | no | alto | alta | alta | estructura intermedia 601 equivalente |
| I1.3.2.1.1 reconocimiento | motor_reconocimiento_menus_i1321.py | C | B/C | Menús + IMPORTACION_IA + MENUS_IA | matching determinista | formatos solo legado | opcional | no | alto | alta | alta | reconocimiento 601 cubre mismas coincidencias |
| I1.3.2.2 árbol semántico | constructor_arbol_semantico_menus_i1322.py | C | B | Motor de Menús | separación principal/guarnición/salsa | contratos dependientes solo de menús legacy | no | no | alto | alta | alta | árbol común usado por simulación e importación |
| I1.3.2.3 resolución asistida | vista_previa_resolucion_asistida_menus_i1323.py | B | B/C | Incidencias + Director IA | contrato de pendientes y decisiones | UI legacy específica | opcional | sí en el futuro | alto | media-alta | alta | misma revisión desde 601 |
| I1.3.2.4 aprendizaje culinario | motor_aprendizaje_culinario_i1324.py | C | A/B | Incidencias + historial importación | esquema de aprendizaje e historial | persistencia separada si se integra mejor | opcional | no | medio-alto | media | media | memoria integrada en 601 |
| I1.3.3 preimportación | preimportador_definitivo_menus_i133.py | B | B | Centro modo SIMULAR | contrato LISTA/BLOQUEADA | concepto aislado fuera del centro | no | no | alto | alta | alta | Centro 601 simula y bloquea antes de escribir |
| I1.3.3.1 bloqueos | resolutor_bloqueos_preimportacion_i1331.py | B | B/C | Incidencias + Recetas/Escandallos | reglas de bloqueo y backup | escritura sobre escandallos legacy | opcional | sí futura | muy alto | alta | alta | resolución 601 con confirmación agrupada |
| I1.3.4.1.1 simulación multihoja | simulador_importacion_menus_i13411.py | C | B | Centro + Menús modo SIMULAR | estructura de simulación | naming legacy | no | no | medio-alto | media | media | simulador común 601 |
| I1.3.4.1.2 clasificador gastronómico | simulador_importacion_menus_i13412.py | C | B/C | Centro + MENUS_IA | reglas válidas + explicación | heurísticas acopladas a flujo legado | opcional | no | medio-alto | media | media | mismo output en estructura común |
| I1.3.4.1.3 bandeja revisión | bandeja_revision_i13413.py | C | B/C | Incidencias + Director IA | operaciones masivas | sesión UI legacy | opcional | sí futura | alto | media | alta | revisión masiva 601 |
| I1.3.4.1.4 interpretación | bandeja_revision_i13414.py | C | C | Engine + Menús | reglas deterministas auxiliares | módulo aislado | sí opcional | no | medio | media | media | propuestas equivalentes explicadas |
| I1.3.4.1.5 conocimiento gastronómico | bandeja_revision_i13415.py | C | C | Engine + Menús | taxonomía/conocimiento actual | UI específica | sí opcional | no | medio | media | media | conocimiento integrado al Engine |
| I1.3.4.2 diagnóstico escritura segura | diagnostico_escritura_segura_i1342.py | C | E | tests y repos 601 | criterios de seguridad | herramienta runtime separada | no | no | medio | baja | baja | garantías cubiertas por tests R6.x |
| I1.3.4.3 importación definitiva menús | importador_definitivo_menus_i1343.py | B | B | Centro + BibliotecaMenus601 | confirmación, idempotencia | sesión revisada legacy | no | no | muy alto | muy alta | alta | importación final 601 con mismas garantías |
| I1.3.4.4 auditoría postimportación | auditor_integridad_postimportacion_i1344.py | B | B | auditoría 601 + historial | reglas de integridad | formato de informe legacy | no | no | alto | media-alta | media | auditoría 601 equivalente |
| I1.3.4.4.1 corrección postimportación | bandeja_correccion_postimportacion_i13441.py | B | B/C | Incidencias + Menús | operaciones de corrección | UI legacy aislada | opcional | sí futura | alto | media-alta | alta | corrección 601 confirmada |
| I1.3.4.4.2 corrección masiva | bandeja_correccion_inteligente_i13442.py | B | B/C | Incidencias + Director IA | agrupaciones y filtros | acoplamiento a bandeja legacy | opcional | sí futura | alto | media-alta | alta | acciones agrupadas 601 |
| I1.3.5 certificación final | certificador_final_importador_i135.py | C | E | suite de tests | criterios de certificación | certificador runtime | no | no | medio | media | media | pruebas nuevas superan cobertura legacy |

## 6. Diseño específico: importación de artículos Excel

### 6.1 Principio
No crear un segundo importador de productos. El flujo futuro debe vivir dentro del Centro de Importación común y escribir únicamente mediante Catálogo Maestro / RepositorioProductosMaestro601.

### 6.2 Reutilización obligatoria
- lector del libro y análisis estructural: reemplazo del pipeline_excel dentro del Centro común.
- detector y mapeador: servicio común del Centro de Importación.
- taxonomía de conflictos del resolutor clásico.
- repositorio de autoridad: RepositorioProductosMaestro601.

### 6.3 Flujo futuro propuesto
1. Analizar libro.
2. Detectar hojas/bloques de tipo productos o mixtos.
3. Construir estructura intermedia normalizada de filas de producto.
4. Validar por fila:
   - nombre obligatorio;
   - unidad base/unidad compra coherentes;
   - precio parseable si existe;
   - proveedor normalizado;
   - formato/cantidad por envase compatibles;
   - stock mínimo no negativo;
   - duplicidad por código y por nombre normalizado.
5. Resolver coincidencias contra catálogo real:
   - exacta por código;
   - exacta por nombre normalizado;
   - probable por similitud controlada;
   - conflicto si hay más de una coincidencia plausible.
6. Preparar vista previa:
   - altas nuevas;
   - actualizaciones seguras;
   - conflictos;
   - precios históricos a registrar;
   - proveedores a crear o vincular.
7. En modo EJECUTAR, solo con confirmación:
   - crear/editar producto;
   - registrar asociación proveedor-producto;
   - registrar histórico de precio;
   - registrar incidencias no resueltas;
   - auditar operación.

### 6.4 Validaciones únicas a conservar
- unidad ausente como aviso explícito;
- parseo tolerante de precio;
- duplicado por ID calculado o código;
- coexistencia de proveedor, familia, ubicación y stock mínimo;
- posibilidad de actualizar existentes bajo política explícita.

### 6.5 Tratamiento de proveedores y precios
- proveedor no se escribe como texto suelto final sin control; debe resolverse contra proveedores reales o crearse vía repositorio maestro.
- el precio no debe escribirse solo en producto actual; debe registrar histórico con fecha, proveedor, unidad y bandera de provisional si aplica.
- si hay cambio fuerte de precio, generar incidencia y requerir confirmación.

### 6.6 Unidades y formatos
- separar:
   - unidad de compra;
   - unidad base;
   - unidad de receta;
   - cantidad por formato.
- si el Excel solo aporta una, se puede proponer derivación, pero no inventarla silenciosamente.

### 6.7 Confirmación masiva
- confirmación agrupada por resumen:
   - altas nuevas;
   - actualizaciones;
   - proveedores nuevos;
   - precios fuertes.
- Director IA puede explicar el impacto, pero la aprobación la hace el usuario.

### 6.8 Incidencias
- se integran en AsistenteResolucionIncidencias601 con estados:
   - pendiente;
   - resuelta;
   - descartada;
   - aceptada con riesgo.

### 6.9 Criterio futuro de retirada del flujo antiguo de artículos
- el Centro común debe igualar o superar:
   - vista previa;
   - importación;
   - tratamiento de duplicados;
   - histórico de precios;
   - gestión de proveedores;
   - incidencias;
   - pruebas equivalentes.

## 7. Diseño específico: inventario Excel

### 7.1 Principio
No permitir que una importación de inventario modifique Stock sin confirmación. El Centro solo prepara y el servicio de Stock ejecuta.

### 7.2 Reparto de responsabilidades
- Centro de Importación:
   - análisis del libro;
   - detector/mapeo;
   - estructura intermedia de líneas de inventario;
   - preview y comparación;
   - consolidación de incidencias;
   - preparación de confirmación.
- Stock:
   - cálculo de diferencias reales;
   - validación de lotes, ubicaciones y unidades;
   - aplicación transaccional de ajustes.
- Catálogo:
   - resolver artículo por código/nombre;
   - alta controlada si el flujo lo permite.
- Incidencias:
   - faltantes de unidad;
   - artículos desconocidos;
   - ubicaciones extrañas;
   - ajustes negativos no aplicables;
   - lotes incompatibles.
- Auditoría:
   - registro de diferencia previa;
   - movimientos creados;
   - confirmación del usuario;
   - rollback si falla una fase crítica.

### 7.3 Flujo futuro propuesto
1. Analizar libro y detectar bloques inventario.
2. Construir líneas normalizadas.
3. Comparar contra stock actual por artículo + unidad + lote + ubicación cuando existan.
4. Generar preview con:
   - sin cambios;
   - sobrantes;
   - faltantes;
   - lote nuevo;
   - lote sin caducidad;
   - unidad incompatible;
   - artículo inexistente.
5. Pedir confirmación explícita antes de escribir.
6. Aplicar en Stock con trazabilidad de movimientos.
7. Verificar consistencia postimportación.

### 7.4 Reglas clave
- no crear artículo silenciosamente si no está resuelto el mínimo catálogo;
- no consumir stock con unidad incompatible;
- no mezclar lotes distintos al consolidar;
- no aplicar ajuste negativo no sustentado;
- no perder caducidad/ubicación/lote al importar.

### 7.5 Criterio futuro de retirada del flujo antiguo de inventario
- preview equivalente;
- comparación equivalente;
- confirmación previa obligatoria;
- trazabilidad completa de movimientos;
- pruebas mejores o equivalentes;
- cero necesidad del importador legacy para un caso operativo real.

## 8. Diseño del detector común de tipo de Excel

### 8.1 Tipos objetivo
- productos
- inventario
- recetas
- escandallos
- menús
- proveedores
- precios
- documento mixto
- desconocido

### 8.2 Arquitectura de decisión
#### Capa 1. Reglas deterministas obligatorias
- nombres de hojas;
- encabezados detectados;
- densidad de celdas;
- tipos de dato por columna;
- patrones de columnas fuertes/secundarias;
- señales de tabla repetida;
- coexistencia de varios tipos por libro.

#### Capa 2. Soporte del Host AI Engine solo en ambigüedad
- recibe resumen estructural, no el libro entero bruto como única fuente;
- devuelve propuesta de tipo, explicación y confianza;
- nunca decide si contradice reglas fuertes;
- si la duda persiste, requiere confirmación del usuario.

### 8.3 Contrato de salida propuesto
- libro_id
- archivo
- hojas[]
  - nombre
  - visible/oculta
  - bloques[]
    - tipo_detectado
    - confianza_determinista
    - confianza_engine
    - confianza_final
    - motivos[]
    - columnas_clave[]
    - requiere_confirmacion
- tipo_principal_libro
- es_mixto
- incidencias[]
- lectura_host_ai

## 9. Diseño del análisis estructural multihoja

### 9.1 Estructura intermedia común
- libro
  - archivo
  - hojas[]
    - nombre
    - visible
    - posición
    - bloques[]
      - bloque_id
      - rango
      - tipo_sugerido
      - cabeceras[]
      - filas[]
      - tablas[]
      - incidencias[]
      - relaciones[]

### 9.2 Casos que debe cubrir
- varias hojas relevantes en un mismo libro;
- cabeceras desplazadas;
- bloques separados por líneas vacías;
- hojas ocultas;
- tablas mixtas;
- múltiples menús por libro;
- varias tarifas o columnas de precio;
- hojas auxiliares;
- fórmulas;
- celdas combinadas.

### 9.3 Reglas mínimas
- no perder referencia a fila/columna/origen;
- no aplanar bloques distintos sin trazabilidad;
- conservar relaciones entre hojas auxiliares y principales;
- marcar ruido e incertidumbre como incidencias, no ignorarlas.

## 10. Cadena avanzada de menús: decisión por tramo

### 10.1 Reconocimiento
- Valor funcional real: localiza recetas/artículos candidatos y evita inventar enlaces.
- Debe migrarse: sí.
- Tipo de sustitución: B/C.
- Determinista: matching por nombre, aliases, secciones, costes, exactas y probables.
- IA: solo para sugerencias explicadas en casos ambiguos.
- Persistencia: no.

### 10.2 Árbol semántico
- Valor: convierte texto culinario en estructura explotable por Menús.
- Debe migrarse: sí.
- Tipo: B.
- Determinista: parsing de conectores, secciones, roles culinarios.
- IA: opcional solo si falla el parsing o la estructura es ambigua.
- Persistencia: no.

### 10.3 Aprendizaje culinario
- Valor: reduce repetición manual y mantiene memoria de decisiones humanas.
- Debe migrarse: sí.
- Tipo: A/B.
- Determinista: esquema e historial.
- IA: no obligatoria; puede consultar esa memoria.
- Persistencia: sí, integrada con historial de incidencias/importación.

### 10.4 Preimportación
- Valor: separa simulación y escritura, hoy crítico.
- Debe migrarse: sí.
- Tipo: B.
- Determinista: cálculo del contrato de importación y estado bloqueado/lista.
- IA: no para decidir; solo explicar.
- Persistencia: no de negocio.

### 10.5 Bloqueos
- Valor: impide importar con componentes no resueltos.
- Debe migrarse: sí.
- Tipo: B/C.
- Determinista: reglas de bloqueo.
- IA: propone vínculos/creaciones; siempre con confirmación.
- Persistencia: solo si se confirma resolución.

### 10.6 Simulación
- Valor: permite ver impacto antes de escribir.
- Debe migrarse: sí.
- Tipo: B.
- Determinista: Motor de Menús + datos resueltos.
- IA: no necesaria salvo explicación.
- Persistencia: no.

### 10.7 Corrección masiva
- Valor: hace operable la revisión de lotes de incidencias.
- Debe migrarse: sí.
- Tipo: B/C.
- Determinista: filtros, agrupaciones, operaciones seguras por lote.
- IA: sugerir agrupación o nombre destino; no guardar por sí sola.
- Persistencia: solo tras confirmación.

### 10.8 Auditoría
- Valor: valida estructura y coherencia después de escribir en menús reales.
- Debe migrarse: sí.
- Tipo: B.
- Determinista: reglas de integridad y consistencia.
- IA: solo explicar resultados.
- Persistencia: historial/auditoría.

### 10.9 Certificación
- Valor: garantiza técnicamente la retirada del legado.
- Debe migrarse: sí, pero fuera de runtime.
- Tipo: E del módulo legacy, B para su cobertura funcional.
- Determinista: tests y diagnósticos.
- IA: no certifica; puede resumir evidencia, no sustituirla.

## 11. Rol de la IA

### 11.1 Capacidades futuras donde sí aporta valor
- interpretar encabezados ambiguos;
- detectar que una hoja es mixta cuando las reglas no bastan;
- reconocer estructura culinaria libre de un menú;
- sugerir correspondencias entre nombre libre y receta/artículo;
- explicar incidencias y opciones de resolución;
- proponer acciones agrupadas sobre incidencias repetidas.

### 11.2 Capacidades donde no debe tener autoridad
- modificar datos sin confirmación;
- inventar precios;
- inventar cantidades;
- fusionar productos automáticamente;
- alterar stock;
- sustituir cálculos de coste o rentabilidad;
- certificar integridad por sí sola;
- marcar una importación como segura sin respaldo determinista.

### 11.3 Regla operacional
La IA solo puede:
- proponer;
- explicar;
- desambiguar;
- resumir impacto;
- preparar confirmaciones.

La autoridad final debe seguir en:
- reglas deterministas;
- servicios de dominio;
- validaciones;
- persistencias controladas;
- confirmación explícita del usuario.

## 12. Plan de migración por sprints

### Sprint 1. Núcleo común del libro Excel
- Alcance: análisis estructural multihoja + detector común + mapeador común.
- Exclusiones: escritura de negocio.
- Módulos afectados: Centro de Importación, detector/mapeador, modelos intermedios.
- Pruebas: equivalencia con test_lector_excel.py, test_detector_documentos_excel.py, test_resolucion_conflictos_excel.py básica.
- Condición de salida: el Centro clasifica productos/inventario/recetas/escandallos/menús/proveedores/precios/desconocido/mixto.
- Legado retirable: ninguno todavía, pero reduce dependencia base.

### Sprint 2. Importación avanzada de artículos
- Alcance: preview e importación confirmada de artículos sobre Catálogo Maestro 601.
- Exclusiones: inventario y menús.
- Módulos afectados: Centro de Importación, Catálogo Maestro, RepositorioProductosMaestro601, incidencias.
- Pruebas: equivalencia con test_importador_articulos_excel.py + nuevos tests 601 de proveedores/precios/histórico.
- Condición de salida: reemplazo funcional del importador_articulos_excel.
- Legado retirable: opciones 5 y 6 del menú clásico, tras convivencia.

### Sprint 3. Preview y comparación de inventario
- Alcance: estructura intermedia de inventario + comparación sin escritura.
- Exclusiones: importación definitiva.
- Módulos afectados: Centro, Stock, Catálogo, incidencias.
- Pruebas: equivalencia con test_importador_inventario_excel.py en modo preview/comparar.
- Condición de salida: preview y diferencias equivalentes.
- Legado retirable: comparar_inventario legacy, no aún importar.

### Sprint 4. Importación confirmada de inventario
- Alcance: confirmación, escritura segura, trazabilidad y rollback de inventario.
- Exclusiones: menús.
- Módulos afectados: Stock, Auditoría, Centro, Catálogo.
- Pruebas: equivalencia funcional más pruebas de rollback y no side-effects.
- Condición de salida: importar inventario sin tocar stock sin confirmación.
- Legado retirable: opciones 7 y 8.

### Sprint 5. Importación segura de recetas
- Alcance: memoria de vinculaciones I1.2 integrada en 601 y flujo seguro de recetas.
- Exclusiones: menús avanzados.
- Módulos afectados: Centro, Recetas, Incidencias, Engine opcional.
- Pruebas: equivalencia con test_i12_importador_seguro_escandallos.py y test_i122_revision_aprendizaje.py.
- Condición de salida: sustituir I1.2 en valor funcional, no solo en UI.
- Legado retirable: I1.2.

### Sprint 6. Menús estructurados: detector, reconocimiento y árbol
- Alcance: detector limpio, reconocimiento, árbol semántico y estructura intermedia de menús.
- Exclusiones: importación definitiva.
- Módulos afectados: Centro, Menús, Engine para ambigüedad.
- Pruebas: equivalencia con test_i131, test_i1321, test_i1322.
- Condición de salida: preprocesado de menús en 601 con paridad funcional.
- Legado retirable: I1.3.1, I1.3.2.1.1, I1.3.2.2.

### Sprint 7. Menús revisables: resolución, aprendizaje, preimportación y bloqueos
- Alcance: resolución asistida, memoria culinaria, modo SIMULAR, estado bloqueado/lista y resolución de bloqueos.
- Exclusiones: postimportación.
- Módulos afectados: Asistente de Incidencias, Menús, Recetas, Engine, Director IA.
- Pruebas: equivalencia con test_i1323, test_i1324, test_i133, test_i1331.
- Condición de salida: sustituir la etapa previa a la importación real.
- Legado retirable: I1.3.2.3, I1.3.2.4, I1.3.3, I1.3.3.1.

### Sprint 8. Simulación, importación final y postimportación de menús
- Alcance: simuladores, importación definitiva, auditoría y corrección agrupada.
- Exclusiones: retirada física del legado.
- Módulos afectados: Centro, Menús, Auditoría, Incidencias, Director IA.
- Pruebas: equivalencia con test_i13411, i13412, i13413, i13414, i13415, i1343, i1344, i13441, i13442.
- Condición de salida: cadena completa de menús cubierta en 601.
- Legado retirable: I1.3.4.1.1 a I1.3.4.4.2.

### Sprint 9. Certificación y retirada controlada del legado
- Alcance: suite de certificación equivalente o superior, documentación, convivencia, redirección y plan de rollback.
- Exclusiones: borrado definitivo de archivos si no se aprueba.
- Módulos afectados: tests, documentación, accesos UI, Engine auditoría.
- Pruebas: sustitución funcional de I135 por certificación R6.x ampliada.
- Condición de salida: criterios objetivos de retirada cumplidos.
- Legado retirable: acceso principal a Excel Importaciones, manteniéndolo quizá como acceso legado temporal.

## 13. Dependencias clave
- El detector común depende del analizador estructural multihoja.
- Artículos e inventario dependen del detector y mapeador comunes.
- Inventario depende de que Catálogo Maestro tenga flujo robusto de resolución de productos.
- Menús dependen de estructura intermedia, reconocimiento y árbol semántico.
- Bloqueos y corrección dependen de incidencias y confirmaciones agrupadas.
- Cualquier uso del Engine depende de contratos deterministas previos y de auditoría de confirmaciones.

## 14. Riesgos
- Riesgo alto si se intenta migrar artículos e inventario dentro del propio flujo legacy en vez de absorberlos en Centro 601.
- Riesgo alto si la IA se usa como autoridad de detección o de escritura.
- Riesgo medio si se trasladan bandejas legacy a una GUI nueva antes de estabilizar contratos de dominio.
- Riesgo medio si se retira el aprendizaje culinario sin una memoria equivalente integrada.
- Riesgo bajo si primero se consolida el núcleo común de libro Excel y luego se sustituyen dominios uno a uno.

## 15. Criterios objetivos de retirada del legado
No retirar Excel Importaciones hasta que se cumplan todos:
1. Todas las funciones únicas tienen sustitución operativa demostrada.
2. Existen pruebas equivalentes o mejores por cada bloque funcional.
3. Persistencias nuevas son compatibles y no crean dobles autoridades.
4. Los datos reales no se pierden y existe rollback probado.
5. El acceso nuevo está disponible en el flujo de uso real relevante, incluido Modo Piloto Privado cuando proceda.
6. La documentación operativa y técnica está actualizada.
7. Ha existido un periodo de convivencia controlada.
8. El acceso antiguo puede redirigir con seguridad al nuevo flujo o quedar etiquetado como legado.
9. La confirmación del usuario existe para todas las escrituras críticas.
10. La certificación del nuevo flujo supera o iguala I135 y la batería legacy relacionada.

## 16. Recomendación final
3. EJECUTAR UNA MIGRACION HIBRIDA POR SPRINTS.

Justificación basada en el código real del proyecto:
- el Centro de Importación 601 ya demuestra que puede absorber importaciones verticales, como escandallos y menús básicos;
- el Catálogo Maestro 601 y las Bibliotecas 601 ya fijan mejor la autoridad de datos que el legado;
- el legado todavía contiene lógica determinista valiosa que conviene reaprovechar, especialmente mapeo, matching, memoria de decisiones y clasificación de filas;
- varias partes semánticas de menús se benefician de apoyo futuro del Engine, pero no deben depender solo de IA real;
- la retirada segura exige primero sustituir artículos, inventario y la cadena avanzada de menús, que hoy siguen siendo críticos y no totalmente cubiertos.
