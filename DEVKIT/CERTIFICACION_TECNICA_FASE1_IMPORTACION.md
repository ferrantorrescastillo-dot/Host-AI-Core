# CERTIFICACIÓN TÉCNICA — FASE 1 IMPORTACIÓN INTELIGENTE

Fecha: 31 de agosto de 2026
Versión base: `af3642d2690b6e3a4243788bab0de244b30c602e`
Rama: `feature/compras-web`
Resultado: CERTIFICADA TÉCNICAMENTE; VALIDACIÓN MANUAL EN CURSO

## Alcance

Fuente, análisis estructural, `HostAIImportPackage 0.1`, normalización, matching determinista, deduplicación, IA opcional, propuestas, borrador revisable, confirmación humana, escritura transaccional e idempotente, auditoría y verificación posterior.

## Evidencia automática

- Regresión focal previa al cambio: 98 pruebas superadas.
- Certificación y regresión parcial tras el cambio: 57 pruebas superadas.
- Suite backend focal final: 117 pruebas superadas, 0 fallos.
- Regresión web de Biblioteca/Importaciones: 31 pruebas superadas, 0 fallos.
- IA de pruebas fake/mock; cero llamadas externas.
- Fixtures y directorios temporales; `DATOS/` no se usó como repositorio de prueba.

## Métricas de escala observadas

Escenario sintético con 40 regiones ambiguas de layout equivalente: 40 apariciones, 1 concepto único, 1 concepto enviado, 1 llamada IA fake, 39 respuestas reutilizadas y 39 llamadas ahorradas. El fake no reporta tokens ni coste y no se estiman.

## Garantías

- ANALYZE/PREVIEW no persisten dominio.
- IA requiere opt-in; el fallback determinista sigue funcionando.
- Salidas IA inseguras o con autoridad operativa se rechazan.
- Las propuestas pasan por adaptador, matchers, revisión y confirmación.
- CONFIRM valida aceptación, usuario, versión/fingerprint, idempotencia, rollback y verificación posterior.
- Reimportar reutiliza entidades confirmadas dentro del contrato probado.
- La decisión humana acepta, modifica, rechaza/ignora, reclasifica o vincula y prevalece sobre la IA.
- La procedencia se conserva en recetas, artículos, propuestas e historial.
- Stock, lotes y autoridad crítica no pueden venir del package ni escribirse durante análisis.
- El completado de recetas separa propuesta IA, preview, confirmación e historial humano.

## Limitaciones

- Alcance automático con datos sintéticos/temporales en Windows y Python 3.13.
- Calidad culinaria y documento real del restaurante pendientes.
- El diagnóstico histórico Boronat no se ejecutó porque copia `DATOS/db`; esta certificación exige aislamiento de los datos privados actuales.
- Proveedor, modelo, tokens y coste solo pueden informar valores reales cuando el proveedor los entregue.

## Evidencia final de cierre tecnico (1 de septiembre de 2026)

Estado actualizado: `FASE 1 - LISTA PARA CIERRE FORMAL`; el cierre sigue pendiente de confirmacion del usuario.

Se repitio `Escandallos Boronat (1).xlsx` mediante los servicios reales, en repositorio temporal limpio, con IA desactivada, exclusion A.P solo para la sesion y sin `CONFIRM`. La clasificacion estructural separa fichas tecnicas `M.P` de menus operativos, deja `PLANTILLA COSTE MENU` como documentacion y `MENU FIN DE AÑO` como documento multicolumna pendiente de desglose explicito. No proyecta titulos contenedores como recetas.

Evidencia ejecutada: 122 pruebas backend de Fase 1 y 31 pruebas web superadas; typecheck correcto. El Excel produjo 21 hojas, 352 articulos documentales, 36 exclusiones A.P, 46 recetas independientes y 10 menus operativos; 129 lineas de menu resueltas y 14 pendientes legitimas. Proveedores y relaciones proveedor: cero. IA externa y escrituras operativas: cero.

Siguiente paso unico: revision final y commit de cierre por el usuario; no iniciar Fase 1.5 antes de ese hito.

## Siguiente paso

Repetir el análisis del mismo Excel de validación y comparar resultados antes/después.

## Correcciones derivadas de la primera validación real

El 31 de agosto de 2026 la validación manual detectó clasificación ausente de menús, relaciones artificiales sin proveedor, propuestas visibles desalineadas con el matching y necesidad de excluir A.P antiguos solo en esa sesión. Se corrigieron los componentes existentes sin crear autoridades paralelas.

Evidencia posterior: 121 pruebas backend de Fase 1 y 31 pruebas web superadas; typecheck correcto. La validación manual no se considera completada hasta repetir el mismo Excel.

## Correccion final del completado masivo (1 de septiembre de 2026)

El contrato publico del batch devuelve ahora `ok=true` en `start`, `get`, `next`, `cancel`, `select` y `preview`; los errores conservan su codigo HTTP y mensaje util. `recipe_ids` ausente mantiene el modo separado de toda la Biblioteca, mientras una lista explicita —incluida la lista vacia— define una frontera cerrada y nunca incorpora recetas adicionales.

