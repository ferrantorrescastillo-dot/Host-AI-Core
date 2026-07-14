from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re
import shutil
import unicodedata
import uuid

from SERVICIOS.preimportador_definitivo_menus_i133 import (
    PreimportadorDefinitivoMenusI133,
    formatear_preimportacion_i133,
)
from SERVICIOS.vista_previa_resolucion_asistida_menus_i1323 import DecisionResolucionI1323


def _norm(value: Any) -> str:
    text = str(value or '').strip().lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', text).strip(' .')


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class ResolutorBloqueosPreimportacionI1331:
    """I1.3.3.1 — resuelve bloqueos y recalcula la preimportación.

    Escrituras permitidas y controladas:
    - crear una receta completa mínima en escandallos.json;
    - actualizar la memoria culinaria confirmada;
    - generar una copia de seguridad antes de escribir.

    Nunca importa el menú.
    """

    VERSION = 'I1.3.3.1'

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()
        self.preimportador = PreimportadorDefinitivoMenusI133(self.base_dir)
        self.ruta_recetas = self.base_dir / 'DATOS' / 'db' / 'escandallos.json'
        self.ruta_articulos = self.base_dir / 'DATOS' / 'db' / 'articulos.json'

    @staticmethod
    def _load_list(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, list):
            raise ValueError(f'Formato no compatible en {path.name}: se esperaba una lista.')
        return data

    def listar_recetas(self) -> list[dict[str, Any]]:
        return [r for r in self._load_list(self.ruta_recetas) if r.get('activo', True)]

    def listar_articulos(self) -> list[dict[str, Any]]:
        return [a for a in self._load_list(self.ruta_articulos) if a.get('activo', True)]

    def buscar_recetas(self, texto: str, limite: int = 12) -> list[dict[str, Any]]:
        q = _norm(texto)
        recetas = self.listar_recetas()
        if not q:
            return recetas[:limite]
        exactas = [r for r in recetas if _norm(r.get('nombre')) == q]
        parciales = [r for r in recetas if q in _norm(r.get('nombre')) and r not in exactas]
        inversas = [r for r in recetas if _norm(r.get('nombre')) in q and r not in exactas and r not in parciales]
        return (exactas + parciales + inversas)[:limite]

    def buscar_articulos(self, texto: str, limite: int = 15) -> list[dict[str, Any]]:
        q = _norm(texto)
        arts = self.listar_articulos()
        exactas = [a for a in arts if _norm(a.get('nombre') or a.get('articulo')) == q]
        parciales = [a for a in arts if q and q in _norm(a.get('nombre') or a.get('articulo')) and a not in exactas]
        return (exactas + parciales)[:limite]

    def _backup(self, path: Path) -> Path:
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.base_dir / 'DATOS' / 'backups' / 'i1331'
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / f'{path.stem}_{stamp}{path.suffix}'
        if path.exists():
            shutil.copy2(path, target)
        else:
            target.write_text('[]', encoding='utf-8')
        return target

    @staticmethod
    def _atomic_write(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + '.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(path)

    def _update_learning(self, bloqueo: dict[str, Any], receta: dict[str, Any]) -> None:
        componente = str(bloqueo.get('componente') or '').strip()
        rol = str(bloqueo.get('rol') or 'COMPONENTE_PENDIENTE')
        receta_id = str(receta.get('receta_id') or receta.get('id') or '')
        # Si el bloqueo procede de una propuesta ya aprendida, transforma ese
        # mismo registro. Así conservamos la clave original del Excel
        # (p. ej. "parmentier patata") y todo su historial.
        for ap in self.preimportador.aprendizaje.listar_aprendizajes():
            if _norm(ap.get('nombre_destino')) == _norm(componente) or _norm(ap.get('texto_origen')) == _norm(componente):
                self.preimportador.aprendizaje.editar_aprendizaje(
                    ap['aprendizaje_id'],
                    rol=rol, accion='VINCULAR_RECETA',
                    nombre_destino=str(receta.get('nombre') or ''),
                    tipo_destino='RECETA', entidad_id=receta_id,
                    confianza=1.0, estado='ACTIVO',
                )
                return
        decision = DecisionResolucionI1323(
            texto_origen=componente, rol=rol, accion='VINCULAR_RECETA',
            nombre_destino=str(receta.get('nombre') or ''),
            tipo_destino='RECETA', entidad_id=receta_id, confianza=1.0,
        )
        self.preimportador.aprendizaje.guardar_decision(decision)

    def vincular_receta(self, bloqueo: dict[str, Any], receta_id: str) -> dict[str, Any]:
        receta = next((r for r in self.listar_recetas() if str(r.get('receta_id') or r.get('id')) == str(receta_id)), None)
        if not receta:
            raise ValueError('La receta seleccionada no existe o no está activa.')
        self._update_learning(bloqueo, receta)
        return {'ok': True, 'accion': 'VINCULAR_RECETA', 'receta': deepcopy(receta), 'datos_modificados': True}

    def crear_receta(self, bloqueo: dict[str, Any], ficha: dict[str, Any]) -> dict[str, Any]:
        nombre = str(ficha.get('nombre') or bloqueo.get('componente') or '').strip()
        if len(nombre) < 3:
            raise ValueError('El nombre de la receta es obligatorio.')
        try:
            raciones = float(ficha.get('raciones_base'))
        except (TypeError, ValueError):
            raise ValueError('El rendimiento base debe ser numérico.')
        if raciones <= 0:
            raise ValueError('El rendimiento base debe ser mayor que cero.')
        ingredientes = list(ficha.get('ingredientes') or [])
        if not ingredientes:
            raise ValueError('La receta debe contener al menos un ingrediente real.')

        articulos = {str(a.get('id') or a.get('articulo_id') or ''): a for a in self.listar_articulos()}
        lineas = []
        coste_total = 0.0
        for ing in ingredientes:
            art_id = str(ing.get('articulo_id') or '')
            art = articulos.get(art_id)
            if not art:
                raise ValueError(f'El ingrediente {ing.get("nombre") or art_id} no existe en el catálogo de artículos.')
            try:
                cantidad = float(ing.get('cantidad'))
            except (TypeError, ValueError):
                raise ValueError(f'Cantidad no válida para {art.get("nombre") or art.get("articulo")}.')
            if cantidad <= 0:
                raise ValueError('Todas las cantidades deben ser mayores que cero.')
            coste_unitario = float(art.get('precio') or art.get('coste_unitario') or 0)
            coste_linea = cantidad * coste_unitario
            coste_total += coste_linea
            lineas.append({
                'nombre': art.get('nombre') or art.get('articulo'),
                'cantidad': cantidad,
                'unidad': str(ing.get('unidad') or art.get('unidad') or '').strip(),
                'tipo': 'articulo',
                'articulo_id': art_id,
                'elaboracion_id': '',
                'merma_porcentaje': 0.0,
                'familia': art.get('familia') or '',
                'proveedor_preferente': art.get('proveedor') or art.get('proveedor_preferente') or '',
                'coste_unitario': coste_unitario,
                'notas': 'Creada desde resolución de bloqueo I1.3.3.1',
                'id': f'LINESC-{uuid.uuid4().hex[:10].upper()}',
                'cantidad_bruta': cantidad,
                'coste_total': round(coste_linea, 6),
            })

        recetas = self._load_list(self.ruta_recetas)
        if any(_norm(r.get('nombre')) == _norm(nombre) and r.get('activo', True) for r in recetas):
            raise ValueError(f'Ya existe una receta activa llamada {nombre}. Vincúlala en lugar de crear otra.')
        ahora = _now()
        receta = {
            'receta_id': f'REC-{uuid.uuid4().hex[:12].upper()}',
            'nombre': nombre,
            'raciones_base': raciones,
            'lineas': lineas,
            'grupo': str(ficha.get('grupo') or bloqueo.get('rol') or 'ELABORACION').strip(),
            'subgrupo': 'Creada desde resolución de preimportación',
            'observaciones': str(ficha.get('observaciones') or 'I1.3.3.1 — creada para resolver un bloqueo de menú').strip(),
            'activo': True,
            'id': f'ESC-{uuid.uuid4().hex[:10].upper()}',
            'creado_en': ahora,
            'actualizado_en': ahora,
            'coste_total_base': round(coste_total, 6),
            'coste_por_racion': round(coste_total / raciones, 6),
        }
        backup = self._backup(self.ruta_recetas)
        recetas.append(receta)
        self._atomic_write(self.ruta_recetas, recetas)
        self._update_learning(bloqueo, receta)
        return {
            'ok': True,
            'accion': 'CREAR_RECETA',
            'receta': deepcopy(receta),
            'backup': str(backup),
            'datos_modificados': True,
        }

    def recalcular(self, ruta_excel: str | Path, hojas: list[str] | None = None) -> dict[str, Any]:
        # Recrea los motores para garantizar que leen el catálogo y memoria recién actualizados.
        self.preimportador = PreimportadorDefinitivoMenusI133(self.base_dir)
        resultado = self.preimportador.preparar(ruta_excel, hojas=hojas)
        resultado['version'] = self.VERSION
        resultado['resolucion_bloqueos_disponible'] = True
        resultado['importacion_disponible'] = False
        return resultado


def formatear_resolucion_i1331(resultado: dict[str, Any]) -> str:
    texto = formatear_preimportacion_i133(resultado)
    texto = texto.replace('I1.3.3 — PREIMPORTACIÓN DEFINITIVA DE MENÚS', 'I1.3.3.1 — RESOLUCIÓN DE BLOQUEOS DE PREIMPORTACIÓN', 1)
    texto = texto.replace('SOLO PREIMPORTACIÓN: I1.3.3 no escribe menús, recetas, artículos ni relaciones.',
                          'RESOLUCIÓN CONTROLADA: puede crear una receta confirmada o actualizar un vínculo; nunca importa el menú.')
    if resultado.get('estado_preimportacion') == 'LISTA':
        texto += '\nESTADO FINAL: LISTA. La importación definitiva continúa deshabilitada hasta I1.3.4.'
    else:
        texto += '\nESTADO FINAL: BLOQUEADA. Deben resolverse todos los bloqueos antes de I1.3.4.'
    return texto
