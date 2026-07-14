# Auditoría funcional Host AI 6.0 — Preparación del piloto interno

## 1. Resumen ejecutivo

Host AI 6.0 no es un prototipo vacío. El ZIP contiene 2.557 archivos, 1.003 módulos Python, más de 300 servicios y 339 archivos de pruebas. Los datos reales ya incluyen 359 artículos, 16 escandallos, 7 menús importados, 4 eventos, 24 proveedores, 1 plan de producción y registros de stock y compras.

La conclusión principal es que el proyecto dispone de aproximadamente el 75–80 % de los motores necesarios para un piloto interno, pero solo alrededor del 50–60 % del flujo diario está integrado y listo para utilizarse sin supervisión técnica.

El principal riesgo no es la falta de funciones. Es la acumulación de rutas históricas, módulos paralelos, tests dependientes de archivos externos y algunos contratos incompatibles entre versiones.

## 2. Estado técnico comprobado

- Compilación de APP, CORE, SERVICIOS, MOTORES, PIPELINES y MODELOS: correcta.
- Tests recogidos: 270 antes de fallos de colección.
- Ejecución parcial amplia: 252 pruebas superadas y 18 fallidas.
- De esas 18 fallidas, 15 dependen de Excel externos ausentes y 3 pertenecen a una rotura real de continuidad conversacional antigua.
- Además existen 4 errores de colección:
  - lanzador manual 6.0.3 inexistente;
  - dos tests antiguos que esperan `gestor_contexto_5410` en un orquestador que ya no lo expone;
  - paralelización de producción importa utilidades privadas que ya no existen.

## 3. Datos operativos disponibles

- Artículos: 359.
- Recetas/escandallos operativos: 16.
- Menús: 7.
- Eventos: 4.
- Planes de producción: 1.
- Proveedores: 24.
- Necesidades de compra: 2.
- Pedidos de compra: 2.
- Lotes de stock: 5.
- Movimientos de stock: 6.

Esto es suficiente para empezar un piloto controlado, pero no para afirmar todavía que el sistema refleja fielmente el stock y la operativa diaria completa del restaurante.

## 4. Estado por área

### Artículos y proveedores — 85 %

Muy avanzados: búsqueda, altas, edición, códigos, familias, proveedores e importación. Para el piloto falta consolidar una única ruta oficial de alta/edición y verificar que factura, stock y escandallos usan la misma identidad de artículo.

### Recetas y escandallos — 80 %

La infraestructura es sólida: importación, resolución de ingredientes, validación culinaria y costes. Falta completar más recetas reales y comprobar que los 7 menús importados pueden calcularse con referencias válidas.

### Menús e importadores — 95 %

La línea I1.3 está terminada y certificada. Es la parte más madura del proyecto.

### Stock — 70 %

Existen entradas, salidas, lotes, caducidad, FIFO y stock mínimo. Falta una carga inicial real y un procedimiento diario simple para ajustes, mermas y conteo.

### Compras y recepción — 75 %

Existen necesidades, pedidos, recepción, históricos y motores de inteligencia. Falta certificar el recorrido único `pedido → recepción/factura → stock → precio → escandallos`.

### Facturas y documentos — 70 %

Hay una cadena extensa de lectura PDF/OCR, líneas, relación de artículos, precios y stock. Es una de las mejores candidatas para convertirse en el primer flujo real del piloto. Falta integrarla en la consola principal y certificarla con 3–5 facturas reales del restaurante.

### Eventos — 70 %

CRUD, ficha, servicios, materiales y costes están presentes. Falta conectar de forma estable un evento con los menús importados y convertirlo en producción real.

### Producción — 70 %

Existen planes, reparto entre cocineros, recursos, seguimiento, optimización y checklist. Hay una rotura histórica en paralelización y todavía debe certificarse con un evento real completo.

### IA conversacional — 60 % para piloto

Tiene mucho desarrollo y contexto persistente, pero existen contratos históricos rotos en el bloque 5.4.1.x. Para el piloto no debe ser crítica: se puede probar como capa de consulta, no como único modo de operar.

### Experiencia de uso — 45 %

La consola principal funciona y reúne eventos, stock, compras, escandallos, costes, producción e importaciones. Sin embargo, hay demasiadas opciones técnicas y diagnósticos. Para un piloto hace falta un modo operativo reducido y diario.

## 5. Riesgos principales

