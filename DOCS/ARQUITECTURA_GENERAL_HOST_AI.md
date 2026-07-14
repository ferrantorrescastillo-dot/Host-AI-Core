# Host AI — Arquitectura General

**Versión documental:** RC1.3  
**Objetivo:** dejar documentado cómo funciona Host AI por dentro antes de avanzar hacia una versión RC1 preparada para piloto real.

---

## 1. Qué es Host AI

Host AI es un sistema operativo inteligente para cocina profesional, restaurantes, caterings y hoteles.

No está planteado como un chatbot ni como una herramienta aislada. Está pensado como un segundo jefe de cocina digital capaz de conectar compras, stock, producción, escandallos, rentabilidad e IA conversacional.

La IA no debe sustituir la lógica del sistema. La IA debe servir como interfaz para entender al usuario, interpretar su intención y activar los motores internos adecuados.

---

## 2. Qué NO es Host AI

Host AI no debe ser:

- Un chatbot sin control sobre datos reales.
- Un Excel con frases bonitas.
- Un conjunto de scripts sueltos.
- Un ERP genérico sin criterio gastronómico.
- Un sistema que dependa de que GPT “invente” decisiones.

Host AI debe tomar decisiones basadas en sus propios datos, modelos, servicios y pipelines.

---

## 3. Principio arquitectónico principal

La arquitectura se basa en una separación clara de responsabilidades:

```text
Usuario / Cocina / Restaurante
        ↓
APP / Interfaz
        ↓
Director Host AI
        ↓
HostAI Core
        ↓
Orquestador
        ↓
Registro de Pipelines
        ↓
Pipeline concreto
        ↓
Servicio de negocio
        ↓
Modelo de datos
        ↓
DATOS / Históricos / Base operativa
```

Cada capa debe tener una responsabilidad concreta y no invadir la capa siguiente.

---

## 4. Capas del sistema

### 4.1 APP

La carpeta `APP` debe contener la capa de entrada del usuario.

Responsabilidad:

- Mostrar menús.
- Recibir órdenes.
- Lanzar acciones.
- Mostrar resultados.

No debería contener lógica pesada de negocio.

---

### 4.2 CORE

La carpeta `CORE` es el núcleo del sistema.

Responsabilidad:

- Inicializar Host AI.
- Registrar pipelines.
- Coordinar la ejecución.
- Conectar Director, Orquestador y Registro.

Archivos principales:

```text
CORE/host_ai_core.py
CORE/orquestador.py
CORE/registro_pipelines.py
CORE/director_host_ai.py
```

Regla:

> CORE coordina, pero no debería calcular lógica de negocio.

---

### 4.3 MODELOS

La carpeta `MODELOS` contiene estructuras de datos.

Responsabilidad:

- Solicitudes.
- Resultados.
- Informes.
- Alertas.
- Predicciones.
- Decisiones.

Regla:

> Los modelos transportan datos. No deben contener lógica pesada.

Modelos clave:

```text
SolicitudPipeline
ResultadoPipeline
```

Estos dos modelos son la base común para que todo Host AI hable el mismo idioma.

---

### 4.4 SERVICIOS

La carpeta `SERVICIOS` contiene la lógica de negocio.

Responsabilidad:

- Analizar compras.
- Comparar proveedores.
- Controlar stock.
- Planificar producción.
- Calcular escandallos.
- Interpretar conversación.
- Generar respuestas.

Regla:

> Los servicios calculan. No deben depender directamente de la interfaz.

---

### 4.5 PIPELINES

La carpeta `PIPELINES` contiene la capa de ejecución estándar.

Responsabilidad:

- Recibir una `SolicitudPipeline`.
- Preparar datos.
- Llamar al servicio correspondiente.
- Devolver un `ResultadoPipeline`.

Regla:

> Un pipeline orquesta una acción concreta, pero no debería convertirse en un servicio gigante.

---

### 4.6 DATOS

La carpeta `DATOS` contiene la base operativa del sistema.

Responsabilidad:

- Artículos.
- Stock.
- Compras.
- Históricos.
- Precios.
- Producción.
- Escandallos.

Regla:

> Los datos deben ser la fuente de verdad del sistema.

A largo plazo, esta capa debería evolucionar progresivamente hacia una base de datos robusta, empezando por SQLite.

---

### 4.7 TESTS

La carpeta `TESTS` valida que el sistema funciona.

Responsabilidad:

- Probar módulos individuales.
- Probar bloques completos.
- Probar Stable Candidate.
- Evitar regresiones.

Regla:

> Si el test estable falla, no se avanza.

Test principal actual:

```powershell
python TESTS\test_host_ai_3_0_stable.py
```

---

## 5. Bloques funcionales de Host AI 3.0

### 5.1 Importación inteligente

Objetivo:

- Leer documentos.
- Interpretar facturas.
- Aplicar OCR.
- Detectar proveedores.
- Extraer líneas.
- Relacionar artículos.

---

### 5.2 Inteligencia de Compras — 3.0.4

