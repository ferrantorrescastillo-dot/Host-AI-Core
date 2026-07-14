from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict
from typing import Any


def _norm(v: Any) -> str:
    t = unicodedata.normalize('NFKD', str(v or ''))
    t = ''.join(c for c in t if not unicodedata.combining(c)).lower().strip()
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', t).split())


@dataclass(frozen=True)
class ConceptoCulinario:
    rol: str
    nombre: str
    confianza: float
    evidencia: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MotorInterpretacionCulinariaI13414:
    """Agrupa fragmentos lingüísticos en conceptos culinarios explicables.

    No busca ni crea entidades. Solo sustituye fragmentos excesivamente atomizados
    por unidades culinarias más útiles para el MUR y la bandeja de revisión.
    """

    VERSION = 'I1.3.4.1.4'
    ACABADOS = {'avellanas', 'almendras', 'pistachos', 'sesamo', 'frambuesa liofilizada', 'cebollino'}
    CONDIMENTOS = {'yondu', 'curri', 'curry', 'sal', 'pimienta', 'aceite'}

    @staticmethod
    def _limpiar(texto: str) -> str:
        return re.sub(r'\s+', ' ', str(texto or '').strip(' .,-;:'))

    def interpretar(self, nombre: str, componentes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        texto = self._limpiar(nombre)
        n = _norm(texto)
        existentes = componentes or []
        catalogados = [c for c in existentes if c.get('catalogado')]
        no_catalogados = [c for c in existentes if not c.get('catalogado')]

        # Las recetas/entidades ya reconocidas prevalecen. El motor no reinterpreta
        # texto residual cuando ya existe un núcleo catalogado; esa limpieza corresponde
        # al clasificador gastronómico (p. ej. MENU/POR PAX).
        if catalogados:
            return {'version': self.VERSION, 'aplicada': False, 'conceptos': [], 'razon': 'Existe conocimiento catalogado que debe conservarse.'}
        if len(no_catalogados) < 2:
            return {'version': self.VERSION, 'aplicada': False, 'conceptos': [], 'razon': 'No existe atomización excesiva.'}

        conceptos: list[ConceptoCulinario] = []
        bajo = texto.lower()

        # Patrones de alta confianza observados en nomenclatura culinaria real.
        m = re.match(r'^(crema de [^,]+),?\s*([^,]+?)\s+con\s+(.+)$', texto, re.I)
        if m:
            conceptos = [
                ConceptoCulinario('RECETA_PRINCIPAL', self._limpiar(m.group(1)), .94, 'Núcleo culinario antes de la coma.'),
                ConceptoCulinario('GUARNICION', self._limpiar(m.group(2)), .78, 'Elemento servido junto al núcleo.'),
                ConceptoCulinario('ELABORACION', self._limpiar(m.group(3)), .84, 'Elaboración compuesta introducida por «con».'),
            ]
        elif re.match(r'^lenguado\s+a\s+la\s+menier', bajo):
            resto = re.sub(r'^lenguado\s+a\s+la\s+menier\s*', '', texto, flags=re.I).strip()
            cond = None
            guarn = []
            m2 = re.match(r'^de\s+(.+?)\s+con\s+(.+)$', resto, re.I)
            if m2:
                cond = self._limpiar(m2.group(1))
                guarn = [self._limpiar(x) for x in re.split(r'\s+y\s+', m2.group(2), flags=re.I)]
            conceptos = [ConceptoCulinario('RECETA_PRINCIPAL', 'Lenguado a la menier', .95, 'Técnica culinaria inseparable del producto principal.')]
            if cond:
                conceptos.append(ConceptoCulinario('CONDIMENTO', cond, .80, 'Ingrediente introducido por «de» tras la técnica.'))
            for idx, x in enumerate(guarn):
                rol = 'ACABADO' if _norm(x) in self.ACABADOS or idx > 0 else 'GUARNICION'
                conceptos.append(ConceptoCulinario(rol, x, .78, 'Componente posterior a «con/y».'))
        elif re.match(r'^tournedo\b', bajo) and re.search(r'\s+con\s+', bajo):
            principal, guarn = re.split(r'\s+con\s+', texto, maxsplit=1, flags=re.I)
            conceptos = [
                ConceptoCulinario('RECETA_PRINCIPAL', self._limpiar(principal), .92, 'Preparación principal completa antes de «con».'),
                ConceptoCulinario('GUARNICION', self._limpiar(guarn), .86, 'Acompañamiento introducido por «con».'),
            ]
        elif re.match(r'^lingote\b', bajo) and ',' in texto:
            partes = [self._limpiar(x) for x in re.split(r',|\s+y\s+', texto, flags=re.I) if self._limpiar(x)]
            if partes:
                conceptos.append(ConceptoCulinario('RECETA_PRINCIPAL', partes[0], .88, 'Primer concepto nominal del postre.'))
                for p in partes[1:]:
                    rol = 'ELABORACION' if re.search(r'\bespuma\b|\bcrema\b|\bgel\b', p, re.I) else 'ACABADO'
                    conceptos.append(ConceptoCulinario(rol, p, .80, 'Componente separado por coma o conjunción.'))
        else:
            # Regla general conservadora: núcleo antes de «con» y grupos completos tras él.
            partes_con = re.split(r'\s+con\s+', texto, maxsplit=1, flags=re.I)
            if len(partes_con) == 2 and len(_norm(partes_con[0]).split()) >= 2:
                conceptos.append(ConceptoCulinario('RECETA_PRINCIPAL', self._limpiar(partes_con[0]), .76, 'Núcleo anterior a «con».'))
                finales = [self._limpiar(x) for x in re.split(r'\s+y\s+|,', partes_con[1], flags=re.I) if self._limpiar(x)]
                for x in finales:
                    xn = _norm(x)
                    if any(k in xn for k in ('salsa', 'alioli', 'romesco', 'pesto')):
                        rol = 'SALSA'
                    elif xn in self.CONDIMENTOS:
                        rol = 'CONDIMENTO'
                    elif xn in self.ACABADOS:
                        rol = 'ACABADO'
                    else:
                        rol = 'GUARNICION'
                    conceptos.append(ConceptoCulinario(rol, x, .70, 'Grupo completo posterior a «con/y».'))

        if len(conceptos) < 2:
            return {'version': self.VERSION, 'aplicada': False, 'conceptos': [], 'razon': 'No hay una interpretación suficientemente segura.'}

        return {
            'version': self.VERSION,
            'aplicada': True,
            'texto_original': texto,
            'conceptos': [c.to_dict() for c in conceptos],
            'fragmentos_anteriores': [str(c.get('nombre') or '') for c in no_catalogados],
            'catalogados_conservados': len(catalogados),
            'confianza_media': round(sum(c.confianza for c in conceptos) / len(conceptos), 3),
            'solo_interpretacion': True,
        }

    def convertir_componentes(self, interpretacion: dict[str, Any]) -> list[dict[str, Any]]:
        salida = []
        for c in interpretacion.get('conceptos', []):
            salida.append({
                'rol': c['rol'], 'grupo': c['rol'], 'nombre': c['nombre'],
                'tipo_entidad': 'NO_CATALOGADO', 'entidad_id': '',
                'estado': 'PENDIENTE_CATALOGO', 'confianza': c['confianza'],
                'catalogado': False, 'origen': 'motor_interpretacion_i13414',
                'evidencia_interpretacion': c['evidencia'],
            })
        return salida
