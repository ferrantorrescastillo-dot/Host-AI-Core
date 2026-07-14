# HOST AI 5.5.6CD.2 — Alta e inicialización segura del inventario

## Objetivo

Crear inventario inicial únicamente con cantidades reales declaradas por el usuario. El sistema nunca inventa existencias.

## Diferencia clave

- **Stock actual:** cantidad real contada. Es obligatorio indicarla.
- **Stock mínimo:** umbral de reposición. Puede usar una recomendación configurable por unidad o familia.

Los mínimos incluidos por defecto son recomendaciones iniciales:

- kg: 2
- l: 2
- u: 10
- g: 500
- ml: 500

Se configuran en `DATOS/config/stock_minimos_defecto_556cd2.json` y no representan stock disponible.

## Uso

### Listar artículos sin inventario

```powershell
python APP/gestionar_inventario_inicial_556cd2.py --listar-sin-inventario
```

### Vista previa de un alta

```powershell
python APP/gestionar_inventario_inicial_556cd2.py --articulo "Patata Monalisa" --cantidad 25 --unidad kg --ubicacion "Almacen seco"
```

### Confirmar el alta

```powershell
python APP/gestionar_inventario_inicial_556cd2.py --articulo "Patata Monalisa" --cantidad 25 --unidad kg --ubicacion "Almacen seco" --confirmar
```

### Definir un mínimo específico

```powershell
python APP/gestionar_inventario_inicial_556cd2.py --articulo "Gamba paella" --cantidad 10 --unidad kg --stock-minimo 3 --ubicacion "Congelador" --confirmar
```

## Seguridad

- Sin `--confirmar`, solo muestra una propuesta.
- No sobrescribe un inventario que ya existe.
- Crea copias de seguridad de stock y movimientos.
- Registra un movimiento `inventario_inicial` con stock antes y después.
- Utiliza escritura atómica para reducir el riesgo de corrupción.
