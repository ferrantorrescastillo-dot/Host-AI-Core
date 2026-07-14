"""Memoria conversacional del bloque Host AI 3.0.8.5.

Mantiene contexto operativo entre turnos sin depender de un LLM externo.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List
from MODELOS.ia_conversacional_308 import EntradaMemoriaConversacional308, MemoriaConversacional308

class MemoriaConversacional308Servicio:
    VERSION = '3.0.8.5'

    def __init__(self, core=None):
        self.core = core
        base = getattr(core, 'base_dir', Path('.')) if core else Path('.')
        self.ruta = Path(base) / 'DATOS' / 'ia_conversacional' / 'memoria_conversacional_3085.json'
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.entradas: Dict[str, Dict[str, Any]] = {}
        self.contexto_actual: Dict[str, Any] = {}
        self._cargar()

    def _cargar(self) -> None:
        if not self.ruta.exists():
            return
        try:
            datos = json.loads(self.ruta.read_text(encoding='utf-8'))
            self.entradas = {e.get('clave',''): e for e in datos.get('entradas', []) if e.get('clave')}
            self.contexto_actual = datos.get('contexto_actual', {}) or {}
        except Exception:
            self.entradas = {}
            self.contexto_actual = {}

    def _guardar(self) -> None:
        datos = {'version': self.VERSION, 'entradas': list(self.entradas.values()), 'contexto_actual': self.contexto_actual}
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding='utf-8')

    def limpiar(self) -> Dict[str, Any]:
        self.entradas.clear()
        self.contexto_actual.clear()
        self._guardar()
        return {'version': self.VERSION, 'total_entradas': 0, 'lectura_host_ai': 'Memoria conversacional 3.0.8.5 limpiada.'}

    def recordar(self, clave: str, valor: Any, tipo: str = 'contexto', prioridad: int = 1, origen: str = 'usuario', tags: List[str] | None = None, metadatos: Dict[str, Any] | None = None) -> Dict[str, Any]:
        clave_norm = (clave or '').strip().lower().replace(' ', '_')
        if not clave_norm:
            clave_norm = f'entrada_{len(self.entradas)+1}'
        entrada = EntradaMemoriaConversacional308(clave_norm, valor, tipo, int(prioridad), origen, tags or [], metadatos or {}).to_dict()
        self.entradas[clave_norm] = entrada
        if tipo in {'contexto','articulo','proveedor','receta','restaurante'}:
            self.contexto_actual[clave_norm] = valor
        self._guardar()
        return {'version': self.VERSION, 'entrada': entrada, 'total_entradas': len(self.entradas), 'lectura_host_ai': f'Memoria 3.0.8.5: guardado {clave_norm}.'}

    def aprender_desde_turno(self, turno: Dict[str, Any]) -> Dict[str, Any]:
        datos = turno.get('datos', {}) if isinstance(turno, dict) else {}
        analisis = datos.get('analisis', {}) or turno.get('analisis', {}) if isinstance(turno, dict) else {}
        recordadas = []
        for ent in analisis.get('entidades', []) or []:
            tipo = ent.get('tipo','entidad')
            valor = ent.get('normalizado') or ent.get('valor')
            if valor:
                recordadas.append(self.recordar(f'ultimo_{tipo}', valor, tipo=tipo, origen='turno', tags=['auto']).get('entrada'))
        if analisis.get('intencion_detectada'):
            recordadas.append(self.recordar('ultima_intencion', analisis.get('intencion_detectada'), tipo='contexto', origen='turno', tags=['auto']).get('entrada'))
        return {'version': self.VERSION, 'recordadas': recordadas, 'total_entradas': len(self.entradas), 'lectura_host_ai': f'Memoria actualizada desde turno: {len(recordadas)} entradas.'}

    def consultar(self, clave: str = '', filtro_tipo: str = '', tags: List[str] | None = None) -> Dict[str, Any]:
        tags = tags or []
        resultados = []
        clave_norm = (clave or '').strip().lower().replace(' ', '_')
        for k, e in self.entradas.items():
            if clave_norm and clave_norm not in k:
                continue
            if filtro_tipo and e.get('tipo') != filtro_tipo:
                continue
            if tags and not set(tags).issubset(set(e.get('tags', []))):
                continue
            resultados.append(e)
        resultados.sort(key=lambda x: x.get('prioridad', 0), reverse=True)
        return MemoriaConversacional308(self.VERSION, len(resultados), resultados, dict(self.contexto_actual), {}, f'Memoria consultada: {len(resultados)} entradas encontradas.').to_dict()

    def resolver_referencias(self, texto: str, contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
        contexto = contexto or {}
        texto_norm = (texto or '').lower()
        referencias = {}
        candidatos = dict(self.contexto_actual)
        candidatos.update(contexto)
        if any(p in texto_norm for p in ['ese ', 'esa ', 'eso ', 'mismo', 'igual', 'anterior', 'último', 'ultimo']):
            for k in ['ultimo_articulo','ultimo_proveedor','ultima_receta','ultima_intencion','ultima_fecha']:
                if k in candidatos:
                    referencias[k] = candidatos[k]
        lectura = 'Referencias resueltas con memoria conversacional.' if referencias else 'No se han detectado referencias dependientes de memoria.'
        return MemoriaConversacional308(self.VERSION, len(self.entradas), list(self.entradas.values()), dict(self.contexto_actual), referencias, lectura).to_dict()

    def exportar(self, nombre: str = '') -> Dict[str, Any]:
        self._guardar()
        return {'version': self.VERSION, 'ruta': str(self.ruta), 'total_entradas': len(self.entradas), 'lectura_host_ai': f'Memoria exportada en {self.ruta}.'}

__all__ = ['MemoriaConversacional308Servicio']
