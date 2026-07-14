# Host AI 4.6.5–4.6.8 Producción operativa avanzada

## 4.6.5 Recursos de cocina
Gestiona recursos como horno, abatidor, brasa, fogones o freidora. Detecta sobrecargas por capacidad y resume el uso previsto.

## 4.6.6 Conflictos y replanificación
Detecta conflictos por recurso, cocinero solapado y dependencias no respetadas. Incluye una replanificación básica y conservadora.

## 4.6.7 Checklist final de producción
Genera comprobaciones finales: elaboración terminada, etiquetado, ubicación, documentación y stock negativo.

## 4.6.8 Informe diario de producción
Resume tareas terminadas, pendientes, carga por cocinero, uso de recursos, checklist e incidencias.

## Pruebas
```powershell
python TESTS/test_465_recursos_cocina.py
python TESTS/test_466_conflictos_replanificacion.py
python TESTS/test_467_checklist_final_produccion.py
python TESTS/test_468_informe_diario_produccion.py
```

## Uso manual
```powershell
python APP/recursos_cocina_465.py
python APP/conflictos_replanificacion_466.py
python APP/checklist_final_produccion_467.py
python APP/informe_diario_produccion_468.py
```
