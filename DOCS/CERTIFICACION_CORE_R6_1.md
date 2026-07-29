# CERTIFICACION CORE R6.1

Fecha: 2026-07-23

## 1) Alcance
Certificacion integral del Core R6.1 centrada en:
- pruebas existentes relevantes por modulo;
- diagnostico y correccion minima de regresion demostrada;
- integridad de datos reales (hash pre/post);
- seguridad de persistencia, trazabilidad y compatibilidad operativa;
- sin funcionalidades nuevas y sin conexion a proveedores IA reales.

Fuera de alcance:
- refactorizaciones generales;
- cambios de arquitectura;
- activacion de proveedores IA externos.

## 2) Entorno
- OS: Windows
- Workspace: Host AI 6.0
- Python: `.venv\\Scripts\\python.exe`
- Runner: `pytest`

## 3) Estado Git (snapshot durante certificacion)
Repositorio en working tree sucio con cambios preexistentes y no relacionados en multiples rutas de APP/CORE/DATOS/MOTORES/PIPELINES/SERVICIOS/TESTS.

Criterio aplicado:
- no revertir cambios preexistentes;
- no ejecutar operaciones destructivas;
- aislar validacion por tests y hashes sobre archivos reales criticos.

## 4) Fuentes de verdad identificadas
1. Codigo real del workspace abierto.
2. Resultado real de tests ejecutados en esta sesion.
3. Hashes SHA256 de datos reales criticos antes y despues.
4. Contratos de comportamiento observados en tests y servicios reales.

## 5) Comandos ejecutados (resumen)
1. Baseline de estado y hashes:
   - `git status --short`
   - `Get-FileHash -Algorithm SHA256` sobre:
     - `DATOS/db/articulos.json`
     - `DATOS/db/proveedores.json`
     - `DATOS/facturas/historico_precios.json`
     - `DATOS/db/eventos.json`
     - `DATOS/db/planes_produccion.json`
     - `DATOS/db/stock_lotes.json`
     - `DATOS/db/stock_movimientos.json`
2. Regresion 601 + Host AI Engine + certificacion R6.1 (lote iniciado y completado en sesion).
3. Regresion operativa:
   - `pytest -q` sobre eventos, produccion, compras, stock, pipelines y compatibilidad.
4. Regresion conversacional/IA/pilotos:
   - `pytest -q` sobre RR15, RR161D, IA11-IA14, asistente conversacional, RR162, RR163, piloto11-14, RP5.
5. Reejecucion afectada tras fix:
   - `pytest -q TESTS/test_rr162_recertificacion_final.py TESTS/test_app_base_ejecutable.py`
6. Cobertura explicita de incidencias:
   - `pytest -q TESTS/test_537_detector_incidencias.py TESTS/test_538_replanificador_inteligente.py TESTS/test_539_integracion_operativa.py TESTS/test_rp5_incidencias_replanificacion.py`
7. Conteo unico de la regresion:
   - `pytest --collect-only -q` sobre union de archivos ejecutados.
8. Hash final + estado Git final:
   - `Get-FileHash -Algorithm SHA256` (mismos archivos)
   - `git status --short`

## 6) Cobertura modular y clasificacion
### 6.1 Modulos objetivo
- Catalogo Maestro: PASSED
- Proveedores y precios: PASSED
- Recetas: PASSED
- Escandallos: PASSED
- Menus: PASSED
- Centro de Importacion: PASSED
- Asistente de Incidencias: PASSED
- Eventos: PASSED
- Produccion: PASSED
- Compras: PASSED
- Stock: PASSED
- Host AI Engine: PASSED
- Director IA, agentes, confirmaciones y auditoria: PASSED
- Orquestacion end-to-end: PASSED
- Tests conversacionales existentes: PASSED

### 6.2 Total de pruebas (union unica ejecutada)
- Total: 183 (collect-only verificado)
- PASSED: 183
- FAILED: 0
- SKIPPED_JUSTIFICADO: 0
- BLOQUEADO_POR_ENTORNO: 0
- NO_IMPLEMENTADO_POR_DISENO: 0

Nota de trazabilidad:
- Durante la primera pasada conversacional hubo 1 fallo transitorio (RR162), corregido y revalidado en reejecucion focal.

## 7) Fallos detectados y severidad
### Hallazgo 1
- Test: `TESTS/test_rr162_recertificacion_final.py::test_rr162_cadena_contexto_costes_compras_stock_e_ia`
- Severidad: ALTO
- Sintoma: `AppConsolaHostAI` fallaba al inicializar con un core minimo (`SimpleNamespace`) por acceso directo a `core.produccion_real`.
- Evidencia: `AttributeError: 'types.SimpleNamespace' object has no attribute 'produccion_real'`.

