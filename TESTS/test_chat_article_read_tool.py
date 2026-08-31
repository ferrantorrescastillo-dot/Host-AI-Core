from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_deterministic_intent_router import HostAIDeterministicIntentRouter, INTENT_BUSCAR_ARTICULOS
from SERVICIOS.host_ai_engine.models import HostAIEngineRequest
from SERVICIOS.host_ai_engine.openai_provider import OpenAIProvider
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.host_ai_tool_resolver import HostAIToolResolver


class _ArticlesRead:
    def __init__(self, items):
        self.items = list(items)
        self.queries = []

    def listar(self, query):
        self.queries.append(dict(query))
        term = str(query.get("q") or "").lower()
        items = [item for item in self.items if term in f"{item.get('id', '')} {item.get('codigo', '')} {item.get('nombre', '')}".lower()]
        return {"ok": True, "catalogo": {"items": items[:10], "total": len(items)}}


def _items(count=0):
    base = [
        {"id": "ART000238", "codigo": "ART000238", "nombre": "Patata Monalisa", "unidad": "kg", "estado": "activo", "precio": 2},
        {"id": "ART000412", "codigo": "ART000412", "nombre": "Patata Monalisa Lavada", "unidad": "kg", "estado": "activo", "proveedor": "NO ENVIAR"},
    ]
    if count:
        return [{"id": f"ART{i:06d}", "codigo": f"ART{i:06d}", "nombre": f"Leche {i}", "unidad": "l", "estado": "activo"} for i in range(count)]
    return base


def _executor(service):
    return HostAIToolExecutor(build_default_tool_registry(), articulos_read_service=service)


def test_registry_resolver_y_router_reconocen_buscar_articulos_read():
    tool = build_default_tool_registry().get("buscar_articulos")
    assert tool is not None and tool.tipo == "READ" and tool.solo_lectura is True
    assert HostAIToolResolver().resolve(INTENT_BUSCAR_ARTICULOS) == "buscar_articulos"

    router = HostAIDeterministicIntentRouter()
    assert router.detectar("Búscame Patata Monalisa").terms["termino"] == "patata monalisa"
    assert router.detectar("¿Qué artículo es ART000238?").terms == {"termino": "art000238", "tipo_consulta": "codigo"}
    assert router.detectar("¿Qué unidad tiene Patata Monalisa?").intent == INTENT_BUSCAR_ARTICULOS


def test_executor_usa_servicio_canonico_y_match_exacto_nombre_y_codigo():
    service = _ArticlesRead(_items())
    executor = _executor(service)

    by_name = executor.execute("buscar_articulos", {"termino": "Patata Monalisa"})
    by_code = executor.execute("buscar_articulos", {"termino": "ART000412"})

    assert service.queries == [
        {"q": "Patata Monalisa", "page": 1, "page_size": 10},
        {"q": "ART000412", "page": 1, "page_size": 10},
    ]
    assert by_name.datos["estado"] == "OK"
    assert by_name.datos["articulos"] == [{"article_id": "ART000238", "codigo": "ART000238", "nombre": "Patata Monalisa", "unidad": "kg", "estado": "activo", "activo": True}]
    assert by_code.datos["articulos"][0]["codigo"] == "ART000412"


def test_executor_ambiguo_no_encontrado_vacio_y_limite_diez():
    ambiguous = _executor(_ArticlesRead(_items())).execute("buscar_articulos", {"termino": "Patata"})
    missing = _executor(_ArticlesRead(_items())).execute("buscar_articulos", {"termino": "Merluza"})
    empty_service = _ArticlesRead(_items())
    empty = _executor(empty_service).execute("buscar_articulos", {"termino": ""})
    limited = _executor(_ArticlesRead(_items(14))).execute("buscar_articulos", {"termino": "Leche"})

    assert ambiguous.datos["estado"] == "AMBIGUO" and len(ambiguous.datos["articulos"]) == 2
    assert missing.datos["estado"] == "NO_ENCONTRADO" and missing.datos["articulos"] == []
    assert empty.datos["estado"] == "REQUIERE_TERMINO" and empty_service.queries == []
    assert len(limited.datos["articulos"]) == 10
    assert limited.datos["total_encontrados"] == 14
    assert ambiguous.datos["puede_abrir_buscador"] is True


