from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json
from MODELOS.alertas_produccion_306 import AlertaProduccion, InformeAlertasProduccion

class MotorAlertasProduccion:
    """Host AI 3.0.6.2 - Motor de Alertas de Producción.

    Genera alertas operativas a partir del análisis de producción: sobrecarga de jornada,
    recursos críticos, dependencias, tiempos pasivos largos, elaboraciones prioritarias y riesgo.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.produccion_dir = self.base_dir / 'DATOS' / 'produccion'
        self.produccion_dir.mkdir(parents=True, exist_ok=True)

    def generar_alertas(self, elaboraciones: List[Dict[str, Any]] | None = None, jornada_horas: float = 7.5, cocineros: int = 3) -> Dict[str, Any]:
        analisis = self.core.analizador_inteligente_produccion.analizar_produccion(elaboraciones=elaboraciones, jornada_horas=jornada_horas, cocineros=cocineros)
        alertas: List[Dict[str, Any]] = []
        resumen = analisis.get('resumen', {})
        ocupacion = float(resumen.get('ocupacion_activa_pct',0) or 0)
        if ocupacion > 115:
            alertas.append(AlertaProduccion('sobrecarga_jornada','sobrecarga_jornada','critica',f'La producción supera la capacidad activa prevista ({ocupacion}%).','Dividir producción en otro día, aumentar cocineros o reducir elaboraciones.', {'ocupacion_activa_pct': ocupacion}).to_dict())
        elif ocupacion > 90:
            alertas.append(AlertaProduccion('jornada_ajustada','jornada_ajustada','aviso',f'La producción va muy ajustada para la jornada ({ocupacion}%).','Preparar mise en place previa y bloquear interrupciones.', {'ocupacion_activa_pct': ocupacion}).to_dict())

        recurso_carga: Dict[str, int] = {}
        for item in analisis.get('items', []):
            for r in item.get('recursos', []) or []:
                recurso_carga[r] = recurso_carga.get(r,0) + int(item.get('tiempo_total_min',0) or 0)
            if item.get('riesgo') == 'alto':
                alertas.append(AlertaProduccion(item.get('clave',''), 'elaboracion_riesgo_alto', 'critica', f"{item.get('nombre')} tiene riesgo alto de producción.", 'Planificar primero, asignar responsable y revisar dependencias.', {'item': item}).to_dict())
            elif item.get('riesgo') == 'medio':
                alertas.append(AlertaProduccion(item.get('clave',''), 'elaboracion_riesgo_medio', 'aviso', f"{item.get('nombre')} requiere seguimiento.", 'Revisar tiempos y recursos antes de arrancar.', {'item': item}).to_dict())
            if item.get('dependencias'):
                alertas.append(AlertaProduccion(item.get('clave','')+'_dep', 'dependencias', 'aviso', f"{item.get('nombre')} depende de: {', '.join(item.get('dependencias', []))}.", 'Programar dependencias antes de esta elaboración.', {'dependencias': item.get('dependencias', [])}).to_dict())
            if int(item.get('tiempo_pasivo_min',0) or 0) >= 180:
                alertas.append(AlertaProduccion(item.get('clave','')+'_pasivo', 'pasivo_largo', 'informativa', f"{item.get('nombre')} tiene pasivo largo ({item.get('tiempo_pasivo_min')} min).", 'Usar el pasivo para adelantar otras elaboraciones.', {'tiempo_pasivo_min': item.get('tiempo_pasivo_min')}).to_dict())

        for recurso, minutos in recurso_carga.items():
            if minutos > int(jornada_horas*60):
                alertas.append(AlertaProduccion(f'recurso_{recurso}', 'recurso_saturado', 'aviso', f"El recurso {recurso} acumula {minutos} min de uso teórico.", 'Revisar solapes y reservar ventanas de uso del recurso.', {'recurso': recurso, 'minutos': minutos}).to_dict())

        alertas = self._deduplicar(alertas)
        alertas.sort(key=lambda a: (self._orden(a.get('gravedad')), a.get('tipo',''), a.get('clave','')))
        criticas = len([a for a in alertas if a.get('gravedad') == 'critica'])
        avisos = len([a for a in alertas if a.get('gravedad') == 'aviso'])
        infos = len([a for a in alertas if a.get('gravedad') == 'informativa'])
        estado = 'critico' if criticas else ('revisar' if avisos else 'ok')
        resumen_alertas = {'estado_general': estado, 'ocupacion_activa_pct': ocupacion, 'recursos_revisar': [r for r,m in recurso_carga.items() if m > int(jornada_horas*60)], 'total_items_analizados': analisis.get('total_elaboraciones',0)}
        lectura = f"Alertas de producción: {len(alertas)} alertas, {criticas} críticas, {avisos} avisos y estado {estado}."
        return InformeAlertasProduccion('3.0.6.2', len(alertas), criticas, avisos, infos, alertas, resumen_alertas, lectura).to_dict()

    def exportar_alertas(self, alertas: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino = self.produccion_dir / (nombre or 'alertas_produccion_3062.json')
        destino.write_text(json.dumps(alertas, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo': str(destino), 'lectura_host_ai': f'Alertas de producción exportadas: {destino.name}.'}

    def _deduplicar(self, alertas):
        vistos=set(); out=[]
        for a in alertas:
            k=(a.get('clave'), a.get('tipo'), a.get('mensaje'))
            if k in vistos: continue
            vistos.add(k); out.append(a)
        return out
    def _orden(self, g): return {'critica':0,'aviso':1,'informativa':2}.get(g,9)
