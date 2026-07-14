# HOST AI 5.5.6E.3.4.1

## Paralelización interna por lotes y equipo

Este parche corrige la planificación de una misma receta cuando existen varias
personas disponibles.

- Divide entre varios cocineros fases como pelar, cortar, preparar, porcionar,
  envasar y etiquetar.
- Mantiene sin dividir fases técnicas que requieren una única secuencia, como
  cocción, enfriado, reposo o mezcla, salvo que la ficha indique expresamente
  que pueden realizarse por lotes.
- Usa el equipo disponible antes de abrir una segunda jornada.
- Respeta el rendimiento canónico, la jornada 08:00–15:30 y el máximo de 450
  minutos activos por cocinero.
- Conserva recursos, tiempos pasivos y modo solo lectura.
- Mantiene compatibilidad con fichas antiguas que todavía no tienen el campo
  `puede_paralelizar`.

## Prueba

```powershell
python TESTS/test_556e341_paralelizacion_interna.py
python APP/planificar_receta_real_556e31.py "Ensaladilla de gamba" 150 --cocineros 3
```

No crea órdenes ni modifica datos reales.
