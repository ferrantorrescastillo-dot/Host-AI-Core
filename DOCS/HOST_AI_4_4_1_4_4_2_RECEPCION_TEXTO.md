# Host AI 4.4.1 + 4.4.2 — Recepción de Mercancía por Texto

## Objetivo

Empezar el flujo conversacional real:

```text
"De Makro han llegado 15 kg arroz bomba a 3,20 €/kg"
```

El sistema:

1. Interpreta el texto.
2. Extrae producto, cantidad, unidad, proveedor y precio.
3. Busca el artículo en el catálogo real.
4. Crea un borrador validado.
5. Todavía NO modifica stock.

## Archivos incluidos

```text
SERVICIOS/interprete_recepcion_texto_441.py
SERVICIOS/validador_recepcion_mercancia_442.py
APP/interpretar_recepcion_texto_441.py
APP/recepcion_mercancia_texto_442.py
TESTS/test_441_interprete_recepcion_texto.py
TESTS/test_442_validador_recepcion_mercancia.py
DOCS/HOST_AI_4_4_1_4_4_2_RECEPCION_TEXTO.md
```

## Pruebas

```powershell
python TESTS\test_441_interprete_recepcion_texto.py
python TESTS\test_442_validador_recepcion_mercancia.py
```

## Uso real

Solo interpretar:

```powershell
python APP\interpretar_recepcion_texto_441.py "De Makro han llegado 15 kg arroz bomba a 3,20 €/kg, 6 l aceite oliva"
```

Interpretar + validar contra artículos:

```powershell
python APP\recepcion_mercancia_texto_442.py "De Makro han llegado 15 kg arroz bomba a 3,20 €/kg, 6 l aceite oliva"
```

## Salidas

```text
DATOS/db/recepcion_texto_4_4_1.json
DATOS/db/recepcion_borrador_4_4_2.json
DATOS/db/recepcion_borrador_4_4_2.txt
```

## Estados posibles

```text
listo_para_aplicar
requiere_revision
parcial
error
```

## Siguiente paso

```text
Host AI 4.4.3 + 4.4.4
Aplicar recepción:
- sumar stock,
- actualizar precios,
- crear artículos pendientes si se acepta.
```
