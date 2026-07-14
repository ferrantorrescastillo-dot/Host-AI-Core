# CERTIFICACIÓN I1.3.2.1 — Motor de reconocimiento

## Alcance certificado
- Reconocimiento exacto completo de recetas.
- Preservación de recetas completas sin fragmentarlas.
- Reconocimiento de varias entidades conocidas dentro de un plato compuesto.
- Reconocimiento de artículos existentes.
- Carga real desde el catálogo canónico de Host AI.
- Encadenamiento con la salida limpia de I1.3.1.
- Operación exclusivamente en modo lectura.

## Pruebas automáticas
Comando:

`python -m pytest -q TESTS/test_i131_detector_limpio_menus.py TESTS/test_i1321_motor_reconocimiento.py TESTS/test_i13_importador_menus_legacy.py`

Resultado: **10 superados, 0 fallos**.

## Prueba manual con Excel oficial
Archivo: `Escandallos Boronat.xlsx`
Hoja: `MENU BODA 31-1`

El motor procesó los 12 platos limpios y generó coincidencias usando el catálogo de
la copia auditada. Las huellas SHA-256 de recetas y artículos fueron idénticas antes
y después de ejecutar el reconocimiento.

## No regresión global
La suite completa no llega a ejecutarse por cuatro errores preexistentes de colección:
1. Módulo ausente `lanzador_host_ai_base_603` en una copia interna 6.0.3.
2. Dos tests 5.4.1.x esperan `gestor_contexto_5410` no disponible.
3. Un test 5.5.6E4 importa `_hora` desde un módulo que no lo expone.

No se modificaron esos módulos porque quedan fuera del alcance del sprint.

## Estado
**CERTIFICADO TÉCNICAMENTE PARA PRUEBA REAL DEL USUARIO.**
La certificación funcional definitiva se cierra al validar la salida en la instalación
actual del usuario, que contiene las recetas importadas más recientes.
