# Host AI 5.3.1–5.3.2 — Flujo operativo inteligente

## 5.3.1 Generador automático del flujo operativo

Construye un plan completo a partir de los datos mínimos del evento recogidos por Host AI 5.2.

No modifica datos reales.

Incluye pasos para:

- evento;
- menú;
- producción;
- recursos;
- stock;
- compras;
- costes/rentabilidad;
- planning.

## 5.3.2 Ejecutor inteligente del flujo

Ejecuta el flujo en modo seguro.

En esta primera versión, las fases que podrían modificar datos reales quedan marcadas como pendientes de confirmación específica.

## Pruebas

```powershell
python -m TESTS.test_531_generador_flujo_operativo
python -m TESTS.test_532_ejecutor_flujo_operativo
```

## Uso manual

```powershell
python -m APP.generador_flujo_operativo_531
python -m APP.ejecutor_flujo_operativo_532
```
