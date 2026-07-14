from pathlib import Path
import json

from SERVICIOS.motor_aprendizaje_culinario_i1324 import MotorAprendizajeCulinarioI1324

BASE = Path(__file__).resolve().parents[1]
EXCEL = Path('/mnt/data/esc_test/Escandallos Boronat.xlsx')


def nuevo_motor(tmp_path):
    motor = MotorAprendizajeCulinarioI1324(BASE)
    motor.ruta_memoria_anterior = tmp_path / 'anterior.json'
    motor.ruta_memoria = tmp_path / 'aprendizaje.json'
    motor.registros = motor._documento_vacio()
    motor.memoria = {}
    return motor


def test_solo_guarda_con_confirmacion_explicita(tmp_path):
    motor = nuevo_motor(tmp_path)
    r = motor.preparar_desde_excel(EXCEL, hojas=['MENU BODA 31-1'])
    motor.aplicar_decision(r, 'parmentier patata', 'GUARNICION', 'PROPONER_NUEVA_RECETA',
                           {'nombre':'Parmentier de patata','tipo':'PROPUESTA_RECETA'}, recordar=False)
    assert not motor.ruta_memoria.exists()
    assert motor.listar_aprendizajes() == []


def test_guarda_metadatos_historial_y_no_crea_receta(tmp_path):
    motor = nuevo_motor(tmp_path)
    antes = len(motor.motor.recetas)
    r = motor.preparar_desde_excel(EXCEL, hojas=['MENU BODA 31-1'])
    motor.aplicar_decision(r, 'parmentier patata', 'GUARNICION', 'PROPONER_NUEVA_RECETA',
                           {'nombre':'Parmentier de patata','tipo':'PROPUESTA_RECETA'}, recordar=True)
    assert motor.ruta_memoria.exists()
    data = json.loads(motor.ruta_memoria.read_text(encoding='utf-8'))
    reg = data['decisiones']['parmentier patata']
    assert reg['nombre_destino'] == 'Parmentier de patata'
    assert reg['rol'] == 'GUARNICION'
    assert reg['usos'] == 0
    assert reg['confianza'] == 1.0
    assert reg['historial'][0]['evento'] == 'CREADO'
    assert len(motor.motor.recetas) == antes


def test_aplica_aprendizaje_incrementa_usos_y_elimina_pregunta(tmp_path):
    motor = nuevo_motor(tmp_path)
    r = motor.preparar_desde_excel(EXCEL, hojas=['MENU BODA 31-1'])
    motor.aplicar_decision(r, 'parmentier patata', 'GUARNICION', 'PROPONER_NUEVA_RECETA',
                           {'nombre':'Parmentier de patata','tipo':'PROPUESTA_RECETA'}, recordar=True)
    motor2 = MotorAprendizajeCulinarioI1324(BASE)
    motor2.ruta_memoria_anterior = tmp_path / 'anterior.json'
    motor2.ruta_memoria = motor.ruta_memoria
    motor2.registros = motor2._cargar_registros()
    motor2.memoria = motor2._memoria_compatible()
    r2 = motor2.preparar_desde_excel(EXCEL, hojas=['MENU BODA 31-1'])
    assert r2['resumen_resolucion']['pendientes_revision'] == 0
    assert r2['resumen_aprendizaje']['aprendizajes_aplicados'] == 1
    reg = motor2.listar_aprendizajes()[0]
    assert reg['usos'] == 1
    assert reg['ultimo_uso_en']


def test_editar_y_desactivar_conserva_historial(tmp_path):
    motor = nuevo_motor(tmp_path)
    r = motor.preparar_desde_excel(EXCEL, hojas=['MENU BODA 31-1'])
    motor.aplicar_decision(r, 'parmentier patata', 'GUARNICION', 'PROPONER_NUEVA_RECETA',
                           {'nombre':'Parmentier de patata','tipo':'PROPUESTA_RECETA'}, recordar=True)
    ap = motor.listar_aprendizajes()[0]
    assert motor.editar_aprendizaje(ap['aprendizaje_id'], nombre_destino='Parmentier cremosa de patata')
    editado = motor.listar_aprendizajes()[0]
    assert editado['nombre_destino'] == 'Parmentier cremosa de patata'
    assert any(h['evento'] == 'EDITADO' for h in editado['historial'])
    assert motor.eliminar_aprendizaje(ap['aprendizaje_id'])
    assert motor.listar_aprendizajes() == []
    inactivo = motor.listar_aprendizajes(incluir_inactivos=True)[0]
    assert inactivo['estado'] == 'INACTIVO'


def test_migra_memoria_i1323_sin_perder_decision(tmp_path):
    anterior = tmp_path / 'anterior.json'
    anterior.write_text(json.dumps({'parmentier patata': {
        'texto_origen':'parmentier patata','rol':'GUARNICION','accion':'PROPONER_NUEVA_RECETA',
        'nombre_destino':'Parmentier de patata','tipo_destino':'PROPUESTA_RECETA','entidad_id':'','confianza':1.0
    }}), encoding='utf-8')
    motor = MotorAprendizajeCulinarioI1324(BASE)
    motor.ruta_memoria_anterior = anterior
    motor.ruta_memoria = tmp_path / 'nuevo.json'
    motor.registros = motor._cargar_registros()
    motor.memoria = motor._memoria_compatible()
    regs = motor.listar_aprendizajes()
    assert len(regs) == 1
    assert regs[0]['origen'] == 'migracion_i1323'
    assert motor.ruta_memoria.exists()