Desde una importacion, la UI calcula el contador con los mismos IDs canonicos que envia. En la copia temporal del estado Boronat se observaron 46 recetas importadas: 30 ya disponian de identidad canonica apta para el batch y 16 aun requerian importacion o resolucion. La UI y la cola quedaron en 30/30, HTTP 200, `ok=true`, cero llamadas IA durante `start`, cancelacion correcta y cero cambios en los datos operativos.

Evidencia final acumulada: 126 pruebas backend y 33 frontend superadas; TypeScript y `git diff --check` correctos. Estado: `LISTA PARA VALIDACION HUMANA FINAL DE FASE 1`; sin commit, push ni inicio de Fase 1.5.

## Tolerancia a fallos y validacion segura de propuestas (1 de septiembre de 2026)

La validacion humana real detecto que un timeout de una receta interrumpia toda la cola y que la seleccion masiva incluia datos sanitarios o de rendimiento. El batch registra ahora cada fallo transitorio como `ERROR_PROVIDER`, continua con la receta siguiente y permite reintento unitario o global sin regenerar los exitos previos. Los intentos quedan limitados a tres por receta y la UI aplica el backoff recomendado antes del reintento explicito.

La seleccion masiva queda cerrada a `descripcion`, `elaboracion` y `observaciones`, despues del filtro de contenido critico. Tiempos, alergenos, vida util, conservacion, congelacion/refrigeracion, regeneracion, rendimiento y numero de raciones requieren seleccion humana individual. El prompt prohibe esconder datos criticos o ingredientes no aportados dentro de texto libre; una validacion posterior de alta confianza rechaza el campo completo ante rendimiento, vida util, temperatura interna de seguridad, HACCP, trazas/alergenos o datos comerciales embebidos. No se recortan frases mediante inferencias culinarias fragiles.

Evidencia ejecutada: 129 pruebas backend de Fase 1 y 268 pruebas frontend superadas; typecheck correcto. Las pruebas usaron provider fake/mock y repositorios temporales, sin IA externa, sin confirmaciones reales y sin escrituras sobre `DATOS/`. Estado: `LISTA PARA REPETIR VALIDACION HUMANA FINAL DE FASE 1`; no equivale a validacion humana completada ni a cierre formal.

## Flujo oficial de completado externo (1 de septiembre de 2026)

Se incorpora el contrato XLSX versionado `HOSTAI_RECIPE_COMPLETION_PACKAGE 0.1`. La exportación conserva selección contextual, orden, IDs canónicos, datos actuales, campos pendientes, campos de propuesta separados, fecha, ámbito, importación de origen y fingerprint. La reimportación valida contenedor, versión, schema, IDs, duplicados, frontera, fingerprints, tipos, tamaños y fórmulas; procesa filas de forma aislada y no escribe.

El adaptador externo no crea una segunda autoridad. Tanto las propuestas de Host AI como las de archivo convergen en la clasificación compartida, el batch, la selección, el preview autorizado, la confirmación idempotente, la procedencia por campo y la lectura posterior de `RecetaDocumentacionWriteService`. La fuente externa registra canal y origen granular; continúa en estado de propuesta/revisión hasta confirmación humana.

Evidencia automática final: 142 pruebas backend relevantes de Fase 1 y 270 pruebas frontend completas, sin fallos; typecheck correcto. El diagnóstico aislado con `Escandallos Boronat (1).xlsx` reprodujo 21 hojas, 1029 filas, 46 recetas, 30 canónicas aptas, 316 artículos efectivos, 300 reutilizados, 16 en revisión, 10 menús y 36 A.P excluidos solo de la sesión. Un timeout controlado en `REC601-000006` quedó aislado, la cola llegó a 30/30, el retry resolvió el fallo y la cancelación siguió operativa. Se exportaron 30 recetas, se reimportó una propuesta sintética, se obtuvo preview de una receta y no se ejecutó confirmación.

IA real: cero llamadas y coste 0. Datos: cero cambios operativos incluso en la copia; el agregado de `DATOS` original permaneció equivalente antes/después del diagnóstico. Estado: `LISTA PARA REPETIR VALIDACION HUMANA FINAL DE FASE 1`; esto no declara cerrada la Fase 1, no inicia Fase 1.5 y mantiene pendiente la validación humana final.

## Corrección del round-trip XLSX físico real (1 de septiembre de 2026)

La validación humana encontró dos condiciones que el contrato inicial no representaba bien. Algunos editores guardan la hoja `RECETAS` sin una dimensión calculada y `openpyxl` devuelve entonces `max_row/max_column=None`; la importación ahora itera de forma acotada sin depender de ese metadato. Además, “fila con propuesta segura” y “fila que requiere revisión” pasan a ser dimensiones simultáneas: una fila mixta conserva sus campos seguros en el batch y mantiene separados los campos críticos para validación individual.

