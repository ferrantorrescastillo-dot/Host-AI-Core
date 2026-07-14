# CHANGELOG — I1.3.2.1 Motor de reconocimiento

## Añadido
- `SERVICIOS/motor_reconocimiento_menus_i1321.py`.
- Carga en solo lectura de `escandallos_canonicos.json` y `articulos.json`.
- Reconocimiento exacto completo de recetas para impedir fragmentaciones incorrectas.
- Mapa de coincidencias exactas parciales con posición por tokens.
- Candidatos probables únicamente cuando no existe coincidencia exacta.
- Preservación prioritaria de recetas frente a artículos solapados.
- Vista previa encadenada con I1.3.1.
- Opción 12 en Excel / Importaciones.

## Garantías
- No determina receta principal, salsa, elaboración o guarnición.
- No importa menús.
- No modifica recetas, artículos ni base de datos.
- I1.3.1 y el importador legacy permanecen operativos.
