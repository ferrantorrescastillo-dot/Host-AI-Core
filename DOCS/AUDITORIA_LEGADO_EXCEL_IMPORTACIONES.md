# AUDITORIA FUNCIONAL DEL MODULO LEGADO EXCEL IMPORTACIONES

Fecha: 2026-07-23
Alcance: auditoria de solo lectura del modulo legado "Excel / importaciones". No se migra, no se elimina y no se modifica comportamiento.

## 1. Puntos de entrada localizados

### Activo en la version abierta
1. Pantalla inicial: [main.py](main.py) delega en [SERVICIOS/lanzador_piloto_01.py](SERVICIOS/lanzador_piloto_01.py).
2. Modo desarrollo: [SERVICIOS/lanzador_piloto_01.py](SERVICIOS/lanzador_piloto_01.py) opcion 2 abre [SERVICIOS/host_ai_launcher.py](SERVICIOS/host_ai_launcher.py).
3. Host AI Base / trabajo diario manual: [SERVICIOS/host_ai_launcher.py](SERVICIOS/host_ai_launcher.py) opcion 1 abre [APP/consola.py](APP/consola.py).
4. Entrada activa del legado Excel Importaciones: [APP/consola.py](APP/consola.py) opcion 10 del menu principal llama a `_menu_excel`.

### Copias historicas no activas por defecto
Existen definiciones equivalentes de `_menu_excel` en snapshots historicos:
- [HOST_AI_6.0.3_MODO_MANUAL_OPERATIVO/APP/consola.py](HOST_AI_6.0.3_MODO_MANUAL_OPERATIVO/APP/consola.py)
- [HOST_AI_RR11_PULIDO_PRODUCCION/APP/consola.py](HOST_AI_RR11_PULIDO_PRODUCCION/APP/consola.py)
- [HOST_AI_RR12_PULIDO_EVENTOS/APP/consola.py](HOST_AI_RR12_PULIDO_EVENTOS/APP/consola.py)
- [HOST_AI_RR13_PULIDO_STOCK_COMPRAS/APP/consola.py](HOST_AI_RR13_PULIDO_STOCK_COMPRAS/APP/consola.py)
- [HOST_AI_RR14_PULIDO_ESCANDALLOS_COSTES/APP/consola.py](HOST_AI_RR14_PULIDO_ESCANDALLOS_COSTES/APP/consola.py)

Conclusion de entrada: en runtime actual solo hay un punto de acceso activo al legado, en [APP/consola.py](APP/consola.py), por la ruta Modo Desarrollo -> Host AI Base -> Excel / importaciones.

## 2. Modulos internos del legado

### Servicios y asistentes nucleares del bloque Excel clasico
- [SERVICIOS/detector_documentos_excel.py](SERVICIOS/detector_documentos_excel.py): deteccion explicable de tipo de documento Excel.
- [SERVICIOS/mapeador_columnas_excel.py](SERVICIOS/mapeador_columnas_excel.py): mapeo de columnas canonicas y aprendizaje de sinonimos.
- [SERVICIOS/resolutor_conflictos_excel.py](SERVICIOS/resolutor_conflictos_excel.py): analisis previo de conflictos sobre articulos, escandallos e inventario.
- [SERVICIOS/importador_articulos_excel.py](SERVICIOS/importador_articulos_excel.py): vista previa e importacion de listados maestros de articulos.
- [SERVICIOS/importador_escandallos_excel.py](SERVICIOS/importador_escandallos_excel.py): vista previa e importacion de escandallos legacy.
- [SERVICIOS/importador_inventario_excel.py](SERVICIOS/importador_inventario_excel.py): vista previa, comparacion e importacion de inventario.
- [SERVICIOS/asistente_importacion_excel.py](SERVICIOS/asistente_importacion_excel.py): orquestacion multi-paso del flujo Excel clasico.
- [PIPELINES/pipeline_excel.py](PIPELINES/pipeline_excel.py): analisis general del Excel.

### Modelos del bloque Excel clasico
- [MODELOS/asistente_importacion_excel.py](MODELOS/asistente_importacion_excel.py): `SesionImportacionExcel` y `PasoImportacionExcel`.
- Modelos asociados por servicio: deteccion, mapeo, conflictos, importacion de articulos, importacion de escandallos e importacion de inventario.

