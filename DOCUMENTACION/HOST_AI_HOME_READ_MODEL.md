# HOST AI HOME READ MODEL

Estado: Implementado en APP-01.5
Fecha: 2026-07-23

## 1. Objetivo

Definir el modelo normalizado de lectura para Host AI Home usando datos reales de solo lectura y tolerancia a fallos parciales.

## 2. Fuentes de datos (solo lectura)

- Eventos: core.eventos.listar_eventos()
- Recetas: RepositorioBibliotecaRecetas601.pendientes()
- Escandallos: RepositorioBibliotecaEscandallos601.listar(...)
- Incidencias: RepositorioCentroImportacion601.incidencias_pendientes()
- Compras: core.compras.listar_necesidades(solo_pendientes=True)
- Stock: core.stock.diagnosticar_stock()
- Produccion: core.produccion_real.listar_planes()
- Menus: BibliotecaMenus601.menus_con_incidencias()

## 3. Servicio utilizado

HostAIHomeReadService

Responsabilidades:

- consultar servicios certificados;
- normalizar resultados heterogeneos;
- devolver modelo unico para la Home;
- registrar errores parciales sin bloquear todo;
- no escribir datos;
- no recalcular logica de negocio.

## 4. Modelo normalizado

Estructura:

- estado_global
- modulos
- indicadores
- bandeja
- errores
- generado_en

Cada modulo incluye:

- estado
- total
- items
- mensaje (opcional)

## 5. Estados soportados

- cargando
- sin_datos
- datos_disponibles
- servicio_no_disponible
- error_parcial
- error_general

Regla:

- Un fallo de modulo no bloquea la Home.
- Se muestra estado individual por modulo.

## 6. Bandeja inteligente determinista

Tarjeta:

- tipo
- titulo
- resumen
- severidad
- cantidad
- modulo_origen
- accion_navegacion
- contexto_id (opcional)
- vigencia (opcional)

Severidades:

- informacion
- atencion
- importante
- critica

## 7. Regla de prioridad reproducible

Ordenamiento por clave determinista:

1. severidad (critica > importante > atencion > informacion)
2. bloqueo operativo (critica priorizada)
3. proximidad temporal (dias a vigencia)
4. cantidad afectada
5. titulo (estable)

## 8. Tratamiento de errores

- servicio ausente -> servicio_no_disponible
- excepcion de lectura -> error_parcial del modulo
- agregacion total con errores -> estado_global=error_parcial
- todos modulos en error/no disponible -> estado_global=error_general

## 9. Limitaciones

- No hay filtros avanzados por pantalla en APP-01.5.
- Algunos modulos aun usan fallback de navegacion.
- No hay persistencia de estado Home fuera de sesion.
