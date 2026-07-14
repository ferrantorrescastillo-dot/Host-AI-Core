# PILOTO-0.1 — Estabilización de la línea base

## Objetivo

Dejar un único punto de entrada oficial y separar la operativa privada del restaurante de las herramientas técnicas acumuladas durante el desarrollo.

## Cambios

- `main.py` pasa a ser el único arranque oficial de la línea piloto.
- Nuevo lanzador `SERVICIOS/lanzador_piloto_01.py`.
- Nuevo `Modo Piloto privado` con menú operativo reducido.
- El modo desarrollo conserva la consola, conversación, diagnósticos y herramientas existentes.
- Configuración y rutas del piloto centralizadas en `SERVICIOS/configuracion_piloto_01.py`.
- Auditoría reproducible de arranque.
- Inventario automático de módulos: ACTIVO, PRUEBA, LEGACY, SOPORTE e HISTÓRICO.
- Certificación de solo lectura con informes JSON/TXT.
- Recuperación del lanzador 6.0.3 que estaba aislado dentro de una carpeta histórica.

## Seguridad

- No se eliminan archivos históricos.
- No se migran ni modifican catálogos de negocio.
- La certificación compara huellas de artículos, recetas y menús antes y después.
