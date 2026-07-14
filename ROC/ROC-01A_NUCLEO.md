# ROC-01A — NÚCLEO DEL SISTEMA
## Registro Oficial de Componentes (ROC)

**Versión:** 1.0
**Estado:** Oficial
**Dominio:** Núcleo del sistema
**Arquitectura:** Host AI 6.x

# 1. Objetivo del documento

Este documento define el Núcleo Oficial de Host AI.

Su objetivo es definir los componentes que hacen posible el funcionamiento de Host AI, establecer claramente sus responsabilidades y fijar las reglas que ningún desarrollador ni ningún agente debe romper.

# 2. Alcance

Incluye:
- HostAICore
- BaseDatosLocal
- BasePipeline
- Orquestador IA

No incluye:
- Producción
- Stock
- Compras
- Eventos
- Costes
- Escandallos
- Recepción
- Mi Jornada
- Bandeja

# 3. Filosofía del Núcleo

El Núcleo no cocina.
El Núcleo no compra.
El Núcleo no mueve stock.
El Núcleo únicamente conecta todas las piezas.

# 4. Principios

- Único punto de entrada: main.py
- Composición desde HostAICore
- Dependencias compartidas
- Separación de responsabilidades

# 5. Arquitectura

main.py
→ Lanzador
→ HostAICore
→ Servicios
→ Motores
→ Modelos
→ Persistencia

# 6. Componentes

## HostAICore
- Inicializa motores
- Comparte instancias
- Construye el entorno
- No contiene lógica de negocio

## BaseDatosLocal
- Persistencia JSON
- Gestiona colecciones
- No decide reglas de negocio

## BasePipeline
- Contrato común de pipelines

## Orquestador IA
- Interpreta peticiones
- Coordina motores
- No es propietario de los datos

# 7. Relaciones

HostAICore
↓
BaseDatosLocal
↓
Motores
↓
Servicios
↓
Interfaz

# 8. Flujo de arranque

main.py
↓
Lanzador
↓
HostAICore
↓
BaseDatosLocal
↓
Motores
↓
Servicios
↓
Consolas

# 9. Responsabilidades de HostAICore

- Crear
- Compartir
- Coordinar
- Exponer

# 10. Qué NO es el Núcleo

No es un ERP, ni un gestor de Producción, Compras o Stock.

# 11. Decisiones oficiales

- Punto de entrada: main.py
- HostAICore es el Composition Root.
- Persistencia activa: BaseDatosLocal (JSON).
- La lógica de negocio pertenece a los motores.

Fin de ROC-01A.
