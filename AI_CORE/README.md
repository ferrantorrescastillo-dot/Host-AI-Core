# AI_CORE v1

Subsistema independiente de solo lectura para preparar contexto documental de Host AI para agentes de IA.

## Alcance

- Detecta la raíz del proyecto sin rutas absolutas.
- Descubre documentación oficial relevante.
- Clasifica cada documento por categoría y dominios.
- Construye un manifiesto determinista.
- Genera un paquete de contexto en Markdown resumido y trazable.

## Seguridad

- No modifica documentación original.
- No accede ni escribe en `DATOS/db`.
- No llama APIs externas.
- No usa dependencias externas (solo biblioteca estándar).

## Ejecución

Desde la raíz del proyecto:

```bash
python -m AI_CORE.cli --domain general
python -m AI_CORE.cli --domain produccion --output TEMP/ai_context_produccion.md
python -m AI_CORE.cli --domain stock --output TEMP/ai_context_stock.md
```

Salida por defecto:

- `TEMP/ai_context.md`
- `TEMP/ai_context_manifest.json`
