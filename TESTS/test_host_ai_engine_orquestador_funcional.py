from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.host_ai_engine import HostAIEngine
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_sandbox(tmp_path: Path, repo_root: Path) -> None:
    db_dir = tmp_path / "DATOS" / "db"
    facturas_dir = tmp_path / "DATOS" / "facturas"
    db_dir.mkdir(parents=True, exist_ok=True)
    facturas_dir.mkdir(parents=True, exist_ok=True)

    for nombre in ["articulos.json", "proveedores.json", "compras_producto_proveedor.json", "menus.json"]:
        origen = repo_root / "DATOS" / "db" / nombre
        destino = db_dir / nombre
        if origen.exists():
            shutil.copy2(origen, destino)
        else:
            destino.write_text("[]", encoding="utf-8")

    hist_origen = repo_root / "DATOS" / "facturas" / "historico_precios.json"
    hist_dest = facturas_dir / "historico_precios.json"
    if hist_origen.exists():
        shutil.copy2(hist_origen, hist_dest)
    else:
        hist_dest.write_text(json.dumps({"version": "3.0.3.5.3", "registros": []}, ensure_ascii=False, indent=2), encoding="utf-8")


def _ensure_producto(repo: RepositorioProductosMaestro601, nombre: str, precio: float, unidad: str = "kg") -> None:
    if repo.buscar_productos({"nombre": nombre}):
        return
    repo.crear_producto(
        {
            "nombre": nombre,
            "familia": "TEST",
            "unidad_base": unidad,
            "unidad_compra": unidad,
            "precio": str(precio),
            "proveedor": "PROV TEST",
            "proveedor_preferente": "PROV TEST",
            "fecha_precio": "2026-07-22",
            "iva": "10",
        }
    )


def _ensure_receta(repo: RepositorioBibliotecaRecetas601, codigo: str, nombre: str, ingrediente: str = "MP HAE TOMATE") -> None:
    if repo.obtener(codigo):
        return
    out = repo.crear(
        {
            "codigo": codigo,
            "nombre": nombre,
            "familia": "PRUEBAS",
            "tipo": "PRINCIPAL",
            "numero_raciones": 10,
            "ingredientes": [ingrediente],
            "cantidades": ["1 kg"],
            "elaboracion": "Mezclar y servir",
            "tiempo_elaboracion": "10 min",
            "conservacion": "Frio",
            "alergenos": [],
            "observaciones": "",
            "fotografia": "",
        }
    )
    assert out.get("ok") is True


def _confirmation_from_output(resultado: dict, *, estado: str, usuario: str, alcance: dict | None = None) -> dict:
    confirmacion = dict((resultado.get("confirmaciones_requeridas") or [])[0])
    confirmacion["estado"] = estado
    confirmacion["usuario_que_responde"] = usuario
    confirmacion["fecha_respuesta"] = "2026-07-22T23:59:59"
    confirmacion["alcance_autorizado"] = dict(alcance or {})
    return confirmacion


def _texto_importacion_dos_recetas() -> str:
    return "\n".join(
        [
            "Receta: RECETA HAE UNO",
            "Raciones: 10",
            "Tomate: 1 kg",
            "Queso: 0.5 kg",
            "Elaboracion: Mezclar todo.",
            "",
            "Receta: RECETA HAE DOS",
            "Raciones: 8",
            "Tomate: 0.8 kg",
            "Queso: 0.3 kg",
            "Elaboracion: Hornear y servir.",
        ]
    )


