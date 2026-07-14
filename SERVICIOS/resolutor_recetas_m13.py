from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime
import json
import re
import shutil
import unicodedata

from CORE.MUR.modelos import (
    AccionResolucion, ConflictoMUR, ResultadoResolucion,
    TipoConflicto, TipoEntidad,
)
from CORE.MUR.registro import IResolutorMUR


def _norm(texto: Any) -> str:
    valor = str(texto or '').strip().lower()
    valor = ''.join(c for c in unicodedata.normalize('NFD', valor) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', valor).strip(' .,-_')


class ResolutorRecetasM13(IResolutorMUR):
    """Primer resolutor real de recetas para el MUR.

    Alcance M1.3: búsqueda, vinculación y creación manual oficial mínima.
    La ingesta desde texto/Word/PDF/Excel se reserva para M1.3.1.
    """

    resolutor_id = 'M1.3-RESOLUTOR-RECETAS'
    version = 'M1.3'
    prioridad = 20

    def __init__(
        self,
        ruta_recetas: str | Path = 'DATOS/db/escandallos.json',
        ruta_articulos: str | Path = 'DATOS/db/articulos.json',
        ruta_backups: str | Path = 'DATOS/backups/m13',
    ) -> None:
        self.ruta_recetas = Path(ruta_recetas)
        self.ruta_articulos = Path(ruta_articulos)
        self.ruta_backups = Path(ruta_backups)

    def soporta(self, conflicto: ConflictoMUR) -> bool:
        return conflicto.tipo_entidad == TipoEntidad.RECETA and conflicto.tipo_conflicto in {
            TipoConflicto.ENTIDAD_NO_EXISTE,
            TipoConflicto.ENTIDAD_AMBIGUA,
            TipoConflicto.ENTIDAD_INCOMPLETA,
            TipoConflicto.DUPLICADO_PROBABLE,
            TipoConflicto.RELACION_NO_RESUELTA,
        }

    def preparar(self, conflicto: ConflictoMUR) -> dict[str, Any]:
        consulta = conflicto.dato_normalizado or conflicto.dato_original
        candidatos = self.buscar_recetas(consulta, limite=10)
        acciones: list[str] = []
        if candidatos:
            acciones.append(AccionResolucion.VINCULAR.value)
        if conflicto.tipo_conflicto != TipoConflicto.ENTIDAD_AMBIGUA:
            acciones.append(AccionResolucion.CREAR.value)
        if conflicto.tipo_conflicto == TipoConflicto.ENTIDAD_INCOMPLETA:
            acciones.append(AccionResolucion.EDITAR.value)
        acciones.extend([AccionResolucion.MANTENER_PENDIENTE.value, AccionResolucion.CANCELAR.value])
        return {
            'consulta': consulta,
            'candidatos': candidatos,
            'acciones': list(dict.fromkeys(acciones)),
            'modos_creacion_disponibles': ['MANUAL'],
            'modos_reservados_m131': ['TEXTO', 'WORD', 'PDF', 'EXCEL', 'DOCUMENTOS'],
        }

    def ejecutar(self, conflicto: ConflictoMUR, accion: str, payload: dict[str, Any]) -> ResultadoResolucion:
        if accion == AccionResolucion.VINCULAR.value:
            return self._vincular(conflicto, payload)
        if accion == AccionResolucion.CREAR.value:
            return self._crear_manual(conflicto, payload)
        if accion == AccionResolucion.EDITAR.value:
            return self._editar(conflicto, payload)
        if accion == AccionResolucion.MANTENER_PENDIENTE.value:
            return ResultadoResolucion(
                False, accion,
                'La receta se mantiene pendiente. El conflicto continúa bloqueante.',
                {'estado_calidad': 'BLOQUEADA', 'bloqueo_resuelto': False},
                requiere_recalculo=False,
            )
        if accion == AccionResolucion.CANCELAR.value:
            return ResultadoResolucion(False, accion, 'Resolución cancelada.', requiere_recalculo=False)
        return ResultadoResolucion(False, accion, f'Acción no soportada: {accion}', requiere_recalculo=False)

    def buscar_recetas(self, texto: str, limite: int = 10) -> list[dict[str, Any]]:
        q = _norm(texto)
        if not q:
            return []
        resultados: list[dict[str, Any]] = []
        for receta in self._leer_recetas():
            nombre = str(receta.get('nombre') or '')
            n = _norm(nombre)
            if not n:
                continue
            if n == q:
                puntuacion = 1.0
            elif q in n or n in q:
                puntuacion = 0.92
            else:
                tq, tn = set(q.split()), set(n.split())
                puntuacion = len(tq & tn) / max(len(tq | tn), 1)
            if puntuacion >= 0.45:
                resultados.append({
                    'receta_id': receta.get('receta_id') or receta.get('id'),
                    'nombre': nombre,
                    'raciones_base': receta.get('raciones_base'),
                    'ingredientes': len(receta.get('lineas') or []),
                    'coste_por_racion': receta.get('coste_por_racion'),
                    'estado_calidad': self._estado_calidad(receta),
                    'puntuacion': round(float(puntuacion), 4),
                })
        resultados.sort(key=lambda x: (-x['puntuacion'], x['nombre'].casefold()))
        return resultados[:limite]

    def _vincular(self, conflicto: ConflictoMUR, payload: dict[str, Any]) -> ResultadoResolucion:
        receta_id = str(payload.get('receta_id') or '').strip()
        receta = self._obtener_receta(receta_id)
        if not receta:
            return ResultadoResolucion(False, AccionResolucion.VINCULAR.value, 'La receta seleccionada no existe.', requiere_recalculo=False)
        estado = self._estado_calidad(receta)
        if estado != 'COMPLETA':
            return ResultadoResolucion(False, AccionResolucion.VINCULAR.value, 'La receta existe pero no está completa.', {'receta': receta, 'estado_calidad': estado}, requiere_recalculo=False)
        return ResultadoResolucion(
            True, AccionResolucion.VINCULAR.value, 'Receta vinculada correctamente.',
            {'receta': receta, 'estado_calidad': estado, 'bloqueo_resuelto': True},
            aprendizaje_sugerido={
                'clave_original': conflicto.dato_original,
                'valor_resuelto': receta.get('nombre'),
                'tipo_entidad': 'RECETA',
                'accion': 'VINCULAR',
                'entidad_id': receta.get('receta_id') or receta.get('id'),
                'confianza': 1.0,
            },
        )

    def _crear_manual(self, conflicto: ConflictoMUR, payload: dict[str, Any]) -> ResultadoResolucion:
        nombre = str(payload.get('nombre') or conflicto.dato_normalizado or conflicto.dato_original).strip()
        rendimiento = payload.get('raciones_base', payload.get('rendimiento'))
        lineas = list(payload.get('ingredientes') or payload.get('lineas') or [])
        if not nombre:
            return ResultadoResolucion(False, AccionResolucion.CREAR.value, 'El nombre es obligatorio.', requiere_recalculo=False)
        try:
            rendimiento = float(rendimiento)
        except (TypeError, ValueError):
            return ResultadoResolucion(False, AccionResolucion.CREAR.value, 'El rendimiento debe ser numérico.', requiere_recalculo=False)
        if rendimiento <= 0:
            return ResultadoResolucion(False, AccionResolucion.CREAR.value, 'El rendimiento debe ser mayor que cero.', requiere_recalculo=False)
        if not lineas:
            return ResultadoResolucion(False, AccionResolucion.CREAR.value, 'Una receta completa necesita al menos un ingrediente.', requiere_recalculo=False)
        duplicados = self.buscar_recetas(nombre, limite=5)
        if duplicados and duplicados[0]['puntuacion'] >= 0.92:
            return ResultadoResolucion(False, AccionResolucion.CREAR.value,
                f"Duplicado probable: {duplicados[0]['nombre']} ({duplicados[0]['puntuacion']:.0%}). Vincula o revisa antes de crear.",
                {'duplicados': duplicados}, requiere_recalculo=False)
        articulos = {str(a.get('codigo') or a.get('id') or a.get('articulo_id')): a for a in self._leer_articulos()}
        normalizadas: list[dict[str, Any]] = []
        errores: list[str] = []
        coste_total = 0.0
        for i, linea in enumerate(lineas, 1):
            articulo_id = str(linea.get('articulo_id') or linea.get('codigo') or '').strip()
            articulo = articulos.get(articulo_id)
            if not articulo:
                errores.append(f'Ingrediente {i}: el artículo {articulo_id or "sin código"} no existe.')
                continue
            try:
                cantidad = float(linea.get('cantidad'))
            except (TypeError, ValueError):
                errores.append(f'Ingrediente {i}: cantidad inválida.')
                continue
            unidad = str(linea.get('unidad') or articulo.get('unidad') or '').strip()
            if cantidad <= 0 or not unidad:
                errores.append(f'Ingrediente {i}: cantidad y unidad son obligatorias.')
                continue
            precio = articulo.get('precio')
            try:
                coste_unitario = float(precio) if precio not in (None, '') else 0.0
            except (TypeError, ValueError):
                coste_unitario = 0.0
            coste_linea = cantidad * coste_unitario
            coste_total += coste_linea
            normalizadas.append({
                'nombre': articulo.get('nombre') or articulo.get('articulo') or articulo_id,
                'cantidad': cantidad,
                'unidad': unidad,
                'tipo': 'articulo',
                'articulo_id': articulo_id,
                'elaboracion_id': '',
                'coste_unitario': coste_unitario,
                'coste_total': round(coste_linea, 6),
            })
        if errores:
            return ResultadoResolucion(False, AccionResolucion.CREAR.value, 'No se creó la receta: ' + ' | '.join(errores), {'errores': errores}, requiere_recalculo=False)
        recetas = self._leer_recetas()
        receta_id = self._nuevo_id_receta(nombre, recetas)
        ahora = datetime.now().isoformat(timespec='seconds')
        receta = {
            'receta_id': receta_id,
            'nombre': nombre,
            'raciones_base': rendimiento,
            'lineas': normalizadas,
            'grupo': str(payload.get('grupo') or conflicto.rol_contextual or '').strip(),
            'subgrupo': str(payload.get('subgrupo') or '').strip(),
            'observaciones': str(payload.get('observaciones') or 'Alta manual controlada por M1.3.').strip(),
            'activo': True,
            'id': f'ESC-{receta_id}',
            'creado_en': ahora,
            'actualizado_en': ahora,
            'coste_total_base': round(coste_total, 6),
            'coste_por_racion': round(coste_total / rendimiento, 6),
            'estado_calidad': 'COMPLETA',
            'origen': 'MUR_M1.3_MANUAL',
        }
        backup = self._backup()
        recetas.append(receta)
        self._guardar_recetas(recetas)
        return ResultadoResolucion(
            True, AccionResolucion.CREAR.value, 'Receta creada desde el flujo oficial manual y vinculada al conflicto.',
            {'receta': receta, 'backup': str(backup) if backup else '', 'estado_calidad': 'COMPLETA', 'bloqueo_resuelto': True},
            aprendizaje_sugerido={
                'clave_original': conflicto.dato_original,
                'valor_resuelto': nombre,
                'tipo_entidad': 'RECETA',
                'accion': 'VINCULAR',
                'entidad_id': receta_id,
                'confianza': 1.0,
            },
        )

    def _editar(self, conflicto: ConflictoMUR, payload: dict[str, Any]) -> ResultadoResolucion:
        receta_id = str(payload.get('receta_id') or conflicto.contexto.get('receta_id') or '').strip()
        recetas = self._leer_recetas()
        receta = next((r for r in recetas if str(r.get('receta_id') or r.get('id')) == receta_id), None)
        if not receta:
            return ResultadoResolucion(False, AccionResolucion.EDITAR.value, 'No se encontró la receta.', requiere_recalculo=False)
        cambios = {k: payload[k] for k in ('nombre', 'raciones_base', 'grupo', 'subgrupo', 'observaciones') if k in payload and payload[k] not in (None, '')}
        if not cambios:
            return ResultadoResolucion(False, AccionResolucion.EDITAR.value, 'No se indicaron cambios.', requiere_recalculo=False)
        if 'raciones_base' in cambios:
            try:
                cambios['raciones_base'] = float(cambios['raciones_base'])
            except (TypeError, ValueError):
                return ResultadoResolucion(False, AccionResolucion.EDITAR.value, 'Rendimiento inválido.', requiere_recalculo=False)
            if cambios['raciones_base'] <= 0:
                return ResultadoResolucion(False, AccionResolucion.EDITAR.value, 'Rendimiento inválido.', requiere_recalculo=False)
        backup = self._backup()
        receta.update(cambios)
        receta['actualizado_en'] = datetime.now().isoformat(timespec='seconds')
        coste = float(receta.get('coste_total_base') or 0)
        rendimiento = float(receta.get('raciones_base') or 0)
        receta['coste_por_racion'] = round(coste / rendimiento, 6) if rendimiento else 0
        receta['estado_calidad'] = self._estado_calidad(receta)
        self._guardar_recetas(recetas)
        return ResultadoResolucion(True, AccionResolucion.EDITAR.value, 'Receta actualizada correctamente.',
            {'receta': receta, 'backup': str(backup) if backup else '', 'estado_calidad': receta['estado_calidad'], 'bloqueo_resuelto': receta['estado_calidad'] == 'COMPLETA'})

    def validar(self, conflicto: ConflictoMUR, resultado: ResultadoResolucion) -> tuple[bool, str]:
        if not resultado.ok:
            return False, resultado.mensaje
        receta = resultado.datos.get('receta') or {}
        if resultado.accion in {AccionResolucion.CREAR.value, AccionResolucion.VINCULAR.value, AccionResolucion.EDITAR.value}:
            if not (receta.get('receta_id') or receta.get('id')):
                return False, 'La resolución no devolvió una receta válida.'
            if self._estado_calidad(receta) != 'COMPLETA':
                return False, 'La receta resultante no cumple la ficha mínima completa.'
        return True, resultado.mensaje

    def _leer_recetas(self) -> list[dict[str, Any]]:
        if not self.ruta_recetas.exists():
            return []
        try:
            data = json.loads(self.ruta_recetas.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            return []
        return data if isinstance(data, list) else list(data.get('escandallos') or [])

    def _guardar_recetas(self, recetas: list[dict[str, Any]]) -> None:
        self.ruta_recetas.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.ruta_recetas.with_suffix(self.ruta_recetas.suffix + '.tmp')
        tmp.write_text(json.dumps(recetas, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(self.ruta_recetas)

    def _leer_articulos(self) -> list[dict[str, Any]]:
        if not self.ruta_articulos.exists():
            return []
        try:
            data = json.loads(self.ruta_articulos.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            return []
        return data if isinstance(data, list) else []

    def _obtener_receta(self, receta_id: str) -> dict[str, Any] | None:
        return next((r for r in self._leer_recetas() if str(r.get('receta_id') or r.get('id')) == receta_id), None)

    def _backup(self) -> Path | None:
        if not self.ruta_recetas.exists():
            return None
        self.ruta_backups.mkdir(parents=True, exist_ok=True)
        destino = self.ruta_backups / f'recetas_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.json'
        shutil.copy2(self.ruta_recetas, destino)
        return destino

    @staticmethod
    def _estado_calidad(receta: dict[str, Any]) -> str:
        nombre = str(receta.get('nombre') or '').strip()
        try:
            rendimiento = float(receta.get('raciones_base') or receta.get('rendimiento') or 0)
        except (TypeError, ValueError):
            rendimiento = 0
        lineas = receta.get('lineas') or receta.get('ingredientes') or []
        if not nombre or rendimiento <= 0 or not lineas:
            return 'BLOQUEADA'
        for linea in lineas:
            if not str(linea.get('articulo_id') or linea.get('elaboracion_id') or '').strip():
                return 'BLOQUEADA'
            try:
                if float(linea.get('cantidad') or 0) <= 0:
                    return 'BLOQUEADA'
            except (TypeError, ValueError):
                return 'BLOQUEADA'
            if not str(linea.get('unidad') or '').strip():
                return 'BLOQUEADA'
        return 'COMPLETA'

    @staticmethod
    def _nuevo_id_receta(nombre: str, recetas: list[dict[str, Any]]) -> str:
        base = re.sub(r'[^A-Z0-9]+', '-', _norm(nombre).upper()).strip('-')[:30] or 'RECETA'
        usados = {str(r.get('receta_id') or '') for r in recetas}
        candidato = f'REC-{base}'
        if candidato not in usados:
            return candidato
        n = 2
        while f'{candidato}-{n}' in usados:
            n += 1
        return f'{candidato}-{n}'


__all__ = ['ResolutorRecetasM13']
