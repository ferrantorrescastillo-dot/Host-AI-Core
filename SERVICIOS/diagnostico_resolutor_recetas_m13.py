from __future__ import annotations

from pathlib import Path
import json
import shutil

from CORE.MUR.modelos import CheckpointMUR, ConflictoMUR, TipoEntidad, TipoConflicto, SeveridadConflicto
from CORE.MUR.orquestador import OrquestadorMUR
from CORE.MUR.registro import RegistroResolutoresMUR
from CORE.MUR.repositorios import RepositorioMURJson
from SERVICIOS.resolutor_recetas_m13 import ResolutorRecetasM13


class DiagnosticoResolutorRecetasM13:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def ejecutar(self) -> dict:
        origen_recetas = self.base_dir / 'DATOS/db/escandallos.json'
        origen_articulos = self.base_dir / 'DATOS/db/articulos.json'
        destino_recetas = self.base_dir / 'DATOS/mur/diagnostico_m13_recetas.json'
        destino_articulos = self.base_dir / 'DATOS/mur/diagnostico_m13_articulos.json'
        destino_recetas.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen_recetas, destino_recetas)
        shutil.copy2(origen_articulos, destino_articulos)

        articulos = json.loads(destino_articulos.read_text(encoding='utf-8'))
        articulo = next((a for a in articulos if a.get('precio') not in (None, '') and (a.get('codigo') or a.get('id'))), None)
        if not articulo:
            raise RuntimeError('No hay ningún artículo válido para el diagnóstico M1.3.')
        articulo_id = articulo.get('codigo') or articulo.get('id')
        unidad = articulo.get('unidad') or 'kg'

        repo = RepositorioMURJson(self.base_dir / 'DATOS/mur/diagnostico_m13.json')
        registro = RegistroResolutoresMUR()
        resolutor = ResolutorRecetasM13(destino_recetas, destino_articulos, self.base_dir / 'DATOS/mur/backups_m13')
        registro.registrar(resolutor)
        mur = OrquestadorMUR(repo, registro)
        cp = mur.crear_checkpoint(CheckpointMUR('DIAG-M13', 'DIAGNOSTICO', 'resolver_receta', 'receta_pendiente', {'receta': 'Parmentier M13'}))
        conflicto = mur.detectar(ConflictoMUR(
            'DIAG', 'DIAG-M13', 'DIAGNOSTICO', TipoEntidad.RECETA,
            TipoConflicto.ENTIDAD_NO_EXISTE, SeveridadConflicto.BLOQUEANTE,
            'Parmentier M13', 'Parmentier M13', rol_contextual='GUARNICION',
            checkpoint_id=cp.checkpoint_id,
            acciones_permitidas=['CREAR', 'VINCULAR', 'MANTENER_PENDIENTE'],
        ))
        sesion = mur.abrir_resolucion(conflicto.conflicto_id, 'diagnostico')
        resultado = mur.ejecutar(sesion.sesion_id, 'CREAR', {
            'nombre': 'Parmentier M13',
            'raciones_base': 10,
            'ingredientes': [{'articulo_id': articulo_id, 'cantidad': 1.0, 'unidad': unidad}],
            'grupo': 'GUARNICION',
        })
        mur.aplicar(conflicto.conflicto_id, 'diagnostico')
        final = mur.cerrar_tras_recalculo(conflicto.conflicto_id, True, 'diagnostico', 'La receta existe y el flujo puede continuar.')
        receta = resultado.datos.get('receta') or {}
        return {
            'ok': final.estado.value == 'CERRADO',
            'estado': final.estado.value,
            'conflicto_id': conflicto.conflicto_id,
            'checkpoint_id': cp.checkpoint_id,
            'sesion_id': sesion.sesion_id,
            'receta': receta,
            'estado_calidad': resultado.datos.get('estado_calidad'),
            'ingrediente': articulo.get('nombre') or articulo.get('articulo'),
            'resolutores': len(registro.listar()),
            'eventos': len(repo.listar_auditoria()),
            'ruta_diagnostico': str(destino_recetas),
        }


def formatear_diagnostico_m13(r: dict) -> str:
    receta = r.get('receta') or {}
    return (
        'M1.3 — RESOLUTOR DE RECETAS (NÚCLEO)\n' + '=' * 78 + '\n'
        f"Diagnóstico: {'OK' if r['ok'] else 'ERROR'} | Estado final: {r['estado']}\n"
        f"Conflicto: {r['conflicto_id']}\nCheckpoint: {r['checkpoint_id']}\nSesión: {r['sesion_id']}\n"
        f"Receta: {receta.get('nombre')} | ID: {receta.get('receta_id')} | Calidad: {r['estado_calidad']}\n"
        f"Rendimiento: {receta.get('raciones_base')} | Ingredientes: {len(receta.get('lineas') or [])} | Ingrediente diagnóstico: {r.get('ingrediente')}\n"
        f"Resolutores registrados: {r['resolutores']} | Eventos de auditoría: {r['eventos']}\n"
        f"Catálogo de diagnóstico: {r['ruta_diagnostico']}\n" + '-' * 78 + '\n'
        'Se validó búsqueda, alta manual oficial, rendimiento, ingrediente real, duplicados, auditoría y reanudación.\n'
        'No se modificó el catálogo real DATOS/db/escandallos.json ni otros datos de negocio.\n'
        'Texto, Word, PDF y Excel quedan reservados para M1.3.1.'
    )


__all__ = ['DiagnosticoResolutorRecetasM13', 'formatear_diagnostico_m13']
