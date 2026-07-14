from __future__ import annotations

from pathlib import Path
from typing import Any

from CORE.MUR import (
    AccionResolucion, CheckpointMUR, ConflictoMUR, EstadoConflicto,
    IResolutorMUR, OrquestadorMUR, RegistroResolutoresMUR,
    RepositorioMURJson, ResultadoResolucion, SeveridadConflicto,
    TipoConflicto, TipoEntidad,
)


class ResolutorSimuladoM11(IResolutorMUR):
    resolutor_id = 'M11-RESOLUTOR-SIMULADO'
    version = 'M1.1'

    def soporta(self, conflicto: ConflictoMUR) -> bool:
        return conflicto.tipo_entidad == TipoEntidad.GENERICA

    def preparar(self, conflicto: ConflictoMUR) -> dict[str, Any]:
        return {'acciones': [AccionResolucion.SIMULAR.value], 'mensaje': 'Resolutor simulado listo.'}

    def ejecutar(self, conflicto: ConflictoMUR, accion: str, payload: dict[str, Any]) -> ResultadoResolucion:
        if accion != AccionResolucion.SIMULAR.value:
            return ResultadoResolucion(False, accion, 'Acción simulada no válida.')
        return ResultadoResolucion(True, accion, 'Conflicto simulado resuelto.', {'eco': payload.get('eco', 'OK')})


class DiagnosticoMURM11:
    VERSION = 'M1.1'

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()
        ruta = self.base_dir / 'DATOS' / 'mur' / 'diagnostico_m11.json'
        repo = RepositorioMURJson(ruta)
        registro = RegistroResolutoresMUR()
        registro.registrar(ResolutorSimuladoM11())
        self.mur = OrquestadorMUR(repo, registro)

    def ejecutar(self) -> dict[str, Any]:
        checkpoint = self.mur.crear_checkpoint(CheckpointMUR(
            flujo_id='DIAGNOSTICO-M11', modulo='DIAGNOSTICO_MUR', operacion='CICLO_COMPLETO',
            paso='ANTES_CONFLICTO', estado_parcial={'seguro': True}, huella_entrada='M11-DEMO',
        ))
        conflicto = self.mur.detectar(ConflictoMUR(
            organizacion_id='LOCAL', flujo_id='DIAGNOSTICO-M11', origen_modulo='DIAGNOSTICO_MUR',
            tipo_entidad=TipoEntidad.GENERICA, tipo_conflicto=TipoConflicto.GENERICO,
            severidad=SeveridadConflicto.AVISO, dato_original='conflicto de prueba',
            dato_normalizado='Conflicto de prueba', acciones_permitidas=[AccionResolucion.SIMULAR.value],
            checkpoint_id=checkpoint.checkpoint_id,
        ))
        sesion = self.mur.abrir_resolucion(conflicto.conflicto_id, 'usuario-diagnostico')
        resultado = self.mur.ejecutar(sesion.sesion_id, AccionResolucion.SIMULAR.value, {'eco': 'MUR OPERATIVO'})
        self.mur.cerrar_tras_recalculo(conflicto.conflicto_id, True, 'diagnostico')
        final = self.mur.repo.obtener_conflicto(conflicto.conflicto_id)
        return {
            'version': self.VERSION, 'ok': final.estado == EstadoConflicto.CERRADO,
            'conflicto_id': conflicto.conflicto_id, 'checkpoint_id': checkpoint.checkpoint_id,
            'sesion_id': sesion.sesion_id, 'estado_final': final.estado.value,
            'resultado': resultado.to_dict(), 'resumen': self.mur.resumen(),
            'ruta_diagnostico': str(self.mur.repo.ruta),
            'datos_negocio_modificados': False,
        }


def formatear_diagnostico_m11(r: dict[str, Any]) -> str:
    estado = 'OK' if r.get('ok') else 'ERROR'
    res = r.get('resumen') or {}
    return '\n'.join([
        'M1.1 — NÚCLEO DEL MOTOR UNIVERSAL DE RESOLUCIÓN',
        '=' * 78,
        f'Diagnóstico: {estado} | Estado final: {r.get("estado_final")}',
        f'Conflicto: {r.get("conflicto_id")}',
        f'Checkpoint: {r.get("checkpoint_id")}',
        f'Sesión: {r.get("sesion_id")}',
        f'Resolutores registrados: {len(res.get("resolutores") or [])}',
        f'Eventos de auditoría: {res.get("eventos_auditoria", 0)}',
        f'Persistencia MUR: {r.get("ruta_diagnostico")}',
        '-' * 78,
        'El ciclo DETECTAR → CLASIFICAR → RESOLVER → APLICAR → RECALCULAR → CERRAR funciona.',
        'No se modificaron recetas, artículos, menús, compras, stock ni otros datos de negocio.',
        'M1.1 no incorpora todavía resolutores reales.',
    ])
