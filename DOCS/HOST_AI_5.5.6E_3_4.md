# HOST AI 5.5.6E.3.4

## Planificación real por rendimiento, lotes y jornadas

Corrige el planificador de fichas reales para que:

- use primero el rendimiento del escandallo canónico;
- trate los tiempos escalados como carga de trabajo en persona-minutos;
- reparta fases escalables y paralelizables entre varios cocineros;
- limite cada cocinero a su jornada real (08:00–15:30 por defecto, 450 minutos);
- use una capacidad diaria de 1.350 minutos con tres cocineros;
- corte el planning al final de la jornada y continúe en DÍA 2 solo cuando sea necesario;
- muestre carga y tiempo libre de cada cocinero por día;
- mantenga los tiempos pasivos liberando al equipo.

No crea órdenes ni modifica datos reales.

## Prueba

```powershell
python TESTS/test_556e34_planificacion_rendimiento_jornadas.py
python APP/planificar_receta_real_556e31.py "Ensaladilla de gamba" 150 --cocineros 3
```
