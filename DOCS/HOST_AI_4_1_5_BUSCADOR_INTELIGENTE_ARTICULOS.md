# Host AI 4.1.5 — Buscador Inteligente de Artículos

## Objetivo

Permitir buscar artículos reales como se trabaja en cocina:

```text
Nombre del artículo
↓
Coincidencias parecidas
↓
Proveedor como ayuda secundaria
```

## Fuente de datos

Lee:

```text
DATOS/db/articulos.json
```

Este archivo se genera con el importador 4.1.4.

## Comando de prueba

```powershell
python TESTS\test_415_buscador_inteligente_articulos.py
```

## Comandos de uso

Buscar por nombre:

```powershell
python APP\buscar_articulos_415.py "aceite"
```

Buscar con proveedor como filtro secundario:

```powershell
python APP\buscar_articulos_415.py "arroz" "Makro"
```

## Qué devuelve

- Código interno.
- Nombre.
- Proveedor.
- Familia.
- Precio.
- Porcentaje de parecido.
- Motivo de coincidencia.

## Regla de trabajo

El usuario busca por nombre.

Host AI usa el código por dentro.
