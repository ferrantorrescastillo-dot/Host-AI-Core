# APP-01 AUDITORIA DE INTERFAZ

Estado: Completada
Fecha: 2026-07-23
Sprint: APP-01
Alcance: Auditoria previa obligatoria para construir base visual unificada

## 1. Tecnologia actual de la interfaz

- Interfaz principal actual: consola interactiva Python (input/print).
- Capa UI principal en APP:
  - APP/consola.py (consola base).
  - APP/consola_piloto_01.py (modo piloto privado).
  - APP/consolas por modulo (recepcion, jornada, produccion, configuracion).
- No hay framework web activo como entrada oficial del producto.

## 2. Punto de entrada principal

- Freeze-A1 (Host AI Core 1.0):
  - ruta oficial unica: main.py -> SERVICIOS/lanzador_piloto_01.py -> modo piloto.
  - ruta desarrollo: SERVICIOS/host_ai_launcher.py.
  - ruta compatibilidad legacy: SERVICIOS/lanzador_host_ai_base_603.py.
  - rutas QA: opciones de auditoria/certificacion del lanzador piloto.
- LanzadorPiloto01 abre:
  - modo piloto privado;
  - modo desarrollo;
  - auditoria;
  - certificacion.

## 3. Sistema actual de navegacion

- Navegacion jerarquica por menus numerados.
- Consola piloto funciona como agregador que delega a modulos existentes.
- Consola base mantiene menu operacional amplio con acceso a eventos, compras, stock, etc.

## 4. Construccion y apertura de modulos

Patron dominante observado:

- UI captura opcion.
- UI delega en metodo de AppConsolaHostAI o abre consola especializada.
- Consola/metodo llama orquestador/core/servicios existentes.

No se detecta necesidad de duplicar logica para integrar un shell de transicion.

## 5. Funcionamiento del Modo Piloto Privado

- Modo piloto es la ruta oficial de uso diario en este entorno.
- Reutiliza AppConsolaHostAI.
- Ya convive con componentes de lineas historicas, pero su foco es operativa diaria.

## 6. Componentes visuales reutilizables existentes

Reutilizables de forma segura:

- Navegacion y menu de APP/consola_piloto_01.py.
- Render de estado/contexto y salida de APP/consola.py.
- Consolas de modulo (eventos/compras/stock/produccion/recetas-escandallos).
- Servicio bandeja operativa piloto en SERVICIOS/bandeja_trabajo_piloto_11.py (para vista provisional determinista).

## 7. Dependencias UI vs logica de negocio

Dependencias actuales:

- UI -> CORE/orquestador (SolicitudHostAI)
- UI -> AppConsolaHostAI -> motores/servicios del core
- Orquestador -> Host AI Engine
- Host AI Engine -> proveedor simulado/not connected

Conclusion:

- La interfaz no debe acceder a proveedores directamente.
- La ruta segura para chat es orquestador -> host_ai_engine_consulta.

## 8. Riesgos de introducir nueva estructura visual

Riesgos:

1. Romper menu piloto actual (alto impacto operativo).
2. Acoplar shell nuevo a persistencias de negocio (riesgo de escrituras no deseadas).
3. Duplicar navegacion en paralelo y desalinear rutas.
4. Llamar proveedor IA directo desde UI por error de integracion.
5. Introducir estado contextual no compatible con flujos actuales.

## 9. Partes reutilizables

- AppConsolaHostAI como puente a modulos certificados.
- ConsolaPiloto01 como contenedor de transicion.
- Host AI Engine + proveedor simulado para chat provisional.
- Contrato de orquestador existente para enrutado seguro.

## 10. Partes a aislar progresivamente

- Estado de interfaz del shell (contexto visual, notificaciones, home).
- Servicio de chat de UI (separado de la consola base).
- Mapeo de navegacion del shell (tabla de rutas y fallback).
- Componentes de mensaje visual reutilizables por tipo.

## 11. Decision de sprint

- Se mantiene tecnologia actual (consola Python).
- No se inicia migracion web en APP-01.
- Se crea un Application Shell de transicion que convive con menus existentes.
- Se prioriza delegacion a modulos certificados sobre reimplementacion.

## 12. Riesgo residual y mitigacion

Riesgo residual principal: coexistencia de dos experiencias (menu piloto y shell).

Mitigacion:

- shell como opcion adicional visible en piloto;
- fallback explicito a modulos existentes;
- pruebas de accesibilidad de modulos y chat simulado.
