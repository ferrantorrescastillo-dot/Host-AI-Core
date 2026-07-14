# Informe automático RR1.6.2

- Fecha: 2026-07-11T19:21:45
- Estado: **NO APROBADA**
- Comando: `C:\Users\ferra\AppData\Local\Programs\Python\Python313\python.exe -m pytest -q`

## Resultado

```text
=================================== ERRORS ====================================
_ ERROR collecting HOST_AI_6.0.3_MODO_MANUAL_OPERATIVO/TESTS/test_603_lanzador_base_operativa.py _
ImportError while importing test module 'C:\PROYECTO HOST IA\Proyecto Host AI  6.0\Host AI 6.0\HOST_AI_6.0.3_MODO_MANUAL_OPERATIVO\TESTS\test_603_lanzador_base_operativa.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Users\ferra\AppData\Local\Programs\Python\Python313\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
HOST_AI_6.0.3_MODO_MANUAL_OPERATIVO\TESTS\test_603_lanzador_base_operativa.py:3: in <module>
    from SERVICIOS.lanzador_host_ai_base_603 import LanzadorHostAIBase603
E   ModuleNotFoundError: No module named 'SERVICIOS.lanzador_host_ai_base_603'
_______ ERROR collecting TESTS/test_5412_confirmaciones_inteligentes.py _______
TESTS\test_5412_confirmaciones_inteligentes.py:22: in <module>
    o.gestor_contexto_5410.activar_flujo({"flujo_pendiente_confirmacion": True, "estado_conversacion": "esperando_seleccion_accion", "confirmaciones": {"acciones_con_confirmacion": acciones}, "datos_flujo": {"tipo": "boda", "personas": 150}, "flujo": {"pasos": []}})
    ^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'OrquestadorInteligente52' object has no attribute 'gestor_contexto_5410'
__________ ERROR collecting TESTS/test_5413_conversacion_natural.py ___________
TESTS\test_5413_conversacion_natural.py:15: in <module>
    o.gestor_contexto_5410.activar_flujo({"flujo_pendiente_confirmacion":True,"estado_conversacion":"esperando_seleccion_accion","confirmaciones":{"acciones_con_confirmacion":acciones},"datos_flujo":{"tipo":"boda","personas":150},"flujo":{"pasos":[]}})
    ^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'OrquestadorInteligente52' object has no attribute 'gestor_contexto_5410'
_____________ ERROR collecting TESTS/test_556e4_paralelizacion.py _____________
ImportError while importing test module 'C:\PROYECTO HOST IA\Proyecto Host AI  6.0\Host AI 6.0\TESTS\test_556e4_paralelizacion.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Users\ferra\AppData\Local\Programs\Python\Python313\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TESTS\test_556e4_paralelizacion.py:11: in <module>
    from SERVICIOS.motor_paralelizacion_produccion_556e4 import MotorParalelizacionProduccion556E4
SERVICIOS\motor_paralelizacion_produccion_556e4.py:7: in <module>
    from SERVICIOS.motor_reparto_cocineros_556e3 import MotorRepartoCocineros556E3, _hora, _minutos_hora
E   ImportError: cannot import name '_hora' from 'SERVICIOS.motor_reparto_cocineros_556e3' (C:\PROYECTO HOST IA\Proyecto Host AI  6.0\Host AI 6.0\SERVICIOS\motor_reparto_cocineros_556e3.py)
=========================== short test summary info ===========================
ERROR HOST_AI_6.0.3_MODO_MANUAL_OPERATIVO/TESTS/test_603_lanzador_base_operativa.py
ERROR TESTS/test_5412_confirmaciones_inteligentes.py - AttributeError: 'Orque...
ERROR TESTS/test_5413_conversacion_natural.py - AttributeError: 'OrquestadorI...
ERROR TESTS/test_556e4_paralelizacion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!
4 errors in 17.23s
```

## Nota

La aprobación automática no sustituye la checklist manual del evento completo.