def test_consulta_simple_receta_atendida_por_un_agente(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)

    repo_prod = RepositorioProductosMaestro601(tmp_path)
    _ensure_producto(repo_prod, "MP HAE TOMATE", 2.5)
    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    _ensure_receta(repo_rec, "REC-HAE-001", "RECETA HAE SIMPLE")

    engine = HostAIEngine(tmp_path)
    resultado = engine.consultar(
        origen="Recetas",
        modulo="recetas",
        tipo_peticion="buscar_receta",
        datos_enviados={"nombre": "HAE SIMPLE"},
        usar_director=True,
        usuario="chef",
        texto_original="Busca la receta HAE SIMPLE",
    )

    assert str(resultado.get("estado") or "") == "COMPLETADA"
    assert str(resultado.get("agente_principal") or "") == "RECETAS_IA"
    assert len(resultado.get("pasos") or []) == 1
    pasos_ejecutados = list((resultado.get("resultado") or {}).get("pasos_ejecutados") or [])
    assert len(pasos_ejecutados) == 1


def test_solicitud_compleja_delegada_a_varios_agentes_y_espera_confirmacion(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)
    repo_prod = RepositorioProductosMaestro601(tmp_path)
    _ensure_producto(repo_prod, "Tomate", 2.5)
    _ensure_producto(repo_prod, "Queso", 6.0)

    engine = HostAIEngine(tmp_path)
    resultado = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="importar_word_crear_recetas_generar_escandallos",
        datos_enviados={"texto_importacion": _texto_importacion_dos_recetas(), "origen_documento": "WORD"},
        usar_director=True,
        usuario="chef",
        texto_original="Importa este Word, crea las recetas y genera los escandallos.",
    )

    assert str(resultado.get("estado") or "") == "ESPERANDO_CONFIRMACION"
    assert str(resultado.get("agente_principal") or "") == "DIRECTOR_IA"
    assert {"IMPORTACION_IA", "CATALOGO_IA", "RECETAS_IA", "ESCANDALLOS_IA"}.issubset(set(resultado.get("agentes_delegados") or []))
    assert len(resultado.get("confirmaciones_requeridas") or []) == 1


def test_confirmacion_aceptada_ejecuta_solo_servicios_autorizados_en_sandbox(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)
    repo_prod = RepositorioProductosMaestro601(tmp_path)
    _ensure_producto(repo_prod, "Tomate", 2.5)
    _ensure_producto(repo_prod, "Queso", 6.0)

    engine = HostAIEngine(tmp_path)
    previo = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="importar_word_crear_recetas_generar_escandallos",
        datos_enviados={"texto_importacion": _texto_importacion_dos_recetas(), "origen_documento": "WORD"},
        usar_director=True,
        usuario="chef",
        texto_original="Importa este Word, crea las recetas y genera los escandallos.",
    )
    confirmacion = _confirmation_from_output(
        previo,
        estado="ACEPTADA",
        usuario="chef",
        alcance={"recetas_autorizadas": ["receta hae uno", "receta hae dos"]},
    )

    final = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="importar_word_crear_recetas_generar_escandallos",
        datos_enviados={"texto_importacion": _texto_importacion_dos_recetas(), "origen_documento": "WORD"},
        usar_director=True,
        usuario="chef",
        texto_original="Importa este Word, crea las recetas y genera los escandallos.",
        confirmaciones_recibidas=[confirmacion],
    )

    assert str(final.get("estado") or "") == "COMPLETADA"
    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    assert repo_rec.buscar(nombre="HAE UNO", incluir_archivadas=True)
    assert repo_rec.buscar(nombre="HAE DOS", incluir_archivadas=True)
    assert int(((final.get("resultado") or {}).get("resultados_por_paso") or {}).get(7, {}).get("total", 0)) >= 1


def test_confirmacion_rechazada_cancela_sin_persistir(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)
    engine = HostAIEngine(tmp_path)

    previo = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="importar_word_crear_recetas_generar_escandallos",
        datos_enviados={"texto_importacion": _texto_importacion_dos_recetas(), "origen_documento": "WORD"},
        usar_director=True,
        usuario="chef",
        texto_original="Importa este Word, crea las recetas y genera los escandallos.",
    )
    confirmacion = _confirmation_from_output(previo, estado="RECHAZADA", usuario="chef")

    final = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="importar_word_crear_recetas_generar_escandallos",
        datos_enviados={"texto_importacion": _texto_importacion_dos_recetas(), "origen_documento": "WORD"},
        usar_director=True,
        usuario="chef",
        texto_original="Importa este Word, crea las recetas y genera los escandallos.",
        confirmaciones_recibidas=[confirmacion],
    )
    assert str(final.get("estado") or "") == "CANCELADA"
    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    assert not repo_rec.buscar(nombre="HAE UNO", incluir_archivadas=True)


