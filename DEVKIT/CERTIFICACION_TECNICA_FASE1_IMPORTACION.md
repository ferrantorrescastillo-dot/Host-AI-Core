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

## Hotfix post-cierre - acceso visible a la reimportación XLSX (5 de septiembre de 2026)

Se corrige una regresión de alcance UX posterior al cierre: con un batch externo activo, `ExternalRecipeCompletion` retornaba directamente la revisión de propuestas y ocultaba el input ya conectado al importador XLSX. La autoridad certificada no cambia: continúa siendo `POST /api/v1/biblioteca/recetas/completado-externo/importar` sobre `RecipeCompletionExchangeService.import_package`.

La UI mantiene visible `Importar XLSX completado`, conserva separado el importador genérico JSON, acepta solo el MIME/extensión XLSX soportado y remonta la revisión con el nuevo `batch_id` retornado. El acuse declara propuestas importadas y ausencia de cambios reales. El flujo sigue sin confirmación ni WRITE automáticos.

Validación técnica: 30/30 backend focales, 47/47 frontend focales, suite frontend completa 282/282, 1/1 Playwright de upload físico con file chooser, 1/1 descarga física y 1/1 regresión Chrome de nombres, `NO_APLICA`, readiness, ficha/escandallo, F5 y reinicio. Typecheck y build correctos. Pendiente únicamente el smoke humano del hotfix antes de preparar su commit separado; staging, commit y push permanecen vacíos/no ejecutados.

## Hotfix de robustez del contrato ChatGPT → XLSX → Host AI (5 de septiembre de 2026)

La auditoría del primer XLSX comercial (SHA-256 `0624F4C00FF2560CB5BF411A5F4E170A33EAEFC69475311BB0BA641DAC81E22C`) separa defectos del fichero de insuficiencias exportadas. Los 219 rechazos originales se distribuyen en: 52 `categoria/EXISTING_VALUE`, 52 `ingredientes_estructurados/ingredient_count_mismatch`, 28 `tiempo_descongelacion`, 26 `vida_util_congelado`, 20 `regeneracion`, 14 `tiempo_enfriamiento`, 6 `tiempo_reposo`, 6 `tiempo_coccion` y 2 `vida_util_refrigerado` por `missing_no_aplica_reason`, más 13 `alergenos/EMPTY_VALUE`. Los 63 bloqueos eran 52 `observaciones` con dos falsos positivos simultáneos (`ALERGENOS_TRAZAS_EMBEBIDOS` y `DATOS_COMERCIALES_EMBEBIDOS`) y 11 `descripcion/ALERGENOS_EMBEBIDOS` legítimos.

La causa en `NO_APLICA` era el rechazo completo de `metadatos_propuestas` al superar 8.000 caracteres: el parser dejaba de ver el motivo por campo y rechazaba en cascada los 102 estados. La causa de ingredientes era la igualdad estricta de longitud/posición: el fichero real omitía/reemplazaba originales en 51 filas y añadía Agua en la receta sentinel. El contrato 0.3 publica ahora hoja `SCHEMA`, claves pendientes canónicas, shapes, enums, unidades, políticas y ejemplos. El parser limita por separado el mapa de metadatos, normaliza `NO_APLICA` como estado estructurado, preserva ingredientes originales por nombre y admite extras como `CANDIDATO_NUEVO`; no relaja las prohibiciones de overwrite ni las declaraciones críticas reales.

El replay del fichero humano corregido por código acepta 1.745 propuestas y conserva como excepciones explicables 52 categorías ya existentes, 51 recetas que realmente omitieron su ingrediente documental, 13 arrays vacíos de alérgenos y 11 descripciones con alérgenos explícitos. El contrato público nuevo se valida aparte con 52 recetas sin importar constantes privadas: 52/52 provisionales, 0 confirmadas, 0 errores, 0 imposibles, 0 rechazos, 0 bloqueos y 52 con `NO_APLICA`. Agua de jamaica conserva Flor de hibiscus, Limones y Azúcar, añade Agua de proceso como candidato, muestra ficha provisional y escandallo parcial (75%, un coste pendiente).

