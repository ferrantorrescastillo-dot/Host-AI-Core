from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import json
import shutil
from datetime import datetime

from CORE.MUR.modelos import (
    AccionResolucion, ConflictoMUR, ResultadoResolucion,
    TipoConflicto, TipoEntidad,
)
from CORE.MUR.registro import IResolutorMUR
from SERVICIOS.buscador_inteligente_articulos_415 import BuscadorInteligenteArticulos415
from SERVICIOS.gestor_articulos_416 import GestorArticulos416


class ResolutorArticulosM12(IResolutorMUR):
    resolutor_id = 'M1.2-RESOLUTOR-ARTICULOS'
    version = 'M1.2'
    prioridad = 10

    def __init__(self, ruta_articulos: str | Path = 'DATOS/db/articulos.json', *, permitir_sin_precio: bool = True,
                 ruta_backups: str | Path = 'DATOS/backups/m12') -> None:
        self.ruta_articulos = Path(ruta_articulos)
        self.permitir_sin_precio = bool(permitir_sin_precio)
        self.ruta_backups = Path(ruta_backups)
        self.buscador = BuscadorInteligenteArticulos415(str(self.ruta_articulos))
        self.gestor = GestorArticulos416(str(self.ruta_articulos))

    def soporta(self, conflicto: ConflictoMUR) -> bool:
        return conflicto.tipo_entidad == TipoEntidad.ARTICULO and conflicto.tipo_conflicto in {
            TipoConflicto.ENTIDAD_NO_EXISTE,
            TipoConflicto.ENTIDAD_AMBIGUA,
            TipoConflicto.ARTICULO_SIN_PRECIO,
            TipoConflicto.DUPLICADO_PROBABLE,
            TipoConflicto.ENTIDAD_INCOMPLETA,
        }

    def preparar(self, conflicto: ConflictoMUR) -> dict[str, Any]:
        consulta = conflicto.dato_normalizado or conflicto.dato_original
        proveedor = str(conflicto.contexto.get('proveedor') or '').strip() or None
        informe = self.buscador.buscar(consulta, limite=10, umbral_minimo=0.45)
        resultados = [asdict(x) for x in informe.resultados]
        if proveedor and not resultados:
            informe = self.buscador.buscar(consulta, proveedor=proveedor, limite=10, umbral_minimo=0.40)
            resultados = [asdict(x) for x in informe.resultados]
        acciones = []
        if resultados:
            acciones.append(AccionResolucion.VINCULAR.value)
        if conflicto.tipo_conflicto != TipoConflicto.ARTICULO_SIN_PRECIO:
            acciones.append(AccionResolucion.CREAR.value)
        if conflicto.tipo_conflicto in {TipoConflicto.ARTICULO_SIN_PRECIO, TipoConflicto.ENTIDAD_INCOMPLETA}:
            acciones.append(AccionResolucion.EDITAR.value)
        acciones.extend([AccionResolucion.MANTENER_PENDIENTE.value, AccionResolucion.CANCELAR.value])
        return {
            'consulta': consulta,
            'proveedor_filtro': proveedor,
            'candidatos': resultados,
            'acciones': list(dict.fromkeys(acciones)),
            'politica_sin_precio': 'PERMITIDO_PENDIENTE' if self.permitir_sin_precio else 'BLOQUEANTE',
        }

    def ejecutar(self, conflicto: ConflictoMUR, accion: str, payload: dict[str, Any]) -> ResultadoResolucion:
        if accion == AccionResolucion.VINCULAR.value:
            return self._vincular(conflicto, payload)
        if accion == AccionResolucion.CREAR.value:
            return self._crear(conflicto, payload)
        if accion == AccionResolucion.EDITAR.value:
            return self._editar(conflicto, payload)
        if accion == AccionResolucion.MANTENER_PENDIENTE.value:
            return ResultadoResolucion(
                True, accion, 'Artículo mantenido pendiente según política.',
                {'estado_calidad': 'PENDIENTE', 'bloqueo_resuelto': self.permitir_sin_precio},
                requiere_recalculo=True,
            )
        if accion == AccionResolucion.CANCELAR.value:
            return ResultadoResolucion(False, accion, 'Resolución cancelada.', requiere_recalculo=False)
        return ResultadoResolucion(False, accion, f'Acción no soportada: {accion}', requiere_recalculo=False)

    def _vincular(self, conflicto: ConflictoMUR, payload: dict[str, Any]) -> ResultadoResolucion:
        codigo = str(payload.get('codigo') or '').strip()
        articulo = self._obtener_por_codigo(codigo)
        if not articulo:
            return ResultadoResolucion(False, AccionResolucion.VINCULAR.value, 'El artículo seleccionado no existe.', requiere_recalculo=False)
        return ResultadoResolucion(
            True, AccionResolucion.VINCULAR.value, 'Artículo vinculado correctamente.',
            {'articulo': articulo, 'estado_calidad': self._estado_calidad(articulo), 'bloqueo_resuelto': True},
            aprendizaje_sugerido={
                'clave_original': conflicto.dato_original,
                'valor_resuelto': articulo.get('nombre'),
                'tipo_entidad': 'ARTICULO',
                'accion': 'VINCULAR',
                'entidad_id': articulo.get('codigo'),
                'confianza': 1.0,
            },
        )

    def _crear(self, conflicto: ConflictoMUR, payload: dict[str, Any]) -> ResultadoResolucion:
        nombre = str(payload.get('nombre') or conflicto.dato_normalizado or conflicto.dato_original).strip()
        proveedor = str(payload.get('proveedor') or conflicto.contexto.get('proveedor') or '').strip() or None
        familia = str(payload.get('familia') or '').strip() or None
        unidad = str(payload.get('unidad') or '').strip()
        precio = payload.get('precio')
        if not nombre:
            return ResultadoResolucion(False, AccionResolucion.CREAR.value, 'El nombre es obligatorio.', requiere_recalculo=False)
        if not unidad:
            return ResultadoResolucion(False, AccionResolucion.CREAR.value, 'La unidad es un dato crítico y es obligatoria.', requiere_recalculo=False)
        duplicados = self.buscador.buscar(nombre, limite=5, umbral_minimo=0.88).resultados
        if duplicados:
            mejor = duplicados[0]
            if mejor.puntuacion >= 0.88:
                return ResultadoResolucion(False, AccionResolucion.CREAR.value,
                    f'Duplicado probable: {mejor.nombre} ({mejor.codigo}, {mejor.puntuacion:.0%}). Vincula o revisa antes de crear.',
                    {'duplicados': [asdict(x) for x in duplicados]}, requiere_recalculo=False)
        if (precio is None or str(precio).strip() == '') and not self.permitir_sin_precio:
            return ResultadoResolucion(False, AccionResolucion.CREAR.value, 'El precio es obligatorio según la política activa.', requiere_recalculo=False)
        backup = self._backup()
        resultado = self.gestor.alta_articulo(nombre, proveedor=proveedor, familia=familia, precio=precio,
                                              observaciones=f'Unidad: {unidad}. Alta controlada por M1.2.')
        if resultado.accion != 'creado':
            return ResultadoResolucion(False, AccionResolucion.CREAR.value, resultado.mensaje, requiere_recalculo=False)
        self._actualizar_campos(resultado.codigo, {'unidad': unidad, 'estado_calidad': 'PENDIENTE' if precio in (None, '') else 'COMPLETA', 'origen': 'MUR_M1.2'})
        articulo = self._obtener_por_codigo(resultado.codigo)
        estado = self._estado_calidad(articulo or {})
        return ResultadoResolucion(
            True, AccionResolucion.CREAR.value, 'Artículo creado desde el módulo oficial y vinculado al conflicto.',
            {'articulo': articulo, 'backup': str(backup) if backup else '', 'estado_calidad': estado,
             'bloqueo_resuelto': estado == 'COMPLETA' or self.permitir_sin_precio},
            aprendizaje_sugerido={
                'clave_original': conflicto.dato_original,
                'valor_resuelto': nombre,
                'tipo_entidad': 'ARTICULO',
                'accion': 'VINCULAR',
                'entidad_id': resultado.codigo,
                'confianza': 1.0,
            },
        )

    def _editar(self, conflicto: ConflictoMUR, payload: dict[str, Any]) -> ResultadoResolucion:
        codigo = str(payload.get('codigo') or conflicto.contexto.get('codigo') or '').strip()
        articulo = self._obtener_por_codigo(codigo)
        if not articulo:
            return ResultadoResolucion(False, AccionResolucion.EDITAR.value, 'No se encontró el artículo a completar.', requiere_recalculo=False)
        cambios = {k: payload[k] for k in ('precio','proveedor','familia','unidad') if k in payload and payload[k] not in (None,'')}
        if not cambios:
            return ResultadoResolucion(False, AccionResolucion.EDITAR.value, 'No se indicaron cambios.', requiere_recalculo=False)
        backup = self._backup()
        self._actualizar_campos(codigo, cambios)
        articulo = self._obtener_por_codigo(codigo)
        estado = self._estado_calidad(articulo or {})
        self._actualizar_campos(codigo, {'estado_calidad': estado})
        return ResultadoResolucion(True, AccionResolucion.EDITAR.value, 'Artículo completado correctamente.',
            {'articulo': self._obtener_por_codigo(codigo), 'backup': str(backup) if backup else '', 'estado_calidad': estado,
             'bloqueo_resuelto': estado == 'COMPLETA' or self.permitir_sin_precio})

    def validar(self, conflicto: ConflictoMUR, resultado: ResultadoResolucion) -> tuple[bool, str]:
        if not resultado.ok:
            return False, resultado.mensaje
        if resultado.accion == AccionResolucion.MANTENER_PENDIENTE.value and not resultado.datos.get('bloqueo_resuelto'):
            return False, 'La política activa no permite continuar con el artículo pendiente.'
        if resultado.accion in {AccionResolucion.CREAR.value, AccionResolucion.VINCULAR.value, AccionResolucion.EDITAR.value}:
            articulo = resultado.datos.get('articulo') or {}
            if not articulo.get('codigo'):
                return False, 'La resolución no devolvió un artículo válido.'
        return True, resultado.mensaje

    def _leer(self) -> list[dict[str, Any]]:
        if not self.ruta_articulos.exists():
            return []
        try:
            data = json.loads(self.ruta_articulos.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return []
        return data if isinstance(data, list) else []

    def _guardar(self, data: list[dict[str, Any]]) -> None:
        self.ruta_articulos.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.ruta_articulos.with_suffix(self.ruta_articulos.suffix + '.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(self.ruta_articulos)

    def _obtener_por_codigo(self, codigo: str) -> dict[str, Any] | None:
        return next((a for a in self._leer() if str(a.get('codigo') or '') == codigo), None)

    def _actualizar_campos(self, codigo: str, cambios: dict[str, Any]) -> None:
        data = self._leer()
        encontrado = False
        for a in data:
            if str(a.get('codigo') or '') == codigo:
                a.update(cambios)
                a['fecha_actualizacion'] = datetime.now().isoformat(timespec='seconds')
                encontrado = True
                break
        if not encontrado:
            raise LookupError(f'No existe el artículo {codigo}.')
        self._guardar(data)

    def _backup(self) -> Path | None:
        if not self.ruta_articulos.exists():
            return None
        self.ruta_backups.mkdir(parents=True, exist_ok=True)
        destino = self.ruta_backups / f'articulos_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.json'
        shutil.copy2(self.ruta_articulos, destino)
        return destino

    @staticmethod
    def _estado_calidad(articulo: dict[str, Any]) -> str:
        unidad = str(articulo.get('unidad') or '').strip()
        precio = articulo.get('precio')
        if not unidad:
            return 'BLOQUEADA'
        if precio is None or str(precio).strip() == '':
            return 'PENDIENTE'
        return 'COMPLETA'


__all__ = ['ResolutorArticulosM12']
