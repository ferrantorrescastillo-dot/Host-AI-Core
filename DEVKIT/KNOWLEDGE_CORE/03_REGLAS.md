# HOST AI — 03_REGLAS

> Reglamento oficial del proyecto  
> Estado: Oficial  
> Ámbito: DEVKIT / Memoria viva  
> Versión del documento: 1.0  
> Fecha de creación: 13 de julio de 2026  
> Documento relacionado: `01_IDENTIDAD.md`

---

# 1. PROPÓSITO DE ESTE DOCUMENTO

Este documento define las reglas que deben respetarse durante el diseño, desarrollo, integración, prueba, certificación y uso de Host AI.

`01_IDENTIDAD.md` explica qué es Host AI.

`03_REGLAS.md` establece cómo debe construirse y cómo debe comportarse para no traicionar esa identidad.

Estas reglas deben utilizarse como referencia obligatoria antes de:

- abrir un sprint;
- crear un módulo;
- modificar un motor;
- cambiar una pantalla;
- añadir una automatización;
- integrar inteligencia artificial;
- importar datos;
- escribir sobre stock;
- modificar recetas o escandallos;
- crear nuevas clasificaciones;
- resolver conflictos;
- certificar una funcionalidad.

Cuando una propuesta contradiga estas reglas, debe detenerse y revisarse antes de desarrollarla.

---

# 2. JERARQUÍA DE AUTORIDAD

Las decisiones del proyecto deben seguir este orden de prioridad:

1. Seguridad de los datos y de la operación.
2. Identidad oficial definida en `01_IDENTIDAD.md`.
3. Reglas oficiales de este documento.
4. Decisiones técnicas registradas en la memoria viva.
5. Arquitectura real del código existente.
6. Funcionalidades certificadas.
7. Roadmap vigente.
8. Preferencias de implementación de cada sprint.

Ninguna preferencia menor puede justificar romper una regla superior.

Ejemplo:

Una mejora visual no puede justificar una escritura insegura.

Una automatización no puede justificar perder trazabilidad.

Una nueva IA no puede sustituir un motor determinista ya certificado.

---

# 3. CLASIFICACIÓN DE LAS REGLAS

Las reglas se clasifican en cuatro niveles.

## 3.1 Reglas constitucionales

Definen la identidad del producto.

Solo pueden modificarse mediante una revisión explícita de `01_IDENTIDAD.md` y de este documento.

Ejemplos:

- Host AI debe adaptarse al cocinero.
- Mi Jornada es el centro operativo.
- La IA no sustituye a los motores.
- No se debe duplicar lógica.

## 3.2 Reglas obligatorias

Deben cumplirse en todos los desarrollos.

Solo pueden incumplirse mediante una excepción documentada y aprobada.

Ejemplos:

- validar antes de escribir;
- probar regresión;
- mantener trazabilidad;
- reutilizar motores existentes.

## 3.3 Reglas recomendadas

Representan la opción preferida.

Pueden adaptarse si existe una razón técnica u operativa clara.

Ejemplo:

- preferir edición por nombre frente a edición por código.

## 3.4 Reglas contextuales

Se aplican únicamente a determinados módulos, tipos de dato o flujos.

Ejemplo:

- reglas específicas de artículos `M.P` y `A.P`;
- reglas de recepción;
- reglas de producción;
- reglas de stock.

Toda excepción debe registrarse con:

- regla afectada;
- motivo;
- alcance;
- riesgos;
- alternativa descartada;
- responsable;
- fecha;
- duración prevista;
- plan de reversión.

---

# 4. REGLAS FUNDAMENTALES DE PRODUCTO

## R-PROD-001 — Host AI debe resolver trabajo real

No debe desarrollarse ninguna función que no responda a una situación operativa concreta.

Antes de aprobar una función debe poder completarse esta frase:

> Cuando en cocina ocurre __________, Host AI ayuda a __________.

Si no puede completarse con claridad, la función no está suficientemente definida.

## R-PROD-002 — El usuario no debe pensar en módulos

La arquitectura interna puede estar dividida en módulos, servicios y motores.

La experiencia del usuario debe empezar por hechos reales:

- ha llegado un proveedor;
- he terminado una producción;
- falta producto;
- ha cambiado un evento;
- quiero saber qué hacer hoy;
- necesito preparar una compra.

No debe obligarse al usuario a saber qué subsistema debe abrir.

## R-PROD-003 — Mi Jornada es el centro operativo

Toda información operativa importante debe poder reflejarse en `Mi Jornada`.

Una funcionalidad que genere:

- tareas;
- alertas;
- bloqueos;
- recepciones pendientes;
- compras;
- producciones;
- eventos;
- incidencias;

debe indicar cómo llega a `Mi Jornada`.

## R-PROD-004 — La utilidad diaria tiene prioridad

Una función útil cada día tiene más prioridad que una función espectacular que se usa una vez al mes.

El orden de prioridad será:

1. fiabilidad;
2. claridad;
3. utilidad;
4. velocidad;
5. automatización;
6. sofisticación;
7. apariencia comercial.

## R-PROD-005 — Validar antes de vender

Host AI debe demostrar que funciona en cocina real antes de priorizar:

- SaaS;
- web comercial;
- marketing;
- escalado masivo;
- multiempresa;
- modelos premium complejos.

## R-PROD-006 — El control final es humano

Las decisiones críticas deben poder ser:

- revisadas;
- confirmadas;
- canceladas;
- corregidas;
- auditadas.

Host AI puede recomendar o automatizar, pero no debe ocultar decisiones relevantes al responsable.

## R-PROD-007 — La automatización debe reducir trabajo

Una automatización se considera fallida si:

- añade más pasos que el proceso manual;
- exige registrar datos irrelevantes;
- obliga a corregir constantemente;
- genera dudas;
- requiere comprender lógica técnica.

## R-PROD-008 — No añadir funciones por acumulación

Cada función nueva debe justificar:

- qué problema resuelve;
- quién la usa;
- en qué momento;
- qué dato necesita;
- qué motor reutiliza;
- cómo se prueba;
- cómo se refleja en la jornada.

---

# 5. REGLAS DE DISEÑO OPERATIVO

## R-OP-001 — Empezar por “qué acaba de pasar”

Los flujos deben describirse desde la situación real.

Ejemplos correctos:

- Ha llegado Makro.
- He terminado una tarea.
- Falta un ingrediente.
- El evento ha cambiado.
- No encuentro un artículo.
- Quiero preparar mañana.

Ejemplos incorrectos:

- Ejecutar importador 04.
- Crear movimiento tipo SAL.
- Abrir módulo de incidencias.
- Lanzar pipeline de conciliación.

## R-OP-002 — Respetar el orden real del trabajo

El software no debe imponer un orden administrativo ideal cuando la cocina trabaja de otra manera.

Ejemplo de recepción real:

1. descargar;
2. comprobar;
3. pesar;
4. anotar;
5. firmar;
6. guardar;
7. registrar más tarde.

Host AI debe permitir este flujo.

## R-OP-003 — Permitir trabajo incompleto

El sistema debe admitir:

- tareas pendientes;
- recepciones parciales;
- documentos sin terminar;
- incidencias abiertas;
- stock por actualizar;
- datos provisionales;
- producciones bloqueadas.

No debe forzar falsos cierres.

## R-OP-004 — No confundir “no registrado” con “no ocurrido”

Si una recepción no está registrada, no significa que no haya llegado.

Si el stock no está actualizado, no significa necesariamente que no exista producto.

El sistema debe diferenciar:

- realidad física;
- registro digital;
- dato estimado;
- dato confirmado.

## R-OP-005 — Los bloqueos deben proponer salidas

Nunca debe mostrarse únicamente:

> Error.

Todo bloqueo debe incluir, cuando sea posible:

- qué ocurre;
- por qué puede haber ocurrido;
- qué efecto tiene;
- qué opciones existen;
- cuál recomienda Host AI.

## R-OP-006 — Priorizar según cocina, no solo según números

La prioridad debe considerar:

- fecha del evento;
- duración;
- dependencias;
- tiempos pasivos;
- recursos;
- disponibilidad de personal;
- caducidad;
- conservación;
- urgencia del servicio;
- tareas ya iniciadas;
- bloqueos;
- entregas de proveedores.

## R-OP-007 — Quien empieza, preferentemente termina

En planificación de producción, una elaboración debe mantenerse con el mismo cocinero siempre que sea razonable.

Excepciones:

- relevo;
- ausencia;
- necesidad urgente;
- tareas estandarizadas;
- decisión explícita del responsable.

## R-OP-008 — Los tiempos pasivos liberan capacidad

Reposos, cocciones, fermentaciones, enfriamientos y abatimientos no deben ocupar al trabajador como tiempo activo continuo.

El sistema debe distinguir:

- tiempo activo;
- tiempo pasivo;
- tiempo de recurso;
- tiempo total.

## R-OP-009 — Las dependencias deben ser visibles

Si una tarea bloquea otra, debe explicarse.

Ejemplo:

> Conviene empezar la demi-glace porque la carrillera la necesita para poder terminarse.

## R-OP-010 — La planificación debe aceptar varios días

Si la carga no cabe en una jornada, debe repartirse.

No debe comprimir tiempos de forma irreal para aparentar que todo cabe.

---

# 6. REGLAS DE EXPERIENCIA DE USUARIO

## R-UX-001 — Lenguaje natural

La interfaz debe usar lenguaje comprensible para cocina.

Evitar:

- identificadores;
- nombres de tablas;
- códigos internos;
- valores técnicos;
- mensajes de excepción;
- etiquetas de desarrollador.

## R-UX-002 — Horas y duraciones legibles

Mostrar:

- `4 h 25 min`
- `1 h`
- `35 min`

No mostrar al usuario:

- `265 min`
- `15900 segundos`
- `4.4167 h`

## R-UX-003 — Fechas humanas

Mostrar:

- Hoy
- Mañana
- Dentro de 3 días
- Este evento ya ha pasado

No mostrar:

- Día -2
- T+3
- Delta negativo

## R-UX-004 — Prioridades humanas

Mostrar:

- 🔴 Muy urgente
- 🟠 Conviene hacerlo hoy
- 🟡 Importante
- 🟢 Puede esperar
- ⚪ Sin urgencia conocida

No mostrar únicamente:

- prioridad 90;
- nivel 4;
- score 0.87.

Los valores internos pueden existir, pero no deben ser la única explicación.

## R-UX-005 — Toda recomendación importante debe explicar el motivo

Ejemplo:

> Empieza por esta producción porque necesita cinco horas y el evento es mañana.

## R-UX-006 — El usuario debe saber qué ha pasado

Después de una acción, Host AI debe confirmar:

- qué se ha cambiado;
- qué no se ha cambiado;
- qué queda pendiente;
- dónde puede revisarse.

## R-UX-007 — Las escrituras críticas requieren vista previa

Antes de:

- actualizar stock;
- importar definitivamente;
- cerrar una producción;
- modificar cantidades masivas;
- eliminar registros;
- recalcular costes históricos;

debe mostrarse una vista previa cuando el impacto lo justifique.

## R-UX-008 — Cancelar debe ser seguro

Toda acción crítica debe poder cancelarse antes de escribir.

Cancelar no debe dejar datos parciales.

## R-UX-009 — No sobrecargar la pantalla

La pantalla principal debe mostrar primero:

- lo urgente;
- la siguiente acción;
- los avisos;
- el resumen.

El detalle técnico debe quedar detrás de opciones secundarias.

## R-UX-010 — La interfaz debe guiar sin infantilizar

Debe ser clara, profesional y directa.

No debe usar un tono excesivamente juguetón ni paternalista.

## R-UX-011 — Los iconos complementan, no sustituyen

Un icono debe ir acompañado de texto.

Nunca depender únicamente del color o del emoji para comunicar un estado.

## R-UX-012 — No exigir memorizar códigos

La edición y búsqueda debe realizarse principalmente por nombre.

Los códigos pueden mostrarse como apoyo, no como requisito.

---

# 7. REGLAS DE ARTÍCULOS Y CLASIFICACIÓN

## R-ART-001 — Buscar primero por nombre

La búsqueda principal de artículos debe priorizar:

1. coincidencia exacta por nombre;
2. nombres normalizados;
3. nombres parecidos;
4. alias;
5. proveedor como filtro secundario;
6. código interno como vía técnica.

## R-ART-002 — Mostrar alternativas parecidas

Si existen varios artículos similares, Host AI no debe elegir silenciosamente sin suficiente confianza.