Evidencia: backend focal 38/38; backend Fase 1 235/235; frontend focal 47/47; frontend completa 282/282; Playwright descarga/subida 2/2; Playwright de contrato realista, `NO_APLICA` visual, F5, reinicio y navegador limpio 1/1; typecheck y build correctos. Ninguna confirmación o escritura real. Estado técnico: `LISTA PARA ÚLTIMO SMOKE HUMANO DEL CIRCUITO REAL`, pendiente de validación humana y sin iniciar Fase 1.5.

## Cierre técnico autónomo con el XLSX GPT real (5 de septiembre de 2026)

La evidencia sintética anterior queda acotada a la validación del contrato público y no se utiliza como prueba del resultado comercial. El fichero GPT real `hostai-completado-recetas-IMPWEB-6F402EBB0868_COMPLETADO_GPT.xlsx`, SHA-256 `0624F4C00FF2560CB5BF411A5F4E170A33EAEFC69475311BB0BA641DAC81E22C`, se reimportó por el endpoint público en el runtime aislado de cierre y originó `RECIPE-BATCH-7B15EDEEADBC`, vinculado a `IMPWEB-6F402EBB0868`.

Resultado real: 52/52 filas útiles, 1.872 campos recibidos, 156 seguros, 1.580 de revisión individual, 136 rechazados con motivo y 1.736 propuestas aceptadas. Hay 1 receta `production_ready_provisional`, 0 confirmadas, 13 recetas con error trazable, 0 imposibles y 34 con `NO_APLICA`. Esta diferencia respecto al completador sintético es evidencia válida: Host AI no rebaja tipos, coherencia ni protección de valores existentes para inflar readiness.

Agua de jamaica es la receta provisionalmente lista. Conserva Flor de hibiscus, Limones y Azúcar y añade Agua como `CANDIDATO_NUEVO`; presenta descripción/elaboración GPT, `regeneracion`, `tiempo_descongelacion` y `vida_util_congelado` como estados `NO_APLICA`, ficha técnica provisional y escandallo `SIN_COSTE`. El runtime final no contiene precio/proveedor de fixture en esa proyección y ninguna propuesta se confirmó.

La regresión final terminó con 76/76 focales backend, 273/273 backend Fase 1, 47/47 frontend focales, 282/282 frontend completas y todos los E2E aislados requeridos: contrato adversarial 4/4, selección/preview/confirmación aislada 1/1, rehidratación limpia 1/1, persistencia/artículos/referencias 2/2, recorrido continuo 1/1 y smoke final GPT real/F5/reinicio 1/1. Typecheck, compilación Python y build correctos. El runtime humano conservó exactamente su huella durante el smoke de solo lectura y `DATOS` real mantuvo 376 archivos y hash `B7C5917CC518D331E6D8F0F41E78ADEF2C00CC95DFA9BCD319DC25FB77440E14`.

Estado técnico: `FASE 1 LISTA PARA SMOKE HUMANO FINAL`. No equivale a confirmación culinaria, no ejecuta WRITE, no inicia Fase 1.5 y no incluye staging, commit ni push.

## Pausa de certificación — nuevo contrato maestro autosuficiente (5 de septiembre de 2026)

La prueba comercial anterior no certifica el nuevo contrato. La autoridad declarativa queda centralizada en `recipe_completion_contract.py`; el XLSX 0.3 deriva de ella un único `PROMPT_IA`, `SCHEMA` de 36 campos y el circuito consolidado `ARTICULOS_PENDIENTES`/`PRECIOS_REFERENCIA`/`SCHEMA_PRECIOS`. Las referencias reimportadas se validan como `REFERENCIA_EXTERNA`/`REFERENCIA_NO_REAL`, sin WRITE.

