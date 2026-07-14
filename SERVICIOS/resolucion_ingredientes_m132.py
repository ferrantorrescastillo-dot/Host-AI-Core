from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable
import hashlib

from CORE.MUR.modelos import (
    AccionResolucion, CheckpointMUR, ConflictoMUR, SeveridadConflicto,
    TipoConflicto, TipoEntidad,
)
from CORE.MUR.orquestador import OrquestadorMUR
from CORE.MUR.registro import RegistroResolutoresMUR
from CORE.MUR.repositorios import RepositorioMURMemoria
from SERVICIOS.importador_inteligente_recetas_m131 import BorradorRecetaM131, ImportadorInteligenteRecetasM131
from SERVICIOS.resolutor_articulos_m12 import ResolutorArticulosM12


@dataclass
class ItemColaM132:
    indice: int
    ingrediente: str
    cantidad: float | None
    unidad: str
    estado: str = 'PENDIENTE'
    conflicto_id: str = ''
    checkpoint_id: str = ''
    sesion_id: str = ''
    articulo_id: str = ''
    articulo_nombre: str = ''
    accion: str = ''
    mensaje: str = ''

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResultadoColaM132:
    borrador: BorradorRecetaM131
    cola: list[ItemColaM132]
    conflictos_creados: int
    conflictos_cerrados: int
    bloqueos_finales: list[str]
    eventos_auditoria: int

    def to_dict(self) -> dict[str, Any]:
        return {
            'borrador': self.borrador.to_dict(),
            'cola': [x.to_dict() for x in self.cola],
            'conflictos_creados': self.conflictos_creados,
            'conflictos_cerrados': self.conflictos_cerrados,
            'bloqueos_finales': list(self.bloqueos_finales),
            'eventos_auditoria': self.eventos_auditoria,
        }