### Cadena I1.x / M1.x integrada en el mismo menu legado
Importada directamente por [APP/consola.py](APP/consola.py):
- I1.1: detector de escandallos antiguos.
- I1.2: importador seguro de recetas.
- I1.3.1 a I1.3.5: cadena completa de deteccion, reconocimiento, aprendizaje, preimportacion, resolucion, simulacion, correccion y certificacion de menus.
- M1.1 a M1.3.3: diagnosticos del nucleo, resolutores e importador inteligente de recetas.

### Persistencias usadas por el legado
- Diccionario aprendido de columnas: `DATOS/diccionarios/diccionario_columnas_excel.json`.
- Persistencia general legacy via `self.core.persistencia.guardar_todo()`.
- Escandallos legacy: `DATOS/db/escandallos.json`.
- Menus reales: `DATOS/db/menus.json`.
- Stock real: colecciones del motor de stock del core.
- Precios/historicos via `costes_inteligente` cuando existe.
- Backups y sesiones auxiliares de la cadena I1.3.x en `DATOS/backups/...` y JSON de sesion revisada.

## 3. Sistemas nuevos usados para comparacion
- Centro de Importacion: [SERVICIOS/centro_importacion_601.py](SERVICIOS/centro_importacion_601.py)
- Catalogo Maestro: [SERVICIOS/catalogo_maestro_productos_601.py](SERVICIOS/catalogo_maestro_productos_601.py)
- Biblioteca de Recetas: [SERVICIOS/biblioteca_recetas_601.py](SERVICIOS/biblioteca_recetas_601.py)
- Escandallos: [SERVICIOS/biblioteca_escandallos_601.py](SERVICIOS/biblioteca_escandallos_601.py)
- Biblioteca de Menus: [SERVICIOS/biblioteca_menus_601.py](SERVICIOS/biblioteca_menus_601.py)
- Asistente de Incidencias: [SERVICIOS/asistente_resolucion_incidencias_601.py](SERVICIOS/asistente_resolucion_incidencias_601.py)
- Host AI Engine: [SERVICIOS/host_ai_engine/__init__.py](SERVICIOS/host_ai_engine/__init__.py)
- Modulo contenedor nuevo: [SERVICIOS/escandallos_recetas_601.py](SERVICIOS/escandallos_recetas_601.py)

## 4. Analisis funcional detallado

### 4.1 Bloque Excel clasico 1-8

#### 1. Analizar archivo Excel
- Archivo legado: [APP/consola.py](APP/consola.py) -> `_menu_excel`, opcion 1.
- Servicio real: [PIPELINES/pipeline_excel.py](PIPELINES/pipeline_excel.py)
- Descripcion: analisis estructural de hojas, filas, columnas y export JSON.
- Flujo: consola -> orquestador -> pipeline `excel` -> `lector_excel.analizar_archivo`.
- Datos: archivo Excel arbitario.
- Persistencias: export JSON del analisis; no modifica negocio.
- Dependencias: lector Excel, orquestador.
- Sigue utilizandose: si, activo por menu legado y cubierto por tests del detector/lector.
- Comparacion nueva: no hay una herramienta equivalente general en Centro 601; este solo opera importacion de recetas/escandallos/menus.
- Estado: C. NO MIGRADA.

#### 2. Detectar tipo de documento Excel
- Archivo legado: [APP/consola.py](APP/consola.py), opcion 2.
- Servicio real: [SERVICIOS/detector_documentos_excel.py](SERVICIOS/detector_documentos_excel.py)
- Descripcion: clasifica hojas como escandallo, listado_articulos, inventario, compras, produccion, proveedores.
- Flujo: consola -> orquestador -> detector -> analisis previo.
- Datos: Excel y metadatos de columnas.
- Persistencias: ninguna de negocio.
- Dependencias: lector Excel.
- Sigue utilizandose: si, activo y con tests.
- Comparacion nueva: Centro 601 no expone un detector general multi-tipo.
- Estado: C. NO MIGRADA.

