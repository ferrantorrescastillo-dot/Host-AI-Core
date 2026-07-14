# Host AI 5.0.5 - Confirmación y aplicación de recepción

## Objetivo

Cerrar el primer flujo conversacional real:

```text
Usuario: Han llegado 25 kg de arroz bomba de Makro a 2,15 €/kg.
Host AI: crea borrador seguro y pregunta confirmación.
Usuario: S
Host AI: aplica líneas seguras al stock usando 4.4.3.
```

## Qué cambia

- Nueva APP: `APP/chat_host_ai_505.py`.
- Nuevo servicio: `SERVICIOS/integracion_nucleo_ia_505.py`.
- Bootloader actualizado: opción 1 abre el chat 5.0.5.
- Nuevo test: `TESTS/test_505_confirmacion_recepcion.py`.

## Seguridad

Host AI no modifica stock al detectar una recepción. Primero crea un borrador.
Solo aplica stock si el usuario confirma con `S`, `sí`, `confirmar`, `aplicar`, etc.

Si la línea queda como `revisar_coincidencia` o `crear_articulo_pendiente`, el aplicador 4.4.3 no la suma automáticamente por seguridad.

## Cómo probar

```powershell
python -m TESTS.test_505_confirmacion_recepcion
python main.py
```

Después:

```text
1
Han llegado 25 kg de arroz bomba de Makro a 2,15 €/kg.
S
```
