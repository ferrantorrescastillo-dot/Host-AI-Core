# Host AI 5.0.3 - Clasificador Inteligente de Intenciones

Objetivo: que Host AI deje de depender de frases exactas y empiece a puntuar posibles intenciones.

Intenciones iniciales:

- recepción de mercancía
- eventos
- compras
- producción
- rentabilidad
- stock
- conversación general

Este bloque no sustituye motores existentes. Decide qué flujo debe activarse.

Prueba recomendada:

```powershell
python -m TESTS.test_503_clasificador_intenciones
python -m APP.clasificador_intenciones_503
```
