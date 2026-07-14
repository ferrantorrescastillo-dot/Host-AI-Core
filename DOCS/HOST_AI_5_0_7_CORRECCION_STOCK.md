# Host AI 5.0.7 - Corrección Stock Clasificador

Corrige la confianza baja en consultas de stock con artículo en medio, por ejemplo:

- ¿Cuánto arroz bomba tengo?
- ¿Cuánto queda de gambón?
- ¿Tengo suficiente pollo?
- Hay arroz suficiente para mañana?

No añade módulos nuevos. Solo ajusta el clasificador 5.0.7.

## Prueba

```powershell
python -m TESTS.test_507_reforzador_clasificador
python -m APP.beta_conversacional_qa_506
```