def test_confirmacion_parcial_limita_alcance_autorizado(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)
    engine = HostAIEngine(tmp_path)

    previo = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="importar_word_crear_recetas_generar_escandallos",
        datos_enviados={"texto_importacion": _texto_importacion_dos_recetas(), "origen_documento": "WORD"},
        usar_director=True,
        usuario="chef",
        texto_original="Importa este Word, crea las recetas y genera los escandallos.",
    )
    confirmacion = _confirmation_from_output(
        previo,
        estado="PARCIAL",
        usuario="chef",
        alcance={"recetas_autorizadas": ["receta hae uno"]},
    )
    final = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="importar_word_crear_recetas_generar_escandallos",
        datos_enviados={"texto_importacion": _texto_importacion_dos_recetas(), "origen_documento": "WORD"},
        usar_director=True,
        usuario="chef",
        texto_original="Importa este Word, crea las recetas y genera los escandallos.",
        confirmaciones_recibidas=[confirmacion],
    )

    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    assert repo_rec.buscar(nombre="HAE UNO", incluir_archivadas=True)
    assert not repo_rec.buscar(nombre="HAE DOS", incluir_archivadas=True)
    omitidas = (((final.get("resultado") or {}).get("resultados_por_paso") or {}).get(6, {}) or {}).get("omitidas", [])
    assert len(omitidas) >= 1


def test_cambio_de_plan_invalida_confirmacion_anterior(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)
    engine = HostAIEngine(tmp_path)

    previo = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="importar_word_crear_recetas_generar_escandallos",
        datos_enviados={"texto_importacion": _texto_importacion_dos_recetas(), "origen_documento": "WORD"},
        usar_director=True,
        usuario="chef",
        texto_original="Importa este Word, crea las recetas y genera los escandallos.",
    )
    confirmacion = _confirmation_from_output(previo, estado="ACEPTADA", usuario="chef", alcance={"recetas_autorizadas": ["receta hae uno"]})
    texto_cambiado = _texto_importacion_dos_recetas() + "\n\nReceta: RECETA HAE TRES\nRaciones: 5\nTomate: 0.3 kg\nElaboracion: Nuevo bloque."

    final = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="importar_word_crear_recetas_generar_escandallos",
        datos_enviados={"texto_importacion": texto_cambiado, "origen_documento": "WORD"},
        usar_director=True,
        usuario="chef",
        texto_original="Importa este Word cambiado.",
        confirmaciones_recibidas=[confirmacion],
    )

    assert str(final.get("estado") or "") == "ESPERANDO_CONFIRMACION"
    incidencias = list(final.get("incidencias") or [])
    assert any("no coincide con el plan actual" in str(i.get("detalle") or "").lower() for i in incidencias)


def test_falta_de_datos_obligatorios_bloquea_la_solicitud(tmp_path: Path) -> None:
    engine = HostAIEngine(tmp_path)
    resultado = engine.consultar(
        origen="Recetas",
        modulo="recetas",
        tipo_peticion="buscar_receta",
        datos_enviados={},
        usar_director=True,
        usuario="chef",
        texto_original="Busca receta",
    )
    assert str(resultado.get("estado") or "") == "BLOQUEADA"
    assert any(str(i.get("tipo") or "") == "DATO_OBLIGATORIO_AUSENTE" for i in list(resultado.get("incidencias") or []))


