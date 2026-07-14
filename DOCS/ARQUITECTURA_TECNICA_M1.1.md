# M1.1 — Arquitectura técnica implementada

## Componentes
- `CORE/MUR/modelos.py`: contratos y enumeraciones.
- `CORE/MUR/estados.py`: máquina de estados.
- `CORE/MUR/registro.py`: interfaz y registro de resolutores.
- `CORE/MUR/repositorios.py`: persistencia intercambiable.
- `CORE/MUR/orquestador.py`: coordinación del ciclo de resolución.
- `SERVICIOS/diagnostico_mur_m11.py`: prueba funcional sin datos de negocio.

## Regla central
El MUR coordina conflictos. Los módulos de dominio seguirán siendo los únicos responsables de validar y escribir sus entidades.

## Ciclo certificado
`DETECTADO → CLASIFICADO → EN_RESOLUCION → RESUELTO → APLICADO → CERRADO`

El paso a `CERRADO` requiere confirmación posterior del flujo de origen.
