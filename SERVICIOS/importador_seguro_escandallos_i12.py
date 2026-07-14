from __future__ import annotations

from dataclasses import dataclass, asdict, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable
import json
import re
import unicodedata

from SERVICIOS.detector_escandallos_antiguos_i11 import DetectorEscandallosAntiguosI11

# Palabras de formato/compra que no identifican el producto.
_STOPWORDS = {
    'de','del','la','el','los','las','con','sin','para','por','y','i','en','un','una',
    'pqt','paq','paquete','pack','caja','bandeja','manojo','botella','garrafa','bolsa','saco',
    'unidad','unidades','unid','ud','uds','formato','aprox','peso','neto','bruto','precio',
    'medio','trozo','precortado','precortada','extra','extras','limpio','limpia','pelado','pelada',
    'rojo','roja','blanco','blanca',
}
_UNIDADES = {
    'kg','kgs','kilo','kilos','g','gr','gramo','gramos','l','lt','lts','litro','litros','ml','cl',
    'cm','mm','u','ud','uds','unidad','unidades','unid'
}
_ALIAS = {
    'galtes': 'carrillera', 'galta': 'carrillera', 'carrilleras': 'carrillera',
    'porc': 'cerdo', 'porco': 'cerdo',
    'carxofa': 'alcachofa', 'carxofes': 'alcachofa', 'alcachofas': 'alcachofa',
    'tomaquet': 'tomate', 'tomates': 'tomate',
    'llimona': 'limon', 'llimones': 'limon', 'limones': 'limon',
    'ceba': 'cebolla', 'cebes': 'cebolla', 'cebollas': 'cebolla',
    'pastanaga': 'zanahoria', 'pastanagues': 'zanahoria', 'zanahorias': 'zanahoria',
    'porros': 'puerro', 'puerros': 'puerro',
    'patates': 'patata', 'patatas': 'patata',
    'ous': 'huevo', 'huevos': 'huevo',
    'formatge': 'queso', 'formatges': 'queso', 'quesos': 'queso',
    'gambas': 'gamba', 'langostinos': 'langostino',
    'aguacates': 'aguacate', 'nachos': 'nacho', 'tortillas': 'tortilla',
    'microbrotes': 'microbrote', 'picatostes': 'picatoste',
}


def _sin_acentos(valor: Any) -> str:
    texto = str(valor or '').strip().lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')


def _tokens(valor: Any, *, conservar_formato: bool = False) -> list[str]:
    texto = _sin_acentos(valor).replace('€', ' ')
    # Elimina cifras, formatos y anotaciones económicas largas.
    texto = re.sub(r'\([^)]*\)', ' ', texto)
    texto = re.sub(r'\b\d+(?:[.,]\d+)?\s*(?:kg|kgs|g|gr|l|lt|lts|ml|cl|u|ud|uds|unid|cm|mm)\b', ' ', texto)
    texto = re.sub(r'\b\d+(?:[.,]\d+)?\b', ' ', texto)
    crudos = re.findall(r'[a-z]+', texto)
    salida: list[str] = []
    for token in crudos:
        token = _ALIAS.get(token, token)
        if not conservar_formato and (token in _STOPWORDS or token in _UNIDADES):
            continue
        # Singularización ligera para plurales regulares.
        if len(token) > 4 and token.endswith('es') and token[:-2] not in {'ques'}:
            token = token[:-2]
        elif len(token) > 3 and token.endswith('s'):
            token = token[:-1]
        token = _ALIAS.get(token, token)
        if token and token not in salida:
            salida.append(token)
    return salida


def _norm(valor: Any) -> str:
    return ' '.join(_tokens(valor))


