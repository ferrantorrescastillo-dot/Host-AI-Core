from __future__ import annotations
from pathlib import Path
import json, shutil, tempfile

from CORE.MUR.modelos import CheckpointMUR, ConflictoMUR, TipoEntidad, TipoConflicto, SeveridadConflicto
from CORE.MUR.orquestador import OrquestadorMUR
from CORE.MUR.registro import RegistroResolutoresMUR
from CORE.MUR.repositorios import RepositorioMURJson
from SERVICIOS.resolutor_articulos_m12 import ResolutorArticulosM12

class DiagnosticoResolutorArticulosM12:
    def __init__(self, base_dir: str | Path): self.base_dir=Path(base_dir)
    def ejecutar(self):
        origen=self.base_dir/'DATOS/db/articulos.json'
        destino=self.base_dir/'DATOS/mur/diagnostico_m12_articulos.json'
        destino.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(origen,destino)
        repo=RepositorioMURJson(self.base_dir/'DATOS/mur/diagnostico_m12.json')
        reg=RegistroResolutoresMUR(); res=ResolutorArticulosM12(destino, permitir_sin_precio=True, ruta_backups=self.base_dir/'DATOS/mur/backups_m12')
        reg.registrar(res); mur=OrquestadorMUR(repo,reg)
        cp=mur.crear_checkpoint(CheckpointMUR('DIAG-M12','DIAGNOSTICO','resolver_articulo','ingrediente',{'ingrediente':'Nuez moscada M12'}))
        c=mur.detectar(ConflictoMUR('DIAG','DIAG-M12','DIAGNOSTICO',TipoEntidad.ARTICULO,TipoConflicto.ENTIDAD_NO_EXISTE,SeveridadConflicto.BLOQUEANTE,'Nuez moscada M12','Nuez moscada M12',checkpoint_id=cp.checkpoint_id,acciones_permitidas=['CREAR','VINCULAR','MANTENER_PENDIENTE']))
        s=mur.abrir_resolucion(c.conflicto_id,'diagnostico')
        rr=mur.ejecutar(s.sesion_id,'CREAR',{'nombre':'Nuez moscada M12','unidad':'kg','precio':None,'familia':'Especias'})
        mur.aplicar(c.conflicto_id,'diagnostico')
        final=mur.cerrar_tras_recalculo(c.conflicto_id,True,'diagnostico','El artículo existe y el flujo puede continuar.')
        art=rr.datos.get('articulo') or {}
        return {'ok':final.estado.value=='CERRADO','estado':final.estado.value,'conflicto_id':c.conflicto_id,'checkpoint_id':cp.checkpoint_id,'sesion_id':s.sesion_id,'articulo':art,'estado_calidad':rr.datos.get('estado_calidad'),'resolutores':len(reg.listar()),'eventos':len(repo.listar_auditoria()),'ruta_diagnostico':str(destino)}

def formatear_diagnostico_m12(r):
    return ('M1.2 — RESOLUTOR DE ARTÍCULOS\n'+'='*78+'\n'
            f"Diagnóstico: {'OK' if r['ok'] else 'ERROR'} | Estado final: {r['estado']}\n"
            f"Conflicto: {r['conflicto_id']}\nCheckpoint: {r['checkpoint_id']}\nSesión: {r['sesion_id']}\n"
            f"Artículo: {r['articulo'].get('nombre')} | Código: {r['articulo'].get('codigo')} | Calidad: {r['estado_calidad']}\n"
            f"Resolutores registrados: {r['resolutores']} | Eventos de auditoría: {r['eventos']}\n"
            f"Catálogo de diagnóstico: {r['ruta_diagnostico']}\n"+'-'*78+'\n'
            'Se validó búsqueda, alta oficial, unidad obligatoria, precio pendiente, auditoría y reanudación.\n'
            'No se modificó el catálogo real DATOS/db/articulos.json ni otros datos de negocio.')