La respuesta incorpora recibo del archivo (`nombre`, tamaño y SHA-256), traza por campo desde `*_propuesto` hasta normalización/política/estado y el aviso explícito `SIN_PROPUESTAS_RECIBIDAS`. La UI muestra el nombre y la huella recibidos, ambos conteos de filas y campos y una alerta específica cuando el fichero seleccionado no contiene ningún valor propuesto.

La comparación aislada de los dos ficheros físicos disponibles explica el resultado observado sin atribuirlo silenciosamente al parser. `hostai-completado-recetas-IMPWEB-418E3E0F5CBE (1).xlsx` (SHA-256 `f693961607d694561f6760176b9cedfd8136cd014281ebffe744cdcb2f42c497`) contiene 30 filas y cero valores `*_propuesto`, por lo que reproduce exactamente 30 recibidas, 0 útiles y batch 0/0. La UI anterior no registraba el nombre/huella y no permite demostrar retrospectivamente qué fichero fue seleccionado. El fichero completado `...-CHATGPT-COMPLETO.xlsx` (SHA-256 `bd21f4317b352f9dfe73371b183170057605c70ca4d33f1bd1bf6513919514af`) sí contiene 376 propuestas y, tras la corrección de compatibilidad, produce 30 filas con propuestas, 30 útiles, 30 con revisión, 0 rechazadas y batch 30/30; clasifica 83 campos seguros, 257 críticos individuales, 29 rechazados por datos ya existentes/política y 7 textos críticos bloqueados.

Evidencia automática: 25 pruebas focales del intercambio físico, 45 de completado/batch/workflow, 153 backend relevantes de Fase 1, 38 frontend focales y 271 frontend completas, sin fallos; typecheck correcto. Todas las importaciones y previews se ejecutaron sobre fixtures o copia temporal, sin IA real, sin confirmación real y sin escritura operativa. Estado: `LISTA PARA REPETIR ROUND-TRIP XLSX REAL`; no cierra Fase 1 ni inicia Fase 1.5.

## Corrección UI selección → preview (1 de septiembre de 2026)

La validación humana confirmó que `POST /seleccion` respondía 200 y persistía correctamente las selecciones, pero por contrato devuelve `preview=null`: cada nueva selección invalida una vista previa anterior. La UI se limitaba a sustituir el estado React con esa respuesta. Dejaba un CTA genérico `Continuar`, mantenía visibles los botones de aceptación y no comunicaba el número seleccionado, por lo que visualmente parecía que el clic no tenía efecto.

El contrato queda explícito y conserva la separación de responsabilidades: `POST /seleccion` valida y persiste la selección en el batch sin escribir; la UI solicita inmediatamente `POST /preview`; el preview autorizado relee las recetas y devuelve únicamente cambios seleccionados; `POST /confirmar` sigue siendo la única transición que puede escribir. Si falla la segunda llamada, la selección permanece guardada y la UI muestra un error específico junto a `Revisar cambios antes de guardar` para reintentar el preview.

La pantalla muestra el número de propuestas seguras y críticas seleccionadas, oculta acciones ya aplicadas y renderiza receta, campo, valor actual, valor propuesto, procedencia, clasificación y acción `Completa/Sobrescribe/Actualiza`. Los críticos no seleccionados individualmente no entran en preview. La selección por receta, la selección masiva y la individual convergen en el mismo helper y los mismos endpoints; no se añadió autoridad de escritura.

Evidencia: 35 pruebas backend focales de batch/exchange, 154 backend relevantes de Fase 1, 38 frontend focales y 271 frontend completas, sin fallos; typecheck correcto. Se probaron HTTP 200, persistencia, repetición sin duplicado, preview no nulo al solicitarlo, exclusión de críticos, selección individual, cero escritura y `datos_reales_modificados=false`. Estado: `LISTA PARA REPETIR SELECCIÓN → PREVIEW EN UI`; sin confirmación real, commit, push ni Fase 1.5.

## Corrección de selección por receta y navegación externa (1 de septiembre de 2026)

La selección segura por receta omitía `individual_selections`. Por contrato, omitir ese miembro conserva las validaciones individuales ya guardadas; por ello, nueve campos críticos residuales podían reaparecer junto a las dos propuestas seguras y producir un preview de once cambios. No fallaban ni el filtro seguro ni el preview: el defecto estaba en la semántica del comando emitido por la UI.

Las acciones seguras global y por receta son ahora operaciones de reemplazo: envían la selección segura exacta y `individual_selections={}`. La aceptación crítica individual sigue siendo acumulativa y solo añade el campo pulsado explícitamente. Así, el caso controlado de dos campos seguros y nueve críticos genera primero un preview exacto de 2, pasa a 3 únicamente al validar una crítica y vuelve a 2 al repetir la acción segura, sin duplicados. El dataset controlado de 30 recetas mantiene exactamente 83 campos seguros y excluye los 257 críticos no seleccionados.

El lote externo importado vivía únicamente en el estado del componente hijo y la inicialización con `initialBatch` evitaba guardar su identificador. Al desmontar el paso para volver al resumen desaparecía la ruta visible de regreso. El resumen conserva ahora el batch externo activo, publica `Revisar propuestas externas · 30 recetas`, persiste solo su identificador por importación y lo rehidrata mediante el GET canónico del batch. La pantalla de preview incorpora `Volver a propuestas`; regresar no reimporta el XLSX ni crea un batch nuevo.