#### 3. Vista previa escandallos Excel
- Archivo legado: [APP/consola.py](APP/consola.py), opcion 3.
- Servicio real: [SERVICIOS/importador_escandallos_excel.py](SERVICIOS/importador_escandallos_excel.py)
- Descripcion: detecta hojas de escandallo, mapea columnas y agrupa lineas por receta sin persistir.
- Flujo: consola -> orquestador -> importador escandallos -> detector -> mapeador -> preview.
- Datos: Excel con recetas/ingredientes/cantidades.
- Persistencias: ninguna en modo preview.
- Dependencias: detector Excel, mapeador, lector Excel, escandallos legacy.
- Sigue utilizandose: si, activo y con tests.
- Comparacion nueva: sustituido por `CentroImportacionUI601.importar_escandallos()` + `BibliotecaEscandallos601`.
- Estado: A. TOTALMENTE MIGRADA.

#### 4. Importar escandallos Excel
- Archivo legado: [APP/consola.py](APP/consola.py), opcion 4.
- Servicio real: [SERVICIOS/importador_escandallos_excel.py](SERVICIOS/importador_escandallos_excel.py)
- Descripcion: registra escandallos en el motor legacy.
- Flujo: igual que opcion 3, con escritura final.
- Datos: Excel de escandallos.
- Persistencias: `DATOS/db/escandallos.json` via persistencia legacy.
- Dependencias: `escandallos_inteligente`, persistencia core.
- Sigue utilizandose: si.
- Comparacion nueva: sustituido funcionalmente por `CentroImportacionUI601.importar_escandallos()` + `BibliotecaEscandallos601`.
- Estado: A. TOTALMENTE MIGRADA.

#### 5. Vista previa articulos Excel
- Archivo legado: [APP/consola.py](APP/consola.py), opcion 5.
- Servicio real: [SERVICIOS/importador_articulos_excel.py](SERVICIOS/importador_articulos_excel.py)
- Descripcion: detecta listados maestros de articulos/productos y prepara preview de altas/cambios.
- Flujo: consola -> orquestador -> importador articulos -> detector -> mapeador -> preview.
- Datos: Excel de catalogo maestro / compras.
- Persistencias: ninguna en preview.
- Dependencias: detector, mapeador, lector Excel.
- Sigue utilizandose: si, activo y con tests.
- Comparacion nueva: Catalogo Maestro 601 tiene importacion desde Excel declarada, pero la UI delega al Centro 601 generico, que no implementa un importador especifico de articulos equivalente.
- Estado: C. NO MIGRADA.

#### 6. Importar articulos Excel
- Archivo legado: [APP/consola.py](APP/consola.py), opcion 6.
- Servicio real: [SERVICIOS/importador_articulos_excel.py](SERVICIOS/importador_articulos_excel.py)
- Descripcion: importa catalogos maestros, registra precios y puede actualizar existentes.
- Flujo: preview -> importador -> persistencia core.
- Datos: articulos, familia, proveedor, precio, stock minimo, ubicacion, alergenos.
- Persistencias: memoria/importador legado + `costes_inteligente` + `persistencia.guardar_todo()`.
- Dependencias: detector, mapeador, lector, costes, persistencia.
- Sigue utilizandose: si, activo y con tests.
- Comparacion nueva: no existe reemplazo operativo equivalente en Centro 601, Catalogo Maestro 601 o Host AI Engine para importar listados de articulos desde Excel con esta ruta clasica.
- Estado: C. NO MIGRADA.

#### 7. Vista previa inventario Excel
- Archivo legado: [APP/consola.py](APP/consola.py), opcion 7.
- Servicio real: [SERVICIOS/importador_inventario_excel.py](SERVICIOS/importador_inventario_excel.py)
- Descripcion: calcula diferencias contra stock actual y prepara cambios sin escribir.
- Flujo: consola -> orquestador -> importador inventario -> detector -> mapeador -> comparacion stock.
- Datos: articulo, cantidad, unidad, ubicacion, caducidad, lote, proveedor, precio.
- Persistencias: ninguna en preview.
- Dependencias: detector, mapeador, lector, stock.
- Sigue utilizandose: si, activo y con tests.
- Comparacion nueva: Centro 601 no importa inventario; Catalogo Maestro/Bibliotecas/Engine tampoco.
- Estado: C. NO MIGRADA.

