# Host AI 3.0.3.1 - Lector PDF / Facturas

## Objetivo
Empezar la fase de PDFs y facturas.

## Añade
- `MODELOS/pdf_facturas.py`
- `SERVICIOS/lector_pdf_facturas.py`
- `PIPELINES/pipeline_pdf_facturas.py`
- `TESTS/test_lector_pdf_facturas.py`

## Nuevas intenciones
- `analizar_pdf_factura`
- `detectar_factura_texto`
- `exportar_analisis_pdf`

## Nota
Esta versión extrae texto de PDFs con texto embebido. OCR vendrá más adelante.

## Prueba
```powershell
python TESTS\test_lector_pdf_facturas.py
```