Evidencia ejecutada: 37 pruebas backend focales de batch/intercambio, 156 backend relevantes de Fase 1, 38 frontend focales y 271 frontend completas, sin fallos; typecheck correcto. Los tests verifican 2/9, 2→3, repetición idempotente, 83/257, navegación a propuestas, CTA persistente, ausencia de confirmación y cero escrituras. Estado: `LISTA PARA REPETIR: SELECCIÓN SEGURA DE 1 RECETA → PREVIEW EXACTO → VOLVER A PROPUESTAS`; sin commit, push ni Fase 1.5.

## Estabilización autónoma y continuidad tras reconstrucción del frontend (1 de septiembre de 2026)

La causa raíz de la pérdida tras F5 era doble: las sesiones de importación y los batches de completado existían sólo en diccionarios del proceso backend, mientras React conservaba la referencia operativa en estado local y `sessionStorage`. El backend vivo podía seguir respondiendo por identificador, pero un remount perdía el batch visible y un reinicio del proceso perdía además importación, propuestas, selección y preview.

El contrato final clasifica el estado de forma explícita. A, durable: sesión normalizada de importación, batch externo, propuestas clasificadas, selecciones, preview e idempotencia de confirmación; se conservan mediante los repositorios seguros del workflow. B, reconstruible: la vista React y sus contadores se reconstruyen desde el detalle backend, que incluye el batch externo activo; el identificador en almacenamiento del navegador es sólo una pista y no contiene autoridad de negocio. C, temporal: el fichero XLSX binario no se retiene después de validarlo; se conservan su resultado normalizado y la trazabilidad necesaria, de modo que F5 no exige reimportarlo. Toda nueva selección invalida el preview anterior y la UI solicita a la autoridad existente que lo regenere.

La prueba física automatizada crea 30 recetas aisladas, exporta y modifica un XLSX real y obtiene exactamente 30 recibidas, 30 útiles, 30 con revisión, 0 rechazadas, 83 seguras, 257 críticas y 340 propuestas. Recorre en Chrome 83 cambios globales, Ensaladilla 2, una crítica adicional 3 y repetición segura 2; vuelve al resumen, ejecuta `page.reload()`, cierra y abre una página nueva y recupera el mismo batch y preview. Comprueba una sola importación externa, cero duplicados, `datos_reales_modificados=false` y hash idéntico del repositorio de recetas. No ejecuta confirmación.

Evidencia final: 157 pruebas backend de Fase 1, 38 frontend focales, 271 frontend completas y 1 E2E real superadas; typecheck y build correctos. Todos los datos del E2E residen en `.test-runs/fase1-e2e`; no se llamó a IA externa ni se confirmó una escritura real. La creación de artículos nuevos derivados de ingredientes continúa pendiente dentro de Fase 1 y no se amplía aquí. Estado: `LISTA PARA SMOKE TEST HUMANO`; no equivale a cierre formal, no inicia Fase 1.5 y no incluye commit ni push.

## Smoke POST-FIX sin reconstrucción de sesiones antiguas (1 de septiembre de 2026)

La sesión que no apareció en el primer smoke es PRE-PERSISTENCE: el único registro del storage real está confirmado y carece de marcador de esquema y timestamps; el batch volátil anterior no existe en disco. No se ha inventado ninguna migración para ese estado perdido.

Se añadió descubrimiento durable por listado y rehidratación frontend sin depender de `sessionStorage/localStorage`. Un fixture E2E completamente aislado atraviesa análisis real, decisiones canónicas conocidas, XLSX físico, reimportación 30/30 y batch externo de 340 propuestas. Playwright cierra Chrome, reinicia los procesos frontend y backend, verifica los mismos identificadores y abre un Chrome limpio que muestra el CTA de 30 recetas y recupera el preview; no reimporta desde el navegador ni confirma.

Evidencia ejecutada: 158 pruebas backend de Fase 1, 39 frontend focales, 272 frontend completas y 1 E2E Playwright; typecheck y build correctos. Los stores aislados tienen `schema_version=2`, `created_at` y `updated_at`. Cero escritura sobre datos reales. Veredicto técnico: `LISTA PARA SMOKE HUMANO SIN REIMPORTAR`; la Fase 1 sigue abierta y Fase 1.5 no se inicia.

## Cierre técnico del flujo de artículos derivados de ingredientes (1 de septiembre de 2026)

El último pendiente funcional de Fase 1 queda conectado sin crear una segunda autoridad. Los ingredientes importados que siguen `SIN_RELACIONAR` o `CREAR_ARTICULO_PROPUESTO` y carecen de artículo se agrupan por nombre normalizado y familia de unidad compatible. Una misma materia prima repetida en varias recetas genera un solo candidato y conserva todas sus apariciones para enlazarlas después.

