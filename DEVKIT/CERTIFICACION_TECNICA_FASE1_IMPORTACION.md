# CERTIFICACIÓN TÉCNICA — FASE 1 IMPORTACIÓN INTELIGENTE

Fecha: 31 de agosto de 2026
Versión base: `af3642d2690b6e3a4243788bab0de244b30c602e`
Rama: `feature/compras-web`
Resultado: CERTIFICADA TÉCNICAMENTE; VALIDACIÓN MANUAL/CULINARIA PENDIENTE

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

## Siguiente paso

VALIDACIÓN MANUAL/CULINARIA DE FASE 1 POR EL USUARIO.