#### 8. Importar inventario Excel
- Archivo legado: [APP/consola.py](APP/consola.py), opcion 8.
- Servicio real: [SERVICIOS/importador_inventario_excel.py](SERVICIOS/importador_inventario_excel.py)
- Descripcion: aplica ajustes de inventario real sobre el motor de stock, creando articulos basicos cuando procede.
- Flujo: preview -> ajuste stock positivo/negativo -> persistencia.
- Datos: stock, lote, caducidad, ubicacion, proveedor, precio.
- Persistencias: colecciones reales de stock y persistencia core.
- Dependencias: stock, importador articulos, costes, persistencia.
- Sigue utilizandose: si, activo y con tests.
- Comparacion nueva: no existe sustitucion operativa equivalente en el sistema 601 ni en Host AI Engine.
- Estado: C. NO MIGRADA.

### 4.2 Cadena I1.x / M1.x / I1.3.4.x / I1.3.5

#### 9. I1.1 Detectar escandallos antiguos
- Archivo legado: [APP/consola.py](APP/consola.py), opcion 9.
- Descripcion: analisis de excels antiguos de escandallos; no importa.
- Flujo: consola -> detector I1.1 -> informe.
- Datos: excels legacy.
- Persistencias: solo export/diagnostico.
- Dependencias: detector de escandallos antiguos.
- Sigue utilizandose: si, desde menu tecnico legado.
- Comparacion nueva: Centro 601 importa escandallos, pero no ofrece un detector especifico de formatos antiguos.
- Estado: C. NO MIGRADA.

#### 10. I1.2 Vista previa e importacion segura de recetas
- Archivo legado: [APP/consola.py](APP/consola.py), opcion 10.
- Descripcion: importa recetas desde Excel con vinculacion inteligente, revision de ingredientes dudosos y cancelacion segura.
- Flujo: catalogo articulos -> importador seguro -> revision manual -> importacion de recetas seguras.
- Datos: recetas, ingredientes, cantidades, equivalencias.
- Persistencias: motor legacy de escandallos/recetas y memoria de equivalencias.
- Dependencias: [SERVICIOS/importador_seguro_escandallos_i12.py](SERVICIOS/importador_seguro_escandallos_i12.py), catalogo local, `escandallos_inteligente`.
- Sigue utilizandose: si.
- Comparacion nueva: sustituido parcialmente por Centro 601 + Biblioteca de Recetas + Asistente de Incidencias + Host AI Engine para flujos orquestados.
- Falta en el nuevo: misma experiencia de aprendizaje de equivalencias y el mismo pipeline de importacion segura legacy.
- Estado: B. MIGRADA PARCIALMENTE.

#### 11. I1.3.1 Detector limpio de menus
- Descripcion: detecta menus y ofrece solo vista previa, sin importacion.
- Comparacion nueva: Centro 601 importa menus, pero no expone una etapa aislada equivalente de detector limpio.
- Estado: B. MIGRADA PARCIALMENTE.

#### 12. I1.3.2.1.1 Catalogo de reconocimiento corregido
- Descripcion: reconocimiento de componentes candidatos en menus.
- Comparacion nueva: no hay modulo 601 equivalente con ese reconocimiento dedicado.
- Estado: C. NO MIGRADA.

#### 13. I1.3.2.2 Constructor del arbol semantico
- Descripcion: construye arbol semantico previo a importacion de menus.
- Comparacion nueva: no existe sustitucion equivalente en Centro 601, BibliotecaMenus601 o Engine.
- Estado: C. NO MIGRADA.

#### 14. I1.3.2.3 Vista previa inteligente y resolucion asistida
- Descripcion: resolucion asistida de componentes ambiguos en menus.
- Comparacion nueva: parcialmente cubierta por Centro 601 + AsistenteResolucionIncidencias601, pero sin el mismo nivel de interpretacion semantica asistida.
- Estado: B. MIGRADA PARCIALMENTE.

#### 15. I1.3.2.4 Motor de aprendizaje culinario
- Descripcion: guarda decisiones reutilizables sobre componentes/menu.
- Comparacion nueva: el asistente 601 resuelve incidencias, pero no replica este motor de aprendizaje culinario dedicado.
- Estado: C. NO MIGRADA.

#### 16. I1.3.3 Preimportacion definitiva de menus
- Descripcion: prepara importacion, calcula bloqueos y deja estado previo.
- Comparacion nueva: Centro 601 cubre importacion de menus, pero no expone la misma fase formal de preimportacion/bloqueo.
- Estado: B. MIGRADA PARCIALMENTE.