El alta pasa por el `SafeCatalogWritePanel` y por `CatalogCrudWriteService`: primero preview, después confirmación humana autorizada y solo entonces escritura del artículo. El registro nace `PENDIENTE_DE_COMPLETAR`, sin precio ni proveedor inventados. Tras una confirmación correcta, la UI actualiza el borrador versionado de importación y enlaza todas las apariciones; si ese PATCH falla, conserva el ID ya creado y ofrece reintentar el enlace sin duplicar el alta.

El artículo incompleto converge después en el flujo existente de referencias externas. La exportación solicita `precio` y `proveedor_referencia`; la reimportación prepara preview y la confirmación escribe exclusivamente `precios_referencia`. Los campos reales `precio` y `proveedor` permanecen intactos y las respuestas lo declaran mediante `precio_real_modificado=false` y `proveedor_real_modificado=false`. La confirmación final de la importación de Biblioteca continúa separada y no se ejecutó durante esta validación.

Evidencia ejecutada sobre repositorios temporales: 37 pruebas backend focales, 183 backend de Fase 1, 54 frontend focales, 274 frontend completas y 2 E2E Playwright en Chrome real. El E2E cubre dos apariciones del mismo ingrediente, un único alta autorizada, enlace de ambas, exportación del artículo incompleto, reimportación de precio/proveedor de referencia, preview, confirmación aislada y lectura posterior con precio/proveedor reales vacíos. Typecheck, build y `git diff --check` correctos. No hubo IA externa, confirmaciones sobre `DATOS`, commit, push ni inicio de Fase 1.5.

Estado: `FLUJO DE ARTÍCULOS NUEVOS IMPLEMENTADO, PROBADO Y VALIDADO E2E EN ENTORNO AISLADO`; la Fase 1 permanece abierta por instrucción expresa del usuario.

## Auditoría final y preparación del smoke de cierre (1 de septiembre de 2026)

La auditoría continua sobre el Excel físico `Documentos/Escandallos Boronat.xlsx` recorre en un único E2E análisis, exclusión A.P de sesión, recetas, menús, decisiones de identidad, intercambio XLSX de completado, selección y preview, reinicio real, candidato de artículo, alta autorizada, enlace de sus dos apariciones, exportación del artículo incompleto, reimportación de precio/proveedor de referencia, preview, confirmación únicamente en el runtime aislado, segundo reinicio y repetición idempotente. El post-read acredita un solo artículo, una sola referencia y un solo evento de auditoría; precio y proveedor reales permanecen vacíos.

Se cerraron cuatro huecos de auditoría: el workflow de referencias externas conserva preview/estado por tenant tras reinicio; la deduplicación de referencias reconoce una confirmación anterior aunque se haya perdido la respuesta y se reinicie el servicio; la UI reconcilia un alta de artículo cuya respuesta se perdió mediante código y nombre deterministas antes de permitir otro alta; y las fronteras XLSX cubren ZIP expandido, `import_id`, scope e IDs de receta ajenos. El analizador estructural y el puente histórico excluyen además el rótulo genérico exacto `TAPA`, conservando nombres específicos como `Tapa de anchoa`.

Evidencia final: 189 pruebas backend de Fase 1 y 50 focales frontend superadas; suite frontend completa superada; 3 E2E Chrome superados (2 sintéticos y 1 continuo Boronat); typecheck y build correctos. El diagnóstico físico aislado observa 21 hojas, 1.017 filas, 47 recetas detectadas, 32 canónicas aptas, 10 menús, 1 A.P excluido y cero rótulos genéricos tratados como receta; un fallo controlado continúa, reintenta y se recupera. IA real: cero llamadas. No se ejecutó confirmación de dominio contra `DATOS` real.

Incidencia de la auditoría: una ejecución adicional de toda la suite histórica `TESTS` —no requerida como suite Fase 1— escribió tres eventos de telemetría en `DATOS/logs/host_ai_general_agent.jsonl` porque algunos tests construyen el shell con la raíz real. No modificó objetos operativos, pero rompe la igualdad de la huella agregada exigida (`376` archivos antes y después, hash distinto). Por instrucción expresa no se restaura ni edita ese log.

Estado: `NO LISTA PARA CERRAR FASE 1` mientras la inmutabilidad estricta de `DATOS` no pueda acreditarse; no equivale a cierre formal, commit, push ni inicio de Fase 1.5.

## Aislamiento total y derivación operativa de escandallo/ficha (1 de septiembre de 2026)

La causa de las tres trazas de telemetría quedó corregida en su test: el shell recibe ahora una raíz temporal explícita. Además, `TESTS/conftest.py` establece una raíz temporal global fuera del repositorio, intercepta aperturas y operaciones de escritura dirigidas a `DATOS` real y compara al terminar un manifiesto SHA-256 de todos sus archivos. Un intento directo falla de inmediato y cualquier mutación que eluda la instrumentación —incluido un subproceso— hace fallar la sesión por diferencia del manifiesto.

