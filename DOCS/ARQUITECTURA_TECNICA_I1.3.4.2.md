# I1.3.4.2 — Arquitectura técnica

Este sprint introduce el motor de persistencia segura que será utilizado por I1.3.4.3.

Flujo: validar rutas → backup → escritura atómica → verificación → commit. Ante cualquier error: rollback → restauración → verificación de integridad.

El motor no interpreta menús ni resuelve conflictos. Solo aplica cambios previamente validados y limita las escrituras a una lista blanca explícita.