Evidencia previa a la pausa: backend focal 66/66 y Fase 1 245/245; frontend focal 47/47 y suite completa correcta; E2E físicos de descarga/subida y contrato público, persistencia, artículo/referencia, Chrome limpio/F5, lote 52 y recorrido continuo correctos; typecheck, build, compilación Python y `git diff --check` correctos. El paquete nuevo `hostai-completado-recetas-IMPWEB-6F402EBB0868.xlsx` contiene 52 recetas, 36 contratos de campo y 10 artículos consolidados pendientes, sin propuestas prefabricadas ni fórmulas.

Estado: `ESPERANDO XLSX GPT REAL`. No se ha ejecutado confirmación, commit, push, staging ni Fase 1.5.

## Ampliación técnica: precio externo en escandallo y revisión agrupada (6 de septiembre de 2026)

El artefacto GPT real nuevo `hostai-completado-recetas-IMPWEB-6F402EBB0868_COMPLETADO_GPT_NUEVO.xlsx`, SHA-256 `72CF33170BB034A9C389DE1639669D7B7E22E27E4BF5BBBE08683EFF61988274`, conserva 52 filas útiles y 1.807 propuestas sin WRITE. El contrato separa 156 seguras, 1.144 operativas agrupables y 507 críticas individuales.

Las referencias de precio se consolidan por identidad exacta y se persisten en el batch schema 3. Seis filas válidas representan tres identidades reutilizables; el lote obtiene 11 escandallos parciales y 41 sin coste. El motor recibe candidatos transitorios solo cuando existe una referencia coincidente y nunca los persiste. Un precio canónico/confirmado prevalece sobre la referencia externa. Los costes parciales con referencia quedan marcados explícitamente como provisionales.

La revisión agrupada dispone de canal de selección propio, preview común y persistencia tras F5/reinicio. No confirma automáticamente y no rebaja los campos críticos reales. Evidencia: backend Fase 1 206/206, frontend 283/283, build/typecheck/compile correctos y diez escenarios Playwright finales verdes distribuidos entre contrato, persistencia, rehidratación, masivo, Boronat y artefacto GPT real. Estado técnico: `LISTA PARA SMOKE HUMANO FINAL DE ESCANDALLO Y EXCEPCIONES`; Fase 1 no se cierra automáticamente.

## Navegación final del lote por receta (6 de septiembre de 2026)

La revisión y el preview consolidado comparten un buscador local por nombre o `recipe_id`, insensible a mayúsculas, espacios exteriores y diacríticos. La búsqueda no inspecciona ingredientes, elaboración ni metadatos, no modifica selecciones o preview y no realiza llamadas al backend. La barra muestra el contador visible/total, permite limpiar con botón o Escape y permanece accesible durante el desplazamiento.

El primer smoke humano falló porque el E2E ejercitaba el buscador antes de reiniciar frontend/backend y cerraba ese contexto; el nuevo proceso dejado en `55718` no recibía después ninguna verificación de navegador. La afirmación inicial de smoke-ready queda revocada. El E2E se reordenó para abrir un Chrome limpio después del reinicio y dejar activo exactamente ese proceso comprobado. Sus aserciones exigen 52 bloques iniciales, uno tras buscar `agua`, `REC601-000007`, escandallo visible y ausencia explícita de Ensaladilla, Crema de calabaza, Gazpacho de tomate, Salmorejo cordobés, Salsa romesco y Paella de alcachofas; Limpiar restaura 52.

Evidencia corregida: test focal frontend 49/49, frontend completo 284/284, Playwright Chrome post-reinicio sobre el lote GPT real 1/1, typecheck y build correctos. Estado técnico: `BUSCADOR CORREGIDO — LISTO PARA REPETIR SMOKE HUMANO`; Fase 1.5 no iniciada.

## Corrección del escandallo en preview rehidratado (6 de septiembre de 2026)