def test_buscar_articulos_batch_conserva_estados_y_article_id_sin_detenerse_por_ambiguedad():
    service = _ArticlesRead(_items())
    result = _executor(service).execute_agent_read("buscar_articulos", {
        "terminos": ["Patata Monalisa", "Patata", "Merluza"],
    })

    assert result.estado == "OK"
    assert [item["estado"] for item in result.datos["resultados"]] == ["OK", "AMBIGUO", "NO_ENCONTRADO"]
    assert result.datos["resultados"][0]["article_id"] == "ART000238"
    assert len(result.datos["resultados"][1]["candidatos"]) == 2
    assert result.datos["resultados"][2]["articulos"] == []
    assert result.datos["batch_size"] == 3
    assert result.datos["resultados_parciales"] is True
    assert len(service.queries) == 3
    assert result.datos["datos_reales_modificados"] is False


def test_buscar_articulos_batch_admite_diez_y_rechaza_mas_de_diez():
    executor = _executor(_ArticlesRead(_items(14)))
    accepted = executor.execute_agent_read("buscar_articulos", {
        "terminos": [f"Leche {index}" for index in range(10)],
    })
    rejected = executor.execute_agent_read("buscar_articulos", {
        "terminos": [f"Leche {index}" for index in range(11)],
    })

    assert accepted.estado == "OK" and accepted.datos["batch_size"] == 10
    assert all(item.get("article_id") for item in accepted.datos["resultados"])
    assert rejected.estado == "ERROR" and rejected.errores == ["invalid_article_search_batch"]


def test_dto_saneado_solo_lectura_y_write_bloqueado():
    result = _executor(_ArticlesRead(_items())).execute("buscar_articulos", {"termino": "Patata"})
    assert result.datos["fuente"] == "catalogo_articulos_canonico"
    assert result.datos["solo_lectura"] is True
    assert result.datos["datos_reales_modificados"] is False
    assert result.datos["puede_abrir_buscador"] is True
    assert "precio" not in result.datos["articulos"][0]
    assert "proveedor" not in result.datos["articulos"][1]
    assert _executor(_ArticlesRead([])).execute("crear_receta", {}).estado == "DESHABILITADA"


class _Orchestrator:
    def __init__(self, result):
        self.host_ai_engine = SimpleNamespace(default_provider="OPENAI")
        self.result = result
        self.requests = []

    def resolver(self, request):
        self.requests.append(request)
        return SimpleNamespace(to_dict=lambda: {"datos": {"host_ai_engine": self.result}})


def test_chat_openai_falso_recibe_contexto_y_fallback_determinista():
    ok = {"estado": "OK", "proveedor": "OPENAI", "respuesta": {"mensaje": "Articulo explicado"}, "errores": []}
    orchestrator = _Orchestrator(ok)
    chat = ServicioChatHostAIShell(orchestrator)
    chat.tool_executor = _executor(_ArticlesRead(_items()))
    response = chat.enviar("Búscame Patata Monalisa")

    context = orchestrator.requests[0].parametros["datos_enviados"]["tool_context"]
    assert context["articulos"][0]["codigo"] == "ART000238"
    assert response["mensaje"] == "Articulo explicado"
    assert response["datos"]["navigation_request"] == {
        "target_module": "CATALOGO",
        "target_view": "articulos",
        "filter_data": {"termino": "patata monalisa"},
        "entity_id": "",
        "source": "chat_host_ai",
        "preserve_chat_session": True,
        "message": "Abrir esta búsqueda en Artículos.",
        "context_update": {},
    }

    failure = {"estado": "ERROR", "proveedor": "OPENAI", "respuesta": {}, "errores": ["fallo"]}
    chat = ServicioChatHostAIShell(_Orchestrator(failure))
    chat.tool_executor = _executor(_ArticlesRead(_items()))
    fallback = chat.enviar("Búscame Patata Monalisa")
    assert "ART000238" in fallback["mensaje"]


def test_chat_resuelve_seleccion_ordinal_codigo_y_nombre_sin_elegir_ambiguedad():
    simulated = {"estado": "OK_SIMULADO", "proveedor": "SIMULADO", "respuesta": {}, "errores": []}
    chat = ServicioChatHostAIShell(_Orchestrator(simulated))
    chat.tool_executor = _executor(_ArticlesRead(_items()))

    first = chat.enviar("Busca artículos de Patata")
    second = chat.enviar("la 2")
    assert first["datos"]["tool_context"]["estado"] == "AMBIGUO"
    assert second["datos"]["tool_context"]["articulos"][0]["codigo"] == "ART000412"
    assert second["datos"]["tool_context"]["seleccion_resuelta"] is True
    assert second["datos"]["tool_context"]["indice_seleccionado"] == 2

    chat.enviar("Busca artículos de Patata")
    by_code = chat.enviar("ART000238")
    assert by_code["datos"]["tool_context"]["articulos"][0]["codigo"] == "ART000238"

    chat.enviar("Busca artículos de Patata")
    by_name = chat.enviar("Patata Monalisa Lavada")
    assert by_name["datos"]["tool_context"]["articulos"][0]["codigo"] == "ART000412"


