from __future__ import annotations

from typing import Any

from CORE.MUR.estados import validar_transicion
from CORE.MUR.modelos import (
    CheckpointMUR, ConflictoMUR, EstadoConflicto, EventoAuditoriaMUR,
    ResultadoResolucion, SesionResolucionMUR, ahora_utc,
)
from CORE.MUR.registro import RegistroResolutoresMUR
from CORE.MUR.repositorios import RepositorioMURMemoria


class OrquestadorMUR:
    VERSION = 'M1.1'

    def __init__(self, repositorio=None, registro: RegistroResolutoresMUR | None = None):
        self.repo = repositorio or RepositorioMURMemoria()
        self.registro = registro or RegistroResolutoresMUR()

    def _auditar(self, conflicto_id: str, evento: str, actor: str, detalle: dict[str, Any] | None = None) -> None:
        self.repo.registrar_evento(EventoAuditoriaMUR(conflicto_id, evento, actor, detalle or {}))

    def crear_checkpoint(self, checkpoint: CheckpointMUR, actor: str = 'sistema') -> CheckpointMUR:
        self.repo.guardar_checkpoint(checkpoint)
        self._auditar('', 'CHECKPOINT_CREADO', actor, {'checkpoint_id': checkpoint.checkpoint_id, 'flujo_id': checkpoint.flujo_id})
        return checkpoint

    def detectar(self, conflicto: ConflictoMUR, actor: str = 'sistema') -> ConflictoMUR:
        if conflicto.checkpoint_id:
            self.repo.obtener_checkpoint(conflicto.checkpoint_id)
        self.repo.guardar_conflicto(conflicto)
        self._auditar(conflicto.conflicto_id, 'CONFLICTO_DETECTADO', actor, conflicto.to_dict())
        return conflicto

    def cambiar_estado(self, conflicto_id: str, nuevo: EstadoConflicto, actor: str, motivo: str = '') -> ConflictoMUR:
        conflicto = self.repo.obtener_conflicto(conflicto_id)
        validar_transicion(conflicto.estado, nuevo)
        anterior = conflicto.estado
        conflicto.estado = nuevo
        conflicto.version += 1
        conflicto.actualizado_en = ahora_utc()
        conflicto.motivo_estado = motivo
        self.repo.guardar_conflicto(conflicto)
        self._auditar(conflicto_id, 'ESTADO_CAMBIADO', actor, {'anterior': anterior.value, 'nuevo': nuevo.value, 'motivo': motivo})
        return conflicto

    def clasificar(self, conflicto_id: str, actor: str = 'sistema') -> ConflictoMUR:
        conflicto = self.repo.obtener_conflicto(conflicto_id)
        resolutor = self.registro.seleccionar(conflicto)
        conflicto.resolutor_id = resolutor.resolutor_id
        self.repo.guardar_conflicto(conflicto)
        conflicto = self.cambiar_estado(conflicto_id, EstadoConflicto.CLASIFICADO, actor, 'Resolutor compatible asignado.')
        return conflicto

    def abrir_resolucion(self, conflicto_id: str, usuario_id: str) -> SesionResolucionMUR:
        conflicto = self.repo.obtener_conflicto(conflicto_id)
        if conflicto.estado in {EstadoConflicto.DETECTADO}:
            conflicto = self.clasificar(conflicto_id, usuario_id)
        resolutor = self.registro.obtener(conflicto.resolutor_id)
        preparacion = resolutor.preparar(conflicto)
        acciones = list(preparacion.get('acciones') or conflicto.acciones_permitidas)
        sesion = SesionResolucionMUR(conflicto_id, usuario_id, resolutor.resolutor_id, acciones, payload={'preparacion': preparacion})
        self.repo.guardar_sesion(sesion)
        self.cambiar_estado(conflicto_id, EstadoConflicto.EN_RESOLUCION, usuario_id, 'Sesión de resolución abierta.')
        self._auditar(conflicto_id, 'RESOLUCION_INICIADA', usuario_id, {'sesion_id': sesion.sesion_id, 'acciones': acciones})
        return sesion

    def ejecutar(self, sesion_id: str, accion: str, payload: dict[str, Any] | None = None) -> ResultadoResolucion:
        sesion = self.repo.obtener_sesion(sesion_id)
        if sesion.estado != 'ABIERTA':
            raise ValueError('La sesión de resolución no está abierta.')
        if accion not in sesion.acciones_disponibles:
            raise ValueError(f'Acción no permitida en esta sesión: {accion}')
        conflicto = self.repo.obtener_conflicto(sesion.conflicto_id)
        resolutor = self.registro.obtener(sesion.resolutor_id)
        try:
            resultado = resolutor.ejecutar(conflicto, accion, payload or {})
            valido, mensaje = resolutor.validar(conflicto, resultado)
            if not valido:
                self.cambiar_estado(conflicto.conflicto_id, EstadoConflicto.FALLIDO, sesion.usuario_id, mensaje)
                self._auditar(conflicto.conflicto_id, 'RESOLUCION_FALLIDA', sesion.usuario_id, resultado.to_dict())
                return resultado
            self.cambiar_estado(conflicto.conflicto_id, EstadoConflicto.RESUELTO, sesion.usuario_id, mensaje)
            sesion.estado = 'RESUELTA'; sesion.actualizada_en = ahora_utc(); sesion.payload['resultado'] = resultado.to_dict()
            self.repo.guardar_sesion(sesion)
            self._auditar(conflicto.conflicto_id, 'RESOLUCION_VALIDADA', sesion.usuario_id, resultado.to_dict())
            return resultado
        except Exception as exc:
            self.cambiar_estado(conflicto.conflicto_id, EstadoConflicto.FALLIDO, sesion.usuario_id, str(exc))
            self._auditar(conflicto.conflicto_id, 'RESOLUCION_ERROR', sesion.usuario_id, {'error': str(exc)})
            raise

    def aplicar(self, conflicto_id: str, actor: str = 'sistema') -> ConflictoMUR:
        return self.cambiar_estado(conflicto_id, EstadoConflicto.APLICADO, actor, 'Solución incorporada al flujo de origen.')

    def cerrar_tras_recalculo(self, conflicto_id: str, desaparecio: bool, actor: str = 'sistema', detalle: str = '') -> ConflictoMUR:
        conflicto = self.repo.obtener_conflicto(conflicto_id)
        if desaparecio:
            if conflicto.estado == EstadoConflicto.RESUELTO:
                conflicto = self.aplicar(conflicto_id, actor)
            return self.cambiar_estado(conflicto_id, EstadoConflicto.CERRADO, actor, detalle or 'El recalculo confirma que el conflicto desapareció.')
        if conflicto.estado == EstadoConflicto.RESUELTO:
            conflicto = self.cambiar_estado(conflicto_id, EstadoConflicto.REABIERTO, actor, detalle or 'El conflicto persiste tras recalcular.')
        elif conflicto.estado == EstadoConflicto.APLICADO:
            conflicto = self.cambiar_estado(conflicto_id, EstadoConflicto.REABIERTO, actor, detalle or 'El conflicto persiste tras aplicar.')
        return conflicto

    def cancelar(self, conflicto_id: str, actor: str, motivo: str) -> ConflictoMUR:
        return self.cambiar_estado(conflicto_id, EstadoConflicto.CANCELADO, actor, motivo)

    def reabrir(self, conflicto_id: str, actor: str, motivo: str) -> ConflictoMUR:
        return self.cambiar_estado(conflicto_id, EstadoConflicto.REABIERTO, actor, motivo)

    def resumen(self) -> dict[str, Any]:
        conflictos = self.repo.listar_conflictos()
        estados: dict[str, int] = {}
        for c in conflictos:
            estados[c.estado.value] = estados.get(c.estado.value, 0) + 1
        return {
            'version': self.VERSION,
            'conflictos': len(conflictos),
            'estados': estados,
            'resolutores': self.registro.listar(),
            'eventos_auditoria': len(self.repo.listar_auditoria()),
        }