Debe mostrar opciones y contexto.

## R-ART-003 — El proveedor es vía secundaria

El proveedor puede ayudar a resolver ambigüedades.

No debe sustituir la búsqueda por nombre.

Ejemplo:

> arroz de Makro

debe interpretarse como artículo “arroz” filtrado o contextualizado por proveedor.

## R-ART-004 — Los códigos internos son opcionales para el usuario

Los códigos deben:

- ser únicos;
- ser estables;
- poder generarse;
- servir a integraciones;
- no reemplazar nombres legibles.

## R-ART-005 — Significado de `M.P`

`M.P` significa **Materia Prima**.

Debe interpretarse como producto base susceptible de:

- compra;
- almacenamiento;
- consumo;
- uso como ingrediente;
- transformación.

## R-ART-006 — Significado de `A.P`

`A.P` significa **Aperitivo**.

Un artículo `A.P` debe interpretarse según su ficha como:

- aperitivo;
- elaboración;
- producto compuesto;
- producto terminado;
- preparación intermedia.

No debe interpretarse automáticamente como materia prima base.

## R-ART-007 — No degradar `A.P` a ingrediente simple

Un `A.P` puede aparecer como componente de otra elaboración, pero eso no elimina su naturaleza de producto compuesto.

La importación, clasificación y resolución de conflictos deben conservar esta distinción.

## R-ART-008 — Las familias no sustituyen la función culinaria

Dos artículos de la misma familia pueden tener usos distintos.

La clasificación debe respetar:

- función;
- estado;
- uso;
- unidad;
- ficha;
- receta asociada.

## R-ART-009 — Unidades explícitas

Todo artículo debe indicar su unidad operativa:

- kg;
- L;
- unidad;
- caja;
- bandeja;
- paquete;
- botella;
- otras.

Las equivalencias deben registrarse, no suponerse.

## R-ART-010 — No convertir unidades sin regla

Una caja no puede convertirse a kg sin una equivalencia conocida.

Una unidad no puede convertirse a litros por inferencia.

## R-ART-011 — Alta automática controlada

Si una importación necesita crear un artículo nuevo:

- debe marcarse como alta automática;
- debe quedar visible para revisión;
- puede tener precio 0 provisional;
- no debe inventar proveedor o unidad;
- debe conservar el origen de la creación.

## R-ART-012 — Evitar duplicados semánticos

Antes de crear un artículo debe comprobarse:

- nombre exacto;
- nombre normalizado;
- alias;
- proveedor;
- unidad;
- familia;
- similitud.

---

# 8. REGLAS DE RECETAS, ELABORACIONES Y ESCANDALLOS

## R-REC-001 — Distinguir receta, elaboración y producto

El sistema debe diferenciar:

- materia prima;
- receta;
- elaboración intermedia;
- producto terminado;
- aperitivo;
- componente comprado;
- componente producido.

## R-REC-002 — La ficha técnica es la fuente culinaria

Una ficha técnica debe poder contener:

- nombre;
- rendimiento;
- unidad de rendimiento;
- ingredientes;
- cantidades;
- proceso;
- fases;
- tiempos;
- temperaturas;
- recursos;
- conservación;
- caducidad;
- alérgenos;
- mermas;
- presentación;
- porcionado;
- coste;
- observaciones.

## R-REC-003 — No inventar cantidades faltantes

Si falta una cantidad, debe:

- preguntarse;
- marcarse como pendiente;
- estimarse solo si el usuario lo autoriza;
- conservarse la condición de estimación.

## R-REC-004 — El rendimiento es obligatorio para escalar

No debe escalarse una receta sin conocer:

- rendimiento base;
- unidad;
- cantidad objetivo.

## R-REC-005 — Las mermas deben ser explícitas

Las mermas no deben ocultarse dentro de cantidades sin documentación.

Deben distinguirse:

- merma de limpieza;
- merma de cocción;
- merma de porcionado;
- pérdida extraordinaria.

## R-REC-006 — El escandallo económico no sustituye la receta

La receta describe cómo producir.

El escandallo calcula coste.

Deben estar relacionados, pero no confundidos.

## R-REC-007 — El precio debe tener fecha

Un coste debe poder relacionarse con:

- proveedor;
- fecha;
- compra;
- unidad;
- precio válido.

## R-REC-008 — No sobrescribir históricos

Actualizar un precio no debe destruir el precio anterior.

## R-REC-009 — Edición por nombre

El usuario debe poder editar recetas e ingredientes por nombre.

Los identificadores internos deben mantenerse de forma transparente.

## R-REC-010 — Trazar cambios importantes

Cambios en:

- rendimiento;
- ingredientes;
- cantidades;
- unidades;
- mermas;
- coste;

deben poder auditarse cuando afecten a producción o históricos.

---

# 9. REGLAS DE MENÚS E IMPORTACIÓN CULINARIA

## R-MEN-001 — Interpretar culinariamente

Un texto de menú no debe tratarse como una lista plana.

Debe reconocer:

- secciones;
- aperitivos;
- entrantes;
- platos;
- guarniciones;
- postres;
- bebidas;
- elaboraciones;
- descripciones comerciales.

## R-MEN-002 — No confundir descripción con ingrediente

Una frase comercial no debe importarse automáticamente como ingrediente.

## R-MEN-003 — Resolver con confianza

Las vinculaciones deben distinguir:

- exactas;
- probables;
- ambiguas;
- sin resolver;
- bloqueadas.

## R-MEN-004 — La ambigüedad debe conservarse

Si no existe suficiente confianza, no debe forzarse una relación.

## R-MEN-005 — Escritura segura

La importación definitiva solo puede realizarse después de:

- vista previa;
- resolución;
- validación;
- confirmación;
- backup;
- auditoría.

## R-MEN-006 — La línea I1.3 está cerrada

La línea certificada de importación de menús no debe reabrirse salvo:

- error real;
- incompatibilidad;
- requisito operativo nuevo claramente documentado.

---

# 10. REGLAS DE PRODUCCIÓN

## R-PRODCC-001 — Producción guiada, no técnica

La pantalla debe responder:

- qué hago ahora;
- por qué;
- cuánto queda;
- quién lo hace;
- qué bloquea;
- qué puede hacerse en paralelo.

## R-PRODCC-002 — Estados humanos y técnicos