def test_dato_ambiguo_se_reporta_sin_inventar_resultado(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)
    repo_prod = RepositorioProductosMaestro601(tmp_path)
    _ensure_producto(repo_prod, "MP HAE TOMATE", 2.5)
    repo_rec = RepositorioBibliotecaRecetas601(tmp_path)
    _ensure_receta(repo_rec, "REC-HAE-A", "CROQUETA BASE A")
    _ensure_receta(repo_rec, "REC-HAE-B", "CROQUETA BASE B")
    engine = HostAIEngine(tmp_path)

    resultado = engine.consultar(
        origen="Recetas",
        modulo="recetas",
        tipo_peticion="buscar_receta",
        datos_enviados={"nombre": "CROQUETA BASE"},
        usar_director=True,
        usuario="chef",
        texto_original="Busca la croqueta base",
    )
    assert str(resultado.get("estado") or "") == "COMPLETADA_CON_INCIDENCIAS"
    incidencias = list(resultado.get("incidencias") or [])
    assert any(str(i.get("tipo") or "") == "DATO_AMBIGUO" for i in incidencias)


def test_capacidad_no_implementada_usa_simulador_determinista(tmp_path: Path) -> None:
    engine = HostAIEngine(tmp_path)
    resultado = engine.consultar(
        origen="Eventos",
        modulo="eventos",
        tipo_peticion="consultar_evento",
        datos_enviados={"sim_scenario": "capacidad_no_disponible", "evento_id": "EV-1"},
        usar_director=True,
        usuario="chef",
        texto_original="Consulta el evento EV-1",
    )
    assert str(resultado.get("estado") or "") == "COMPLETADA_CON_INCIDENCIAS"
    paso = (((resultado.get("resultado") or {}).get("resultados_por_paso") or {}).get(1) or {})
    assert paso.get("simulado") is True


def test_error_en_paso_se_registra_y_no_persiste(tmp_path: Path) -> None:
    engine = HostAIEngine(tmp_path)
    resultado = engine.consultar(
        origen="Recetas",
        modulo="recetas",
        tipo_peticion="buscar_receta",
        datos_enviados={"nombre": "cualquiera", "forzar_error_step": "buscar_receta"},
        usar_director=True,
        usuario="chef",
        texto_original="Busca receta forzando error",
    )
    assert str(resultado.get("estado") or "") == "ERROR"
    assert resultado.get("errores")


def test_cancelacion_antes_de_persistir(tmp_path: Path) -> None:
    engine = HostAIEngine(tmp_path)
    resultado = engine.consultar(
        origen="Importacion",
        modulo="importacion",
        tipo_peticion="importar_word_crear_recetas_generar_escandallos",
        datos_enviados={"cancelar": True, "texto_importacion": _texto_importacion_dos_recetas()},
        usar_director=True,
        usuario="chef",
        texto_original="Cancela esto",
    )
    assert str(resultado.get("estado") or "") == "CANCELADA"


def test_auditoria_completa_y_datos_reales_intactos(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _seed_sandbox(tmp_path, repo_root)
    reales = {
        "articulos": repo_root / "DATOS" / "db" / "articulos.json",
        "proveedores": repo_root / "DATOS" / "db" / "proveedores.json",
        "menus": repo_root / "DATOS" / "db" / "menus.json",
        "historico": repo_root / "DATOS" / "facturas" / "historico_precios.json",
    }
    huellas_antes = {k: _sha256(v) for k, v in reales.items() if v.exists()}

    engine = HostAIEngine(tmp_path)
    _ = engine.consultar(
        origen="Compras",
        modulo="compras",
        tipo_peticion="consultar_necesidades",
        datos_enviados={"sim_scenario": "consulta_simple_receta"},
        usar_director=True,
        usuario="chef",
        texto_original="Consulta necesidades",
    )

    audit_path = tmp_path / "DATOS" / "logs" / "host_ai_engine_auditoria.jsonl"
    assert audit_path.exists()
    contenido = audit_path.read_text(encoding="utf-8")
    assert "id_solicitud" in contenido

    huellas_despues = {k: _sha256(v) for k, v in reales.items() if v.exists()}
    assert huellas_antes == huellas_despues