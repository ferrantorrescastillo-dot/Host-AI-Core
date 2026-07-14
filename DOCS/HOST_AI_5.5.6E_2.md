# HOST AI 5.5.6E.2 — Recursos de cocina

Asigna recursos requeridos a cada fase del motor 5.5.6E.1 y detecta recursos no configurados. Incluye un detector de solapamientos para varias producciones. Todo funciona en solo lectura.

La capacidad inicial se configura en `DATOS/config/recursos_cocina_556e2.json`.

```powershell
python TESTS/test_556e2_motor_recursos.py
python APP/probar_recursos_produccion_556e2.py "Ensaladilla de gamba" 150
```
