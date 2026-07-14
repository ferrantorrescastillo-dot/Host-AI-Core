# Host AI 5.5.6E.3.1 — Planificación basada en recetas reales

Corrige el reparto genérico de 5.5.6E.3. Antes de planificar comprueba si existe una ficha de producción validada. Si falta, no inventa fases ni tiempos: solicita registrar el proceso real.

## Flujo

1. Crear plantilla:

```powershell
python APP/gestionar_ficha_produccion_556e31.py "Ensaladilla de gamba" --plantilla "ensaladilla_proceso.json"
```

2. Completar el JSON con fases, tiempos, tipo activo/pasivo, recursos y rendimiento.

3. Vista previa:

```powershell
python APP/gestionar_ficha_produccion_556e31.py "Ensaladilla de gamba" --desde-json "ensaladilla_proceso.json"
```

4. Confirmar guardado:

```powershell
python APP/gestionar_ficha_produccion_556e31.py "Ensaladilla de gamba" --desde-json "ensaladilla_proceso.json" --confirmar
```

5. Planificar:

```powershell
python APP/planificar_receta_real_556e31.py "Ensaladilla de gamba" 150 --cocineros 3
```

El planning trabaja en solo lectura y no crea órdenes reales.
