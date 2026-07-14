# Host AI 4.1.3 — Generador de Códigos Internos de Artículos

## Objetivo

Crear códigos internos estables para todos los artículos del restaurante.

## Regla principal

```text
Si Codigo está vacío:
    generar ART000001, ART000002, ART000003...

Si Codigo ya existe:
    respetarlo

Si Codigo está duplicado:
    respetarlo pero marcar revisión
```

## Por qué es importante

El cocinero busca por nombre, pero Host AI debe trabajar internamente con un ID estable.

Así evitamos problemas como:

```text
Tomate cherry
Tomate cherri
Cherry tomate
```

Todos pueden buscarse por nombre, pero por dentro Host AI usará un código único.

## Comando de prueba

```powershell
python TESTS\test_413_generador_codigos_articulos.py
```

## Comando con Excel real

```powershell
python APP\generar_codigos_articulos_413.py "C:\Proyecto Host IA 3.0\DATOS\Escandallos Boronat  (HostIA).xlsx"
```

El Excel original no se modifica.

Se genera una copia con:

```text
Codigos 4.1.3
Resumen 4.1.3
```
