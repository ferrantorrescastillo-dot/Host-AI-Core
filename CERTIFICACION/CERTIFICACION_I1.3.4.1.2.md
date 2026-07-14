# CERTIFICACIÓN I1.3.4.1.2

## Estado
APTO PARA PRUEBA REAL DEL USUARIO.

## Pruebas automatizadas
- Regresión completa I1.3 + M1.1–M1.3.3 + I1.3.4.1/.1.1/.1.2: 112 superadas.
- Fallos: 0.

## Prueba con Escandallos Boronat.xlsx
- Hojas: 21.
- Menús seleccionados: 11.
- Elementos clasificados: 158.
- Acciones: 253.
- Ejecutables: 237.
- Bloqueadas: 16.
- Relaciones de bebida: 13.
- Identificadores de acción duplicados: 0.
- Archivos de negocio modificados: 0.

## Casos verificados
- Pan de cristal con jamón sigue siendo receta.
- CLOS PINELL se clasifica como vino.
- CAVA ROGER DE FLOR se clasifica como cava.
- Agua Font Vella se clasifica como agua.
- Caña de cerveza se clasifica como bebida y no genera conflictos `caña`/`cerveza`.
- A.P se clasifica como aperitivo preparado.
- M.P se clasifica como materia prima.
- POR PAX y MENU CALÇOTADA no se convierten en componentes culinarios.
- POSTRES duplicado se deduplica.