class ResolucionIngredientesM132:
    """Resuelve artículos faltantes de un borrador de receta mediante conflictos MUR anidados.

    M1.3.2 crea una cola estable, un checkpoint por ingrediente, delega en
    ResolutorArticulosM12 y vuelve al borrador. No crea la receta final: solo
    deja el borrador listo para el resolutor de recetas.
    """

    VERSION = 'M1.3.2'

    def __init__(self, ruta_articulos: str | Path, *, permitir_sin_precio: bool = True):
        self.ruta_articulos = Path(ruta_articulos)
        self.repo = RepositorioMURMemoria()
        self.registro = RegistroResolutoresMUR()
        self.resolutor_articulos = ResolutorArticulosM12(
            self.ruta_articulos,
            permitir_sin_precio=permitir_sin_precio,
            ruta_backups=self.ruta_articulos.parent / 'backups_m132',
        )
        self.registro.registrar(self.resolutor_articulos)
        self.mur = OrquestadorMUR(self.repo, self.registro)

    def construir_cola(self, borrador: BorradorRecetaM131) -> list[ItemColaM132]:
        cola: list[ItemColaM132] = []
        for idx, ing in enumerate(borrador.ingredientes):
            if ing.articulo_id and ing.estado == 'VINCULADO':
                continue
            cola.append(ItemColaM132(idx, ing.nombre, ing.cantidad, ing.unidad))
        return cola

    def resolver(
        self,
        borrador: BorradorRecetaM131,
        decisiones: dict[str, dict[str, Any]] | None = None,
        proveedor: str = '',
        usuario_id: str = 'usuario',
        decisor: Callable[[ItemColaM132, dict[str, Any]], dict[str, Any]] | None = None,
    ) -> ResultadoColaM132:
        decisiones = decisiones or {}
        cola = self.construir_cola(borrador)
        cerrados = 0
        flujo_id = f'M132-{hashlib.sha1((borrador.nombre + borrador.origen_ruta).encode("utf-8")).hexdigest()[:10].upper()}'

        for item in cola:
            checkpoint = CheckpointMUR(
                flujo_id=flujo_id,
                modulo='IMPORTADOR_RECETAS_M1.3.1',
                operacion='RESOLVER_INGREDIENTE',
                paso=f'ingrediente_{item.indice}',
                estado_parcial={'borrador': borrador.to_dict(), 'indice': item.indice},
                dependencias=[x.conflicto_id for x in cola if x.conflicto_id],
            )
            self.mur.crear_checkpoint(checkpoint, usuario_id)
            item.checkpoint_id = checkpoint.checkpoint_id
            conflicto = ConflictoMUR(
                organizacion_id='HOST_AI', flujo_id=flujo_id,
                origen_modulo='IMPORTADOR_INTELIGENTE_RECETAS_M131',
                tipo_entidad=TipoEntidad.ARTICULO,
                tipo_conflicto=TipoConflicto.ENTIDAD_NO_EXISTE,
                severidad=SeveridadConflicto.BLOQUEANTE,
                dato_original=item.ingrediente,
                dato_normalizado=item.ingrediente,
                rol_contextual='INGREDIENTE',
                contexto={'receta': borrador.nombre, 'indice_ingrediente': item.indice,
                          'cantidad': item.cantidad, 'unidad': item.unidad, 'proveedor': proveedor,
                          'conflicto_padre': flujo_id},
                checkpoint_id=checkpoint.checkpoint_id,
            )
            self.mur.detectar(conflicto, usuario_id)
            item.conflicto_id = conflicto.conflicto_id
            sesion = self.mur.abrir_resolucion(conflicto.conflicto_id, usuario_id)
            item.sesion_id = sesion.sesion_id
            preparacion = dict(sesion.payload.get('preparacion') or {})
            decision = decisiones.get(item.ingrediente) or decisiones.get(item.ingrediente.lower())
            if decision is None and decisor:
                decision = decisor(item, preparacion)
            if decision is None:
                item.estado = 'PENDIENTE_USUARIO'
                item.mensaje = 'No existe una decisión para resolver el ingrediente.'
                continue

            accion = str(decision.get('accion') or '').upper()
            payload = dict(decision.get('payload') or {})
            if accion == AccionResolucion.CREAR.value:
                payload.setdefault('nombre', item.ingrediente)
                payload.setdefault('unidad', item.unidad)
            resultado = self.mur.ejecutar(sesion.sesion_id, accion, payload)
            item.accion = accion
            item.mensaje = resultado.mensaje
            if not resultado.ok:
                item.estado = 'FALLIDO'
                continue

            articulo = dict(resultado.datos.get('articulo') or {})
            articulo_id = str(articulo.get('codigo') or articulo.get('id') or '')
            if not articulo_id:
                item.estado = 'FALLIDO'
                item.mensaje = 'La resolución no devolvió un artículo válido.'
                continue

            ing = borrador.ingredientes[item.indice]
            ing.articulo_id = articulo_id
            ing.articulo_nombre = str(articulo.get('nombre') or articulo.get('articulo') or item.ingrediente)
            ing.confianza = 1.0
            ing.estado = 'VINCULADO'
            ing.clase_articulo = 'MATERIA_PRIMA'
            item.articulo_id = articulo_id
            item.articulo_nombre = ing.articulo_nombre
            item.estado = 'RESUELTO'
            self.mur.cerrar_tras_recalculo(conflicto.conflicto_id, True, usuario_id,
                                           'El ingrediente ya está vinculado a un artículo real.')
            cerrados += 1

        # Revalidar el borrador con el catálogo actualizado.
        ImportadorInteligenteRecetasM131(self.ruta_articulos)._validar(borrador)
        return ResultadoColaM132(
            borrador=borrador,
            cola=cola,
            conflictos_creados=len(cola),
            conflictos_cerrados=cerrados,
            bloqueos_finales=list(borrador.bloqueos or []),
            eventos_auditoria=len(self.repo.listar_auditoria()),
        )


__all__ = ['ResolucionIngredientesM132', 'ItemColaM132', 'ResultadoColaM132']
