# HOST AI 5.5.6E.1 — Motor de tiempos

Descompone una producción en tiempos activos y pasivos, ajusta de forma prudente por volumen y conserva la trazabilidad de la fuente del cálculo.

Prioridad: perfil real configurado > estimación del plan 5.5.6D. No crea órdenes ni modifica datos.

```powershell
python TESTS/test_556e1_motor_tiempos.py
python APP/probar_tiempos_produccion_556e1.py "Ensaladilla de gamba" 150
```
