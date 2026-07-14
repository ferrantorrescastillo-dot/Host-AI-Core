# HOST AI — Estándar de Desarrollo RC1

## Objetivo

Este documento define las reglas técnicas mínimas para seguir desarrollando Host AI sin romper la arquitectura existente.

Host AI no debe crecer como scripts sueltos. Cada nueva función debe integrarse de forma controlada en la arquitectura actual.

---

## Regla principal

Todo módulo nuevo debe tener, como mínimo:

1. Modelo si transporta datos propios.
2. Servicio con la lógica real.
3. Pipeline que conecte el servicio con Host AI Core.
4. Registro en el sistema de pipelines.
5. Test individual.
6. Test de integración si pertenece a un bloque mayor.
7. Documentación o changelog.

---

## Estructura obligatoria

### MODELOS

Los modelos deben contener datos, no lógica pesada.

Permitido:

- dataclasses
- estructuras de entrada
- estructuras de salida
- informes
- alertas
- recomendaciones

No permitido:

- cálculos complejos
- acceso a archivos
- llamadas a servicios
- lógica de negocio pesada

---

### SERVICIOS

Los servicios contienen la lógica de negocio.

Un servicio debe:

- recibir datos claros
- procesar la lógica
- devolver modelos o diccionarios estructurados
- no depender directamente de la interfaz
- no imprimir salvo que sea estrictamente necesario

Un servicio no debería:

- modificar el Core
- registrar pipelines
- depender de PowerShell
- pedir input interactivo

---

### PIPELINES

Los pipelines conectan Host AI con los servicios.

Un pipeline debe:

- recibir una SolicitudPipeline
- llamar a un servicio
- devolver ResultadoPipeline
- controlar errores básicos
- no contener lógica pesada

El pipeline no debe sustituir al servicio.

---

### CORE

El Core debe coordinar, no calcular.

Debe encargarse de:

- crear servicios principales
- registrar pipelines
- exponer ejecución común
- mantener el sistema centralizado

No debe convertirse en un archivo donde se programe toda la lógica.

---

### ORQUESTADOR

El orquestador decide qué pipeline ejecutar.

Debe trabajar con:

- intención
- contexto
- entidades detectadas
- pipeline recomendado

No debe hacer cálculos de negocio.

---

## Reglas de tests

Todo cambio debe pasar al menos:

```powershell
python TESTS\test_host_ai_3_0_stable.py
```

Si se modifica un bloque concreto, también debe ejecutarse su test combinado.

Ejemplos:

```powershell
python TESTS\test_inteligencia_compras_3041_3042_3043_3044_3045_3046_3047_3048.py
python TESTS\test_gestion_inteligente_stock_3051_3052_3053_3054_3055_3056_3057_3058.py
python TESTS\test_produccion_3061_3062_3063_3064_3065_3066_3067_3068.py
python TESTS\test_escandallos_inteligentes_3071_3072_3073_3074_3075_3076_3077_3078.py
python TESTS\test_ia_conversacional_3081_3082_3083_3084_3085_3086_3087_3088.py
```

---

## Regla de cambios pequeños

No modificar muchos archivos a la vez salvo que sea imprescindible.

Preferencia:

- 1 a 3 archivos por parche.
- Parche pequeño.
- Test inmediato.
- Validación en PowerShell.

---

## Regla de documentación

Cada cambio relevante debe documentarse en:

- changelog
- documento técnico
- comentario interno si afecta arquitectura

---

## Regla de compatibilidad

No eliminar funciones antiguas sin comprobar:

- qué tests las usan
- qué pipelines las llaman
- si pertenecen a módulos legacy
- si pueden afectar a datos reales

---

## Regla para piloto con restaurantes

Antes de usar Host AI en un restaurante real:

1. Ejecutar test stable.
2. Revisar datos de prueba.
3. Usar copia de seguridad.
4. No escribir sobre datos reales sin confirmación.
5. Registrar errores y feedback.

---

## Conclusión

Host AI debe crecer como un producto profesional:

- modelos para datos
- servicios para lógica
- pipelines para conexión
- core para coordinación
- tests para validar
- documentación para mantener

Este estándar queda como referencia obligatoria para RC1 y siguientes versiones.