La suite histórica completa se ejecutó bajo esa protección: 1.753 pruebas superadas, 1 omitida y 48 fallos legacy no relacionados; ninguno fue `TEST_DATA_ISOLATION_GUARD`. El baseline y el resultado fueron idénticos: 376 archivos y hash agregado `B7C5917CC518D331E6D8F0F41E78ADEF2C00CC95DFA9BCD319DC25FB77440E14`. No se restauraron los tres eventos anteriores ni se editó `DATOS`.

La auditoría económica confirma una única autoridad existente: la importación crea la receta y su escandallo asociado; `MotorCalculoEscandallos601` calcula desde cantidades, unidades y el catálogo; `BibliotecaCulinariaReadService` deriva escandallo y ficha en cada lectura. Se completó la proyección pública para conservar la clasificación del precio: el histórico de compra se publica como `REAL`, la asociación de proveedor o el precio de catálogo canónico como `CONFIRMADO`, y una referencia externa como `REFERENCIA`. Esta última sólo actúa como fallback y produce `estado_coste=PROVISIONAL`, nunca `DISPONIBLE`. La respuesta expone fuente, fecha, proveedor o tienda de referencia, porcentaje calculable, ingredientes pendientes y coste por kg/l/u cuando la unidad de rendimiento lo permite. La UI lo presenta como “Escandallo provisional” y la ficha reutiliza receta, escandallo y procedencia canónicos sin persistir una copia económica desconectada.

Evidencia: casos A-E backend y regresión contractual, 218/218; focales frontend, 74/74; suite frontend completa, 276/276; 3/3 E2E Playwright en Chrome, separados en runtime sintético y runtime Boronat; typecheck, build y `git diff --check` correctos. No hubo IA real, escritura en `DATOS`, commit, push ni inicio de Fase 1.5.

Estado técnico: `LISTA PARA SMOKE FINAL DE CIERRE DE FASE 1`; la Fase 1 sigue abierta y el smoke humano no se ejecutó.

## Completado operativo total y proyección provisional (2 de septiembre de 2026)

El completado de recetas amplía su contrato sin crear otra autoridad. `RecetaDocumentacionWriteService` conserva la precedencia `DOCUMENTO > CALCULADO > CONTEXTO_INTERNO > IA_PROPUESTA > REFERENCIA_EXTERNA > PENDIENTE`, propone únicamente huecos razonables y mantiene como únicos campos seguros para selección masiva `descripcion`, `elaboracion` y `observaciones`. Rendimiento, raciones, conservación, regeneración, tiempos, producción, personal, recursos e ingredientes estructurados requieren selección individual; las cantidades, unidades, mermas e identificadores documentales existentes no se sobrescriben.

La ficha y el escandallo provisionales son una proyección READ sobre una copia en memoria de la receta y reutilizan `MotorCalculoEscandallos601` y `BibliotecaCulinariaReadService`. Exponen rendimiento, coste total/por ración, líneas calculables, procedencia y pendientes sin persistir. Tras confirmación humana aislada, la misma lectura canónica recalcula desde los campos confirmados y la confirmación repetida resulta idempotente. El intercambio `HOSTAI_RECIPE_COMPLETION_PACKAGE` exporta ahora versión `0.2`, conserva importación compatible de `0.1` e incorpora contexto, campos operativos estructurados y metadatos por propuesta.

Evidencia final de esta ampliación: 248/248 pruebas backend de Fase 1, 41/41 focales frontend, 276/276 frontend completas y 3/3 E2E Playwright en Chrome. El E2E continuo Boronat cubre `Agua de jamaica`, preview y confirmación exclusivamente en copia aislada, coste post-read, alta de artículo, referencia externa, dos reinicios e idempotencia. Typecheck, compilación Python y build correctos; el build conserva únicamente el aviso no bloqueante de chunk grande. El manifiesto de `DATOS` permanece en 376 archivos y hash `B7C5917CC518D331E6D8F0F41E78ADEF2C00CC95DFA9BCD319DC25FB77440E14`; IA real, escrituras de dominio sobre `DATOS`, commit, push y staging: cero.

Estado técnico: `LISTA PARA REANUDAR SMOKE FINAL DE FASE 1`. La Fase 1 continúa abierta por instrucción expresa del usuario y no se inicia Fase 1.5.

## Round-trip operativo XLSX 0.3 y estado NO_APLICA (5 de septiembre de 2026)

El intercambio físico `HOSTAI_RECIPE_COMPLETION_PACKAGE` exporta versión `0.3` y conserva compatibilidad de lectura con `0.1` y `0.2`. La nueva hoja `INSTRUCCIONES` fija el contrato para el completador externo: proponer solo huecos, conservar `import_id`/`recipe_id`, aportar procedencia, confianza y motivo, y no considerar ningún valor escrito hasta pasar por selección, preview y confirmación humana. Las filas incluyen contexto documental, ingredientes/artículos, menús/servicio/pax y estados actuales/calculados sin transferir autoridad de escritura.

`NO_APLICA` queda modelado como estado semántico explícito en descongelación, vida útil congelado y regeneración. El preview lo muestra con su procedencia, confianza y motivo; la confirmación aislada persiste el estado, no el sentinel dentro del escalar. Los campos críticos no seleccionados individualmente continúan excluidos.