Puede existir un estado interno normalizado.

La interfaz debe traducirlo:

- pendiente;
- en marcha;
- pausada;
- bloqueada;
- terminada;
- cancelada.

## R-PRODCC-003 — No finalizar sin validar

Antes de cerrar producción debe comprobarse:

- tarea válida;
- cantidad producida;
- receta o relación disponible;
- stock necesario;
- duplicidad;
- permisos;
- trazabilidad.

## R-PRODCC-004 — Producción y stock deben ser transaccionales

El cierre debe evitar estados parciales.

Si falla una escritura crítica, debe revertirse el conjunto cuando sea técnicamente posible.

## R-PRODCC-005 — Protección contra duplicados

Una producción ya registrada no puede volver a consumir stock por error.

## R-PRODCC-006 — Stock insuficiente bloquea el cierre normal

Si falta stock:

- no se descuenta;
- no se añade producto terminado;
- no se marca como cerrada;
- se propone incidencia o resolución.

## R-PRODCC-007 — El forzado debe ser explícito

Si se permite forzar:

- requiere permiso;
- exige motivo;
- queda auditado;
- muestra consecuencias;
- no debe ser la opción predeterminada.

## R-PRODCC-008 — Registrar producción terminada

Cuando se cierra correctamente debe registrarse:

- fecha;
- hora;
- operario;
- receta;
- cantidad;
- unidad;
- lote si existe;
- ingredientes consumidos;
- producto generado;
- movimientos de stock;
- origen de la operación.

## R-PRODCC-009 — No descontar logística como ingrediente

Tareas como:

- transporte;
- montaje;
- cierre;
- retorno;

no deben generar consumos de receta salvo configuración explícita.

## R-PRODCC-010 — Bloqueos reutilizables

Los bloqueos de producción deben usar un modelo común para poder integrarse con:

- Mi Jornada;
- stock;
- recepción;
- compras;
- eventos;
- asistente de resolución.

---

# 11. REGLAS DE STOCK

## R-STK-001 — Diferenciar stock físico y stock registrado

El sistema debe poder admitir que el stock registrado esté pendiente de actualización.

No debe presentar como certeza física un dato desactualizado.

## R-STK-002 — Todo movimiento debe tener origen

Un movimiento debe indicar:

- tipo;
- artículo;
- cantidad;
- unidad;
- fecha;
- origen;
- usuario o proceso;
- documento relacionado;
- observaciones.

## R-STK-003 — No modificar stock sin movimiento

El valor de stock no debe cambiar silenciosamente.

Toda modificación debe quedar trazada.

## R-STK-004 — Unidades coherentes

No debe mezclarse kg, L y unidades sin conversión válida.

## R-STK-005 — Evitar stock negativo silencioso

Si una operación genera stock negativo:

- debe bloquearse;
- advertirse;
- o registrarse como forzada con motivo y permiso.

## R-STK-006 — Consumo por lotes cuando exista trazabilidad

Cuando se gestione lote, debe respetarse el criterio definido:

- FIFO;
- FEFO;
- selección manual;
- otro criterio configurado.

## R-STK-007 — Los ajustes son excepciones

Un ajuste manual debe:

- indicar motivo;
- registrar antes y después;
- identificar responsable;
- quedar separado de compras y producción.

## R-STK-008 — El stock mínimo no es stock real

El stock mínimo es una regla de alerta.

No debe confundirse con cantidad disponible.

## R-STK-009 — Las cajas requieren equivalencia

Las entradas por cajas deben registrar:

- número de cajas;
- contenido por caja;
- unidad base;
- equivalencia utilizada.

## R-STK-010 — Las reservas deben distinguirse

Cuando se implemente stock reservado, debe diferenciarse:

- disponible;
- reservado;
- comprometido;
- en tránsito;
- pendiente de recepción.

---

# 12. REGLAS DE RECEPCIÓN DE MERCANCÍA

## R-RCP-001 — El flujo empieza por el proveedor

La interacción debe comenzar con una situación como:

> Ha llegado Makro.

No con:

> Importar archivo.

## R-RCP-002 — Permitir recepción sin actualización inmediata

La recepción puede quedar confirmada operativamente y pendiente de stock.

## R-RCP-003 — Comparar contra pedido cuando exista

Debe poder mostrar:

- pedido;
- recibido;
- diferencia;
- faltantes;
- exceso;
- sustituciones;
- incidencias.

## R-RCP-004 — Pesos reales prevalecen

Si un producto se pesa al recibirlo, el peso real debe prevalecer sobre la cantidad teórica.

## R-RCP-005 — Conservar documento original

Factura, albarán o imagen deben quedar vinculados a la recepción.

## R-RCP-006 — No aceptar silenciosamente ambigüedades

Si una línea no se relaciona con un artículo con suficiente confianza, debe quedar pendiente.

## R-RCP-007 — La recepción parcial es válida

Un pedido puede recibirse en varias entregas.

## R-RCP-008 — Las incidencias deben clasificarse

Ejemplos:

- falta cantidad;
- sobra cantidad;
- producto dañado;
- temperatura incorrecta;
- sustitución;
- peso incorrecto;
- precio diferente;
- producto no pedido.

## R-RCP-009 — Recepción → Stock debe ser confirmable

Antes de escribir stock debe mostrarse qué entradas se realizarán.

## R-RCP-010 — Resolver bloqueos relacionados

Una recepción confirmada debe poder resolver bloqueos de producción relacionados, sin resolverlos silenciosamente si existe ambigüedad.

---

# 13. REGLAS DE COMPRAS Y PROVEEDORES

## R-CMP-001 — Comprar desde necesidad real

Las recomendaciones deben considerar:

- stock;
- mínimos;
- producción;
- eventos;
- pedidos pendientes;
- recepciones pendientes;
- consumo histórico;
- caducidad;
- proveedor;
- formato de compra.

## R-CMP-002 — No recomendar compras duplicadas

Antes de recomendar debe comprobarse:

- pedido ya creado;
- pedido enviado;
- mercancía en tránsito;
- recepción pendiente;
- stock reservado.

## R-CMP-003 — Comparar proveedores con contexto

No elegir únicamente por precio.

Considerar:

- unidad;
- formato;
- calidad;
- plazo;
- mínimo de compra;
- histórico;
- fiabilidad;
- sustituciones;
- coste logístico.

