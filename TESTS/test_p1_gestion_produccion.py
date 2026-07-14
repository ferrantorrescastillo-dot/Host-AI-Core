from pathlib import Path
from CORE.host_ai_core import HostAICore

def test_p1_crud_y_persistencia(tmp_path: Path):
    core=HostAICore(tmp_path)
    creado=core.produccion_real.crear_plan_manual("Producción lunes","2026-07-13","Ferran","Preparar servicio")
    assert creado["estado"]=="borrador"
    assert core.produccion_real.buscar_planes("ferran")[0]["id"]==creado["id"]
    editado=core.produccion_real.editar_plan(creado["id"],{"estado":"pendiente","responsable":"Marc"})
    assert editado["estado"]=="pendiente" and editado["responsable"]=="Marc"
    dup=core.produccion_real.duplicar_plan(creado["id"],"Producción martes","2026-07-14")
    assert dup["id"]!=creado["id"] and dup["estado"]=="borrador"
    core2=HostAICore(tmp_path)
    assert len(core2.produccion_real.listar_planes())==2
    core2.produccion_real.eliminar_plan(creado["id"])
    assert len(core2.produccion_real.listar_planes())==1
