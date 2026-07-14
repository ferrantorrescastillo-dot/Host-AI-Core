# Host AI 4.8.1–4.8.4 - Costes y Rentabilidad Inteligente

## 4.8.1 Coste real por receta
Calcula el coste actualizado de una receta usando ingredientes, cantidades, mermas y precios actuales o historicos.

## 4.8.2 Margen por plato, menu o evento
Calcula margen unitario, porcentaje de margen y clasificacion economica.

## 4.8.3 Rentabilidad de carta
Analiza la carta cruzando margen y ventas. Recomienda mantener, revisar, subir precio, reformular o dar visibilidad.

## 4.8.4 Simulador de precios
Permite simular precios, subidas porcentuales y calcular precio recomendado para un margen objetivo.

## Pruebas
```powershell
python -m TESTS.test_481_coste_real_receta
python -m TESTS.test_482_margen_plato_menu
python -m TESTS.test_483_rentabilidad_carta
python -m TESTS.test_484_simulador_precios
```

## Uso manual
```powershell
python APP/coste_real_receta_481.py
python APP/margen_plato_menu_482.py
python APP/rentabilidad_carta_483.py
python APP/simulador_precios_484.py
```
