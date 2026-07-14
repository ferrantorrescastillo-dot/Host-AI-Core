# HOST AI 5.5.5B — Parte 5

## Objetivo

Convertir las fichas depuradas de la Parte 4 al modelo canónico 5.5.5A y realizar una importación controlada.

## Funciones

- Convierte únicamente fichas marcadas como `PREPARADA`.
- Omite títulos inválidos y fichas pendientes de revisión.
- Evita importar dos veces duplicados exactos.
- No decide automáticamente entre variantes con el mismo nombre.
- Relaciona ingredientes con `DATOS/db/articulos.json` mediante coincidencia exacta o evidencia muy alta.
- Conserva candidatos cuando la relación no es inequívoca.
- Compara con `DATOS/db/escandallos_canonicos.json` y clasifica cada ficha como:
  - `CREAR`
  - `ACTUALIZAR`
  - `SIN_CAMBIOS`
  - `OMITIR`
- Genera códigos estables basados en nombre, hoja y fila de origen.
- La vista previa es el modo predeterminado.
- La escritura exige `--confirmar`.
- Si ya existe una base canónica, crea una copia de seguridad antes de escribir.

## Prueba técnica

```powershell
python TESTS/test_555b_parte5.py
```

## Vista previa con el Excel real

```powershell
python APP/preimportar_escandallos_555b.py "C:\ruta\Escandallos.xlsx" --informe "DATOS\informes\preimportacion_555b.json"
```

## Importación confirmada

Revisa primero el informe. Después:

```powershell
python APP/preimportar_escandallos_555b.py "C:\ruta\Escandallos.xlsx" --confirmar --informe "DATOS\informes\importacion_555b.json"
```

## Seguridad

No se modifica el Excel. Sin `--confirmar`, tampoco se modifica la base interna. Las variantes ambiguas se dejan pendientes de revisión.
