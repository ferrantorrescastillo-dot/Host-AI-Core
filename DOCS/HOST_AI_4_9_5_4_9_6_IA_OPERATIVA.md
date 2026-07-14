# Host AI 4.9.5–4.9.6 — IA Operativa Central

## 4.9.5 — Asistente de urgencias

Detecta incidencias críticas antes de que rompan el servicio:

- roturas de stock;
- eventos próximos;
- producción bloqueada;
- proveedores no confirmados;
- pedidos pendientes;
- incidencias con cliente;
- riesgos económicos.

No ejecuta cambios directos. Devuelve prioridades y acciones recomendadas para que Host AI pueda pedir confirmación.

Archivos:

- `SERVICIOS/asistente_urgencias_495.py`
- `APP/asistente_urgencias_495.py`
- `TESTS/test_495_asistente_urgencias.py`

## 4.9.6 — Recomendaciones inteligentes

Genera recomendaciones prácticas sobre:

- stock;
- compras;
- producción;
- rentabilidad;
- carta.

Ejemplos:

- comprar producto bajo mínimos;
- renegociar una subida de proveedor;
- reducir sobrestock;
- revisar un plato con margen bajo;
- mejorar venta de un plato rentable pero poco vendido.

Archivos:

- `SERVICIOS/recomendaciones_inteligentes_496.py`
- `APP/recomendaciones_inteligentes_496.py`
- `TESTS/test_496_recomendaciones_inteligentes.py`

## Pruebas

```powershell
python -m TESTS.test_495_asistente_urgencias
python -m TESTS.test_496_recomendaciones_inteligentes
```

## Uso manual

```powershell
python APP/asistente_urgencias_495.py
python APP/recomendaciones_inteligentes_496.py
```