#### 17. I1.3.3.1 Resolucion de bloqueos de preimportacion
- Descripcion: resuelve bloqueos creando/vinculando recetas y recalculando preimportacion.
- Persistencias: recetas/escandallos legacy + backups especificos.
- Comparacion nueva: asistente 601 resuelve incidencias basicas, pero no sustituye esta resolucion culinaria previa con recalculo de preimportacion.
- Estado: B. MIGRADA PARCIALMENTE.

#### 18. M1.1 Diagnostico del nucleo MUR
- Descripcion: diagnostico tecnico del nucleo de migracion.
- Comparacion nueva: no hay equivalente 601/Engine.
- Estado: C. NO MIGRADA.

#### 19. M1.2 Diagnostico del resolutor de articulos
- Comparacion nueva: no equivalente.
- Estado: C. NO MIGRADA.

#### 20. M1.3 Diagnostico del resolutor de recetas
- Comparacion nueva: no equivalente.
- Estado: C. NO MIGRADA.

#### 21. M1.3.1 Diagnostico del importador inteligente de recetas
- Comparacion nueva: no equivalente.
- Estado: C. NO MIGRADA.

#### 22. M1.3.2 Diagnostico de resolucion automatica de ingredientes
- Comparacion nueva: no equivalente.
- Estado: C. NO MIGRADA.

#### 23. M1.3.3 Diagnostico de validacion culinaria inteligente
- Comparacion nueva: no equivalente.
- Estado: C. NO MIGRADA.

#### 24. I1.3.4.1.1 Deteccion y simulacion multmenu
- Comparacion nueva: Centro 601 puede importar menus, pero no ofrece esta simulacion especifica multmenu.
- Estado: C. NO MIGRADA.

#### 25. I1.3.4.1.2 Clasificador gastronomico y simulacion multmenu
- Comparacion nueva: no equivalente.
- Estado: C. NO MIGRADA.

#### 26. I1.3.4.1.3 Bandeja de revision y limpieza masiva
- Comparacion nueva: el nuevo sistema revisa incidencias, pero no replica esta bandeja avanzada de limpieza masiva.
- Estado: C. NO MIGRADA.

#### 27. I1.3.4.1.4 Motor de interpretacion culinaria
- Comparacion nueva: no equivalente directo.
- Estado: C. NO MIGRADA.

#### 28. I1.3.4.1.5 Motor de conocimiento gastronomico
- Comparacion nueva: no equivalente directo.
- Estado: C. NO MIGRADA.

#### 29. I1.3.4.2 Diagnostico del motor de escritura segura
- Comparacion nueva: la escritura segura existe en repositorios 601, pero no este diagnostico especifico del flujo legacy de menus.
- Estado: C. NO MIGRADA.

#### 30. I1.3.4.3 Diagnostico / importacion definitiva de menus
- Descripcion: diagnostico aislado o importacion real de sesion revisada con confirmacion y control transaccional.
- Persistencias: `DATOS/db/menus.json`, backup e integridad.
- Comparacion nueva: parcialmente cubierta por `CentroImportacionUI601.importar_menus()` + `BibliotecaMenus601`.
- Falta en el nuevo: ciclo basado en sesion revisada validada e importacion final desde plan revisado.
- Estado: B. MIGRADA PARCIALMENTE.

#### 31. I1.3.4.4 Auditoria e integridad postimportacion
- Descripcion: audita menus reales ya escritos.
- Comparacion nueva: BibliotecaMenus601 maneja menus y estados, pero no expone una auditoria dedicada equivalente.
- Estado: B. MIGRADA PARCIALMENTE.

#### 32. I1.3.4.4.1 Bandeja de correccion postimportacion
- Descripcion: corrige menus reales tras auditoria, con guardado confirmado.
- Comparacion nueva: parcialmente cubierta por BibliotecaMenus601 + AsistenteIncidencias601, pero sin esta bandeja especializada.
- Estado: B. MIGRADA PARCIALMENTE.

#### 33. I1.3.4.4.2 Correccion inteligente masiva y navegacion
- Descripcion: correccion masiva, agrupacion por tipo/menu, guardado real confirmado.
- Comparacion nueva: no equivalente completo.
- Estado: B. MIGRADA PARCIALMENTE.