## R-CMP-004 — Mantener histórico de precios

Toda compra debe poder alimentar el histórico.

## R-CMP-005 — Explicar la recomendación

Ejemplo:

> Compra 12 kg porque necesitas 9 kg para producción, tienes 2 kg disponibles y conviene mantener 1 kg de seguridad.

## R-CMP-006 — Permitir decisión humana

El usuario puede:

- aceptar;
- modificar;
- aplazar;
- rechazar;
- cambiar proveedor.

La decisión debe quedar registrada cuando sea relevante.

---

# 14. REGLAS DE EVENTOS

## R-EVT-001 — El evento es un flujo completo

Un evento puede generar:

- menú;
- previsión;
- compras;
- producción;
- personal;
- transporte;
- montaje;
- servicio;
- cierre;
- retorno;
- costes;
- incidencias.

## R-EVT-002 — Las fechas pasadas deben explicarse

No mostrar valores negativos sin interpretar.

## R-EVT-003 — Cambios deben propagarse

Un cambio de comensales, menú o fecha debe indicar qué áreas afecta.

## R-EVT-004 — No recalcular silenciosamente

Los cambios de impacto deben mostrar vista previa:

- producción;
- compras;
- coste;
- personal;
- transporte.

## R-EVT-005 — Diferenciar estimado y real

Costes y consumos deben poder tener:

- previsto;
- comprometido;
- real;
- diferencia.

## R-EVT-006 — Cierre obligatorio

Un evento no termina al finalizar el servicio.

Debe contemplar:

- retorno;
- sobrantes;
- mermas;
- incidencias;
- horas;
- coste real;
- cierre administrativo.

---

# 15. REGLAS DE COSTES Y RENTABILIDAD

## R-CST-001 — Todo coste debe indicar origen

Puede proceder de:

- receta;
- compra;
- personal;
- transporte;
- alquiler;
- consumibles;
- merma;
- servicio externo;
- coste indirecto.

## R-CST-002 — No mezclar coste previsto y real

Deben mostrarse por separado.

## R-CST-003 — Los históricos no se reescriben sin control

Recalcular una receta hoy no debe alterar automáticamente el coste histórico de un evento pasado.

## R-CST-004 — Las unidades deben coincidir

No comparar precios sin normalizar unidad y formato.

## R-CST-005 — La rentabilidad debe explicar la diferencia

No mostrar solo margen.

Debe poder explicar:

- subida de precios;
- merma;
- exceso de horas;
- cambio de proveedor;
- sobreproducción;
- devolución;
- descuento.

## R-CST-006 — Marcar aproximaciones

Todo cálculo aproximado debe identificarse como tal.

---

# 16. REGLAS DE DATOS

## R-DAT-001 — Una fuente de verdad por entidad

Cada entidad debe tener una fuente oficial.

No deben coexistir varias copias activas sin reglas de sincronización.

## R-DAT-002 — No asumir estructuras

Antes de importar o modificar deben comprobarse:

- nombres de hojas;
- columnas;
- tipos;
- claves;
- versiones;
- relaciones.

## R-DAT-003 — Lectura antes que escritura

Toda integración nueva debe empezar en modo:

- lectura;
- diagnóstico;
- vista previa;
- simulación.

Solo después debe habilitar escritura.

## R-DAT-004 — Backups antes de escrituras masivas

Toda operación masiva debe generar o verificar backup.

## R-DAT-005 — Identificadores estables

Los nombres pueden cambiar.

Los identificadores internos deben permanecer estables cuando sea posible.

## R-DAT-006 — Fechas con zona horaria cuando proceda

Los registros operativos deben evitar ambigüedad temporal.

## R-DAT-007 — Estados normalizados

Los estados deben definirse centralmente.

No crear variantes como:

- terminado;
- finalizado;
- completo;
- completado;

sin una correspondencia oficial.

## R-DAT-008 — Campos desconocidos no se inventan

Usar:

- desconocido;
- pendiente;
- no informado;
- estimado;

según corresponda.

## R-DAT-009 — Trazabilidad del origen

Todo dato importado debe poder indicar:

- archivo;
- documento;
- usuario;
- proceso;
- fecha;
- confianza;
- transformación aplicada.

## R-DAT-010 — Normalizar sin destruir

La normalización debe conservar el valor original cuando sea relevante.

## R-DAT-011 — No borrar para corregir

Las correcciones deben preferir:

- actualización auditada;
- anulación;
- versión;
- reversión.

## R-DAT-012 — Privacidad por diseño

Solo deben conservarse los datos personales necesarios para la operación.

---

# 17. REGLAS DE ARQUITECTURA

## R-ARQ-001 — Revisar antes de crear

Antes de crear un archivo nuevo debe buscarse si ya existe:

- módulo equivalente;
- servicio reutilizable;
- motor relacionado;
- modelo común;
- utilidad.

## R-ARQ-002 — No duplicar motores

Una regla de negocio debe tener un responsable claro.

No deben existir dos motores diferentes calculando lo mismo.

## R-ARQ-003 — Separar responsabilidades

Preferencia arquitectónica:

- `CORE` o motores: lógica determinista;
- `SERVICIOS`: coordinación;
- `MODELOS`: estructuras;
- `APP`: interacción;
- `DATOS`: persistencia;
- `TESTS`: validación;
- `DEVKIT`: desarrollo y memoria.

## R-ARQ-004 — La interfaz no debe contener lógica crítica

La consola o pantalla no debe calcular:

- stock;
- coste;
- escandallo;
- prioridades complejas;
- trazabilidad.

Debe delegar.

## R-ARQ-005 — Los servicios no deben duplicar persistencia

La persistencia debe centralizarse en repositorios o motores existentes cuando la arquitectura lo permita.

## R-ARQ-006 — Dependencias explícitas

Evitar imports circulares y dependencias ocultas.

## R-ARQ-007 — Compatibilidad hacia atrás

Los campos o contratos utilizados por funciones certificadas deben conservarse o migrarse explícitamente.

## R-ARQ-008 — Configuración central

Rutas, hojas, estados, límites y opciones comunes no deben dispersarse como valores mágicos.

## R-ARQ-009 — Errores con contexto

Las excepciones internas deben:

- conservar causa;
- indicar operación;
- no mostrar trazas técnicas al usuario final;
- quedar disponibles para diagnóstico.