def test_seleccion_leche_conserva_semantica_para_openai_y_no_altera_catalogo(tmp_path: Path):
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    catalog = db / "articulos.json"
    milk_items = [
        {"id": "ART000357", "codigo": "ART000357", "nombre": "Leche entera", "unidad": "kg", "estado": "ACTIVO"},
        {"id": "ART000182", "codigo": "ART000182", "nombre": "Leche entera.", "unidad": "kg", "estado": "PENDIENTE_DE_COMPLETAR"},
    ]
    catalog.write_text(json.dumps(milk_items, ensure_ascii=False), encoding="utf-8")
    before = catalog.read_bytes()
    ok = {"estado": "OK", "proveedor": "OPENAI", "respuesta": {"mensaje": "Has seleccionado ART000182 — Leche entera."}, "errores": []}
    orchestrator = _Orchestrator(ok)
    chat = ServicioChatHostAIShell(orchestrator)
    chat.tool_executor = _executor(_ArticlesRead(milk_items))

    ambiguous = chat.enviar("Busca artículos de leche")
    selected = chat.enviar("la 2")
    context = orchestrator.requests[-1].parametros["datos_enviados"]["tool_context"]

    assert ambiguous["datos"]["tool_context"]["estado"] == "AMBIGUO"
    assert context["seleccion_resuelta"] is True
    assert context["seleccion_original"] == "la 2"
    assert context["indice_seleccionado"] == 2
    assert context["criterio_seleccion"] == "ordinal"
    assert context["articulo_seleccionado"]["codigo"] == "ART000182"
    assert context["articulos"] == [context["articulo_seleccionado"]]
    assert context["datos_reales_modificados"] is False
    assert selected["mensaje"] == "Has seleccionado ART000182 — Leche entera."
    prompt = OpenAIProvider._input_text(HostAIEngineRequest(
        origen="CHAT",
        modulo="chat_host_ai",
        tipo_peticion="consulta_general",
        datos_enviados={"pregunta": "la 2", "tool_context": context},
        proveedor_preferido="OPENAI",
    ))
    assert "La selección conversacional ya fue resuelta" in prompt
    assert "No vuelvas a interpretar el ordinal" in prompt
    assert "ART000182" in prompt
    assert catalog.read_bytes() == before


def test_seleccion_primera_y_ordinal_fuera_de_rango_no_eligen_arbitrariamente():
    simulated = {"estado": "OK_SIMULADO", "proveedor": "SIMULADO", "respuesta": {}, "errores": []}
    chat = ServicioChatHostAIShell(_Orchestrator(simulated))
    chat.tool_executor = _executor(_ArticlesRead(_items()))
    chat.enviar("Busca artículos de Patata")
    first = chat.enviar("la 1")
    assert first["datos"]["tool_context"]["articulo_seleccionado"]["codigo"] == "ART000238"

    fresh = ServicioChatHostAIShell(_Orchestrator(simulated))
    fresh.tool_executor = _executor(_ArticlesRead(_items()))
    fresh.enviar("Busca artículos de Patata")
    outside = fresh.enviar("la 5")
    assert "tool_context" not in outside["datos"]
    assert fresh.estado_sesion()["ultimo_elemento"] == ""


def _write_catalog(base: Path):
    db = base / "DATOS" / "db"
    db.mkdir(parents=True)
    path = db / "articulos.json"
    path.write_text(json.dumps(_items(), ensure_ascii=False), encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = base / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text('{"registros": []}', encoding="utf-8")
    return path


def test_post_chat_busca_articulo_por_ruta_real_sin_modificar_catalogo(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("HOST_AI_AI_PROVIDER", "SIMULADO")
    catalog = _write_catalog(tmp_path)
    before = catalog.read_bytes()
    response = HostAIPlatformAPI(base_dir=tmp_path).handle(
        ApiRequest(method="POST", path="/api/v1/chat", body={"mensaje": "Búscame Patata Monalisa", "contexto": {}})
    )
    assert response.status_code == 200
    assert response.payload["ok"] is True
    assert response.payload["datos_reales_modificados"] is False
    assert response.payload["chat"]["datos"]["tool_context"]["articulos"][0]["codigo"] == "ART000238"
    assert catalog.read_bytes() == before
