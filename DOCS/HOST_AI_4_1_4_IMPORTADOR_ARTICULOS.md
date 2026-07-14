# Host AI 4.1.4 — Importador Inteligente de Artículos

## Objetivo

Importar los artículos reales del restaurante a:

```text
DATOS/db/articulos.json
```

## Reglas

- Usa `Codigo Host AI` si existe la hoja `Codigos 4.1.3`.
- Si no existe, usa la columna `Codigo`.
- No duplica artículos.
- Si el código ya existe, actualiza el artículo.
- El Excel original no se modifica.

## Comando de prueba

```powershell
python TESTS\test_414_importador_articulos_restaurante.py
```

## Comando con tu Excel real

Usa el archivo generado en 4.1.3:

```powershell
python APP\importar_articulos_414.py "C:\Proyecto Host IA 3.0\Documentos\Escandallos Boronat  (HostIA)_CODIGOS_4_1_3.xlsx"
```

## Resultado esperado

```text
HOST AI 4.1.4 - Importación de artículos completada
Procesados: 354
Nuevos: 354
Actualizados: 0
Errores: 0
```

## Archivo generado

```text
DATOS/db/articulos.json
```

A partir de ahí Host AI ya tendrá un catálogo real de artículos con código interno.
