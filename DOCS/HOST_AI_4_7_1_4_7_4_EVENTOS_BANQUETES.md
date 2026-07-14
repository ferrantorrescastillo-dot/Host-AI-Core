# Host AI 4.7.1 - 4.7.4 Eventos y banquetes inteligentes

Este parche inicia el bloque 4.7, orientado a eventos, banquetes, caterings y servicios especiales.

## 4.7.1 Gestion de eventos

Permite crear, validar, guardar, cargar y buscar eventos con datos clave:

- fecha
- hora
- tipo de evento
- cliente
- lugar
- personas
- presupuesto
- estado

## 4.7.2 Menus del evento

Permite construir menus con platos, coste por persona, precio de venta, margen y resumen economico por numero de comensales.

## 4.7.3 Produccion automatica del evento

Genera tareas de produccion segun el menu, las personas, los tiempos activos/pasivos y la hora de servicio.

## 4.7.4 Compras automaticas

Calcula necesidades de ingredientes, compara con stock disponible y genera un pedido borrador para el evento.

## Pruebas

```powershell
python -m TESTS.test_471_gestion_eventos
python -m TESTS.test_472_menus_evento
python -m TESTS.test_473_produccion_evento
python -m TESTS.test_474_compras_evento
```

Tambien se pueden ejecutar directamente desde la raiz del proyecto:

```powershell
python TESTS/test_471_gestion_eventos.py
python TESTS/test_472_menus_evento.py
python TESTS/test_473_produccion_evento.py
python TESTS/test_474_compras_evento.py
```

## Uso manual

```powershell
python APP/gestion_eventos_471.py
python APP/menus_evento_472.py
python APP/produccion_evento_473.py
python APP/compras_evento_474.py
```