## R-ARQ-010 — Funciones pequeñas y comprobables

Las operaciones críticas deben dividirse en pasos que puedan probarse de forma aislada.

## R-ARQ-011 — No refactorizar sin objetivo

Una refactorización debe justificar:

- problema;
- beneficio;
- riesgo;
- tests;
- alcance.

## R-ARQ-012 — El tamaño del proyecto no justifica complejidad nueva

La solución más simple compatible con la arquitectura debe preferirse.

---

# 18. REGLAS DE INTELIGENCIA ARTIFICIAL

## R-IA-001 — La IA interpreta, no inventa operaciones

Puede:

- entender lenguaje;
- clasificar intención;
- resumir;
- explicar;
- proponer;
- relacionar con confianza.

No debe inventar:

- stock;
- precios;
- cantidades;
- proveedores;
- recetas oficiales;
- movimientos;
- certificaciones.

## R-IA-002 — Los motores son autoridad operativa

Cuando IA y motor discrepen, prevalece el motor o se detiene la operación para revisión.

## R-IA-003 — Mostrar incertidumbre

La IA debe indicar cuando:

- no está segura;
- hay varias coincidencias;
- falta contexto;
- una relación es probable;
- usa una estimación.

## R-IA-004 — Confirmación para escrituras

Una intención conversacional no debe producir una escritura crítica sin:

- interpretación;
- vista previa;
- confirmación;
- validación del motor.

## R-IA-005 — No ocultar reglas deterministas dentro de prompts

Las reglas críticas deben estar en código o configuración versionada.

## R-IA-006 — Prompts versionados

Los prompts importantes deben:

- estar en el repositorio;
- tener versión;
- estar probados;
- documentar su propósito.

## R-IA-007 — Contexto mínimo necesario

No enviar a la IA datos irrelevantes o sensibles.

## R-IA-008 — Respuestas accionables

La IA debe terminar en acciones claras cuando el contexto sea operativo.

## R-IA-009 — No fingir ejecución

La IA no debe afirmar que ha:

- actualizado;
- enviado;
- comprado;
- descontado;
- certificado;

si la operación no ha sido ejecutada y confirmada.

## R-IA-010 — Coste controlado

Las funciones de IA deben diseñarse considerando:

- frecuencia;
- tamaño de contexto;
- reutilización;
- caché;
- modelo adecuado;
- coste por cliente.

---

# 19. REGLAS DE SEGURIDAD Y ESCRITURA

## R-SEG-001 — Validar antes de modificar

Ninguna escritura crítica debe comenzar sin validación previa.

## R-SEG-002 — Transacciones

Cuando varias escrituras formen una operación única deben tratarse como unidad.

## R-SEG-003 — Rollback

Si una operación parcial puede dejar inconsistencias, debe existir reversión.

## R-SEG-004 — Idempotencia

Repetir una solicitud no debe duplicar el efecto cuando la operación deba ser única.

## R-SEG-005 — Auditoría

Registrar:

- quién;
- qué;
- cuándo;
- origen;
- antes;
- después;
- motivo.

## R-SEG-006 — Permisos

Las acciones sensibles deben diferenciar perfiles cuando se implemente control de usuarios.

## R-SEG-007 — Borrado controlado

Preferir:

- archivar;
- anular;
- desactivar;

antes que eliminar definitivamente.

## R-SEG-008 — Confirmación reforzada

Operaciones especialmente sensibles pueden requerir:

- segunda confirmación;
- contraseña;
- rol;
- motivo.

## R-SEG-009 — No exponer secretos

Claves, tokens y credenciales no deben quedar en:

- código;
- logs;
- ZIPs;
- documentación;
- prompts.

## R-SEG-010 — Diagnóstico sin daño

Los diagnósticos deben ser de solo lectura salvo que indiquen explícitamente lo contrario.

---

# 20. REGLAS DE TESTS

## R-TST-001 — Todo sprint funcional debe tener tests

Los tests deben cubrir:

- caso normal;
- caso límite;
- error;
- regresión;
- escritura segura;
- duplicados cuando proceda.

## R-TST-002 — Probar comportamiento, no solo implementación

Los tests deben validar resultados observables.

## R-TST-003 — Datos aislados

Los tests no deben modificar datos reales.

## R-TST-004 — Reproducibilidad

Un test debe dar el mismo resultado bajo las mismas condiciones.

## R-TST-005 — Regresión obligatoria

Todo cambio debe ejecutar los tests de los componentes afectados y de los pilotos certificados relacionados.

## R-TST-006 — Los tests no certifican por sí solos

También se requiere:

- diagnóstico;
- revisión del flujo;
- compatibilidad;
- documentación.

## R-TST-007 — No adaptar la lógica para “pasar el test”

Si un test refleja mal la operación real, debe revisarse el test y documentarse.

## R-TST-008 — Casos de cocina real

Las pruebas deben incluir escenarios realistas:

- stock desactualizado;
- recepción pendiente;
- producción parcial;
- eventos pasados;
- unidades distintas;
- artículos parecidos;
- tareas bloqueadas.

## R-TST-009 — Salida clara

Los scripts de comprobación deben indicar:

- resultado;
- métricas;
- errores;
- siguiente acción.

## R-TST-010 — No ocultar tests fallidos

Una certificación no puede declarar éxito con fallos conocidos no documentados.

---

# 21. REGLAS DE DIAGNÓSTICO

## R-DIAG-001 — Diagnóstico aislado por sprint

Cada sprint relevante debe incluir un diagnóstico ejecutable de forma independiente.

## R-DIAG-002 — Solo lectura por defecto

No debe modificar datos reales.

## R-DIAG-003 — Debe explicar qué valida

No basta con mostrar `OK`.

Debe resumir:

- componentes;
- casos;
- garantías;
- limitaciones.

## R-DIAG-004 — Detectar incompatibilidades

Debe comprobar:

- imports;
- archivos;
- contratos;
- configuración;
- datos mínimos;
- versiones.

## R-DIAG-005 — Separar error de advertencia

Un aviso no debe marcarse como fallo si no invalida el sprint.

---

# 22. REGLAS DE SPRINTS

## R-SPR-001 — Un sprint, un objetivo principal

Evitar sprints que mezclen demasiados cambios no relacionados.

## R-SPR-002 — Definición antes de código

