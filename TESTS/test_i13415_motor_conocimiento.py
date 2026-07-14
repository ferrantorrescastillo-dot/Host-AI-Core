from SERVICIOS.motor_conocimiento_gastronomico_i13415 import MotorConocimientoGastronomicoI13415
from SERVICIOS.bandeja_revision_i13415 import BandejaRevisionI13415


def test_conocimiento_casos_gastronomicos():
    m = MotorConocimientoGastronomicoI13415()
    assert m.clasificar('A.P GAZPACHO DE FRAMBUESA').tipo == 'APERITIVO_PREPARADO'
    assert m.clasificar('Salsa romesco').tipo == 'SALSA'
    assert m.clasificar('Salsa Allioli natural bote de 1 lt').tipo == 'SALSA_COMERCIAL'
    assert m.clasificar('Tartar de fuet').tipo == 'APERITIVO_PREPARADO'
    assert m.clasificar('Coulant de chocolate').tipo == 'POSTRE'
    assert m.clasificar('Crema calenta tomàquet').tipo == 'RECETA'


def test_conocimiento_no_inventa_desconocido():
    m = MotorConocimientoGastronomicoI13415()
    r = m.clasificar('Elemento X sin contexto')
    assert r.tipo == 'DESCONOCIDO'
    assert r.confianza < .90


def test_bandeja_oculta_aviso_automatizado(tmp_path):
    b = BandejaRevisionI13415(tmp_path)
    plan = {
        'plan_id': 'P1', 'acciones': [{
            'accion_id': 'A1', 'tipo': 'VINCULAR', 'entidad': 'APERITIVO_PREPARADO',
            'nombre': 'Tartar de fuet', 'estado': 'PLANIFICADA',
            'detalle': {'menu': 'M1', 'conocimiento_gastronomico': {
                'tipo': 'APERITIVO_PREPARADO', 'confianza': .92,
                'motivo': 'Preparación culinaria.', 'destino_importacion': 'APERITIVO_PREPARADO'
            }}
        }],
        'bloqueos': [], 'resumen': {'acciones': 1, 'ejecutables': 1, 'bloqueadas': 0, 'vincular': 1, 'relaciones': 0},
        'estado_simulacion': 'LISTA_PARA_TRANSACCION'
    }
    assert b._extraer_incidencias(plan) == []


def test_bandeja_conserva_bloqueo_aunque_conozca_rol(tmp_path):
    b = BandejaRevisionI13415(tmp_path)
    plan = {
        'plan_id': 'P2', 'acciones': [{
            'accion_id': 'A2', 'tipo': 'RESOLVER_ANTES_DE_IMPORTAR', 'entidad': 'RECETA',
            'nombre': 'Lenguado a la menier', 'estado': 'BLOQUEADA',
            'detalle': {'menu': 'M1', 'plato': 'Lenguado...', 'conocimiento_gastronomico': {
                'tipo': 'RECETA', 'confianza': .90, 'motivo': 'Receta principal.', 'destino_importacion': 'PLATO_MENU'
            }}
        }],
        'bloqueos': [{}], 'resumen': {'acciones': 1, 'ejecutables': 0, 'bloqueadas': 1, 'vincular': 0, 'relaciones': 0},
        'estado_simulacion': 'BLOQUEADA'
    }
    inc = b._extraer_incidencias(plan)
    assert len(inc) == 1
    assert inc[0].nivel == 'BLOQUEANTE'
    assert inc[0].propuesta == 'RECETA'
