# Host AI 4.2.2.1 — Fix Editor de Proveedores

## Corrección

Se corrige conflicto de parámetros en:

```python
editar_por_nombre()
```

Antes el método usaba `nombre` como parámetro de búsqueda y también como campo editable.

Ahora usa:

```python
nombre_busqueda
```

Así permite:

```powershell
python APP\editar_proveedor_422.py Makro nombre=Makro estado=activo
```

## Prueba

```powershell
python TESTS\test_422_editor_proveedores.py
```
