# Changelog - Host AI 5.3.7 + 5.3.8

## Añadido

### 5.3.7 Detector Inteligente de Incidencias

- Nuevo servicio `SERVICIOS/detector_incidencias_537.py`.
- Nueva app de prueba manual `APP/detector_incidencias_537.py`.
- Nuevo test `TESTS/test_537_detector_incidencias.py`.
- Clasificación de incidencias por nivel: crítico, alto, medio y bajo.

### 5.3.8 Replanificador Inteligente

- Nuevo servicio `SERVICIOS/replanificador_inteligente_538.py`.
- Nueva app de prueba manual `APP/replanificador_inteligente_538.py`.
- Nuevo test `TESTS/test_538_replanificador_inteligente.py`.
- Generación de planning alternativo sin aplicar cambios reales.
- Confirmación obligatoria antes de aplicar cambios.

## Seguridad

- No se modifica stock real.
- No se crean pedidos reales.
- No se cambia la base de datos.
- Todo funciona en modo propuesta/lectura.

## Pruebas

Ejecutar desde la raíz del proyecto:

```bash
python TESTS/test_537_detector_incidencias.py
python TESTS/test_538_replanificador_inteligente.py
```