#### 34. I1.3.5 Refactorizacion y certificacion final del importador
- Descripcion: certifica tecnicamente la cadena legacy del importador.
- Comparacion nueva: no existe certificador equivalente dentro del Centro 601.
- Estado: C. NO MIGRADA.

## 5. Tabla resumen de equivalencias

| FUNCION | ARCHIVO LEGADO | SUSTITUYE | ESTADO | OBSERVACIONES |
| --- | --- | --- | --- | --- |
| Analizar archivo Excel | APP/consola.py + PIPELINES/pipeline_excel.py | Ninguno en 601 | C | Analisis general multihoja sigue siendo unico |
| Detectar tipo de documento Excel | APP/consola.py + SERVICIOS/detector_documentos_excel.py | Ninguno en 601 | C | Detector general multi-tipo no existe en Centro 601 |
| Vista previa escandallos Excel | APP/consola.py + SERVICIOS/importador_escandallos_excel.py | CentroImportacionUI601 + BibliotecaEscandallos601 | A | Cobertura funcional operativa equivalente |
| Importar escandallos Excel | APP/consola.py + SERVICIOS/importador_escandallos_excel.py | CentroImportacionUI601 + BibliotecaEscandallos601 | A | Sustituido por flujo 601 |
| Vista previa articulos Excel | APP/consola.py + SERVICIOS/importador_articulos_excel.py | Catalogo Maestro 601 (sin importador real equivalente) | C | La UI 601 no replica este preview especifico |
| Importar articulos Excel | APP/consola.py + SERVICIOS/importador_articulos_excel.py | Ninguno completo | C | Funcion critica aun unica |
| Vista previa inventario Excel | APP/consola.py + SERVICIOS/importador_inventario_excel.py | Ninguno | C | No existe flujo 601 para inventario |
| Importar inventario Excel | APP/consola.py + SERVICIOS/importador_inventario_excel.py | Ninguno | C | Funcion critica aun unica |
| I1.1 Detectar escandallos antiguos | APP/consola.py + detector I1.1 | Ninguno | C | Detector legacy especifico |
| I1.2 Importacion segura de recetas | APP/consola.py + importador I1.2 | Centro 601 + BibliotecaRecetas601 + AsistenteIncidencias601 + HostAIEngine | B | Falta la misma logica de aprendizaje/vinculacion segura |
| I1.3.1 Detector limpio de menus | APP/consola.py + detector I131 | CentroImportacionUI601.importar_menus | B | Falta la etapa aislada de detector limpio |
| I1.3.2.1.1 Reconocimiento corregido | APP/consola.py + motor I1321 | Ninguno | C | Sin sustitucion directa |
| I1.3.2.2 Arbol semantico | APP/consola.py + constructor I1322 | Ninguno | C | Sin sustitucion directa |
| I1.3.2.3 Resolucion asistida | APP/consola.py + asistente I1323 | Centro 601 + AsistenteIncidencias601 | B | Falta semantica asistida equivalente |
| I1.3.2.4 Aprendizaje culinario | APP/consola.py + motor I1324 | Ninguno | C | Persistencia de aprendizaje no migrada |
| I1.3.3 Preimportacion definitiva de menus | APP/consola.py + preimportador I133 | CentroImportacionUI601.importar_menus | B | Falta el estado formal de preimportacion |
| I1.3.3.1 Resolucion de bloqueos | APP/consola.py + resolutor I1331 | AsistenteIncidencias601 parcial | B | Falta recalculo y bloqueo culinario equivalente |
| M1.1 Diagnostico nucleo MUR | APP/consola.py + diag M11 | Ninguno | C | Sigue siendo tecnico y unico |
| M1.2 Diagnostico resolutor articulos | APP/consola.py + diag M12 | Ninguno | C | Sigue siendo tecnico y unico |
| M1.3 Diagnostico resolutor recetas | APP/consola.py + diag M13 | Ninguno | C | Sigue siendo tecnico y unico |
| M1.3.1 Diagnostico importador recetas | APP/consola.py + diag M131 | Ninguno | C | Sigue siendo tecnico y unico |
| M1.3.2 Diagnostico ingredientes | APP/consola.py + diag M132 | Ninguno | C | Sigue siendo tecnico y unico |
| M1.3.3 Diagnostico validacion culinaria | APP/consola.py + diag M133 | Ninguno | C | Sigue siendo tecnico y unico |
| I1.3.4.1.1 Simulacion multmenu | APP/consola.py + sim I13411 | Ninguno | C | Simulacion no cubierta en 601 |
| I1.3.4.1.2 Clasificador gastronomico | APP/consola.py + sim I13412 | Ninguno | C | Sin sustitucion |
| I1.3.4.1.3 Bandeja revision | APP/consola.py + bandeja I13413 | Ninguno completo | C | Limpieza masiva no migrada |
| I1.3.4.1.4 Interpretacion culinaria | APP/consola.py + bandeja I13414 | Ninguno | C | Sin sustitucion |
| I1.3.4.1.5 Conocimiento gastronomico | APP/consola.py + bandeja I13415 | Ninguno | C | Sin sustitucion |
| I1.3.4.2 Diagnostico escritura segura | APP/consola.py + diag I1342 | Repos 601 solo a nivel bajo | C | El diagnostico especifico no esta migrado |
| I1.3.4.3 Importacion definitiva de menus | APP/consola.py + importador I1343 | CentroImportacionUI601 + BibliotecaMenus601 | B | Falta sesion revisada validada equivalente |
| I1.3.4.4 Auditoria postimportacion | APP/consola.py + auditor I1344 | BibliotecaMenus601 parcial | B | Falta auditoria especializada |
| I1.3.4.4.1 Correccion postimportacion | APP/consola.py + bandeja I13441 | BibliotecaMenus601 + AsistenteIncidencias601 parcial | B | Falta bandeja dedicada |
| I1.3.4.4.2 Correccion inteligente masiva | APP/consola.py + bandeja I13442 | Ninguno completo | B | No hay correccion masiva equivalente |
| I1.3.5 Certificacion final importador | APP/consola.py + certificador I135 | Ninguno | C | Certificador tecnico del legado |

