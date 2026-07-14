# Host AI 4.1.7 — Editor de Artículos

## Objetivo

Editar artículos reales ya importados en:

```text
DATOS/db/articulos.json
```

## Comando de prueba

```powershell
python TESTS\test_417_editor_articulos.py
```

## Editar por código

```powershell
python APP\editar_articulo_417.py ART000355 precio=3,45 proveedor=Makro familia=Arroces
```

## Editar por nombre exacto

```powershell
python APP\editar_articulo_417.py "Arroz bomba" precio=3,45 proveedor=Makro
```

## Campos editables

```text
nombre
proveedor
familia
precio
observaciones
activo
```

## Siguiente paso

Después de editar, puedes buscar:

```powershell
python APP\buscar_articulos_415.py "arroz bomba"
```