La regresión backend ampliada terminó 250/250 y el E2E físico continuo Boronat terminó 1/1 en Chrome (2,4 minutos). Este último recorrió exportación XLSX, fixture GPT local sin llamadas externas, reimportación, selección, preview, confirmación solo en `.test-runs/fase1-closing-e2e`, lectura posterior, artículo nuevo, precio/proveedor de referencia, dos reinicios e idempotencia. En esta continuación también constan frontend focal 41/41, frontend completo 276/276, typecheck, compilación Python y build correctos. La confirmación manual de referencias ya no caduca por el cambio de segundo entre preview y confirmación y tiene regresión dedicada.

No hubo IA externa, escritura sobre `DATOS`, commit, push, staging ni inicio de Fase 1.5. El único paso pendiente es el smoke humano final sobre el runtime aislado preparado; no se ha cerrado formalmente la Fase 1.

Estado técnico: `LISTA PARA SMOKE FINAL DEL ROUND-TRIP HOST AI → GPT → HOST AI`.

## Corrección de rehidratación post-confirmación (5 de septiembre de 2026)

El smoke humano reveló que el batch externo durable existía, pero el detalle de importación no lo publicaba cuando su estado era `COMPLETADO`. La causa exacta era el filtro de `RecetaDocumentacionBatchService.active_external`, que excluía `COMPLETADO` y `COMPLETADO_PARCIAL`; React recibió correctamente `completado_recetas_activo=null` y mostró el CTA de crear otro intercambio.

La consulta conserva ahora el último batch externo no cancelado también después de confirmar. El batch original `RECIPE-BATCH-CBF31653B5A5` no fue recreado: sigue vinculado a `IMPWEB-9CFB9A4EC21E`, con 34 recetas y 392 propuestas. Tests: backend focal 40/40, backend Fase 1 250/250, frontend focal 41/41, frontend completo 276/276 y E2E focal Chrome limpio/F5 1/1. Typecheck y build correctos. `DATOS` real no se modificó.

Estado: `LISTA PARA REANUDAR SMOKE FINAL`; Fase 1 permanece abierta.

## Ampliación production-ready masiva (5 de septiembre de 2026)

La autoridad de completado cubre ahora explícitamente los datos estructurales necesarios para una futura planificación provisional: identidad/tipo, rendimiento y servicio, ingredientes normalizados, tiempos activos/pasivos/totales y específicos, capacidad por tanda, personal, recursos y conservación. El resultado diferencia `production_ready_provisional` de `production_ready_confirmed`, conserva la resolución y procedencia por campo y no concede autoridad de escritura a IA, XLSX, selección, ficha o escandallo provisional.

La revisión opera por lote y por excepción. El resumen y los filtros distinguen bloqueadas, no production-ready, críticos, baja confianza, pendientes, `NO_APLICA`, errores, precio/proveedor e imposibles de estimar. Las filas rechazadas por stale y los errores de campo permanecen visibles como `ERROR_VALIDACION` sin abortar ni reducir silenciosamente el batch.

El escenario físico masivo crea 52 recetas dentro de `.test-runs`, exporta una vez XLSX 0.3 y lo reimporta una vez. La evidencia resultante es: 52 analizadas, 1.195 propuestas, 49 production-ready provisionales, dos recetas con error, una imposible con motivo y 51 con al menos un `NO_APLICA`. Incluye `Agua de jamaica` production-ready provisional con ficha y escandallo derivados, artículo nuevo consolidable y referencia externa que no sustituye precio/proveedor reales. Chrome valida selección, preview, confirmación aislada, post-read, F5, reinicio e idempotencia.

Regresión final: 233 pruebas backend de Fase 1, 42 frontend focales, 277 frontend completas, E2E masivo y E2E continuo Boronat correctos, además de typecheck, build y compilación Python. La primera ejecución frontend concurrente agotó el timeout de una prueba histórica de recepción; el archivo pasó 3/3 en aislamiento y la suite completa pasó dos veces después sin modificarla. No se realizaron llamadas a IA externa ni escrituras de dominio sobre `DATOS`; su manifiesto permaneció en 376 archivos y hash `B7C5917CC518D331E6D8F0F41E78ADEF2C00CC95DFA9BCD319DC25FB77440E14`.

Estado técnico: `LISTA PARA SMOKE FINAL PRODUCTION-READY MASIVO DE FASE 1`. La certificación no equivale a calidad culinaria validada ni cierra formalmente la fase.

## Corrección del CTA de descarga externa (5 de septiembre de 2026)

La reproducción Playwright del fallo humano demostró que el CTA principal no enviaba ningún POST de exportación y agotaba el evento de descarga. La UI solo cambiaba su paso interno; la operación real permanecía detrás de un segundo botón que no se renderizaba con un batch externo existente.