## 6. Riesgos si hoy se eliminara Excel Importaciones

Clasificacion global: Impacto alto.

### Funciones que se perderian de forma inmediata
1. Analisis general de archivos Excel y deteccion multi-tipo.
2. Importacion de articulos desde Excel.
3. Importacion y comparacion de inventario desde Excel.
4. Resolucion de conflictos Excel antes de importar.
5. Cadena avanzada legacy para menus: reconocimiento, arbol semantico, aprendizaje culinario, preimportacion, bloqueos, simulacion, correccion masiva, auditoria y certificacion.
6. Diagnosticos tecnicos M1.x/I1.x que siguen siendo la unica instrumentacion de esa cadena.

### Impacto practico
- Catalogo maestro: perderia su unica importacion Excel clasica operativa.
- Stock: perderia la unica importacion masiva de inventario por Excel.
- Menus legacy: perderian la unica cadena avanzada de revision/normalizacion previa y posterior.
- Soporte tecnico: perderia detectores, simuladores, resolutores y certificadores especificos.

## 7. Conclusion unica

3. Debe mantenerse porque aun existen funciones criticas sin migrar.

### Funciones criticas aun no migradas
1. Analizar archivo Excel.
2. Detectar tipo de documento Excel.
3. Vista previa e importacion de articulos Excel.
4. Vista previa, comparacion e importacion de inventario Excel.
5. Resolucion de conflictos Excel previa a importar.
6. I1.1 detector de escandallos antiguos.
7. I1.3.2.1.1 reconocimiento corregido de menus.
8. I1.3.2.2 arbol semantico de menus.
9. I1.3.2.4 motor de aprendizaje culinario.
10. M1.1 a M1.3.3 diagnosticos tecnicos.
11. I1.3.4.1.1 a I1.3.5 simulacion, bandejas de revision/correccion, auditoria y certificacion de la cadena legacy de menus.

## 8. Recomendacion operativa inmediata
- Mantener Excel Importaciones como acceso legado.
- No retirarlo mientras no exista sustitucion demostrada para articulos, inventario y la cadena avanzada de menus.
- Si mas adelante se plantea retirada, hacerlo por bloques funcionales y con pruebas equivalentes por cada grupo.