## 8) Correcciones realizadas
- Archivo modificado: `APP/consola.py`
- Cambio: inicializacion defensiva de `ProduccionStockPiloto14` solo cuando el core expone `produccion_real`.
- Tipo: correccion minima demostrada, sin ampliar alcance funcional.
- Revalidacion afectada: PASSED (`test_rr162_recertificacion_final.py`).

## 9) Escenario integral de boda
- Test: `TESTS/test_certificacion_core_r6_1_boda_integral.py`
- Resultado final: PASSED
- Estado: escenario integral de boda 180 en sandbox validado.

## 10) Integridad de datos reales (hashes)
### Hash baseline (antes)
- DATOS/db/articulos.json = F6C8183B1675F08F24A977617A45F690F850AF808D8E1C4BDBE464EC68FE9BF2
- DATOS/db/proveedores.json = 5DFBCBB0BA2B4ED697800669A3FF2E5073E0706DFF1ECEF96B68A46639195C61
- DATOS/facturas/historico_precios.json = 8E8679ADE7DFECEC0C7A1D974FA3217CB0EE9BA078D679760AE7DE4C5CE68A0D
- DATOS/db/eventos.json = 432784D701B18F45C7415629FB3ACF2E1D72DEB2D1E36C326634D4715EB47825
- DATOS/db/planes_produccion.json = B2D826E0BC036B25FA93FBDEBAEE33A0CC5FC7ED546E155652A6797355E0B554
- DATOS/db/stock_lotes.json = 4AE37FF54EA0ECB99CF28B2516B6A1AA3226C95076F49C07EAEBE8F34C73B80B
- DATOS/db/stock_movimientos.json = FA640A76CD8E7EC7F70C4346A4CE4D59EB11F0154DEDB610127EC95C940A703A

### Hash final (despues)
- DATOS/db/articulos.json = F6C8183B1675F08F24A977617A45F690F850AF808D8E1C4BDBE464EC68FE9BF2
- DATOS/db/proveedores.json = 5DFBCBB0BA2B4ED697800669A3FF2E5073E0706DFF1ECEF96B68A46639195C61
- DATOS/facturas/historico_precios.json = 8E8679ADE7DFECEC0C7A1D974FA3217CB0EE9BA078D679760AE7DE4C5CE68A0D
- DATOS/db/eventos.json = 432784D701B18F45C7415629FB3ACF2E1D72DEB2D1E36C326634D4715EB47825
- DATOS/db/planes_produccion.json = B2D826E0BC036B25FA93FBDEBAEE33A0CC5FC7ED546E155652A6797355E0B554
- DATOS/db/stock_lotes.json = 4AE37FF54EA0ECB99CF28B2516B6A1AA3226C95076F49C07EAEBE8F34C73B80B
- DATOS/db/stock_movimientos.json = FA640A76CD8E7EC7F70C4346A4CE4D59EB11F0154DEDB610127EC95C940A703A

Conclusion de integridad:
- Hashes antes/despues identicos en los 7 archivos reales criticos auditados.
- No se evidencia modificacion de datos reales en esos artefactos.

## 11) Modulos certificados y no certificados
### Certificados
- Todos los modulos listados en el alcance de esta certificacion R6.1 (15/15) quedan en estado PASSED.

### No certificados
- Ninguno dentro del alcance definido en esta ejecucion.

## 12) Limitaciones restantes
1. Working tree con cambios preexistentes y artefactos no versionados ajenos a esta certificacion.
2. La certificacion no incluye conexion a proveedores IA reales por restriccion explicita de seguridad/alcance.
3. La certificacion se ejecuta sobre subconjunto relevante de tests (183), no sobre la suite completa del repositorio.

## 13) Riesgos
- Riesgo BAJO de regresiones fuera del subconjunto certificado debido al tamano total del repositorio y al estado sucio preexistente.
- Riesgo MEDIO si se activa IA real sin fase previa de smoke controlado por proveedor y credenciales.

## 14) Recomendaciones
- Congelar Core: SI, con ventana corta de hardening final y sin ampliar alcance funcional.
- Conectar IA real: NO de inmediato; primero ejecutar smoke por proveedor en entorno controlado, con auditoria de prompts/sanitizacion y rollback operativo.
- Comenzar interfaz grafica: SI, en paralelo controlado, manteniendo al Core como unica autoridad y sin duplicar logica en UI.

## 15) Estado final unico
CERTIFICADO_CON_LIMITACIONES

Motivo:
- No quedan fallos abiertos en el alcance certificado.
- Existe limitacion explicita por estado sucio preexistente del repositorio y por no incluir conectividad IA real en esta fase.
