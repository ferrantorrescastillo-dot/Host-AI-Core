# Host AI 4.1.5.1 — Mejora del Buscador Inteligente de Artículos

## Objetivo

Reducir falsos positivos detectados con datos reales.

Ejemplo de problema anterior:

```text
Buscar: arroz bomba
Resultado incorrecto: Aros metálicos
```

## Cambios

- Si ninguna palabra buscada aparece en el nombre, no se muestra.
- Se sube el umbral mínimo.
- Se priorizan palabras exactas.
- El proveedor se mantiene como filtro secundario.
- Se añade modo diagnóstico.

## Prueba

```powershell
python TESTS\test_4151_buscador_inteligente_articulos_mejorado.py
```

## Uso normal

```powershell
python APP\buscar_articulos_415.py "arroz bomba"
python APP\buscar_articulos_415.py "arroz bomba" "Makro"
```

## Diagnóstico

```powershell
python APP\buscar_articulos_415.py --diagnostico "arroz"
python APP\buscar_articulos_415.py --diagnostico "makro"
```
