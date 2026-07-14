from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


def _norm(value: Any) -> str:
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch)).lower().strip()
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', text).split())


@dataclass(frozen=True)
class ConocimientoGastronomico:
    tipo: str
    confianza: float
    motivo: str
    destino_importacion: str
    activa_arbol: bool
    aprendido: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MotorConocimientoGastronomicoI13415:
    """Clasifica la naturaleza gastronómica de conceptos ya interpretados.

    No crea recetas ni artículos. Solo propone/aplica una clasificación explicable.
    Las decisiones confirmadas por el usuario prevalecen sobre las reglas internas.
    """

    VERSION = 'I1.3.4.1.5'

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir).resolve() if base_dir else None
        self.ruta_aprendizaje = (
            self.base_dir / 'DATOS' / 'mur' / 'aprendizajes_revision_i13413.json'
            if self.base_dir else None
        )
        self.aprendizajes = self._cargar_aprendizajes()

    def _cargar_aprendizajes(self) -> dict[str, dict[str, Any]]:
        if not self.ruta_aprendizaje or not self.ruta_aprendizaje.exists():
            return {}
        try:
            data = json.loads(self.ruta_aprendizaje.read_text(encoding='utf-8'))
        except Exception:
            return {}
        salida: dict[str, dict[str, Any]] = {}
        for item in data if isinstance(data, list) else []:
            texto = _norm(item.get('texto'))
            if texto and item.get('confirmado'):
                salida[texto] = item
        return salida

    @staticmethod
    def _es_comercial(n: str) -> bool:
        return any(x in n for x in (
            ' caja ', ' bote ', ' botella ', ' lata ', ' kg ', ' lt ', ' litro ',
            ' unid ', ' precio ', ' sin cargo ', ' bag in box ', ' sobre de '
        )) or bool(re.search(r'\b\d+[,.]?\d*\s*(kg|gr|g|lt|l|ml|unid)\b', n))

    def clasificar(self, nombre: str, contexto: dict[str, Any] | None = None) -> ConocimientoGastronomico:
        n = _norm(nombre)
        ctx = contexto or {}
        aprendido = self.aprendizajes.get(n)
        if aprendido:
            accion = str(aprendido.get('accion') or '').upper()
            valor = str(aprendido.get('valor') or '').upper()
            tipo = valor if accion == 'CLASIFICAR' and valor else 'ELEMENTO_APRENDIDO'
            return ConocimientoGastronomico(tipo, 1.0, 'Decisión confirmada anteriormente por el usuario.', tipo, tipo.startswith('PLATO'), True)

        if re.match(r'^(a\s*p|ap)\b', n):
            return ConocimientoGastronomico('APERITIVO_PREPARADO', 1.0, 'El prefijo A.P identifica un aperitivo preparado.', 'APERITIVO_PREPARADO', False)
        if re.match(r'^(m\s*p|mp)\b', n):
            return ConocimientoGastronomico('MATERIA_PRIMA', 1.0, 'El prefijo M.P identifica una materia prima.', 'ARTICULO_DIRECTO', False)

        # En conceptos ya interpretados, el rol culinario prevalece sobre palabras residuales
        # como «unid» o «precio» que puedan formar parte de un texto antiguo.
        if ctx.get('rol') in {'GUARNICION', 'CONDIMENTO', 'ACABADO', 'ELABORACION', 'SALSA'}:
            rol = str(ctx['rol'])
            return ConocimientoGastronomico(rol, .82, f'Rol culinario proporcionado por el intérprete: {rol}.', rol + '_MENU', False)

        comercial = self._es_comercial(' ' + n + ' ')
        if comercial:
            if any(x in n for x in ('salsa', 'allioli', 'romesco')):
                return ConocimientoGastronomico('SALSA_COMERCIAL', .96, 'Es una salsa con formato de compra/envase comercial.', 'ARTICULO_DIRECTO', False)
            return ConocimientoGastronomico('ARTICULO_COMERCIAL', .94, 'Contiene envase, precio o unidad de compra.', 'ARTICULO_DIRECTO', False)

        if re.search(r'\b(coulant|lingote|tarta|pastel|tiramisu|mousse)\b', n):
            return ConocimientoGastronomico('POSTRE', .96, 'Patrón gastronómico inequívoco de postre.', 'POSTRE_MENU', False)
        if any(x in n for x in ('salsa romesco', 'allioli', 'alioli', 'salsa ')) or n.startswith('romesco'):
            return ConocimientoGastronomico('SALSA', .98, 'Denominación culinaria propia de una salsa.', 'SALSA_MENU', False)
        if any(x in n for x in ('tartar', 'tempura', 'hamburguesa', 'parrillada', 'croqueta')):
            return ConocimientoGastronomico('APERITIVO_PREPARADO', .92, 'Preparación culinaria servible como unidad gastronómica.', 'APERITIVO_PREPARADO', False)
        if any(x in n for x in ('ensalada', 'ensaladilla')):
            return ConocimientoGastronomico('ELABORACION', .91, 'Preparación culinaria compuesta, no mero complemento comercial.', 'ELABORACION_MENU', False)
        if any(x in n for x in ('crema de ', 'crema calenta', 'crema caliente', 'lenguado ', 'tournedo ', 'solomillo ', 'carpaccio ', 'huevos rotos')):
            return ConocimientoGastronomico('RECETA', .90, 'Nombre completo de una preparación culinaria principal.', 'PLATO_MENU', True)
        if any(x in n for x in ('gazpacho', 'salmorejo', 'brocheta', 'ostra', 'mini burguer', 'arroz negro', 'fideos rossos')):
            return ConocimientoGastronomico('APERITIVO_PREPARADO', .90, 'Preparación culinaria habitual de cóctel o aperitivo.', 'APERITIVO_PREPARADO', False)
        return ConocimientoGastronomico('DESCONOCIDO', .45, 'No hay conocimiento suficiente para automatizar la clasificación.', 'REVISION', False)

    @staticmethod
    def es_alta_confianza(resultado: ConocimientoGastronomico, umbral: float = .90) -> bool:
        return resultado.confianza >= umbral and resultado.tipo != 'DESCONOCIDO'
