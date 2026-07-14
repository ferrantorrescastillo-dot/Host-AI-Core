# I1.3.4.1.5 — Motor de conocimiento gastronómico

## Objetivo
Clasificar la naturaleza gastronómica de elementos ya detectados e interpretados, aplicando decisiones aprendidas y reglas explicables antes de enviarlos a la bandeja de revisión.

## Principios
- El aprendizaje confirmado por el usuario prevalece.
- Solo se automatizan decisiones con confianza >= 90 %.
- Conocer el tipo de un elemento no equivale a resolver un vínculo real: los bloqueos siguen abiertos hasta vincular o crear la entidad correspondiente.
- No se escriben menús, recetas, artículos ni relaciones.

## Tipos reconocidos
- APERITIVO_PREPARADO
- MATERIA_PRIMA
- RECETA
- ELABORACION
- SALSA / SALSA_COMERCIAL
- GUARNICION
- CONDIMENTO
- ACABADO
- POSTRE
- ARTICULO_COMERCIAL
- DESCONOCIDO

## Integración
1. I1.3.4.1.4 agrupa conceptos culinarios.
2. I1.3.4.1.5 evalúa su naturaleza gastronómica.
3. Las decisiones de alta confianza actualizan únicamente el plan de simulación.
4. La bandeja oculta avisos ya resueltos automáticamente.
5. Los bloqueos reales permanecen para revisión, vínculo o creación mediante el MUR.

## Seguridad
- Umbral automático fijo y visible: 90 %.
- Motivo y confianza por clasificación.
- Datos de negocio: solo lectura.
- Sesiones guardadas únicamente en `DATOS/mur/revisiones_i13415/`.
