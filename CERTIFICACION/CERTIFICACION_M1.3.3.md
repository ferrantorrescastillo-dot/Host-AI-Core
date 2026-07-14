# CERTIFICACIÓN M1.3.3

## Estado
CANDIDATO A CERTIFICACIÓN REAL

## Resultado automatizado
- Tests específicos: 8/8 superados.
- Regresión total relacionada: 82/82 superados.
- Compilación de consola y servicios: correcta.
- Escrituras en datos reales: 0.

## Caso coherente
Parmentier de patata, 10 raciones, 4 materias primas, elaboración, tiempo, conservación y alérgenos revisados.

Resultado esperado:
- errores: 0;
- estado: REVISAR;
- único aviso: coste incompleto por artículo sin precio;
- coste conocido por ración calculado.

## Caso adverso
- patata con cantidad cero;
- `A.P Briox...` forzado como ingrediente;
- mantequilla expresada en litros;
- elaboración insuficiente y documentación incompleta.

Resultado esperado:
- estado BLOQUEADA;
- error por cantidad no positiva;
- error por `A.P` usado como materia prima;
- avisos explicables para el resto.

## Criterio de cierre
M1.3.3 quedará certificado cuando el diagnóstico real muestre `Diagnóstico: OK` y reproduzca la diferenciación entre errores y avisos sin modificar catálogos reales.
