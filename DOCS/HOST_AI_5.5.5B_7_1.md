# HOST AI 5.5.5B.7.1 — Motor de importación canónica segura

## Objetivo

Aplicar a la base canónica únicamente las decisiones automáticas seguras ya
validadas por las Partes 5 y 6.

## Reglas de seguridad

- La ejecución normal es una vista previa.
- La escritura requiere `--confirmar`.
- Las variantes reales, fusiones y títulos dudosos quedan pendientes.
- Antes de reemplazar una base existente se crea una copia de seguridad.
- La escritura se realiza en archivo temporal, se vuelve a leer y solo después
  se reemplaza el destino.
- Se genera un diario JSON de la transacción.

## Prueba

```powershell
python TESTS/test_555b71_importador_canonico_seguro.py
```

## Vista previa con datos reales

```powershell
python APP/importar_canonico_seguro_555b71.py \
  --preimportacion "DATOS/informes/preimportacion_555b.json" \
  --resolucion "DATOS/informes/resolucion_variantes_555b.json"
```

## Importación confirmada

Solo después de revisar la vista previa:

```powershell
python APP/importar_canonico_seguro_555b71.py \
  --preimportacion "DATOS/informes/preimportacion_555b.json" \
  --resolucion "DATOS/informes/resolucion_variantes_555b.json" \
  --confirmar
```