def _codigo(nombre: str, usados: set[str]) -> str:
    base = re.sub(r'[^A-Z0-9]+', '-', _norm(nombre).upper()).strip('-')[:28] or 'RECETA'
    cod = f'REC-{base}'
    n = 2
    while cod in usados:
        cod = f'REC-{base[:24]}-{n}'
        n += 1
    usados.add(cod)
    return cod


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _cobertura(origen: set[str], destino: set[str]) -> float:
    if not origen:
        return 0.0
    return len(origen & destino) / len(origen)


def _similitud_nombre(origen: str, destino: str) -> tuple[float, list[str]]:
    no, nd = _norm(origen), _norm(destino)
    to, td = set(no.split()), set(nd.split())
    if not no or not nd:
        return 0.0, []
    if no == nd:
        return 1.0, ['nombre normalizado idéntico']

    seq = SequenceMatcher(None, no, nd).ratio()
    jac = _jaccard(to, td)
    cov_o = _cobertura(to, td)
    cov_d = _cobertura(td, to)
    motivos: list[str] = []

    # Coincidencia por núcleo: el catálogo suele contener un nombre corto y el Excel añade formato/envase.
    if td and td.issubset(to):
        nucleo = min(1.0, 0.90 + 0.02 * min(len(td), 4))
        motivos.append('el nombre del catálogo está contenido en la descripción del Excel')
    elif to and to.issubset(td):
        nucleo = min(1.0, 0.88 + 0.02 * min(len(to), 4))
        motivos.append('la descripción del Excel está contenida en el nombre del catálogo')
    else:
        nucleo = 0.0

    score = max(
        nucleo,
        0.48 * jac + 0.32 * max(cov_o, cov_d) + 0.20 * seq,
        0.78 * max(cov_o, cov_d) + 0.22 * seq if min(len(to), len(td)) <= 3 else 0.0,
    )
    if jac >= .5:
        motivos.append('comparte la mayoría de palabras relevantes')
    if seq >= .8:
        motivos.append('texto muy parecido')
    return min(1.0, score), motivos


@dataclass
class VinculoIngredienteI12:
    nombre_excel: str
    cantidad: float | None
    unidad: str
    precio_unitario: float | None
    coste: float | None
    articulo_id: str = ''
    articulo_nombre: str = ''
    confianza: float = 0.0
    estado: str = 'sin_resolver'  # exacto | probable | sin_resolver
    candidatos: list[dict[str, Any]] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    motivo_vinculo: str = ''


@dataclass
class RecetaPreviaI12:
    hoja: str
    nombre: str
    receta_id: str
    raciones_base: int
    unidad_rendimiento: str
    grupo: str
    ingredientes: list[VinculoIngredienteI12]
    duplicado: bool = False
    duplicado_id: str = ''
    bloqueada: bool = False
    avisos: list[str] = field(default_factory=list)

    def a_dict(self):
        return asdict(self)


