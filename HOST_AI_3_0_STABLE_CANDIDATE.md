# Host AI 3.0 Stable Candidate

Esta versión crea una prueba global no interactiva para validar los cinco bloques principales de Host AI 3.0 antes de iniciar pruebas reales con restaurantes.

## Test principal

```powershell
python TESTS\test_host_ai_3_0_stable.py
```

## Bloques validados

- 3.0.4 Inteligencia de Compras
- 3.0.5 Gestión Inteligente del Stock
- 3.0.6 Producción
- 3.0.7 Escandallos Inteligentes
- 3.0.8 IA Conversacional

## Criterio de OK

El test debe terminar mostrando:

```text
TEST OK - Host AI 3.0 Stable Candidate
```

Si falla un bloque, el test indica exactamente qué test combinado ha fallado.
