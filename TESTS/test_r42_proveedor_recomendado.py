from pathlib import Path

from CORE.host_ai_core import HostAICore
from MODELOS.compras import PropuestaCompraInteligente


def _crear_proveedor(core, nombre):
    return core.compras.crear_proveedor_manual(nombre=nombre)


def _mock_propuesta_unica(core, producto="Carrillera de ternera", cantidad=8.0, stock=2.0, proveedor_pref=""):
    core.produccion_real.listar_planes = lambda: [
        {
            "id": "PLAN-001",
            "nombre": "Plan",
            "estado": "planificado",
            "tareas": [{"receta_id": "REC-1", "cantidad": 1, "titulo": "Tarea"}],
        }
    ]
    core.escandallos_inteligente.calcular_necesidades_receta = lambda _rid, _r, origen="": {
        "necesidades": [
            {
                "nombre": producto,
                "unidad": "kg",
                "articulo_id": "ART-CARRI",
                "cantidad_bruta": cantidad,
                "origen": origen or "Plan / Tarea",
                "proveedor_preferente": proveedor_pref,
            }
        ]
    }
    core.stock.stock_actual = lambda: {
        "items": [{"nombre": producto, "unidad": "kg", "articulo_id": "ART-CARRI", "cantidad": stock}]
    }


def test_r42_caso_1_sin_historial(tmp_path: Path):
    core = HostAICore(tmp_path)
    rec = core.compras.recomendar_proveedor("Producto nuevo")
    assert rec["proveedor_nombre"] == ""
    assert rec["fuente"] == "sin_recomendacion"


def test_r42_caso_2_preferente(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "Bundo")
    b = _crear_proveedor(core, "Carnes Girona")
    core.compras.asociar_producto_proveedor_detallado("Carrillera de ternera", a.id)
    core.compras.asociar_producto_proveedor_detallado("Carrillera de ternera", b.id)
    core.compras.marcar_proveedor_preferente_producto("Carrillera de ternera", b.id)
    rec = core.compras.recomendar_proveedor("Carrillera de ternera")
    assert rec["proveedor_nombre"] == "Carnes Girona"
    assert rec["fuente"] == "preferente"


def test_r42_caso_3_frecuencia(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "Proveedor A")
    b = _crear_proveedor(core, "Proveedor B")
    for _ in range(5):
        core.compras.registrar_uso_proveedor("Tomate", proveedor_id=a.id)
    for _ in range(2):
        core.compras.registrar_uso_proveedor("Tomate", proveedor_id=b.id)
    rec = core.compras.recomendar_proveedor("Tomate")
    assert rec["proveedor_nombre"] == "Proveedor A"
    assert rec["fuente"] == "frecuencia"


def test_r42_caso_4_recencia(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "Proveedor A")
    b = _crear_proveedor(core, "Proveedor B")
    core.compras.registrar_uso_proveedor("Cebolla", proveedor_id=a.id, fecha="2026-01-01T10:00:00")
    core.compras.registrar_uso_proveedor("Cebolla", proveedor_id=a.id, fecha="2026-01-02T10:00:00")
    core.compras.registrar_uso_proveedor("Cebolla", proveedor_id=b.id, fecha="2026-01-01T10:00:00")
    core.compras.registrar_uso_proveedor("Cebolla", proveedor_id=b.id, fecha="2026-02-01T10:00:00")
    rec = core.compras.recomendar_proveedor("Cebolla")
    assert rec["proveedor_nombre"] == "Proveedor B"


def test_r42_caso_5_proveedor_inactivo(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "Proveedor A")
    b = _crear_proveedor(core, "Proveedor B")
    for _ in range(4):
        core.compras.registrar_uso_proveedor("Zanahoria", proveedor_id=a.id)
    core.compras.registrar_uso_proveedor("Zanahoria", proveedor_id=b.id)
    core.compras.desactivar_proveedor(a.id)
    rec = core.compras.recomendar_proveedor("Zanahoria")
    assert rec["proveedor_nombre"] == "Proveedor B"


def test_r42_caso_6_aprendizaje_confirmar_propuesta(tmp_path: Path):
    core = HostAICore(tmp_path)
    prov = _crear_proveedor(core, "Bundo")
    _mock_propuesta_unica(core, proveedor_pref="Bundo")
    generado = core.compras.generar_propuesta_compra_inteligente(core)
    pid = generado["propuestas"][0]["id"]
    core.compras.confirmar_propuesta_compra(pid, proveedor="Bundo")

    asociados = core.compras.listar_proveedores_producto("Carrillera de ternera")
    assert len(asociados) == 1
    assert asociados[0]["proveedor_id"] == prov.id
    assert asociados[0]["veces_usado"] >= 1
    assert asociados[0]["ultima_compra"]


def test_r42_caso_7_aprendizaje_compra_manual(tmp_path: Path):
    core = HostAICore(tmp_path)
    _crear_proveedor(core, "Pau Gavalda")
    core.compras.registrar_compra_manual("Zanahoria", 5, "kg", "Pau Gavalda")
    rec = core.compras.recomendar_proveedor("Zanahoria")
    assert rec["proveedor_nombre"] == "Pau Gavalda"


