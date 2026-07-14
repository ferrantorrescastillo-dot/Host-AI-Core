# Host AI 5.5.5A — Parte 3

## Objetivo

Conectar el modelo canónico de escandallos de las Partes 1 y 2 con los motores operativos, sin duplicar lógica ni escribir sobre datos reales.

## Componentes

- Integrador de stock: escala ingredientes según personas y contrasta inventario.
- Integrador de compras: propone solo los faltantes; no genera pedidos reales.
- Integrador de producción: prepara cantidades preliminares; no crea órdenes.
- Integrador de eventos: une evento, escandallo, producción, stock, compras e incidencias.
- Gestor/fachada: punto único para que IA y otros motores consuman la integración.

## Seguridad

Toda la Parte 3 funciona en modo de lectura y simulación:

- no descuenta stock;
- no crea pedidos;
- no crea órdenes de producción;
- no modifica eventos;
- no inventa escandallos inexistentes.

## Instalación

Copiar este parche después de instalar `5.5.5A PARTE 1` y `PARTE 2`.

## Prueba

```bash
python TESTS/test_555a_parte3.py
```

Resultado esperado:

```text
TEST OK 5.5.5A PARTE 3 - Integración stock, compras, producción y eventos
```
