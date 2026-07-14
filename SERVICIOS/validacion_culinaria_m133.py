from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable
import json
import re
import unicodedata

from SERVICIOS.importador_inteligente_recetas_m131 import (
    BorradorRecetaM131,
    clasificar_prefijo_articulo,
)


def _norm(value: Any) -> str:
    text = str(value or '').strip().lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', text).strip(' .,:;-_')


@dataclass(frozen=True)
class HallazgoCulinarioM133:
    codigo: str
    severidad: str
    categoria: str
    mensaje: str
    evidencia: str = ''
    recomendacion: str = ''
    ingrediente: str = ''

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResultadoValidacionM133:
    receta: str
    estado: str
    errores: int
    avisos: int
    informativos: int
    coste_total: float | None
    coste_por_racion: float | None
    ingredientes: int
    hallazgos: list[HallazgoCulinarioM133]
    criterios_aplicados: list[str]

    @property
    def bloqueada(self) -> bool:
        return self.errores > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            'receta': self.receta,
            'estado': self.estado,
            'errores': self.errores,
            'avisos': self.avisos,
            'informativos': self.informativos,
            'coste_total': self.coste_total,
            'coste_por_racion': self.coste_por_racion,
            'ingredientes': self.ingredientes,
            'hallazgos': [h.to_dict() for h in self.hallazgos],
            'criterios_aplicados': list(self.criterios_aplicados),
        }


