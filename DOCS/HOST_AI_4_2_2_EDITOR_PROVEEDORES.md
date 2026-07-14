# Host AI 4.2.2 — Editor de Proveedores

## Objetivo

Editar y normalizar proveedores reales en:

```text
DATOS/db/proveedores.json
```

## Comando de prueba

```powershell
python TESTS\test_422_editor_proveedores.py
```

## Editar por código

```powershell
python APP\editar_proveedor_422.py PROV0001 nombre=Makro observaciones="Nombre oficial revisado"
```

## Editar por nombre

```powershell
python APP\editar_proveedor_422.py Makro nombre=Makro estado=activo
```

## Campos editables

```text
nombre
estado
observaciones
```

## Siguiente paso

Después de normalizar proveedores, seguiremos con informe final de proveedores.
