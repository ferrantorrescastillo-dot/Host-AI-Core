# Host AI 4.6.1–4.6.4 — Producción operativa inteligente

## Objetivo
Convertir Host AI en un planificador operativo de cocina capaz de organizar el trabajo diario como un jefe de cocina.

## Incluye

### 4.6.1 Planificador diario de producción
Integra prioridades, asignación de cocineros y tiempos activos/pasivos para generar un plan diario.

### 4.6.2 Prioridades inteligentes de cocina
Ordena elaboraciones según prioridad, dependencias, tiempo pasivo, tiempo total y hora de servicio.

### 4.6.3 Asignación inteligente de cocineros
Reparte tareas activas equilibrando carga y manteniendo la regla: quien empieza intenta terminar.

### 4.6.4 Gestión de tiempos activos y pasivos
Distingue trabajo real del cocinero frente a horno, reposo, fermentación, abatimiento o cocción pasiva.

## Pruebas
```powershell
python TESTS/test_461_planificador_diario_produccion.py
python TESTS/test_462_prioridades_inteligentes_cocina.py
python TESTS/test_463_asignacion_cocineros.py
python TESTS/test_464_tiempos_activos_pasivos.py
```

## Uso manual
```powershell
python APP/planificador_diario_produccion_461.py
python APP/prioridades_inteligentes_cocina_462.py
python APP/asignacion_cocineros_463.py
python APP/tiempos_activos_pasivos_464.py
```