1. **Demasiadas versiones acumuladas dentro del mismo ZIP.** Hay carpetas de versiones y módulos históricos que pueden confundir pruebas e imports.
2. **Contratos duplicados o antiguos.** Especialmente en IA contextual y producción paralela.
3. **Tests ligados a rutas absolutas externas.** Esto impide una certificación reproducible en otro equipo.
4. **JSON como almacenamiento operativo principal.** Es válido para el piloto privado, pero exige backup y un único escritor por flujo.
5. **Catálogo real aún incompleto.** Menús importados contienen referencias pendientes o corregidas parcialmente.
6. **No existe todavía un único flujo diario.** Los motores están, pero el cocinero debe navegar por módulos separados.

## 6. Qué falta exactamente antes del piloto

No hacen falta 30 sprints. Recomiendo 8 sprints cortos y enfocados.

### PILOTO-0.1 — Estabilización de la línea base

- Elegir un único `main.py` y una única consola oficial.
- Excluir carpetas históricas del runtime y de pytest.
- Corregir los 4 errores de colección.
- Sustituir rutas externas de Excel por fixtures incluidos en el proyecto.
- Generar una certificación reproducible.

### PILOTO-0.2 — Modo Piloto

Crear un menú reducido:

1. Apertura del día.
2. Registrar factura/albarán.
3. Crear o abrir evento.
4. Generar producción.
5. Generar compras.
6. Cerrar día.

Sin diagnósticos ni opciones técnicas visibles.

### PILOTO-1 — Factura real de proveedor

Con 3–5 facturas reales:

`PDF/foto → líneas → artículos → revisión → precios → stock → histórico → escandallos afectados`.

Este debería ser el primer flujo operativo porque se usa continuamente y ya tiene muchos motores construidos.

### PILOTO-2 — Stock inicial y rutina diaria

- Importar/consolidar stock inicial real.
- Entrada por recepción.
- Salida por producción.
- Merma y ajuste manual.
- Alertas de mínimos.
- Conteo rápido al cierre.

### PILOTO-3 — Evento real con menú importado

- Crear un evento real.
- Elegir uno de los 7 menús.
- Definir pax, fecha, pases y restricciones.
- Ver coste y rentabilidad provisional.

### PILOTO-4 — Evento → necesidades de producción

- Multiplicar recetas por pax y rendimiento.
- Agrupar elaboraciones compartidas.
- Identificar recetas o datos faltantes.
- Generar una lista de producción verificable.

### PILOTO-5 — Producción → stock → compras

- Restar stock disponible.
- Generar faltantes.
- Agrupar por proveedor.
- Crear pedido borrador.
- No enviar nada automáticamente.

### PILOTO-6 — Plan diario de cocina

- Prioridades.
- Asignación a cocineros.
- Tiempos activos/pasivos.
- Recursos.
- Checklist y pendientes.

### PILOTO-7 — Cierre y aprendizaje del piloto

- Registrar lo terminado y lo pendiente.
- Coste real vs previsto.
- Incidencias.
- Cambios necesarios.
- Informe semanal de mejora.

## 7. Orden recomendado

1. PILOTO-0.1 Estabilización.
2. PILOTO-0.2 Modo Piloto.
3. PILOTO-1 Facturas reales.
4. PILOTO-2 Stock real.
5. PILOTO-3 Evento real.
6. PILOTO-4 Producción necesaria.
7. PILOTO-5 Compras.
8. PILOTO-6 Plan diario.
9. PILOTO-7 Cierre y aprendizaje.

## 8. Cuándo empezar a usarlo en el restaurante

No hace falta esperar a completar todo. El piloto puede empezar por fases:

- Tras PILOTO-1: usar Host AI para revisar facturas y precios.
- Tras PILOTO-2: usarlo también para stock.
- Tras PILOTO-4: probar un evento real en paralelo con el método habitual.
- Tras PILOTO-6: utilizarlo durante una jornada completa, manteniendo el sistema manual como respaldo.

Nunca recomiendo sustituir de golpe el método actual. Durante las primeras 2–4 semanas debe trabajar en paralelo y comparar resultados.

## 9. Recomendación final

El primer sprint debe ser **PILOTO-0.1 — Estabilización de la línea base**. No añade una función comercial, pero evita construir el piloto sobre una base con imports y tests históricos rotos.

Después, el primer flujo funcional debe ser **PILOTO-1 — Factura real de proveedor**, porque:

- ya está muy avanzado;
- aporta utilidad diaria inmediata;
- alimenta artículos, precios, stock, proveedores y escandallos;
- prepara los datos necesarios para producción y compras.

La página web, multiempresa, permisos y SaaS deben quedar fuera de esta etapa.
