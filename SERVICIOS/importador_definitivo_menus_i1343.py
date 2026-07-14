from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from SERVICIOS.motor_escritura_segura_i1342 import MotorEscrituraSeguraI1342
from SERVICIOS.simulador_importacion_menus_i13411 import _norm, _stable_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ImportadorDefinitivoMenusI1343:
    VERSION = 'I1.3.4.3c'
    RUTA_MENUS = 'DATOS/db/menus.json'

    def __init__(self, base_dir: str | Path, ruta_menus: str | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.ruta_menus = ruta_menus or self.RUTA_MENUS
        self.motor = MotorEscrituraSeguraI1342(self.base_dir, [self.ruta_menus])

    def _cargar(self) -> list[dict[str, Any]]:
        path = self.base_dir / self.ruta_menus
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, list):
            raise ValueError('El catálogo de menús debe ser una lista JSON.')
        return data

    @staticmethod
    def _validar_plan(plan: dict[str, Any]) -> None:
        if plan.get('estado_simulacion') != 'LISTA_PARA_TRANSACCION':
            raise ValueError('El plan no está listo para transacción.')
        bloqueadas = [a for a in plan.get('acciones', []) if a.get('estado') == 'BLOQUEADA']
        if bloqueadas or plan.get('bloqueos'):
            raise ValueError('El plan contiene bloqueos pendientes.')
        if not plan.get('acciones'):
            raise ValueError('El plan no contiene acciones.')


    def cargar_sesion_revisada(self, ruta_sesion: str | Path) -> dict[str, Any]:
        """Carga y valida una sesión revisada antes de permitir cualquier escritura real.

        Esta validación ocurre antes de iniciar el motor transaccional. Por tanto, cualquier
        error de ruta, JSON o estado de revisión termina sin modificar datos de negocio.
        """
        texto_ruta = str(ruta_sesion or '').strip().strip('\"')
        if not texto_ruta:
            raise ValueError('No se indicó la ruta del JSON de sesión revisada.')

        path = Path(texto_ruta).expanduser()
        if not path.is_absolute():
            path = (self.base_dir / path).resolve()
        else:
            path = path.resolve()

        if not path.exists():
            raise FileNotFoundError(f'No existe el archivo de sesión revisada: {path}')
        if not path.is_file():
            raise ValueError(f'La ruta indicada no es un archivo: {path}')
        if path.suffix.lower() != '.json':
            raise ValueError('La sesión revisada debe ser un archivo JSON.')

        try:
            sesion = json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            raise ValueError(f'El JSON de la sesión revisada no es válido: {exc.msg}.') from exc

        if not isinstance(sesion, dict):
            raise ValueError('La sesión revisada debe contener un objeto JSON.')
        plan = sesion.get('plan')
        resumen = sesion.get('resumen_revision')
        if not isinstance(plan, dict):
            raise ValueError('La sesión no contiene un plan de importación válido.')
        if not isinstance(resumen, dict):
            raise ValueError('La sesión no contiene un resumen de revisión válido.')

        pendientes = int(resumen.get('pendientes') or 0)
        bloqueantes = int(resumen.get('bloqueantes') or 0)
        if pendientes != 0 or bloqueantes != 0:
            raise ValueError(
                f'La sesión todavía no está lista: pendientes={pendientes}, bloqueantes={bloqueantes}.'
            )

        self._validar_plan(plan)
        sesion['_ruta_validada'] = str(path)
        return sesion

    @staticmethod
    def _menu_base(menu_id: str, nombre: str, hoja: str | None) -> dict[str, Any]:
        return {
            'menu_id': menu_id,
            'nombre': nombre,
            'hoja_origen': hoja,
            'estado': 'ACTIVO',
            'secciones': [],
            'platos': [],
            'articulos_directos': [],
            'bebidas': [],
            'complementos': [],
            'servicios': [],
            'economico': {},
            'origen_importacion': 'I1.3.4.3',
            'actualizado_en': _now(),
        }

    @staticmethod
    def _plato_id_estable(menu_id: str, accion: dict[str, Any]) -> str:
        """Devuelve un identificador estable para el plato padre.

        Prioriza identificadores persistidos por la simulación/revisión y, como
        compatibilidad con sesiones anteriores, deriva uno usando menú + nombre.
        """
        detalle = accion.get('detalle') or {}
        return str(
            detalle.get('plato_id')
            or detalle.get('id_plato')
            or _stable_id('PLATO', menu_id, accion.get('nombre'))
        )

    @staticmethod
    def _referencias_plato(accion: dict[str, Any]) -> list[str]:
        """Extrae todas las referencias conocidas al plato padre de una acción."""
        d = accion.get('detalle') or {}
        valores = [
            d.get('plato_id'), d.get('id_plato'), d.get('plato_accion_id'),
            d.get('plato'), d.get('plato_original'), d.get('plato_destino'),
            d.get('nombre_plato'), d.get('plato_renombrado'),
        ]
        return [str(v).strip() for v in valores if str(v or '').strip()]

    @staticmethod
    def _claves_identidad_plato(menu_id: str, accion: dict[str, Any]) -> list[str]:
        """Construye identidades canónicas para deduplicar un plato lógico.

        Las sesiones antiguas pueden contener varias acciones PLATO_MENU o alias
        distintos para el mismo plato. Esta función genera claves por identidad
        explícita, acción padre y nombres originales/renombrados, siempre dentro
        del menú correspondiente.
        """
        d = accion.get('detalle') or {}
        claves: list[str] = []

        for campo in ('plato_id', 'id_plato'):
            valor = str(d.get(campo) or '').strip()
            if valor:
                claves.append(f'ID:{menu_id}:{valor}')

        for campo in ('plato_accion_id', 'accion_plato_id', 'accion_padre_id'):
            valor = str(d.get(campo) or '').strip()
            if valor:
                claves.append(f'ACCION:{menu_id}:{valor}')

        nombres = [
            accion.get('nombre'), d.get('plato'), d.get('plato_original'),
            d.get('nombre_original'), d.get('plato_destino'),
            d.get('plato_renombrado'), d.get('nombre_plato'),
        ]
        for nombre in nombres:
            normalizado = _norm(nombre)
            if normalizado:
                claves.append(f'NOMBRE:{menu_id}:{normalizado}')

        # Mantener orden y eliminar repeticiones.
        return list(dict.fromkeys(claves))

    def construir_catalogo(self, plan: dict[str, Any], existentes: list[dict[str, Any]] | None = None) -> tuple[list[dict[str, Any]], dict[str, int]]:
        self._validar_plan(plan)
        catalogo = deepcopy(existentes if existentes is not None else self._cargar())
        por_id = {str(m.get('menu_id') or m.get('id')): m for m in catalogo if m.get('menu_id') or m.get('id')}
        por_nombre = {_norm(m.get('nombre')): m for m in catalogo}
        creados = actualizados = 0

        acciones = plan.get('acciones', [])
        for a in acciones:
            if a.get('entidad') != 'MENU':
                continue
            d = a.get('detalle', {})
            menu_id = str(d.get('menu_id') or _stable_id('MENU', a.get('nombre'), d.get('hoja')))
            existente = por_id.get(menu_id) or por_nombre.get(_norm(a.get('nombre')))
            nuevo = self._menu_base(menu_id, str(a.get('nombre') or 'Menú sin nombre'), d.get('hoja'))
            if existente:
                nuevo['creado_en'] = existente.get('creado_en') or _now()
                actualizados += 1
                idx = catalogo.index(existente)
                catalogo[idx] = nuevo
            else:
                nuevo['creado_en'] = _now()
                catalogo.append(nuevo)
                creados += 1
            por_id[menu_id] = nuevo
            por_nombre[_norm(nuevo['nombre'])] = nuevo

        def menu_de(a: dict[str, Any]) -> dict[str, Any]:
            d = a.get('detalle', {})
            mid = str(d.get('menu_id') or '')
            m = por_id.get(mid) or por_nombre.get(_norm(d.get('menu') or a.get('nombre')))
            if not m:
                raise ValueError(f"No se encontró el menú destino para la acción {a.get('accion_id')}")
            return m

        # Primera pasada: secciones y platos. Ningún componente se procesa antes
        # de que existan todos sus posibles platos padre, independientemente del
        # orden de las acciones guardadas en la sesión revisada.
        platos_por_id: dict[tuple[str, str], dict[str, Any]] = {}
        platos_por_alias: dict[tuple[str, str], list[dict[str, Any]]] = {}
        plato_por_accion: dict[tuple[str, str], dict[str, Any]] = {}
        plato_por_identidad: dict[str, dict[str, Any]] = {}

        for a in acciones:
            if a.get('estado') != 'PLANIFICADA' or a.get('entidad') == 'MENU':
                continue
            entidad = str(a.get('entidad') or '')
            if entidad not in {'SECCION', 'PLATO_MENU'}:
                continue
            m = menu_de(a)
            d = a.get('detalle', {})
            nombre = str(a.get('nombre') or '')
            if entidad == 'SECCION':
                if _norm(nombre) not in {_norm(x.get('nombre')) for x in m['secciones']}:
                    m['secciones'].append({'seccion_id': _stable_id('SEC', m['menu_id'], nombre), 'nombre': nombre})
                continue

            claves_identidad = self._claves_identidad_plato(m['menu_id'], a)
            existentes_identidad = []
            for clave in claves_identidad:
                p = plato_por_identidad.get(clave)
                if p is not None and all(x.get('plato_id') != p.get('plato_id') for x in existentes_identidad):
                    existentes_identidad.append(p)

            if len(existentes_identidad) > 1:
                ids = ', '.join(str(p.get('plato_id')) for p in existentes_identidad)
                raise ValueError(
                    f"Identidad de plato contradictoria en {m.get('nombre')}: {nombre} apunta a {ids}."
                )

            plato = existentes_identidad[0] if existentes_identidad else None
            if plato is None:
                plato_id = self._plato_id_estable(m['menu_id'], a)
                # Si el id ya existe, reutilizar exactamente ese plato lógico.
                plato = platos_por_id.get((m['menu_id'], plato_id))
                if plato is None:
                    plato = {
                        'plato_id': plato_id,
                        'nombre': nombre,
                        'seccion': d.get('seccion'),
                        'coste_racion': d.get('coste_racion'),
                        'componentes': [],
                        'fila_origen': d.get('fila'),
                        'accion_origen': a.get('accion_id'),
                        'acciones_origen': [],
                        'alias': [],
                    }
                    m['platos'].append(plato)
                    platos_por_id[(m['menu_id'], plato_id)] = plato

            # Completar datos sin destruir los ya revisados.
            if not plato.get('nombre') and nombre:
                plato['nombre'] = nombre
            if plato.get('seccion') in (None, '') and d.get('seccion') not in (None, ''):
                plato['seccion'] = d.get('seccion')
            if plato.get('coste_racion') in (None, '') and d.get('coste_racion') not in (None, ''):
                plato['coste_racion'] = d.get('coste_racion')

            accion_id = str(a.get('accion_id') or '').strip()
            if accion_id:
                plato_por_accion[(m['menu_id'], accion_id)] = plato
                if accion_id not in plato['acciones_origen']:
                    plato['acciones_origen'].append(accion_id)

            aliases = {
                nombre, d.get('plato'), d.get('plato_original'), d.get('nombre_original'),
                d.get('plato_destino'), d.get('plato_renombrado'), d.get('nombre_plato'),
            }
            for alias in aliases:
                normalizado = _norm(alias)
                if not normalizado:
                    continue
                if normalizado not in plato['alias']:
                    plato['alias'].append(normalizado)
                bucket = platos_por_alias.setdefault((m['menu_id'], normalizado), [])
                if all(x.get('plato_id') != plato.get('plato_id') for x in bucket):
                    bucket.append(plato)

            for clave in claves_identidad:
                previo = plato_por_identidad.get(clave)
                if previo is not None and previo.get('plato_id') != plato.get('plato_id'):
                    raise ValueError(
                        f"Identidad de plato duplicada en {m.get('nombre')}: {nombre}."
                    )
                plato_por_identidad[clave] = plato

        def resolver_plato_padre(m: dict[str, Any], accion: dict[str, Any]) -> dict[str, Any] | None:
            d = accion.get('detalle') or {}
            # 1) Identidad estable explícita.
            for campo in ('plato_id', 'id_plato'):
                valor = str(d.get(campo) or '').strip()
                if valor:
                    encontrado = platos_por_id.get((m['menu_id'], valor))
                    if encontrado:
                        return encontrado
            # 2) Acción padre explícita.
            accion_padre = str(d.get('plato_accion_id') or '').strip()
            if accion_padre:
                encontrado = plato_por_accion.get((m['menu_id'], accion_padre))
                if encontrado:
                    return encontrado
            # 3) Alias textuales conservados durante revisión/renombrado.
            candidatos_por_id: dict[str, dict[str, Any]] = {}
            for ref in self._referencias_plato(accion):
                encontrados = platos_por_alias.get((m['menu_id'], _norm(ref)), [])
                for p in encontrados:
                    candidatos_por_id[str(p.get('plato_id'))] = p
            candidatos = list(candidatos_por_id.values())
            if len(candidatos) == 1:
                return candidatos[0]
            if len(candidatos) > 1:
                detalle_candidatos = '; '.join(
                    f"{p.get('plato_id')}={p.get('nombre')}" for p in candidatos
                )
                raise ValueError(
                    f"Destino de componente ambiguo: {accion.get('nombre')} coincide con "
                    f"{len(candidatos)} platos lógicos del menú {m.get('nombre')}: "
                    f"{detalle_candidatos}."
                )

            # 4) Compatibilidad con sesiones antiguas que fueron renombradas antes
            # de existir plato_id. Se usa una coincidencia conservadora por tokens:
            # debe ser única, compartir al menos dos términos y superar el umbral.
            referencias = [r for r in self._referencias_plato(accion) if _norm(r)]
            if referencias:
                puntuados: list[tuple[float, dict[str, Any]]] = []
                for p in m.get('platos', []):
                    tokens_p = set(_norm(p.get('nombre')).split())
                    if not tokens_p:
                        continue
                    mejor = 0.0
                    for ref in referencias:
                        tokens_r = set(_norm(ref).split())
                        comunes = tokens_p & tokens_r
                        if len(comunes) < 2:
                            continue
                        cobertura_p = len(comunes) / len(tokens_p)
                        cobertura_r = len(comunes) / len(tokens_r)
                        # Favorece que el nombre nuevo sea una versión abreviada del original.
                        mejor = max(mejor, max(cobertura_p, cobertura_r), (2 * len(comunes)) / (len(tokens_p) + len(tokens_r)))
                    if mejor >= 0.55:
                        puntuados.append((mejor, p))
                puntuados.sort(key=lambda x: x[0], reverse=True)
                if puntuados:
                    mejor = puntuados[0][0]
                    empatados_por_id: dict[str, dict[str, Any]] = {}
                    for score, p in puntuados:
                        if abs(score - mejor) < 1e-9:
                            empatados_por_id[str(p.get('plato_id'))] = p
                    empatados = list(empatados_por_id.values())
                    if len(empatados) == 1:
                        return empatados[0]
                    raise ValueError(
                        f"Destino de componente ambiguo tras renombrado: {accion.get('nombre')} "
                        f"coincide con {len(empatados)} platos lógicos del menú {m.get('nombre')}."
                    )
            return None

        # Segunda pasada: resto de entidades y componentes.
        for a in acciones:
            if a.get('estado') != 'PLANIFICADA' or a.get('entidad') in {'MENU', 'SECCION', 'PLATO_MENU'}:
                continue
            m = menu_de(a)
            d = a.get('detalle', {})
            entidad = str(a.get('entidad') or '')
            nombre = str(a.get('nombre') or '')
            if entidad in {'RECETA_PRINCIPAL','SALSA','GUARNICION','ELABORACION','CONDIMENTO','ACABADO','RECETA'}:
                plato = resolver_plato_padre(m, a)
                if plato is None:
                    referencias = self._referencias_plato(a)
                    ref_txt = ', '.join(referencias) if referencias else 'sin referencia de plato'
                    raise ValueError(
                        f"Componente sin plato destino: {nombre}. "
                        f"Menú: {m.get('nombre')}. Referencias: {ref_txt}."
                    )
                componente_id = str(
                    d.get('componente_id')
                    or _stable_id('COMP', m['menu_id'], plato['plato_id'], entidad, nombre)
                )
                # Idempotencia también dentro del plato: no repetir la misma relación.
                duplicado = next((
                    c for c in plato['componentes']
                    if c.get('componente_id') == componente_id
                    or (_norm(c.get('nombre')) == _norm(nombre) and c.get('rol') == entidad)
                ), None)
                if not duplicado:
                    plato['componentes'].append({
                        'componente_id': componente_id,
                        'rol': entidad,
                        'nombre': nombre,
                        'catalogado': True,
                        'accion_id': a.get('accion_id'),
                        'plato_id': plato['plato_id'],
                    })
            elif entidad in {'ARTICULO_DIRECTO','APERITIVO_PREPARADO','MATERIA_PRIMA'}:
                m['articulos_directos'].append({'nombre': nombre, 'tipo': entidad, 'coste_racion': d.get('coste_racion')})
            elif entidad == 'BEBIDA_MENU':
                m['bebidas'].append({'nombre': nombre, 'tipo': d.get('tipo_gastronomico') or d.get('clasificacion_revision') or 'BEBIDA'})
            elif entidad in {'COMPLEMENTO','SALSA_MENU','POSTRE_MENU','ELABORACION_MENU'}:
                m['complementos'].append({'nombre': nombre, 'tipo': entidad})
            elif entidad == 'SERVICIO':
                m['servicios'].append({'nombre': nombre})
            elif entidad == 'DATOS_ECONOMICOS':
                m['economico'] = {
                    'precio_venta': d.get('precio_venta'), 'venta_neta': d.get('venta_neta'),
                    'coste_total': d.get('coste_total'), 'food_cost_pct': d.get('food_cost_pct'),
                    'beneficio': d.get('beneficio')}

        for m in catalogo:
            if m.get('origen_importacion') == 'I1.3.4.3':
                for plato in m.get('platos', []):
                    plato.pop('alias', None)
                    plato.pop('acciones_origen', None)
                m['resumen'] = {
                    'secciones': len(m['secciones']), 'platos': len(m['platos']),
                    'componentes': sum(len(p.get('componentes', [])) for p in m['platos']),
                    'articulos_directos': len(m['articulos_directos']), 'bebidas': len(m['bebidas']),
                    'complementos': len(m['complementos'])}
        return catalogo, {'creados': creados, 'actualizados': actualizados}

    def importar(self, plan: dict[str, Any], *, confirmar: bool = False, idempotency_key: str | None = None):
        if not confirmar:
            raise PermissionError('La importación definitiva requiere confirmación explícita.')
        existentes = self._cargar()
        catalogo, resumen = self.construir_catalogo(plan, existentes)
        resultado = self.motor.ejecutar({self.ruta_menus: catalogo}, idempotency_key=idempotency_key or plan.get('plan_id'))
        return {'version': self.VERSION, 'resultado_transaccion': resultado.to_dict(), 'resumen_importacion': resumen,
                'menus_totales': len(catalogo), 'plan_id': plan.get('plan_id')}
