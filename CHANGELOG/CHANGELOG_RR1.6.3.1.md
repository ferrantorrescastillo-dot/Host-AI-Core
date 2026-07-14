# RR1.6.3.1 — Hotfix del ejecutor de certificación

## Corregido

- `TESTS/test_rr163_ejecutor_certificacion.py` construía por error la ruta:
  `TESTS/ejecutar_certificacion_rr163.py`.
- Ahora resuelve correctamente el ejecutor en la raíz del proyecto:
  `ejecutar_certificacion_rr163.py`.

## Validación

```text
2 passed
0 failed
```