class ImportadorSeguroEscandallosI12:
    """I1.2.1: importación segura con vinculación culinaria inteligente."""

    def __init__(self, detector=None, umbral_probable: float = .66, umbral_exacto: float = .91, ruta_memoria: str | Path | None = None):
        self.detector = detector or DetectorEscandallosAntiguosI11()
        self.umbral_probable = float(umbral_probable)
        self.umbral_exacto = float(umbral_exacto)
        self.ruta_memoria = Path(ruta_memoria) if ruta_memoria else Path('DATOS') / 'db' / 'memoria_vinculaciones_i122.json'

    def cargar_memoria(self) -> dict[str, dict[str, Any]]:
        try:
            datos = json.loads(self.ruta_memoria.read_text(encoding='utf-8'))
            return datos if isinstance(datos, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def guardar_memoria(self, memoria: dict[str, dict[str, Any]]) -> None:
        self.ruta_memoria.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_memoria.write_text(json.dumps(memoria, ensure_ascii=False, indent=2), encoding='utf-8')

    def recordar_vinculo(self, nombre_excel: str, articulo: dict[str, Any], *, origen: str = 'revision_manual') -> dict[str, Any]:
        clave = _norm(nombre_excel)
        if not clave:
            raise ValueError('No se puede recordar un ingrediente vacío.')
        memoria = self.cargar_memoria()
        memoria[clave] = {
            'nombre_excel': nombre_excel,
            'articulo_id': str(articulo.get('articulo_id') or articulo.get('id') or articulo.get('codigo') or ''),
            'articulo_nombre': str(articulo.get('articulo_nombre') or articulo.get('nombre') or articulo.get('articulo') or ''),
            'proveedor': str(articulo.get('proveedor') or ''),
            'familia': str(articulo.get('familia') or ''),
            'origen': origen,
        }
        self.guardar_memoria(memoria)
        return memoria[clave]

    def olvidar_vinculo(self, nombre_excel: str) -> bool:
        clave = _norm(nombre_excel)
        memoria = self.cargar_memoria()
        if clave not in memoria:
            return False
        memoria.pop(clave, None)
        self.guardar_memoria(memoria)
        return True

    def aplicar_decision(self, previa: dict[str, Any], nombre_excel: str, articulo: dict[str, Any], *, recordar: bool = True) -> bool:
        clave = _norm(nombre_excel)
        encontrado = False
        for receta in previa.get('recetas', []):
            for ing in receta.get('ingredientes', []):
                if _norm(ing.get('nombre_excel')) != clave:
                    continue
                ing['articulo_id'] = str(articulo.get('articulo_id') or articulo.get('id') or articulo.get('codigo') or '')
                ing['articulo_nombre'] = str(articulo.get('articulo_nombre') or articulo.get('nombre') or articulo.get('articulo') or '')
                ing['confianza'] = 1.0
                ing['estado'] = 'exacto'
                ing['motivo_vinculo'] = 'vínculo confirmado manualmente'
                ing['avisos'] = [a for a in ing.get('avisos', []) if 'revisar' not in a.lower() and 'sin artículo' not in a.lower() and 'candidatos' not in a.lower()]
                encontrado = True
        if encontrado and recordar:
            self.recordar_vinculo(nombre_excel, articulo)
        self._recalcular_resumen(previa)
        return encontrado

    @staticmethod
    def _recalcular_resumen(previa: dict[str, Any]) -> None:
        recetas = previa.get('recetas', [])
        s = previa.setdefault('resumen', {})
        s['ingredientes'] = sum(len(r.get('ingredientes', [])) for r in recetas)
        s['vinculos_exactos'] = sum(1 for r in recetas for i in r.get('ingredientes', []) if i.get('estado') == 'exacto')
        s['vinculos_probables'] = sum(1 for r in recetas for i in r.get('ingredientes', []) if i.get('estado') == 'probable')
        s['sin_resolver'] = sum(1 for r in recetas for i in r.get('ingredientes', []) if i.get('estado') == 'sin_resolver')

    def pendientes_revision(self, previa: dict[str, Any]) -> list[dict[str, Any]]:
        vistos: set[str] = set()
        salida = []
        for receta in previa.get('recetas', []):
            for ing in receta.get('ingredientes', []):
                if ing.get('estado') == 'exacto':
                    continue
                clave = _norm(ing.get('nombre_excel'))
                if not clave or clave in vistos:
                    continue
                vistos.add(clave)
                salida.append(ing)
        return salida

    @staticmethod
    def _catalogo(datos: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
        out = []
        for a in datos or []:
            nombre = str(a.get('nombre') or a.get('articulo') or a.get('Artículo') or '').strip()
            if not nombre:
                continue
            precio_raw = a.get('precio_unitario') or a.get('precio') or a.get('Precio') or ''
            try:
                precio = float(str(precio_raw).replace(',', '.')) if str(precio_raw).strip() else 0.0
            except (TypeError, ValueError):
                precio = 0.0
            out.append({
                'id': str(a.get('id') or a.get('articulo_id') or a.get('codigo') or a.get('Código') or ''),
                'nombre': nombre,
                'unidad': str(a.get('unidad') or a.get('Unidad') or ''),
                'precio': precio,
                'familia': str(a.get('familia') or a.get('Familia') or ''),
                'proveedor': str(a.get('proveedor') or a.get('Proveedor') or ''),
            })
        return out

    @staticmethod
    def _bonus_contexto(ing: Any, articulo: dict[str, Any]) -> tuple[float, list[str]]:
        bonus = 0.0
        motivos: list[str] = []
        proveedor_ing = _norm(getattr(ing, 'proveedor', '') or '')
        familia_ing = _norm(getattr(ing, 'familia', '') or '')
        proveedor_art = _norm(articulo.get('proveedor', ''))
        familia_art = _norm(articulo.get('familia', ''))
        if proveedor_ing and proveedor_art and proveedor_ing == proveedor_art:
            bonus += .05
            motivos.append('mismo proveedor')
        if familia_ing and familia_art and familia_ing == familia_art:
            bonus += .05
            motivos.append('misma familia')
        return bonus, motivos

    def _vincular(self, ing: Any, catalogo: list[dict[str, Any]]) -> VinculoIngredienteI12:
        puntuados: list[tuple[float, dict[str, Any], list[str]]] = []
        for articulo in catalogo:
            score_nombre, motivos = _similitud_nombre(ing.nombre, articulo['nombre'])
            bonus, motivos_bonus = self._bonus_contexto(ing, articulo)
            score = min(1.0, score_nombre + bonus)
            if score >= .34:
                puntuados.append((score, articulo, motivos + motivos_bonus))

        puntuados.sort(key=lambda x: (x[0], len(_tokens(x[1]['nombre']))), reverse=True)
        candidatos = [
            {
                'articulo_id': a['id'],
                'nombre': a['nombre'],
                'confianza': round(score, 3),
                'proveedor': a.get('proveedor', ''),
                'familia': a.get('familia', ''),
                'motivo': '; '.join(motivos) or 'similitud textual',
            }
            for score, a, motivos in puntuados[:5]
        ]

        top_score = puntuados[0][0] if puntuados else 0.0
        segundo = puntuados[1][0] if len(puntuados) > 1 else 0.0
        margen = top_score - segundo
        if top_score >= self.umbral_exacto and (margen >= .04 or top_score >= .985):
            estado = 'exacto'
        elif top_score >= self.umbral_probable:
            estado = 'probable'
        else:
            estado = 'sin_resolver'

        best = puntuados[0][1] if puntuados else {}
        motivos_best = puntuados[0][2] if puntuados else []
        avisos = list(getattr(ing, 'avisos', []) or [])
        if estado == 'probable':
            avisos.append('Coincidencia probable: revisar antes de importar.')
        if estado == 'sin_resolver':
            avisos.append('Ingrediente sin artículo vinculado.')
        if estado != 'sin_resolver' and margen < .04 and len(puntuados) > 1:
            avisos.append('Hay dos candidatos muy parecidos; revisar la selección.')
            estado = 'probable'

        return VinculoIngredienteI12(
            nombre_excel=ing.nombre,
            cantidad=ing.cantidad,
            unidad=ing.unidad,
            precio_unitario=ing.precio_unitario,
            coste=ing.coste,
            articulo_id=best.get('id', '') if estado != 'sin_resolver' else '',
            articulo_nombre=best.get('nombre', '') if estado != 'sin_resolver' else '',
            confianza=round(top_score, 3),
            estado=estado,
            candidatos=candidatos,
            avisos=avisos,
            motivo_vinculo='; '.join(motivos_best) or ('sin candidato suficiente' if not puntuados else 'similitud textual'),
        )

    def preparar(self, ruta_excel: str | Path, hojas=None, catalogo_articulos=None, escandallos_existentes=None):
        analisis = self.detector.analizar(ruta_excel, hojas=hojas, exportar_json=False)
        catalogo = self._catalogo(catalogo_articulos)
        memoria = self.cargar_memoria()
        por_id_catalogo = {str(a.get('id') or ''): a for a in catalogo if str(a.get('id') or '')}
        por_nombre_catalogo = {_norm(a.get('nombre')): a for a in catalogo}
        existentes = list(escandallos_existentes or [])
        usados = {str(e.get('receta_id', '')).upper() for e in existentes}
        por_nombre = {_norm(e.get('nombre')): e for e in existentes}
        recetas = []
        for e in analisis.get('escandallos', []):
            nombre = e.get('nombre', 'Escandallo sin nombre')
            dup = por_nombre.get(_norm(nombre))
            rid = str(dup.get('receta_id')) if dup else _codigo(nombre, usados)
            ings = []
            for i in e.get('ingredientes', []):
                vinculo = self._vincular(type('Obj', (), i), catalogo)
                aprendido = memoria.get(_norm(i.get('nombre')))
                if aprendido:
                    art = por_id_catalogo.get(str(aprendido.get('articulo_id') or '')) or por_nombre_catalogo.get(_norm(aprendido.get('articulo_nombre')))
                    if art:
                        vinculo.articulo_id = art.get('id', '')
                        vinculo.articulo_nombre = art.get('nombre', '')
                        vinculo.confianza = 1.0
                        vinculo.estado = 'exacto'
                        vinculo.motivo_vinculo = 'vínculo aprendido en una revisión anterior'
                        vinculo.avisos = []
                ings.append(vinculo)
            rend = e.get('rendimiento_cantidad') or 1
            raciones = max(1, int(round(float(rend))))
            avisos = list(e.get('avisos', []) or [])
            graves = [a for a in avisos if 'No se detectaron ingredientes' in a or 'sin nombre' in a.lower()]
            if not ings:
                graves.append('Receta sin ingredientes.')
            recetas.append(RecetaPreviaI12(
                hoja=e.get('hoja', ''), nombre=nombre, receta_id=rid, raciones_base=raciones,
                unidad_rendimiento=e.get('rendimiento_unidad', ''), grupo=e.get('tipo', ''),
                ingredientes=ings, duplicado=bool(dup),
                duplicado_id=str(dup.get('receta_id', '')) if dup else '',
                bloqueada=bool(graves), avisos=avisos + graves,
            ).a_dict())
        resumen = {
            'catalogo_articulos': len(catalogo),
            'motor_vinculacion_activo': bool(catalogo),
            'recetas_detectadas': len(recetas),
            'duplicadas': sum(1 for r in recetas if r['duplicado']),
            'bloqueadas': sum(1 for r in recetas if r['bloqueada']),
            'ingredientes': sum(len(r['ingredientes']) for r in recetas),
            'vinculos_exactos': sum(1 for r in recetas for i in r['ingredientes'] if i['estado'] == 'exacto'),
            'vinculos_probables': sum(1 for r in recetas for i in r['ingredientes'] if i['estado'] == 'probable'),
            'sin_resolver': sum(1 for r in recetas for i in r['ingredientes'] if i['estado'] == 'sin_resolver'),
        }
        return {'ok': True, 'ruta': str(ruta_excel), 'recetas': recetas, 'resumen': resumen, 'modo': 'vista_previa_sin_escritura'}

    def importar(self, previa: dict[str, Any], motor_escandallos, seleccion=None,
                 confirmar: bool = False, permitir_probables: bool = False,
                 permitir_sin_resolver: bool = False):
        if not confirmar:
            raise ValueError('La importación requiere confirmación explícita.')
        seleccion = set(seleccion or [r['receta_id'] for r in previa.get('recetas', [])])
        importadas = []
        omitidas = []
        errores = []
        for r in previa.get('recetas', []):
            if r['receta_id'] not in seleccion:
                continue
            motivos = []
            if r.get('duplicado'):
                motivos.append('duplicada')
            if r.get('bloqueada'):
                motivos.append('bloqueada')
            if not permitir_probables and any(i['estado'] == 'probable' for i in r['ingredientes']):
                motivos.append('vínculos probables')
            if not permitir_sin_resolver and any(i['estado'] == 'sin_resolver' for i in r['ingredientes']):
                motivos.append('ingredientes sin resolver')
            if motivos:
                omitidas.append({'receta_id': r['receta_id'], 'nombre': r['nombre'], 'motivo': ', '.join(motivos)})
                continue
            lineas = []
            for i in r['ingredientes']:
                if not i.get('cantidad') or float(i['cantidad']) <= 0:
                    continue
                lineas.append({
                    'nombre': i.get('articulo_nombre') or i['nombre_excel'],
                    'cantidad': float(i['cantidad']), 'unidad': i.get('unidad') or '',
                    'articulo_id': i.get('articulo_id') or '',
                    'coste_unitario': float(i.get('precio_unitario') or 0),
                    'notas': f"Importado desde {r['hoja']} | original: {i['nombre_excel']}",
                })
            try:
                dato = motor_escandallos.registrar_escandallo(
                    receta_id=r['receta_id'], nombre=r['nombre'], raciones_base=r['raciones_base'],
                    lineas=lineas, grupo=r.get('grupo', ''), subgrupo='Importado Excel legacy',
                    observaciones=f"I1.2.1 importado desde hoja {r['hoja']}")
                importadas.append(dato)
            except Exception as exc:
                errores.append({'receta_id': r['receta_id'], 'nombre': r['nombre'], 'error': str(exc)})
        return {'ok': not errores, 'importadas': importadas, 'omitidas': omitidas, 'errores': errores,
                'resumen': {'importadas': len(importadas), 'omitidas': len(omitidas), 'errores': len(errores)}}


def formatear_previa_i12(p):
    s = p['resumen']
    lineas = [
        'I1.2.1 — VISTA PREVIA CON VINCULACIÓN INTELIGENTE', '=' * 74,
        f"Catálogo: {s.get('catalogo_articulos', 0)} artículo(s) | Motor: {'ACTIVO' if s.get('motor_vinculacion_activo') else 'INACTIVO'}",
        f"Recetas: {s['recetas_detectadas']} | Duplicadas: {s['duplicadas']} | Bloqueadas: {s['bloqueadas']}",
        f"Ingredientes: {s['ingredientes']} | Exactos: {s['vinculos_exactos']} | Probables: {s['vinculos_probables']} | Sin resolver: {s['sin_resolver']}",
    ]
    for n, r in enumerate(p['recetas'], 1):
        estado = []
        if r['duplicado']:
            estado.append('DUPLICADA')
        if r['bloqueada']:
            estado.append('BLOQUEADA')
        lineas.append(f"{n}. {r['receta_id']} | {r['nombre']} | {r['raciones_base']} base | {len(r['ingredientes'])} ingredientes" + (f" | {'/'.join(estado)}" if estado else ''))
        for i in r['ingredientes']:
            destino = i['articulo_nombre'] or 'SIN VINCULAR'
            lineas.append(f"   - {i['nombre_excel']} -> {destino} [{i['estado']}, {i['confianza']:.0%}]")
            if i.get('motivo_vinculo') and i['estado'] != 'sin_resolver':
                lineas.append(f"     Motivo: {i['motivo_vinculo']}")
            if i['estado'] != 'exacto' and i.get('candidatos'):
                alternativas = ', '.join(f"{c['nombre']} ({c['confianza']:.0%})" for c in i['candidatos'][:3])
                lineas.append(f"     Candidatos: {alternativas}")
    lineas += ['=' * 74, 'VISTA PREVIA: no se ha modificado la base de datos.']
    return '\n'.join(lineas)
