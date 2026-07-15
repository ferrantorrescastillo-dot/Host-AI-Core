from pathlib import Path
from types import SimpleNamespace

from APP.consola_recepcion_piloto_1 import ConsolaRecepcionPiloto1


def _salida():
    lineas = []
    return lineas, lineas.append


def test_menu_habla_como_cocina_y_agrupa_tecnico():
    consola = ConsolaRecepcionPiloto1.__new__(ConsolaRecepcionPiloto1)
    lineas, imprimir = _salida()
    consola.ejecutar(input_fn=lambda _p: "0", print_fn=imprimir)
    texto = "\n".join(lineas)
    assert "Ha llegado un proveedor" in texto
    assert "Recibir un pedido esperado" in texto
    assert "Continuar una recepción pendiente" in texto
    assert texto.index("Ha llegado un proveedor") < texto.index("OPCIONES TÉCNICAS")


def test_sin_pedidos_ofrece_alternativas_y_avisa_bloqueo():
    consola = ConsolaRecepcionPiloto1.__new__(ConsolaRecepcionPiloto1)
    consola.core = SimpleNamespace(
        produccion_real=SimpleNamespace(listar_planes=lambda: [{"tareas": [{"titulo": "Carrillera", "bloqueo": "Falta producto"}]}]),
        eventos=SimpleNamespace(listar_eventos=lambda: []),
    )
    lineas, imprimir = _salida()
    consola._mostrar_sin_pedidos(imprimir)
    texto = "\n".join(lineas)
    assert "No hay pedidos pendientes de recibir" in texto
    assert "Registrar una recepción manual" in texto
    assert "Revisar pedidos y necesidades" in texto
    assert "Producción bloqueada: Carrillera" in texto
    assert "Siguiente acción recomendada" in texto


def test_resumen_muestra_diferencias_antes_del_detalle():
    preview = {
        "proveedor_llegada": "Makro",
        "lineas_esperadas": [{"estado_linea": "parcial"}, {"estado_linea": "no_recibida"}],
        "resumen": {"esperadas": 2, "aceptadas": 0, "parciales": 1, "no_recibidas": 1, "rechazadas": 0},
        "diferencias": [
            {"tipo": "cantidad_incorrecta", "detalle": "Esperado 5, recibido 3"},
            {"tipo": "no_recibido", "detalle": "No llegó"},
            {"tipo": "precio_incorrecto", "detalle": "Precio esperado 2 vs recibido 3"},
        ],
    }
    lineas, imprimir = _salida()
    ConsolaRecepcionPiloto1._mostrar_resumen_diferencias(preview, imprimir)
    texto = "\n".join(lineas)
    assert "Makro — 2 líneas" in texto
    assert "1 recibida(s) parcialmente" in texto
    assert "1 no recibida(s)" in texto
    assert "1 diferencia(s) de precio" in texto
    assert texto.index("Revisa estas 3 diferencias") < texto.index("Cantidad parcial:")


def test_documento_escaneado_conserva_contexto_si_se_aplaza():
    class Servicio:
        def preparar(self, *_args, **_kwargs):
            raise ValueError("El PDF no contiene texto extraíble. Pega el texto OCR/manual para continuar.")

    consola = ConsolaRecepcionPiloto1.__new__(ConsolaRecepcionPiloto1)
    consola.service = Servicio()
    consola.core = SimpleNamespace(motor_ocr_simulado=SimpleNamespace(extraer_texto=lambda _ruta: {"texto_extraido": ""}))
    consola._contexto_documento = {}
    respuestas = iter(["albaran_escaneado.pdf", "Makro", "3"])
    lineas, imprimir = _salida()
    consola._nueva(lambda _p: next(respuestas), imprimir)
    texto = "\n".join(lineas)
    assert "EL DOCUMENTO PARECE ESTAR ESCANEADO" in texto
    assert "No hay lectura visual automática" in texto
    assert consola._contexto_documento["ruta"] == "albaran_escaneado.pdf"
    assert consola._contexto_documento["proveedor"] == "Makro"
    assert consola._contexto_documento["estado"] == "pendiente_lectura"


def test_cancelacion_manual_no_inicia_lectura():
    consola = ConsolaRecepcionPiloto1.__new__(ConsolaRecepcionPiloto1)
    consola._contexto_documento = {}
    lineas, imprimir = _salida()
    consola._nueva(lambda _p: "0", imprimir)
    assert "No se ha modificado ningún dato" in "\n".join(lineas)


def test_final_de_recepcion_ofrece_siguiente_paso():
    consola = ConsolaRecepcionPiloto1.__new__(ConsolaRecepcionPiloto1)
    resultado = {"registro": {"entradas_stock": [{"nombre": "Patata"}], "incidencias": []}}
    preview = {"resumen": {"parciales": 0, "no_recibidas": 0, "rechazadas": 0}}
    lineas, imprimir = _salida()
    consola._mostrar_final_rp3(resultado, preview, lambda _p: "1", imprimir)
    texto = "\n".join(lineas)
    assert "RECEPCIÓN GUARDADA Y STOCK ACTUALIZADO" in texto
    assert "Continuar con otra recepción" in texto
    assert "Siguiente paso: continúa con la jornada" in texto


def test_pendientes_vacios_explican_estado(tmp_path: Path):
    consola = ConsolaRecepcionPiloto1.__new__(ConsolaRecepcionPiloto1)
    consola.base_dir = tmp_path
    lineas, imprimir = _salida()
    assert consola._listar_pendientes(imprimir) == []
    texto = "\n".join(lineas)
    assert "todo lo guardado está resuelto o aplicado" in texto
    assert "Siguiente paso" in texto


def test_vista_previa_no_muestra_estado_tecnico_de_linea():
    plan = {
        "proveedor": "Makro",
        "resumen": {"lineas": 1, "exactas": 0, "probables": 0, "pendientes": 1},
        "lineas": [{"numero": 1, "descripcion": "Patata", "cantidad": 5, "unidad": "kg", "precio_unitario": 1.2, "articulo_nombre": ""}],
    }
    lineas, imprimir = _salida()
    ConsolaRecepcionPiloto1._mostrar(plan, imprimir)
    texto = "\n".join(lineas)
    assert "No he podido identificar este producto" in texto
    assert "SIN VINCULAR" not in texto
