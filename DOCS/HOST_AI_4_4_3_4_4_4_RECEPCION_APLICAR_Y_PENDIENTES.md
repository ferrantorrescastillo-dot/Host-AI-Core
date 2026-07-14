# Host AI 4.4.3 + 4.4.4 — Aplicar Recepción y Gestionar Pendientes

## 4.4.3 — Aplicar recepción a stock

Lee:

```text
DATOS/db/recepcion_mercancia_validada_4_4_2.json
```

Actualiza:

```text
DATOS/db/stock_inicial.json
DATOS/db/stock_movimientos.json
DATOS/db/precios.json
```

Comando:

```powershell
python APP\aplicar_recepcion_mercancia_443.py
```

## 4.4.4 — Gestionar artículos pendientes

Detecta artículos recibidos que no tienen código/artículo validado.

Modo revisión:

```powershell
python APP\gestionar_pendientes_recepcion_444.py
```

Modo crear artículos:

```powershell
python APP\gestionar_pendientes_recepcion_444.py --crear
```

## Tests

```powershell
python TESTS\test_443_aplicador_recepcion_mercancia.py
python TESTS\test_444_gestor_pendientes_recepcion.py
```

## Flujo recomendado

```text
4.4.1 interpretar texto
4.4.2 validar contra catálogo
4.4.4 revisar/crear pendientes si hay productos nuevos
4.4.3 aplicar al stock
```

## Importante

4.4.4 no crea artículos salvo que uses `--crear`.