Objetivo:

- Analizar compras.
- Generar recomendaciones.
- Detectar anomalías.
- Predecir precios.
- Comparar proveedores.
- Predecir roturas.
- Generar decisiones de pedido.

---

### 5.3 Gestión Inteligente del Stock — 3.0.5

Objetivo:

- Analizar stock.
- Generar alertas.
- Controlar entradas y salidas.
- Reconciliar stock real y teórico.
- Predecir necesidades.
- Optimizar compras y ubicaciones.

---

### 5.4 Producción — 3.0.6

Objetivo:

- Analizar producción.
- Alertar riesgos.
- Planificar elaboraciones.
- Asignar recursos y cocineros.
- Controlar ejecución.
- Replanificar.
- Optimizar producción.

---

### 5.5 Escandallos Inteligentes — 3.0.7

Objetivo:

- Analizar costes.
- Detectar alertas.
- Optimizar recetas.
- Comparar históricos.
- Simular costes.
- Predecir rentabilidad.
- Optimizar carta.

---

### 5.6 IA Conversacional — 3.0.8

Objetivo:

- Entender lenguaje natural.
- Mantener conversación.
- Seleccionar motores.
- Generar respuestas.
- Recordar contexto.
- Automatizar acciones.
- Actuar como asistente operativo.

---

## 6. Flujo completo de restaurante

Ejemplo conceptual:

```text
Llega una factura PDF
        ↓
Importador universal la procesa
        ↓
OCR extrae texto y líneas
        ↓
Se detecta proveedor
        ↓
Se relacionan artículos
        ↓
Se actualizan precios
        ↓
Se actualiza stock
        ↓
Compras detecta anomalías
        ↓
Stock calcula necesidades
        ↓
Producción planifica elaboraciones
        ↓
Escandallos recalculan costes
        ↓
IA Conversacional permite preguntar y actuar
```

---

## 7. Reglas de desarrollo Host AI

### Regla 1 — No scripts sueltos

Todo módulo debe integrarse como:

```text
Modelo + Servicio + Pipeline + Test + Documentación
```

---

### Regla 2 — La lógica va en servicios

Los servicios contienen la lógica de negocio.

Los pipelines solo coordinan.

---

### Regla 3 — Los modelos no calculan

Los modelos deben ser estructuras de datos limpias.

---

### Regla 4 — El Core no debe crecer indefinidamente

Cada vez que el Core crece demasiado, se debe valorar extraer registro automático, catálogos o configuración.

---

### Regla 5 — Toda acción crítica debe tener test

Especialmente:

- Cambios de stock.
- Cambios de precio.
- Creación de pedidos.
- Actualización de escandallos.
- Acciones automatizadas.

---

### Regla 6 — No avanzar si Stable falla

Antes de cualquier cambio importante:

```powershell
python TESTS\test_host_ai_3_0_stable.py
```

Debe terminar en OK.

---

## 8. Estado de madurez por área

| Área | Estado | Comentario |
|---|---:|---|
| Importación | Alta | Base completa, requiere pruebas con documentos reales variados. |
| Compras | Alta | Buen cierre funcional. |
| Stock | Media-Alta | Funciona, pero requiere especial cuidado con datos reales. |
| Producción | Alta | Muy valioso para cocina real. |
| Escandallos | Media-Alta | Muy potente, pero crítico para rentabilidad. |
| IA Conversacional | Alta como capa interna | Lista para pruebas controladas, no para prometer IA externa avanzada todavía. |
| Documentación | Media | Necesita manual central y guía piloto. |
| Producto comercial | Inicial | Falta interfaz, instalación y piloto real. |

---

## 9. Camino hacia Host AI 3.0 RC1

Antes de considerar Host AI 3.0 RC1, deben completarse estos puntos:

1. Mantener test estable global.
2. Corregir o documentar estados `revisar` y `critico`.
3. Limpiar duplicados de carpetas y `__pycache__`.
4. Clasificar tests automáticos y manuales.
5. Documentar instalación piloto.
6. Crear checklist de prueba en restaurante.
7. Definir datos mínimos reales para probar.

---

## 10. Camino hacia Host AI 4.0

Host AI 4.0 debería integrar modelos LLM como capa de lenguaje y razonamiento asistido, pero no como sustituto de los motores internos.

La separación correcta será:

```text
LLM / GPT
  interpreta lenguaje
  resume información
  genera comunicación
  propone opciones

Host AI Core
  valida datos
  ejecuta pipelines
  calcula decisiones
  actualiza stock
  genera pedidos
  protege la coherencia
```

Principio clave:

> GPT conversa. Host AI decide con datos.

---

## 11. Conclusión

Host AI tiene una arquitectura sólida para un proyecto en fase 3.0. La prioridad ahora no es añadir más módulos, sino estabilizar, documentar, limpiar y preparar una prueba real con restaurantes.

El siguiente objetivo técnico debe ser convertir esta arquitectura en una versión RC1 mantenible, verificable y preparada para piloto controlado.
