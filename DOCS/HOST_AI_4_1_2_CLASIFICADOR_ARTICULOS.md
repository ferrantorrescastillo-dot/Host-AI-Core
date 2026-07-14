# Host AI 4.1.2 — Clasificador Inteligente de Artículos

## Objetivo

Clasificar automáticamente los artículos reales del restaurante antes de importarlos definitivamente.

## Hoja esperada

```text
Listado de Artículos
```

## Columnas esperadas

```text
Codigo
Articulo
Observaciones
Proveedor
Familia
Precio
```

## Comando de prueba

```powershell
python TESTS\test_412_clasificador_articulos_restaurante.py
```

## Comando con el Excel real

```powershell
python APP\clasificar_articulos_412.py "C:\Proyecto Host IA 3.0\DATOS\Escandallos Boronat  (HostIA).xlsx"
```

El archivo original no se modifica.

Se genera una copia con una hoja nueva:

```text
Clasificacion 4.1.2
```

Y otra hoja:

```text
Resumen 4.1.2
```

## Siguiente paso

Revisar en Excel las filas donde:

```text
Revisar = SI
Revisar = REVISAR
```

Cuando estén corregidas, pasaremos a la importación real.
