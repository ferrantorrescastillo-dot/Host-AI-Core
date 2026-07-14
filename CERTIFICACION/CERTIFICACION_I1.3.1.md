# Certificación I1.3.1 — Detector limpio de menús

## Estado
**CERTIFICADO PARA PRUEBA DEL USUARIO**

## Alcance certificado
- Vista previa exclusivamente en modo lectura.
- Sin vinculación de recetas.
- Sin importación de menús.
- Sin escrituras en base de datos.
- Clasificación previa de filas.
- Lectura económica por cabeceras detectadas.

## Caso oficial probado
Archivo externo del usuario: `Escandallos Boronat.xlsx`  
Hoja: `MENU BODA 31-1`

Resultado:
- Menús: 1
- Platos: 12
- Artículos directos: 1
- Complementos: 1
- Secciones: 6
- Ruido: 0
- Precio de venta: 75.0 €
- Venta neta: 67.5 €
- Coste total: 8.867970689655172 €
- Food cost: 11.823960919540228 %
- Beneficio: 66.13202931034483 €

## Tests
- Tests I1.3.1: OK.
- Regresión I1.3 legacy: OK.
- Cadena I1.1 + I1.2 + I1.3 + I1.3.1: **11 superados, 0 fallos**.

## Incidencias preexistentes fuera de alcance
La ejecución global `pytest -q` del ZIP original no puede completar la colección por cuatro incidencias ajenas a I1.3.1:
1. Falta `SERVICIOS.lanzador_host_ai_base_603` en una copia interna `HOST_AI_6.0.3_MODO_MANUAL_OPERATIVO`.
2. Dos tests 5.4.1.x esperan `gestor_contexto_5410` en un orquestador que no lo expone.
3. Un test 5.5.6e4 importa `_hora` desde un módulo que no la exporta.

No se han corregido porque pertenecen a otros módulos y hacerlo mezclaría sprints certificados.

## Archivos del sprint
- `SERVICIOS/detector_limpio_menus_i131.py`
- `APP/consola.py`
- `TESTS/test_i131_detector_limpio_menus.py`
- `CHANGELOG_I1.3.1.md`
- `LEEME_I1.3.1.txt`
- `CERTIFICACION/CERTIFICACION_I1.3.1.md`
