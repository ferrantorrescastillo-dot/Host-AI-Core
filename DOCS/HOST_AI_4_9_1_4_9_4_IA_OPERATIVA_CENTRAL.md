# HOST AI 4.9.1–4.9.4 — IA Operativa Central

Este bloque empieza a unir los módulos anteriores para que Host AI funcione como un segundo jefe de cocina: prioriza, propone acciones y explica decisiones con criterio operativo.

## 4.9.1 Motor de decisiones operativas
Analiza señales de stock, producción, eventos, compras, costes y alertas. Devuelve prioridad, motivos y acción recomendada.

## 4.9.2 Acciones automáticas seguras
Clasifica acciones como seguras, pendientes de confirmación o bloqueadas. Preparado para registrar acciones sin ejecutar cambios peligrosos sin confirmación.

## 4.9.3 Respuestas tipo jefe de cocina
Convierte decisiones técnicas en respuestas útiles para cocina: qué pasa, por qué importa y qué hacer primero.

## 4.9.4 Flujo diario automático
Genera el plan del día: tareas, compras, producción, incidencias y resumen operativo.

## Pruebas

```powershell
python -m TESTS.test_491_motor_decisiones_operativas
python -m TESTS.test_492_acciones_automaticas_seguras
python -m TESTS.test_493_respuestas_jefe_cocina
python -m TESTS.test_494_flujo_diario_automatico
```

## Uso manual

```powershell
python APP/motor_decisiones_operativas_491.py
python APP/acciones_automaticas_seguras_492.py
python APP/respuestas_jefe_cocina_493.py
python APP/flujo_diario_automatico_494.py
```

## Nota de arquitectura

Este parche no sustituye motores existentes. Actúa como capa de coordinación: recibe datos ya calculados por stock, producción, eventos, costes y alertas, y decide prioridades operativas.