El CTA ejecuta ahora directamente la autoridad de exportación compartida, descarga el fichero, informa progreso/éxito/error y bloquea solicitudes concurrentes. La prueba Chrome guarda el fichero bajo `.test-runs`, lo abre con `openpyxl` y acredita tres hojas, contrato 0.3, 52 filas, `import_id` y contexto. El escenario se ejecutó con batch previo y sin batch: el primero conserva el mismo identificador; el segundo no crea uno hasta una futura reimportación.

Evidencia final: backend focal 30/30, backend Fase 1 233/233, frontend focal 44/44, frontend completo 279/279, E2E descarga con batch 1/1, sin batch 1/1 y descarga más rehidratación/F5 del runtime humano 2/2. Typecheck, build y compilación Python correctos. No hubo confirmación ni escritura sobre `DATOS` real.

Estado técnico: `LISTA PARA SMOKE DE DESCARGA XLSX`; Fase 1 sigue abierta.

## Corrección visual final de NO_APLICA (5 de septiembre de 2026)

La ficha técnica provisional consume ahora el mapa estructurado `estados_campos_operativos` al presentar campos operativos. `regeneracion=NO_APLICA` y `tiempo_descongelacion=NO_APLICA` se muestran como «No aplica», con procedencia, motivo, confianza y estado de revisión disponibles; un campo sin valor ni estado sigue mostrándose como «Sin dato». No se modifica el valor escalar, la autoridad de readiness, XLSX, batches, escandallo ni las fronteras de confirmación y WRITE.

Evidencia: focal backend 4/4, focal frontend 45/45, E2E Playwright Chrome de solo lectura 1/1 sobre Agua de jamaica y F5, suite frontend completa, typecheck y build correctos. No hubo confirmación ni escritura en `DATOS` real.

Estado técnico: `LISTA PARA CIERRE FORMAL DE FASE 1`. La fase no se cierra automáticamente.

## Corrección del fixture nominal de cierre (5 de septiembre de 2026)

La trazabilidad de `REC601-000002`, `REC601-000003`, `REC601-000004` y `REC601-000007` confirma que el producto no perdía nombres: el fixture masivo originaba `Receta 2`, `Receta 3` y `Receta 4`, y todas las capas posteriores conservaban esos valores. El fixture se corrigió en la primera capa y ahora usa 52 nombres humanos explícitos. Las comparaciones canónico→XLSX físico→batch y batch→HTTP son por `recipe_id`; React renderiza el nombre recibido y reserva «Receta sin nombre» para ausencia real.

Evidencia: backend XLSX/API 30/30, frontend focal 46/46, frontend completo 281/281, descarga XLSX Chrome 1/1 y smoke de nombres/NO_APLICA/F5/reinicio Chrome 1/1, typecheck y build correctos. No hubo WRITE ni confirmación sobre `DATOS` real.

Estado técnico: `LISTA PARA CIERRE FORMAL DE FASE 1`. La fase permanece abierta hasta decisión humana expresa.

## Cierre formal y certificación definitiva (5 de septiembre de 2026)

**FASE 1 — IMPORTACIÓN INTELIGENTE — ESTADO: CERRADA / CERTIFICADA.**

El smoke humano final queda aprobado. La fase entrega un pipeline determinista como primera autoridad y mantiene la IA como mecanismo opcional de propuestas, sin escritura directa. El recorrido certificado incluye análisis e importación, exportación física `HOSTAI_RECIPE_COMPLETION_PACKAGE 0.3`, completado externo masivo, reimportación segura, selección, preview, confirmación humana, persistencia y rehidratación tras F5/reinicio.

La certificación cubre conservación de nombres humanos por `recipe_id`, `NO_APLICA` como estado estructurado separado del valor escalar, `production_ready_provisional`, ficha técnica y escandallo provisionales de solo lectura, y el flujo de ingredientes nuevos hacia candidatos de artículo y referencias externas de precio/proveedor sin convertirlas en datos reales del restaurante. El smoke humano verificó descarga, 52 recetas, nombres, Agua de jamaica y ambos estados `NO_APLICA`; no aceptó ni confirmó cambios reales.

Reconciliación de contadores: `1070` es el número de propuestas críticas presentes en `datos_requieren_revision_individual`. El total de validación `campos.requieren_revision=1071` añade un único `PENDIENTE_IMPOSIBLE_DE_ESTIMAR` (`REC601-000003`, `unidad_tanda`, motivo: falta capacidad del equipo). Ese campo requiere atención, pero no es propuesta seleccionable, no forma parte de las 1.195 propuestas y nunca entra en WRITE. La diferencia es legítima y no constituye un bug funcional.

Evidencia final existente: backend XLSX/API 30/30, frontend focal 46/46, frontend completo 281/281, Playwright de descarga física 1/1 y Playwright de nombres/`NO_APLICA`/F5/reinicio 1/1, typecheck, build y `git diff --check` correctos. La validación técnica y humana no escribió en `DATOS` real; baseline final: 376 archivos y hash `B7C5917CC518D331E6D8F0F41E78ADEF2C00CC95DFA9BCD319DC25FB77440E14`.

Estado final: `FASE 1 CERRADA Y CERTIFICADA`. Fase 1.5 no iniciada.
