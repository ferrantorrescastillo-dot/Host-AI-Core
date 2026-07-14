# HOST AI RC3.1 - Calidad para Piloto

## Objetivo
Preparar Host AI para pruebas con restaurantes reales añadiendo una primera capa de validación de calidad de datos.

## Archivos añadidos

```text
SERVICIOS/validador_calidad_piloto.py
TESTS/test_rc3_1_calidad_piloto.py
DOCS/RC3_1_CALIDAD_PILOTO.md
```

## Qué valida

- Artículos sin nombre, unidad, proveedor o precio válido.
- Stock negativo.
- Facturas sin líneas o líneas incompletas.
- Recetas sin ingredientes, raciones inválidas o ingredientes mal definidos.
- Producciones sin elaboración, cantidad inválida o tiempos negativos.

## Qué NO hace todavía

- No modifica motores existentes.
- No bloquea acciones reales.
- No altera datos.
- No cambia el comportamiento de Host AI.

## Comandos

```powershell
python TESTS\test_rc3_1_calidad_piloto.py
python TESTS\test_host_ai_3_0_stable.py
```

## Siguiente paso recomendado

RC3.2: conectar estas validaciones de forma gradual con los puntos críticos de entrada: facturas, artículos, recetas y producción.