def test_r42_caso_8_cambio_manual_proveedor(tmp_path: Path):
    core = HostAICore(tmp_path)
    _crear_proveedor(core, "Proveedor A")
    _crear_proveedor(core, "Proveedor B")
    core.compras.registrar_uso_proveedor("Tomate", proveedor="Proveedor A")
    _mock_propuesta_unica(core, producto="Tomate", proveedor_pref="")
    generado = core.compras.generar_propuesta_compra_inteligente(core)
    pid = generado["propuestas"][0]["id"]
    compra = core.compras.confirmar_propuesta_compra(pid, proveedor="Proveedor B")
    assert compra.proveedor == "Proveedor B"
    rec = core.compras.recomendar_proveedor("Tomate")
    assert rec["proveedor_nombre"] in {"Proveedor A", "Proveedor B"}
    assert any(a["proveedor_nombre"] == "Proveedor B" for a in core.compras.listar_proveedores_producto("Tomate"))


def test_r42_caso_9_preferente_unico(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "A")
    b = _crear_proveedor(core, "B")
    core.compras.asociar_producto_proveedor_detallado("Pimiento", a.id)
    core.compras.asociar_producto_proveedor_detallado("Pimiento", b.id)
    core.compras.marcar_proveedor_preferente_producto("Pimiento", a.id)
    core.compras.marcar_proveedor_preferente_producto("Pimiento", b.id)
    asociados = core.compras.listar_proveedores_producto("Pimiento", solo_activos=False)
    pref = [x for x in asociados if x.get("preferente")]
    assert len(pref) == 1
    assert pref[0]["proveedor_id"] == b.id


def test_r42_caso_10_normalizacion(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "Bundo")
    core.compras.registrar_uso_proveedor("Carrillera de ternera", proveedor_id=p.id)
    core.compras.registrar_uso_proveedor(" carrillera  de  ternera ", proveedor_id=p.id)
    core.compras.registrar_uso_proveedor("CARRILLERA DE TERNERA", proveedor_id=p.id)
    asociados = core.compras.listar_proveedores_producto("Carrillera de ternera", solo_activos=False)
    assert len(asociados) == 1


def test_r42_caso_11_no_duplicar_asociaciones(tmp_path: Path):
    core = HostAICore(tmp_path)
    p = _crear_proveedor(core, "Bundo")
    core.compras.registrar_compra_manual("Huesos", 1, "kg", "Bundo")
    core.compras.registrar_compra_manual("Huesos", 2, "kg", "Bundo")
    asociados = core.compras.listar_proveedores_producto("Huesos", solo_activos=False)
    assert len(asociados) == 1
    assert asociados[0]["veces_usado"] >= 2


def test_r42_caso_12_agrupacion(tmp_path: Path):
    core = HostAICore(tmp_path)
    a = _crear_proveedor(core, "Proveedor A")
    b = _crear_proveedor(core, "Proveedor B")
    core.compras.registrar_uso_proveedor("Producto 1", proveedor_id=a.id)
    core.compras.registrar_uso_proveedor("Producto 2", proveedor_id=a.id)
    core.compras.registrar_uso_proveedor("Producto 3", proveedor_id=b.id)

    for nombre in ["Producto 1", "Producto 2", "Producto 3", "Producto 4"]:
        p = PropuestaCompraInteligente(
            producto=nombre,
            necesario=5,
            disponible=0,
            comprar=5,
            unidad="kg",
            origen="Plan X",
            prioridad="Alta",
            estado="pendiente",
        )
        core.compras.propuestas_compra[p.id] = p
    core.compras._guardar()

    grupos = core.compras.agrupar_propuestas_por_proveedor_recomendado()
    nombres = {g["proveedor"] for g in grupos["grupos"]}
    assert "Proveedor A" in nombres
    assert "Proveedor B" in nombres
    assert "Sin proveedor recomendado" in nombres


def test_r42_caso_13_idempotencia_consulta_recomendaciones(tmp_path: Path):
    core = HostAICore(tmp_path)
    _crear_proveedor(core, "Bundo")
    _mock_propuesta_unica(core, proveedor_pref="Bundo")
    core.compras.generar_propuesta_compra_inteligente(core)
    antes = len(core.compras.listar_propuestas_compra(solo_pendientes=True))
    for _ in range(5):
        propuestas = core.compras.listar_propuestas_compra(solo_pendientes=True)
        for p in propuestas:
            core.compras.recomendar_proveedor_para_propuesta(p["id"])
    despues = len(core.compras.listar_propuestas_compra(solo_pendientes=True))
    assert antes == despues == 1


def test_r42_caso_14_persistencia_antigua_crea_archivo(tmp_path: Path):
    db_file = tmp_path / "DATOS" / "db" / "compras_producto_proveedor.json"
    if db_file.exists():
        db_file.unlink()

    core = HostAICore(tmp_path)
    assert db_file.exists()
    assert core.db.cargar("compras_producto_proveedor") == []

    core_2 = HostAICore(tmp_path)
    assert core_2.db.cargar("compras_producto_proveedor") == []
