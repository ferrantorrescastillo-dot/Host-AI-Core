from pathlib import Path
import json

import pytest

from CORE.MUR import (
    AccionResolucion, CheckpointMUR, ConflictoMUR, EstadoConflicto,
    IResolutorMUR, OrquestadorMUR, RegistroResolutoresMUR,
    RepositorioMURJson, RepositorioMURMemoria, ResultadoResolucion,
    SeveridadConflicto, TipoConflicto, TipoEntidad,
)
from CORE.MUR.estados import TransicionEstadoInvalida
from SERVICIOS.diagnostico_mur_m11 import DiagnosticoMURM11


class ResolutorPrueba(IResolutorMUR):
    resolutor_id = 'TEST-GENERICO'
    version = '1'

    def soporta(self, conflicto):
        return conflicto.tipo_entidad == TipoEntidad.GENERICA

    def preparar(self, conflicto):
        return {'acciones': [AccionResolucion.SIMULAR.value]}

    def ejecutar(self, conflicto, accion, payload):
        return ResultadoResolucion(True, accion, 'ok', {'valor': payload.get('valor')})


def mur_memoria():
    registro = RegistroResolutoresMUR(); registro.registrar(ResolutorPrueba())
    return OrquestadorMUR(RepositorioMURMemoria(), registro)


def conflicto(checkpoint_id=''):
    return ConflictoMUR(
        organizacion_id='ORG', flujo_id='FLUJO', origen_modulo='TEST',
        tipo_entidad=TipoEntidad.GENERICA, tipo_conflicto=TipoConflicto.GENERICO,
        severidad=SeveridadConflicto.AVISO, dato_original='x', dato_normalizado='X',
        acciones_permitidas=[AccionResolucion.SIMULAR.value], checkpoint_id=checkpoint_id,
    )


def test_ciclo_completo_cierra_solo_tras_recalculo():
    mur = mur_memoria()
    c = mur.detectar(conflicto())
    ses = mur.abrir_resolucion(c.conflicto_id, 'u')
    out = mur.ejecutar(ses.sesion_id, AccionResolucion.SIMULAR.value, {'valor': 7})
    assert out.ok and out.datos['valor'] == 7
    assert mur.repo.obtener_conflicto(c.conflicto_id).estado == EstadoConflicto.RESUELTO
    mur.cerrar_tras_recalculo(c.conflicto_id, True)
    assert mur.repo.obtener_conflicto(c.conflicto_id).estado == EstadoConflicto.CERRADO


def test_recalculo_negativo_reabre():
    mur = mur_memoria(); c = mur.detectar(conflicto())
    ses = mur.abrir_resolucion(c.conflicto_id, 'u'); mur.ejecutar(ses.sesion_id, 'SIMULAR', {})
    final = mur.cerrar_tras_recalculo(c.conflicto_id, False)
    assert final.estado == EstadoConflicto.REABIERTO


def test_transicion_invalida_bloqueada():
    mur = mur_memoria(); c = mur.detectar(conflicto())
    with pytest.raises(TransicionEstadoInvalida):
        mur.cambiar_estado(c.conflicto_id, EstadoConflicto.CERRADO, 'u')


def test_checkpoint_obligatorio_debe_existir():
    mur = mur_memoria()
    with pytest.raises(KeyError):
        mur.detectar(conflicto('CHK-INEXISTENTE'))
    chk = mur.crear_checkpoint(CheckpointMUR('F','M','O','P',{'a':1}))
    c = mur.detectar(conflicto(chk.checkpoint_id))
    assert c.checkpoint_id == chk.checkpoint_id


def test_registro_evitar_duplicados_y_selecciona():
    reg = RegistroResolutoresMUR(); reg.registrar(ResolutorPrueba())
    with pytest.raises(ValueError): reg.registrar(ResolutorPrueba())
    assert reg.seleccionar(conflicto()).resolutor_id == 'TEST-GENERICO'


def test_accion_no_permitida_no_ejecuta():
    mur = mur_memoria(); c = mur.detectar(conflicto()); ses = mur.abrir_resolucion(c.conflicto_id,'u')
    with pytest.raises(ValueError): mur.ejecutar(ses.sesion_id, 'CREAR', {})


def test_persistencia_json_recupera_estado(tmp_path):
    ruta = tmp_path/'mur.json'; reg = RegistroResolutoresMUR(); reg.registrar(ResolutorPrueba())
    mur = OrquestadorMUR(RepositorioMURJson(ruta), reg)
    c = mur.detectar(conflicto())
    assert ruta.exists()
    data=json.loads(ruta.read_text(encoding='utf-8'))
    assert c.conflicto_id in data['conflictos']
    repo2=RepositorioMURJson(ruta)
    assert repo2.obtener_conflicto(c.conflicto_id).dato_original == 'x'


def test_auditoria_registra_ciclo():
    mur=mur_memoria(); c=mur.detectar(conflicto()); ses=mur.abrir_resolucion(c.conflicto_id,'u'); mur.ejecutar(ses.sesion_id,'SIMULAR',{})
    eventos=[x.evento for x in mur.repo.listar_auditoria(c.conflicto_id)]
    assert 'CONFLICTO_DETECTADO' in eventos
    assert 'RESOLUCION_INICIADA' in eventos
    assert 'RESOLUCION_VALIDADA' in eventos


def test_diagnostico_no_toca_datos_negocio(tmp_path):
    (tmp_path/'DATOS/db').mkdir(parents=True)
    recetas=tmp_path/'DATOS/db/escandallos.json'; recetas.write_text('[]',encoding='utf-8')
    antes=recetas.read_bytes()
    out=DiagnosticoMURM11(tmp_path).ejecutar()
    assert out['ok'] is True and out['estado_final']=='CERRADO'
    assert out['datos_negocio_modificados'] is False
    assert recetas.read_bytes()==antes