class ValidadorCulinarioM133:
    """Validador explicable de borradores de receta.

    M1.3.3 no modifica recetas ni artículos. Clasifica cada hallazgo como:
    - ERROR: dato crítico que bloquea la creación.
    - AVISO: incoherencia o información de calidad que requiere revisión.
    - INFO: observación útil que no impide continuar.

    Las reglas culinarias ambiguas nunca se convierten en errores automáticos.
    """

    VERSION = 'M1.3.3'
    UNIDADES_MASA = {'kg', 'g', 'gr'}
    UNIDADES_VOLUMEN = {'l', 'ml', 'cl'}
    UNIDADES_UNIDAD = {'ud', 'u', 'unidad', 'unidades'}
    LIQUIDOS = {'agua', 'leche', 'nata', 'caldo', 'zumo', 'jugo', 'vino', 'cerveza', 'aceite', 'vinagre'}
    SOLIDOS_GRASOS = {'mantequilla', 'margarina', 'grasa', 'manteca'}
    ESPECIAS = {'sal', 'pimienta', 'nuez moscada', 'comino', 'canela', 'pimenton', 'curry', 'oregano', 'tomillo'}
    UNIDADES_VALIDAS = UNIDADES_MASA | UNIDADES_VOLUMEN | UNIDADES_UNIDAD

    def __init__(
        self,
        ruta_articulos: str | Path,
        *,
        coste_racion_aviso_alto: float = 50.0,
        coste_racion_aviso_bajo: float = 0.01,
    ):
        self.ruta_articulos = Path(ruta_articulos)
        self.coste_racion_aviso_alto = float(coste_racion_aviso_alto)
        self.coste_racion_aviso_bajo = float(coste_racion_aviso_bajo)

    def validar(
        self,
        borrador: BorradorRecetaM131,
        *,
        metadatos: dict[str, Any] | None = None,
    ) -> ResultadoValidacionM133:
        metadatos = dict(metadatos or {})
        articulos = self._indice_articulos()
        hallazgos: list[HallazgoCulinarioM133] = []
        criterios: list[str] = []

        self._validar_identidad_y_rendimiento(borrador, hallazgos, criterios)
        self._validar_ingredientes(borrador, articulos, hallazgos, criterios)
        coste_total, coste_racion = self._validar_coste(borrador, articulos, hallazgos, criterios)
        self._validar_documentacion(borrador, metadatos, hallazgos, criterios)

        errores = sum(1 for h in hallazgos if h.severidad == 'ERROR')
        avisos = sum(1 for h in hallazgos if h.severidad == 'AVISO')
        informativos = sum(1 for h in hallazgos if h.severidad == 'INFO')
        if errores:
            estado = 'BLOQUEADA'
        elif avisos:
            estado = 'REVISAR'
        else:
            estado = 'VALIDADA'
        return ResultadoValidacionM133(
            receta=borrador.nombre,
            estado=estado,
            errores=errores,
            avisos=avisos,
            informativos=informativos,
            coste_total=coste_total,
            coste_por_racion=coste_racion,
            ingredientes=len(borrador.ingredientes),
            hallazgos=hallazgos,
            criterios_aplicados=list(dict.fromkeys(criterios)),
        )

    def _validar_identidad_y_rendimiento(self, b, hallazgos, criterios) -> None:
        criterios.append('IDENTIDAD_Y_RENDIMIENTO')
        if not str(b.nombre or '').strip():
            hallazgos.append(self._h('RECETA_SIN_NOMBRE', 'ERROR', 'IDENTIDAD', 'La receta no tiene nombre.', recomendacion='Indica un nombre único y reconocible.'))
        try:
            rendimiento = float(b.rendimiento or 0)
        except (TypeError, ValueError):
            rendimiento = 0
        if rendimiento <= 0:
            hallazgos.append(self._h('RENDIMIENTO_INVALIDO', 'ERROR', 'RENDIMIENTO', 'El rendimiento debe ser mayor que cero.', evidencia=str(b.rendimiento), recomendacion='Indica raciones o unidades finales reales.'))
        elif rendimiento > 10000:
            hallazgos.append(self._h('RENDIMIENTO_ATIPICO', 'AVISO', 'RENDIMIENTO', 'El rendimiento es extraordinariamente alto.', evidencia=str(rendimiento), recomendacion='Confirma que no se ha confundido rendimiento con gramos o mililitros.'))

    def _validar_ingredientes(self, b, articulos, hallazgos, criterios) -> None:
        criterios.extend(['INGREDIENTES_CRITICOS', 'DUPLICADOS', 'UNIDADES', 'PREFIJOS_MP_AP'])
        if not b.ingredientes:
            hallazgos.append(self._h('SIN_INGREDIENTES', 'ERROR', 'INGREDIENTES', 'No se detectaron ingredientes.', recomendacion='Añade al menos una materia prima o elaboración válida.'))
            return
        vistos: dict[str, int] = {}
        for ing in b.ingredientes:
            nombre = str(ing.nombre or '').strip()
            clave = str(ing.articulo_id or _norm(nombre))
            vistos[clave] = vistos.get(clave, 0) + 1
            if ing.cantidad is None:
                hallazgos.append(self._h('INGREDIENTE_SIN_CANTIDAD', 'ERROR', 'CANTIDAD', f'{nombre} no tiene cantidad.', ingrediente=nombre, recomendacion='Indica una cantidad mayor que cero.'))
            else:
                try:
                    cantidad = float(ing.cantidad)
                except (TypeError, ValueError):
                    cantidad = 0
                if cantidad <= 0:
                    hallazgos.append(self._h('CANTIDAD_NO_POSITIVA', 'ERROR', 'CANTIDAD', f'{nombre} tiene una cantidad inválida.', evidencia=str(ing.cantidad), ingrediente=nombre, recomendacion='La cantidad debe ser mayor que cero.'))
                elif cantidad > 10000:
                    hallazgos.append(self._h('CANTIDAD_ATIPICA', 'AVISO', 'CANTIDAD', f'{nombre} tiene una cantidad extraordinariamente alta.', evidencia=f'{cantidad} {ing.unidad}', ingrediente=nombre, recomendacion='Comprueba la escala y la unidad.'))
            unidad = _norm(ing.unidad)
            if not unidad:
                hallazgos.append(self._h('INGREDIENTE_SIN_UNIDAD', 'ERROR', 'UNIDAD', f'{nombre} no tiene unidad.', ingrediente=nombre, recomendacion='Indica kg, g, l, ml o ud.'))
            elif unidad not in self.UNIDADES_VALIDAS:
                hallazgos.append(self._h('UNIDAD_NO_NORMALIZADA', 'AVISO', 'UNIDAD', f'{nombre} utiliza una unidad no normalizada.', evidencia=ing.unidad, ingrediente=nombre, recomendacion='Define una conversión o normaliza la unidad.'))
            if not str(ing.articulo_id or '').strip():
                hallazgos.append(self._h('ARTICULO_NO_VINCULADO', 'ERROR', 'VINCULACION', f'{nombre} no está vinculado a un artículo real.', ingrediente=nombre, recomendacion='Resuelve el ingrediente mediante M1.2.'))
                continue
            articulo = articulos.get(str(ing.articulo_id))
            if not articulo:
                hallazgos.append(self._h('ARTICULO_INEXISTENTE', 'ERROR', 'VINCULACION', f'El artículo vinculado a {nombre} ya no existe.', evidencia=str(ing.articulo_id), ingrediente=nombre, recomendacion='Vuelve a vincular el ingrediente.'))
                continue
            clase = clasificar_prefijo_articulo(articulo)
            if clase == 'APERITIVO' or str(ing.clase_articulo or '').upper() == 'APERITIVO':
                hallazgos.append(self._h('AP_COMO_MATERIA_PRIMA', 'ERROR', 'CLASIFICACION', f'{nombre} es un A.P (Aperitivo), no una M.P.', evidencia=str(ing.articulo_id), ingrediente=nombre, recomendacion='Vincula una materia prima o confirma explícitamente que se trata de un componente compuesto.'))
            self._validar_coherencia_unidad(nombre, unidad, hallazgos)
        for clave, total in vistos.items():
            if total > 1:
                hallazgos.append(self._h('INGREDIENTE_DUPLICADO', 'AVISO', 'DUPLICADOS', 'El mismo ingrediente aparece más de una vez.', evidencia=f'{clave} × {total}', recomendacion='Agrupa las líneas si no representan fases distintas.'))

    def _validar_coherencia_unidad(self, nombre: str, unidad: str, hallazgos) -> None:
        n = _norm(nombre)
        tokens = set(n.split())
        if tokens & self.SOLIDOS_GRASOS and unidad in self.UNIDADES_VOLUMEN:
            hallazgos.append(self._h('UNIDAD_SOSPECHOSA_SOLIDO', 'AVISO', 'COHERENCIA_CULINARIA', f'{nombre} está expresado en volumen.', evidencia=unidad, ingrediente=nombre, recomendacion='Confirma si debe expresarse en kg o g.'))
        elif tokens & self.LIQUIDOS and unidad in self.UNIDADES_UNIDAD:
            hallazgos.append(self._h('UNIDAD_SOSPECHOSA_LIQUIDO', 'AVISO', 'COHERENCIA_CULINARIA', f'{nombre} líquido está expresado en unidades.', evidencia=unidad, ingrediente=nombre, recomendacion='Confirma si debe expresarse en l, ml o kg.'))
        if any(especia in n for especia in self.ESPECIAS) and unidad in self.UNIDADES_VOLUMEN:
            hallazgos.append(self._h('UNIDAD_SOSPECHOSA_ESPECIA', 'AVISO', 'COHERENCIA_CULINARIA', f'{nombre} está expresado en volumen.', evidencia=unidad, ingrediente=nombre, recomendacion='Confirma si debe expresarse en g o kg.'))

    def _validar_coste(self, b, articulos, hallazgos, criterios) -> tuple[float | None, float | None]:
        criterios.append('COHERENCIA_ECONOMICA')
        if not b.ingredientes:
            return None, None
        coste_total = 0.0
        con_precio = 0
        sin_precio = []
        for ing in b.ingredientes:
            articulo = articulos.get(str(ing.articulo_id or ''))
            if not articulo or ing.cantidad is None:
                continue
            precio = articulo.get('precio')
            try:
                precio_f = float(precio) if precio not in (None, '') else None
            except (TypeError, ValueError):
                precio_f = None
            if precio_f is None or precio_f < 0:
                sin_precio.append(ing.nombre)
                continue
            con_precio += 1
            coste_total += float(ing.cantidad) * precio_f
        if sin_precio:
            hallazgos.append(self._h('COSTE_INCOMPLETO', 'AVISO', 'COSTE', 'No se puede cerrar el coste real porque hay artículos sin precio.', evidencia=', '.join(sin_precio), recomendacion='Completa precios antes de usar el escandallo como definitivo.'))
        try:
            rendimiento = float(b.rendimiento or 0)
        except (TypeError, ValueError):
            rendimiento = 0
        if con_precio == 0 or rendimiento <= 0:
            return None, None
        coste_total = round(coste_total, 6)
        coste_racion = round(coste_total / rendimiento, 6)
        if coste_racion > self.coste_racion_aviso_alto:
            hallazgos.append(self._h('COSTE_RACION_ALTO', 'AVISO', 'COSTE', 'El coste por ración supera el umbral de revisión.', evidencia=f'{coste_racion:.4f} €', recomendacion='Comprueba cantidades, unidades y precios.'))
        elif 0 < coste_racion < self.coste_racion_aviso_bajo:
            hallazgos.append(self._h('COSTE_RACION_BAJO', 'AVISO', 'COSTE', 'El coste por ración es excepcionalmente bajo.', evidencia=f'{coste_racion:.4f} €', recomendacion='Comprueba precios, cantidades y rendimiento.'))
        return coste_total, coste_racion

    def _validar_documentacion(self, b, metadatos, hallazgos, criterios) -> None:
        criterios.append('DOCUMENTACION_OPERATIVA')
        elaboracion = str(b.elaboracion or '').strip()
        if not elaboracion:
            hallazgos.append(self._h('SIN_ELABORACION', 'AVISO', 'ELABORACION', 'La receta no contiene un procedimiento de elaboración.', recomendacion='Añade fases claras de preparación, cocción y acabado.'))
        elif len(_norm(elaboracion).split()) < 4:
            hallazgos.append(self._h('ELABORACION_INSUFICIENTE', 'AVISO', 'ELABORACION', 'La elaboración es demasiado breve para una ficha operativa.', evidencia=elaboracion, recomendacion='Describe las fases críticas y los puntos de control.'))
        texto = _norm(elaboracion)
        tiempos = metadatos.get('tiempos') or re.search(r'\b\d+\s*(min|minutos?|h|horas?)\b', texto)
        if not tiempos:
            hallazgos.append(self._h('SIN_TIEMPOS', 'AVISO', 'TIEMPOS', 'No se han indicado tiempos de elaboración o cocción.', recomendacion='Añade tiempos activos, pasivos y de cocción cuando proceda.'))
        conservacion = metadatos.get('conservacion') or any(x in texto for x in ('conservar', 'nevera', 'refriger', 'congel', 'caduc', 'abat'))
        if not conservacion:
            hallazgos.append(self._h('SIN_CONSERVACION', 'AVISO', 'CONSERVACION', 'No se ha indicado conservación o vida útil.', recomendacion='Indica temperatura, recipiente y duración segura.'))
        alergenos = metadatos.get('alergenos')
        if not alergenos:
            hallazgos.append(self._h('ALERGENOS_NO_REVISADOS', 'AVISO', 'ALERGENOS', 'Los alérgenos no constan como revisados.', recomendacion='Revisa alérgenos desde los artículos y confirma el resultado.'))

    def _indice_articulos(self) -> dict[str, dict[str, Any]]:
        if not self.ruta_articulos.exists():
            return {}
        try:
            data = json.loads(self.ruta_articulos.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, list):
            data = list(data.get('articulos') or []) if isinstance(data, dict) else []
        return {
            str(a.get('codigo') or a.get('id') or a.get('articulo_id')): a
            for a in data if a.get('codigo') or a.get('id') or a.get('articulo_id')
        }

    @staticmethod
    def _h(codigo, severidad, categoria, mensaje, evidencia='', recomendacion='', ingrediente=''):
        return HallazgoCulinarioM133(codigo, severidad, categoria, mensaje, evidencia, recomendacion, ingrediente)


__all__ = ['ValidadorCulinarioM133', 'ResultadoValidacionM133', 'HallazgoCulinarioM133']