Cada sprint debe definir:

- problema;
- objetivo;
- alcance;
- fuera de alcance;
- archivos probables;
- riesgos;
- pruebas;
- criterio de aceptación.

## R-SPR-003 — Auditar el código real

No desarrollar basándose únicamente en documentos o memoria.

La arquitectura real del proyecto es referencia obligatoria.

## R-SPR-004 — Reutilizar antes de crear

El sprint debe identificar qué motores existentes utiliza.

## R-SPR-005 — No romper lo certificado

Los cambios deben ser mínimos y localizados.

## R-SPR-006 — Entrega completa

Una entrega debe contener, cuando corresponda:

- código;
- tests;
- diagnóstico;
- changelog;
- certificación;
- guía de comprobación;
- archivos modificados.

## R-SPR-007 — Certificar solo lo probado

No declarar terminado un sprint que no ha sido ejecutado.

## R-SPR-008 — Estado explícito

Estados permitidos:

- propuesto;
- definido;
- en desarrollo;
- en pruebas;
- bloqueado;
- certificado;
- rechazado;
- sustituido.

## R-SPR-009 — Los descubrimientos se registran

Una mejora descubierta durante pruebas debe:

- resolverse si está dentro del alcance;
- o añadirse a pendientes;
- o abrir un sub-sprint.

## R-SPR-010 — No reabrir líneas cerradas sin motivo

Las líneas certificadas solo se reabren por:

- bug;
- cambio real de requisito;
- incompatibilidad;
- riesgo de datos;
- mejora imprescindible.

---

# 23. REGLAS DE CERTIFICACIÓN

## R-CER-001 — Certificación basada en evidencia

Debe indicar:

- qué se probó;
- cuántos tests;
- qué diagnóstico;
- qué regresión;
- limitaciones;
- resultado.

## R-CER-002 — No usar lenguaje absoluto sin prueba

Evitar afirmar:

- “perfecto”;
- “sin ningún error”;
- “100 % seguro”;

si no existe evidencia suficiente.

## R-CER-003 — Limitaciones visibles

Toda limitación conocida debe quedar documentada.

## R-CER-004 — Relación con versión

La certificación debe identificar el código o parche exacto.

## R-CER-005 — Certificación no sustituye validación real

Un sprint puede estar técnicamente certificado y todavía requerir validación en cocina.

## R-CER-006 — Revocación

Una certificación puede revocarse si aparece:

- bug crítico;
- pérdida de datos;
- incompatibilidad;
- supuesto incorrecto.

---

# 24. REGLAS DE DOCUMENTACIÓN Y MEMORIA VIVA

## R-DOC-001 — El proyecto debe describirse a sí mismo

La memoria viva debe permitir conocer:

- identidad;
- reglas;
- arquitectura;
- roadmap;
- estado;
- sprints;
- decisiones;
- certificaciones;
- pendientes.

## R-DOC-002 — No depender del chat

Las decisiones importantes deben estar en el repositorio.

## R-DOC-003 — Documentación versionada

Los documentos oficiales deben tener:

- versión;
- fecha;
- estado;
- relación con otros documentos.

## R-DOC-004 — Evitar duplicidad documental

Cada tipo de información debe tener un documento principal.

## R-DOC-005 — Actualizar al cerrar sprint

Debe actualizarse:

- estado actual;
- roadmap;
- sprints;
- certificaciones;
- pendientes;
- decisiones si aplica.

## R-DOC-006 — Diferenciar hechos y planes

No escribir como terminado lo que está propuesto.

## R-DOC-007 — Mantener rutas estables

Ruta recomendada:

```text
DEVKIT/
└── KNOWLEDGE_CORE/
```

## R-DOC-008 — La memoria no sustituye al código

Describe y orienta.

El código real sigue siendo la fuente técnica.

---

# 25. REGLAS DE GIT Y VERSIONADO

## R-GIT-001 — No trabajar directamente sobre estable

Los cambios deben realizarse en rama o copia controlada.

## R-GIT-002 — Un commit debe ser comprensible

Debe indicar:

- sprint;
- objetivo;
- alcance.

## R-GIT-003 — No mezclar cambios accidentales

Evitar incluir archivos no relacionados.

## R-GIT-004 — Versionar documentación junto al código

La memoria y certificaciones deben acompañar el cambio.

## R-GIT-005 — Etiquetar versiones certificadas

Cuando el flujo esté implantado, usar tags o referencias equivalentes.

## R-GIT-006 — No versionar secretos ni datos sensibles

## R-GIT-007 — El ZIP es entrega, no fuente de verdad

La fuente principal debe ser el repositorio.

El ZIP puede utilizarse como parche o distribución.

---

# 26. REGLAS DE RENDIMIENTO Y ESCALABILIDAD

## R-RND-001 — Optimizar después de medir

No añadir complejidad por rendimiento sin evidencia.

## R-RND-002 — Evitar cargar todo innecesariamente

Un proyecto grande no debe implicar que cada operación lea todos los archivos o datos.

## R-RND-003 — Caché con invalidación clara

No utilizar caché si puede dejar datos operativos desactualizados sin aviso.

## R-RND-004 — Escalabilidad gradual

Primero:

- un restaurante;
- uso real;
- estabilidad.

Después:

- varios establecimientos;
- usuarios;
- nube;
- SaaS.

## R-RND-005 — Mantener modo local funcional

Mientras el piloto sea local, no depender innecesariamente de servicios externos.

---

# 27. REGLAS DE COMPATIBILIDAD Y MIGRACIÓN

## R-MIG-001 — No romper formatos sin migración

Si cambia una estructura:

- detectar versión;
- migrar;
- respaldar;
- validar;
- informar.

## R-MIG-002 — Excel legacy en solo lectura inicial

Las nuevas integraciones con Excel deben comenzar comprobando estructura y contenido.

## R-MIG-003 — Migración a SQLite trazable

Debe conservar:

- origen;
- fecha;
- correspondencias;
- errores;
- filas rechazadas.

## R-MIG-004 — Campos nuevos con valores seguros

No asumir datos retroactivos inexistentes.

## R-MIG-005 — Poder reanudar migraciones

Las migraciones grandes deben evitar duplicados al repetirse.

---

# 28. REGLAS DE BLOQUEOS E INCIDENCIAS

## R-BLQ-001 — Modelo común