El smoke humano reveló una divergencia dentro del mismo batch `RECIPE-BATCH-27AD1C3C567B`: `resultados` exponía correctamente Agua de jamaica como `PARCIAL`, 11,63 EUR conocidos, 75 % de cobertura y tres referencias, pero `preview.items` conservaba el snapshot `SIN_COSTE` calculado únicamente con los campos operativos seleccionados. Las referencias seguían visibles en las líneas del snapshot, produciendo la contradicción visual.

`RecetaDocumentacionBatchService` reutiliza ahora la proyección integral y solo-lectura del resultado tanto al crear como al rehidratar el preview; los 1.144 cambios confirmables permanecen separados y `ingredientes_estructurados` continúa fuera del preview de confirmación. `BibliotecaImportPage` presenta el coste parcial conocido, cobertura e ingrediente pendiente sin rotularlo como no calculable. La prioridad económica canónica permanece `REAL/CONFIRMADO > REFERENCIA_EXTERNA > SIN_PRECIO`.

Evidencia: backend focal 83/83, backend Fase 1 227/227, frontend focal 49/49, frontend completo 284/284 y E2E Chrome del XLSX GPT real 1/1 con F5, reinicio completo y navegador limpio. Agua de jamaica conserva 11,63 EUR, 75 %, tres referencias no reales y Agua pendiente; el batch sigue con 52/52 provisionalmente listas, 1.807 propuestas, 1.144 agrupadas, 507 críticas y 11 escandallos parciales. No hubo confirmación ni WRITE real.

Estado técnico: `ESCANDALLO CORREGIDO — LISTO PARA SMOKE HUMANO FINAL`; Fase 1 no se cierra automáticamente y Fase 1.5 no se inicia.

## Hotfix de reproducibilidad del sentinel económico (6 de septiembre de 2026)

Un checkout limpio del SHA publicado `875f75387903c7f60c4695939acd02c217cb2019` demostró que la prueba económica final no era reproducible sin el XLSX y el manifiesto del smoke humano conservados fuera de Git. El fallo era del escenario de certificación: el preparador creaba 30 recetas y no publicaba `source_file`, `source_sha256` ni `protected_hashes`; el test intentaba resolver `Downloads/undefined`. La aplicación y el E2E independiente del contrato público sí completaron correctamente el recorrido limpio de 52 recetas.

El harness versionado prepara ahora su propio XLSX físico y sus referencias de control dentro del runtime aislado. La aserción económica conserva el sentinel exacto de Agua de jamaica (11,63 EUR conocidos, `PARCIAL`, 75 %, tres referencias externas y Agua pendiente), prueba búsqueda 52→1→52 en revisión y preview, F5, contextos Chrome limpios, reinicio de frontend, reinicio de backend y reinicio conjunto. Las referencias permanecen `REFERENCIA_NO_REAL` y nunca `CONFIRMADO` ni precio real de compra; los hashes protegidos verifican ausencia de WRITE de dominio.

Regresión previa a republicación: backend Fase 1 227/227, frontend completo 284/284, E2E masivo 1/1 y E2E económico autocontenido 1/1, typecheck, build, compilación Python y `git diff --check` correctos. El cambio afecta solo a `TESTS/fase1_e2e_server.py`, `HOST_AI_WEB/e2e/fase1-supervisor.mjs` y `HOST_AI_WEB/e2e/economic-exceptions-real.spec.ts`; no modifica producto ni `DATOS` real. Fase 1.5 no se inicia.

La primera repetición remota del hotfix reveló una segunda dependencia histórica: seis tests de importación referenciaban `BORONAT_HOSTAI_IMPORT_PACKAGE_0.1.json` y `BORONAT_HOSTAI_IMPORT_CHATGPT.json` dentro de `Documentos/Importaciones`, excluido deliberadamente de Git por contener documentos privados. No se versionan esos ficheros. `test_hostai_chatgpt_import_v01_converter.py` usa ahora un prototipo representativo en memoria con recetas, fusión por escala, variantes, menú, contexto y hallazgo semántico; `test_hostai_import_package.py` reutiliza el fixture público seguro existente. La focal pasa 48/48 y backend Fase 1 227/227 desde una raíz temporal aislada.
