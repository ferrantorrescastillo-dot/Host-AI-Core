# Host AI 4.10.5 - 4.10.6

## 4.10.5 Clasificador de tests históricos

Clasifica automáticamente los tests antiguos y actuales en bloques funcionales:

- 4.1 Catálogo
- 4.2 Proveedores
- 4.3 Stock
- 4.4 Recepción
- 4.5 Producto/Base
- 4.6 Producción
- 4.7 Eventos
- 4.8 Rentabilidad
- 4.9 IA Operativa
- 4.10 Auditoría/Cierre

Objetivo: preparar el Runner de tests para no depender de nombres manuales.

## 4.10.6 Limpieza de APPs antiguas

Analiza la carpeta APP y detecta:

- wrappers válidos con servicio parecido;
- APPs sin servicio parecido;
- APPs sin test parecido;
- candidatas a revisión antes de la interfaz 5.0.

Importante: este módulo no borra nada automáticamente. Solo informa.

## Pruebas

```powershell
python -m TESTS.test_4105_clasificador_tests_historicos
python -m TESTS.test_4106_limpieza_apps_antiguas
```

## Uso manual

```powershell
python APP/clasificar_tests_historicos_4105.py
python APP/limpieza_apps_antiguas_4106.py
```
