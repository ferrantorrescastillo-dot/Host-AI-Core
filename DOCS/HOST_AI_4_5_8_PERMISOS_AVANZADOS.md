# Host AI 4.5.8 - Permisos avanzados

Este sprint amplía usuarios y roles con permisos por módulo.

## Roles incluidos

- admin
- gerente
- jefe_cocina
- compras
- almacen
- cocinero
- solo_lectura

## Permisos

Soporta permisos exactos (`stock.ver`) y comodines por módulo (`stock.*`).

## Uso

```powershell
python APP/permisos_avanzados_458.py
python TESTS/test_458_permisos_avanzados.py
```

El servicio principal es `SERVICIOS/permisos_avanzados_458.py`.
