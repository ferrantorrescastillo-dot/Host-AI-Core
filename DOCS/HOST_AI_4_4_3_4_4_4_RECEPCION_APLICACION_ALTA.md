# Host AI 4.4.3 + 4.4.4 — Aplicación de Recepción y Alta de Artículos Nuevos

## 4.4.3 — Aplicar recepción validada

Lee:

```text
DATOS/db/recepcion_borrador_4_4_2.json
```

Hace:

- suma stock para líneas con `entrada_stock`;
- registra movimiento en `stock_movimientos.json`;
- actualiza precio si el precio recibido cambia;
- deja pendientes los artículos nuevos;
- omite coincidencias dudosas por seguridad.

Comando:

```powershell
python TESTS\test_443_aplicador_recepcion_mercancia.py
python APP\aplicar_recepcion_mercancia_443.py
```

Genera:

```text
DATOS/db/recepcion_aplicada_4_4_3.json
DATOS/db/recepcion_aplicada_4_4_3.txt
```

## 4.4.4 — Crear artículos nuevos pendientes

Lee el mismo borrador y crea solo las líneas con:

```text
crear_articulo_pendiente
```

Comando:

```powershell
python TESTS\test_444_alta_articulos_recepcion.py
python APP\alta_articulos_recepcion_444.py
```

Genera:

```text
DATOS/db/articulos_nuevos_recepcion_4_4_4.json
DATOS/db/articulos_nuevos_recepcion_4_4_4.txt
```

## Flujo recomendado

1. Ejecutar 4.4.2 para crear borrador.
2. Ejecutar 4.4.3 para aplicar artículos encontrados.
3. Si hay artículos nuevos, ejecutar 4.4.4.
4. Volver a ejecutar 4.4.2 para validar otra vez con los nuevos artículos.
5. Ejecutar 4.4.3 de nuevo.

## Ejemplo

```powershell
python APP\recepcion_mercancia_texto_442.py "De Makro han llegado 15 kg arroz bomba a 3,20 €/kg, 5 kg harina fuerza a 1,20 €/kg"
python APP\aplicar_recepcion_mercancia_443.py
python APP\alta_articulos_recepcion_444.py
```
