# CERTIFICACIÓN M1.3 — Resolutor de recetas (núcleo)

Estado: **CERTIFICADO PARA PRUEBA REAL**

## Resultado
- Tests M1.3: 8/8.
- Regresión M1.1 + M1.2 + I1.3 + M1.3: 60/60.
- Compilación: correcta.
- Diagnóstico aislado: estado CERRADO.
- Catálogo real `DATOS/db/escandallos.json`: huella idéntica antes/después.

## Alcance certificado
- búsqueda por nombre;
- vínculo de receta completa;
- alta manual con rendimiento e ingredientes reales;
- validación de artículos existentes;
- prevención de duplicados;
- backup y escritura atómica;
- coste básico por rendimiento;
- aprendizaje sugerido, auditoría y reanudación.

## Exclusiones
Texto, Word, PDF, Excel, documentos y conflictos anidados quedan fuera hasta M1.3.1/M1.3.2.
