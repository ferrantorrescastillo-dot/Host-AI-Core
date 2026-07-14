# Prompt Operativo para Copilot

Objetivo: Producción
Dominio: produccion

## Restricciones
- No tocar DATOS, DB ni Documentos/AI.docx.
- No romper AI_CORE v1/v2.1.
- Cambios minimos y verificables.

## Documentacion prioritaria
- AGENTS.md (p=2)
- MASTER_PLAN.md (p=3)
- CODEX-01.md (p=4)
- CODEX-02.md (p=5)
- ROC/ROC-01A_NUCLEO.md (p=110)
- ROC/ROC-01B_NUCLEO.md (p=110)
- ROC/ROC-02A_OPERACION.md (p=110)
- ROC/ROC-02B_OPERACION.md (p=110)

## Archivos de codigo foco
- APP/checklist_final_produccion_467.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- APP/conector_produccion_real_556.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- APP/consola_produccion_guiada_piloto_13.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- APP/gestionar_ficha_produccion_556e31.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- APP/informe_diario_produccion_468.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- APP/planificador_diario_produccion_461.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- APP/probar_recursos_produccion_556e2.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- APP/probar_tiempos_produccion_556e1.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- APP/produccion_evento_473.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- MODELOS/alertas_produccion_306.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- MODELOS/analisis_produccion_306.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- MODELOS/ejecucion_produccion_306.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- MODELOS/optimizacion_produccion_306.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- MODELOS/planificacion_produccion_306.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- MODELOS/produccion_completa.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- MODELOS/produccion_real.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- MOTORES/motor_produccion_completa.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- MOTORES/motor_produccion_real.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- MOTORES/motor_simulador_produccion_evento.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)
- PIPELINES/pipeline_analizador_inteligente_produccion.py (p=62, motivo=match_keyword:produccion,match_keyword:prod)

## Tests relacionados
- TESTS/test_461_planificador_diario_produccion.py (match_stem:test_461_planificador_diario_produccion)
- TESTS/test_467_checklist_final_produccion.py (match_stem:test_467_checklist_final_produccion)
- TESTS/test_468_informe_diario_produccion.py (match_stem:test_468_informe_diario_produccion)
- TESTS/test_473_produccion_evento.py (match_stem:test_473_produccion_evento)
- TESTS/test_556_conector_produccion_real.py (match_stem:test_556_conector_produccion_real)
- TESTS/test_556e34_planificacion_rendimiento_jornadas.py (match_keyword:jornada)
- TESTS/test_analizador_inteligente_produccion.py (match_stem:test_analizador_inteligente_produccion)
- TESTS/test_asignador_recursos_produccion.py (match_stem:test_asignador_recursos_produccion)
- TESTS/test_cierre_inteligente_produccion.py (match_stem:test_cierre_inteligente_produccion)
- TESTS/test_control_ejecucion_produccion.py (match_stem:test_control_ejecucion_produccion)
- TESTS/test_motor_alertas_produccion.py (match_stem:motor_alertas_produccion)
- TESTS/test_motor_produccion_real.py (match_stem:produccion_real)
- TESTS/test_optimizador_inteligente_produccion.py (match_stem:optimizador_inteligente_produccion)
- TESTS/test_p1_gestion_produccion.py (match_keyword:produccion)
- TESTS/test_p33_panel_produccion.py (match_keyword:produccion)
- TESTS/test_piloto_12_jornada.py (match_keyword:jornada)
- TESTS/test_piloto_13_produccion_guiada.py (match_keyword:produccion)
- TESTS/test_piloto_14_produccion_stock.py (match_keyword:produccion)
- TESTS/test_pipeline_produccion_completa.py (match_stem:produccion_completa)
- TESTS/test_planificador_inteligente_produccion.py (match_stem:planificador_inteligente_produccion)

## Entrega esperada
- Implementacion acotada al objetivo.
- Tests relevantes en verde.
- Resumen tecnico de cambios con riesgos.
