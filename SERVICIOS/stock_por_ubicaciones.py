from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json
from MODELOS.stock_ubicaciones import ResumenUbicacionStock, MovimientoUbicacionStock, InformeStockUbicaciones

class StockPorUbicaciones:
    """Host AI 3.0.5.7 - Stock por Ubicaciones.

    Agrupa, audita y mueve stock por zonas operativas: cámara, congelador, seco,
    cuarto frío, producción, evento y almacén externo.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.stock_dir = self.base_dir / 'DATOS' / 'stock'
        self.stock_dir.mkdir(parents=True, exist_ok=True)

    def analizar_ubicaciones(self) -> Dict[str, Any]:
        stock = getattr(self.core, 'stock', None)
        actual = stock.stock_actual() if stock else {'items': [], 'total_lotes': 0}
        por_ubicacion: Dict[str, Dict[str, Any]] = {}
        sin_ubicacion: List[Dict[str, Any]] = []
        alertas: List[Dict[str, Any]] = []
        total_valor = 0.0
        articulos_globales = set()

        for item in actual.get('items', []):
            clave = item.get('articulo_id') or item.get('clave') or item.get('nombre','').lower().strip()
            articulos_globales.add(clave)
            for lote in item.get('lotes', []) or []:
                ubicacion = (lote.get('ubicacion') or '').strip()
                cantidad = float(lote.get('cantidad', 0) or 0)
                coste = float(lote.get('coste_unitario', 0) or 0)
                valor = round(cantidad * coste, 4)
                total_valor += valor
                fila = {
                    'clave': clave,
                    'nombre': lote.get('nombre') or item.get('nombre', clave),
                    'articulo_id': lote.get('articulo_id') or item.get('articulo_id',''),
                    'lote_id': lote.get('id',''),
                    'cantidad': round(cantidad, 4),
                    'unidad': lote.get('unidad') or item.get('unidad',''),
                    'familia': lote.get('familia') or item.get('familia',''),
                    'proveedor': lote.get('proveedor',''),
                    'caducidad': lote.get('caducidad',''),
                    'coste_unitario': coste,
                    'valor_estimado': valor,
                    'ubicacion': ubicacion,
                }
                if not ubicacion:
                    sin_ubicacion.append(fila)
                    alertas.append({'tipo':'sin_ubicacion','gravedad':'aviso','mensaje':f"{fila['nombre']} no tiene ubicación registrada.", 'item': fila})
                    ubicacion = 'SIN_UBICACION'
                bucket = por_ubicacion.setdefault(ubicacion, {'articulos': {}, 'lotes': [], 'valor': 0.0, 'cantidad': 0.0, 'alertas': []})
                bucket['lotes'].append(fila); bucket['valor'] += valor; bucket['cantidad'] += cantidad
                art = bucket['articulos'].setdefault(clave, {'clave': clave, 'nombre': fila['nombre'], 'articulo_id': fila['articulo_id'], 'cantidad': 0.0, 'unidad': fila['unidad'], 'valor_estimado': 0.0, 'lotes': 0})
                art['cantidad'] += cantidad; art['valor_estimado'] += valor; art['lotes'] += 1

        ubicaciones: List[Dict[str, Any]] = []
        for nombre, datos in por_ubicacion.items():
            arts=[]
            for a in datos['articulos'].values():
                a['cantidad']=round(a['cantidad'],4); a['valor_estimado']=round(a['valor_estimado'],4); arts.append(a)
            arts.sort(key=lambda x: (-x.get('valor_estimado',0), x.get('nombre','')))
            bucket_alertas=[]
            if nombre == 'SIN_UBICACION':
                bucket_alertas.append({'tipo':'ubicacion_pendiente','gravedad':'aviso','mensaje':'Hay lotes pendientes de asignar a una ubicación real.'})
            ubicaciones.append(ResumenUbicacionStock(
                ubicacion=nombre, total_articulos=len(arts), total_lotes=len(datos['lotes']), cantidad_total=round(datos['cantidad'],4),
                valor_estimado=round(datos['valor'],4), articulos=arts, alertas=bucket_alertas).to_dict())
        ubicaciones.sort(key=lambda x: (x['ubicacion']=='SIN_UBICACION', -x['valor_estimado'], x['ubicacion']))
        resumen = {'estado_general':'revisar' if alertas else 'ok', 'ubicaciones_operativas': len([u for u in ubicaciones if u['ubicacion']!='SIN_UBICACION']), 'lotes_sin_ubicacion': len(sin_ubicacion)}
        lectura = f"Stock por ubicaciones: {len(ubicaciones)} ubicaciones, {actual.get('total_lotes',0)} lotes y {len(sin_ubicacion)} lotes sin ubicación."
        return InformeStockUbicaciones(len(ubicaciones), len(articulos_globales), int(actual.get('total_lotes',0) or 0), round(total_valor,4), ubicaciones, sin_ubicacion, alertas, resumen, lectura).to_dict()

    def mover_stock(self, nombre: str, cantidad: float, unidad: str, origen: str, destino: str, articulo_id: str = '', lote_id: str = '') -> Dict[str, Any]:
        stock = getattr(self.core, 'stock', None)
        if not stock:
            return MovimientoUbicacionStock(nombre, articulo_id, origen, destino, cantidad, unidad, lote_id, False, 'Motor de stock no disponible.').to_dict()
        pendiente = float(cantidad)
        movidos=[]
        origen_norm=(origen or '').strip(); destino_norm=(destino or '').strip()
        lotes = list(getattr(stock, 'lotes', {}).values())
        for lote in lotes:
            if pendiente <= 0: break
            mismo_lote = bool(lote_id) and getattr(lote, 'id', '') == lote_id
            mismo_art = bool(articulo_id) and getattr(lote, 'articulo_id', '') == articulo_id
            mismo_nombre = getattr(lote, 'nombre', '').lower().strip() == nombre.lower().strip()
            misma_unidad = getattr(lote, 'unidad', '') == unidad
            misma_ubicacion = (getattr(lote, 'ubicacion', '') or '').strip() == origen_norm
            if (mismo_lote or (not lote_id and (mismo_art or mismo_nombre))) and misma_unidad and misma_ubicacion and getattr(lote, 'cantidad', 0) > 0:
                usar = min(float(lote.cantidad), pendiente)
                if usar == float(lote.cantidad):
                    lote.ubicacion = destino_norm
                    movidos.append({'lote_id': lote.id, 'cantidad': usar, 'accion':'mover_lote_completo'})
                else:
                    lote.cantidad -= usar
                    nuevo = stock.registrar_entrada(lote.nombre, usar, lote.unidad, getattr(lote,'familia',''), destino_norm, getattr(lote,'proveedor',''), getattr(lote,'articulo_id',''), getattr(lote,'caducidad',''), getattr(lote,'coste_unitario',0), 'traspaso ubicación')
                    movidos.append({'lote_id': lote.id, 'nuevo_lote_id': nuevo['lote']['id'], 'cantidad': usar, 'accion':'dividir_lote'})
                pendiente -= usar
        ok = pendiente <= 0
        msg = f"Movimiento de ubicación registrado: {cantidad} {unidad} de {nombre} de {origen} a {destino}." if ok else f"No hay stock suficiente en {origen}. Faltan {round(pendiente,4)} {unidad}."
        return MovimientoUbicacionStock(nombre, articulo_id, origen, destino, round(float(cantidad)-max(0,pendiente),4), unidad, lote_id, ok, msg, {'movidos': movidos, 'cantidad_solicitada': float(cantidad), 'cantidad_faltante': round(max(0,pendiente),4)}).to_dict()

    def exportar_ubicaciones(self, informe: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino = self.stock_dir / (nombre or 'stock_por_ubicaciones.json')
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo': str(destino), 'lectura_host_ai': f'Stock por ubicaciones exportado: {destino.name}.'}
