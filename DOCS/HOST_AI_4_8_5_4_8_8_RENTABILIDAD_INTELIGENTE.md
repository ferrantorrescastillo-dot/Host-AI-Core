# HOST AI 4.8.5–4.8.8 — Rentabilidad Inteligente

## 4.8.5 Control de mermas
Registra pérdidas por caducidad, sobreproducción, porcionado, errores o desperdicio. Calcula coste total por motivo y por área.

## 4.8.6 Comparador económico de proveedores
Compara ofertas teniendo en cuenta precio, cantidad, transporte, descuentos y fiabilidad del proveedor. No decide solo por precio unitario.

## 4.8.7 Alertas de rentabilidad
Detecta platos, menús o productos con margen inferior al mínimo definido. Genera alertas con severidad.

## 4.8.8 Informe financiero inteligente
Resume ventas, costes, mermas, beneficio, margen y recomendaciones para tomar decisiones.

## Pruebas

```powershell
python -m TESTS.test_485_control_mermas
python -m TESTS.test_486_comparador_economico_proveedores
python -m TESTS.test_487_alertas_rentabilidad
python -m TESTS.test_488_informe_financiero_inteligente
```

## Uso manual

```powershell
python APP/control_mermas_485.py
python APP/comparador_economico_proveedores_486.py
python APP/alertas_rentabilidad_487.py
python APP/informe_financiero_inteligente_488.py
```
