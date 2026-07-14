# Host AI 5.0.7 - Reforzador del Clasificador de Intenciones

## Objetivo

Mejorar los fallos detectados por la Beta Conversacional QA 5.0.6, especialmente en:

- stock;
- producción;
- compras;
- rentabilidad.

## Qué modifica

Sobrescribe `SERVICIOS/clasificador_intenciones_503.py` manteniendo el mismo nombre de clase (`ClasificadorIntenciones503`) para no romper imports existentes.

## Mejoras principales

### Stock
Reconoce frases como:

- ¿Cuánto arroz bomba tengo?
- ¿Cuánto queda de gambón?
- ¿Tengo suficiente pollo?
- Mira si queda leche.
- Revisa existencias de pescado.

### Producción
Reconoce frases como:

- ¿Qué elaboraciones puedo adelantar hoy?
- Prepara fondos y salsas para el sábado.
- Necesito un plan de trabajo de cocina.
- Controla tiempos activos y pasivos.

### Compras
Reconoce frases como:

- Me falta aceite para el servicio.
- ¿Qué artículos están por debajo del mínimo?
- ¿A quién compro el gambón?

### Rentabilidad
Reconoce frases como:

- Cuál es el plato menos rentable.
- Qué receta me hace perder dinero.
- Qué producto me deja menos margen.

## Pruebas

```powershell
python -m TESTS.test_507_reforzador_clasificador
python -m APP.beta_conversacional_qa_506
```

## Nota

Este sprint no ejecuta motores nuevos. Refuerza la clasificación para que los siguientes sprints puedan enrutar mejor los flujos reales.
