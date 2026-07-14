# CHANGELOG — RR1.6.3 Limpieza y estabilización

## Correcciones

- El ejecutor ya no lanza `pytest` contra toda la carpeta del proyecto.
- La certificación utiliza una suite oficial declarada en un manifiesto.
- Se excluyen carpetas históricas y tests legacy del alcance oficial.
- Se comprueba que `pytest` esté instalado antes de ejecutar.
- Si falta una prueba oficial, la certificación se detiene y no aprueba parcialmente.
- El informe distingue claramente entre APROBADA, NO APROBADA y NO EJECUTADA.
- Se añade una herramienta opcional y segura para clasificar tests legacy.
- Ningún test antiguo se borra o mueve automáticamente.

## Archivos

- `ejecutar_certificacion_rr163.py`
- `pytest_rr163.ini`
- `CERTIFICACION/suite_oficial_rr163.txt`
- `HERRAMIENTAS/clasificar_tests_legacy.py`
