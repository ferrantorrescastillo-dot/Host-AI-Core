# Host AI 5.5.5A — Parte 2

Añade la capa de persistencia y validación del modelo canónico creado en la Parte 1.

## Archivos

- `SERVICIOS/schema_escandallos_555a.py`: versión de esquema y normalización de unidades.
- `SERVICIOS/validador_escandallos_555a.py`: valida ingredientes, recetas, escandallos, menús y duplicados.
- `SERVICIOS/repositorio_escandallos_555a.py`: repositorio JSON con lectura, búsqueda y escritura atómica.
- `DATOS/esquemas/escandallo_canonico_555a.schema.json`: contrato documental JSON Schema.
- `TESTS/test_555a_parte2.py`: prueba de validación, alta, actualización y búsquedas.

## Seguridad

- No toca `DATOS/db/escandallos.json` antiguo.
- Por defecto usa `DATOS/db/escandallos_canonicos.json`.
- No guarda entidades inválidas.
- La escritura se realiza mediante archivo temporal y reemplazo atómico.

## Prueba

Desde la raíz del proyecto, tras instalar también la Parte 1:

```powershell
python TESTS/test_555a_parte2.py
```

Resultado esperado:

```text
TEST OK 5.5.5A PARTE 2 - Repositorio, schema y validación
```
