# Host AI 5.0.4 - Integración Chat Host AI

## Objetivo

Conectar el bootloader con una conversación real de Host AI.

Antes, la opción 1 del bootloader solo comprobaba `APP.consola` y volvía al menú.
Ahora la opción 1 abre:

```text
APP.chat_host_ai_504
```

## Qué hace

- Usa el clasificador de intenciones 5.0.3.
- Detecta recepción de mercancía en frases naturales.
- Llama a los motores 4.4.1 y 4.4.2 para crear un borrador seguro.
- No modifica stock todavía.

## Cómo probar

```powershell
python -m TESTS.test_504_integracion_chat_host_ai
python main.py
```

Después elige opción 1 y escribe:

```text
Han llegado 25 kg de arroz bomba de Makro a 2,15 €/kg.
```

Debe crear un borrador de recepción y avisar que todavía no ha modificado stock.
