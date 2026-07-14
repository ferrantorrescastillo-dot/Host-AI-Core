# Host AI 4.3.11.4 — Aplicador de Ajustes de Inventario

## Objetivo

Aplicar los ajustes de inventario ya comparados usando el motor de movimientos 4.3.7.

## Entrada

```text
DATOS/db/comparacion_inventario_4_3_11_3.json
```

## Actualiza

```text
DATOS/db/stock_inicial.json
DATOS/db/stock_movimientos.json
```

## Reglas

- Aplica `faltante` y `sobrante`.
- Omite `ok`.
- Omite `revisar` por seguridad.

## Prueba

```powershell
python TESTS\test_43114_aplicador_ajustes_inventario.py
```

## Ejecutar con datos reales

```powershell
python APP\aplicar_ajustes_inventario_43114.py
```

Con motivo personalizado:

```powershell
python APP\aplicar_ajustes_inventario_43114.py "Inventario cierre julio"
```

## Salida

```text
DATOS/db/ajustes_inventario_4_3_11_4.txt
```

## Siguiente paso

```text
Host AI 4.3.11.5 — Informe final de inventario
```