Todos los bloqueos deben compartir una estructura común.

Campos mínimos:

- tipo;
- gravedad;
- origen;
- título;
- explicación;
- causa probable;
- acciones;
- estado;
- fecha;
- contexto.

## R-BLQ-002 — Clasificación inicial

Tipos previstos:

- stock insuficiente;
- recurso ocupado;
- dependencia;
- receta incompleta;
- recepción pendiente;
- sin operario;
- documentación;
- configuración;
- desconocido.

## R-BLQ-003 — No resolver sin evidencia

Un bloqueo solo se cierra automáticamente si la condición se ha resuelto de forma verificable.

## R-BLQ-004 — Recomendaciones ordenadas

El asistente debe priorizar la solución más probable y menos disruptiva.

## R-BLQ-005 — Mantener contexto

Al saltar a recepción, stock o compras, debe conservarse qué producción originó el bloqueo.

## R-BLQ-006 — Volver al flujo original

Después de resolver, debe facilitar volver a la tarea bloqueada.

## R-BLQ-007 — Las incidencias no deben duplicarse

Si ya existe una incidencia activa equivalente, debe actualizarse o reutilizarse.

## R-BLQ-008 — Explicación humana

No mostrar únicamente códigos.

---

# 29. REGLAS DE NOMENCLATURA

## R-NOM-001 — Nombres en español cuando formen parte del dominio

Los conceptos de cocina y operación deben ser comprensibles para el equipo.

## R-NOM-002 — Consistencia

No alternar sin motivo:

- recepción / entrada;
- artículo / producto;
- producción / elaboración;
- tarea / orden.

Debe existir glosario.

## R-NOM-003 — Archivos con propósito claro

Evitar nombres genéricos:

- nuevo.py;
- prueba2.py;
- final_final.py.

## R-NOM-004 — Versiones en documentación, no en duplicados innecesarios

Preferir Git y changelog antes que múltiples copias.

## R-NOM-005 — Mantener nombres certificados si cambiarlos rompe compatibilidad

---

# 30. REGLAS DE EXCEPCIÓN

Una regla solo puede exceptuarse si:

1. existe un motivo concreto;
2. se documenta;
3. se evalúan riesgos;
4. se limita el alcance;
5. se define duración;
6. se crea plan de corrección;
7. no compromete seguridad crítica.

Formato recomendado:

```text
EXCEPCIÓN:
Regla:
Motivo:
Alcance:
Riesgo:
Compensación:
Responsable:
Fecha:
Caducidad:
```

Una excepción temporal no debe convertirse silenciosamente en regla permanente.

---

# 31. LISTA DE COMPROBACIÓN ANTES DE DESARROLLAR

Antes de escribir código:

- [ ] ¿Se ha leído `01_IDENTIDAD.md`?
- [ ] ¿Se ha leído `03_REGLAS.md`?
- [ ] ¿Existe un problema real?
- [ ] ¿Está definido el flujo de cocina?
- [ ] ¿Se ha revisado el código real?
- [ ] ¿Existe un motor reutilizable?
- [ ] ¿Está claro qué queda fuera?
- [ ] ¿Se conocen las escrituras?
- [ ] ¿Se han identificado riesgos?
- [ ] ¿Se sabe cómo probarlo?
- [ ] ¿Se sabe cómo llega a Mi Jornada?
- [ ] ¿La experiencia usa lenguaje natural?

---

# 32. LISTA DE COMPROBACIÓN ANTES DE CERTIFICAR

- [ ] Código integrado.
- [ ] Tests nuevos.
- [ ] Regresión.
- [ ] Diagnóstico aislado.
- [ ] Escrituras seguras.
- [ ] Duplicados controlados.
- [ ] Rollback cuando aplica.
- [ ] Mensajes humanos.
- [ ] Limitaciones documentadas.
- [ ] Changelog.
- [ ] Certificación.
- [ ] Guía de prueba.
- [ ] Memoria viva actualizada.
- [ ] Estado del sprint actualizado.
- [ ] Validación manual prevista.

---

# 33. REGLAS QUE NUNCA DEBEN OLVIDARSE

1. Host AI debe adaptarse al cocinero.
2. Mi Jornada es el centro.
3. La IA no sustituye a los motores.
4. No se duplica lógica.
5. Se lee antes de escribir.
6. Se valida antes de modificar.
7. Toda escritura importante deja trazabilidad.
8. Los errores deben proponer soluciones.
9. Los datos desconocidos no se inventan.
10. Lo certificado se protege.
11. Un sprint no termina solo porque el código funcione.
12. La cocina real tiene prioridad sobre la teoría.
13. `M.P` significa Materia Prima.
14. `A.P` significa Aperitivo o elaboración según ficha, no materia prima automática.
15. La búsqueda prioriza nombre y después proveedor.
16. El usuario no debe memorizar códigos.
17. El stock registrado puede diferir temporalmente del físico.
18. Una producción no consume stock dos veces.
19. Una operación crítica no debe quedar a medias.
20. Host AI debe decir la verdad sobre lo que sabe y lo que no sabe.

---

# 34. DEFINICIÓN DE CUMPLIMIENTO

Un desarrollo cumple las reglas de Host AI cuando:

- resuelve una necesidad real;
- respeta la identidad;
- reutiliza arquitectura;
- protege datos;
- mantiene trazabilidad;
- usa lenguaje humano;
- integra el flujo;
- puede probarse;
- no rompe lo certificado;
- queda documentado;
- ayuda realmente al cocinero.

Cumplir la sintaxis o pasar tests no es suficiente si el resultado obliga al usuario a trabajar como una máquina.

---

# 35. ESTATUS DEL DOCUMENTO

Este documento se considera el reglamento oficial de Host AI.

Ruta oficial:

```text
DEVKIT/
└── KNOWLEDGE_CORE/
    └── 03_REGLAS.md
```

Debe ser leído junto con:

```text
01_IDENTIDAD.md
```

Los cambios deben:

- quedar versionados;
- explicar el motivo;
- indicar las reglas modificadas;
- revisar impacto en arquitectura, pruebas y documentación.

Este documento debe evolucionar con prudencia.

Las nuevas reglas deben añadirse cuando exista aprendizaje real del proyecto o de la cocina, no por preferencia temporal.

---

**Fin del documento oficial `03_REGLAS.md`.**
