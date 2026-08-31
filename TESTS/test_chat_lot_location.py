from types import SimpleNamespace

from CORE.host_ai_core import HostAICore
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell


def _chat(tmp_path):
    core = HostAICore(tmp_path)
    core.stock.registrar_entrada("Referencia 1", 1, "kg", ubicacion="Cámara 1", articulo_id="REF-1")
    core.stock.registrar_entrada("Referencia 10", 1, "kg", ubicacion="Cámara 10", articulo_id="REF-10")
    lot = core.stock.registrar_entrada("Patata", 2, "kg", ubicacion="", articulo_id="ART-PAT")["lote"]
    home = SimpleNamespace(core=core)
    chat = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=None), home, session_id="lot-chat")
    return core, lot, chat


def test_chat_lot_location_explicit_preview_confirm_and_open_lot(tmp_path):
    core, lot, chat = _chat(tmp_path)
    preview = chat.enviar(f"Pon el lote {lot['id']} en Cámara 1.")
    assert preview["tipo_mensaje"] == "CONFIRMACION"
    assert preview["datos"]["datos_reales_modificados"] is False
    assert [item["action_id"] for item in preview["datos"]["confirmation_actions"]] == [
        "APPLY_PENDING_LOT_LOCATION", "DISCARD_PENDING_LOT_LOCATION",
    ]
    assert core.stock.lotes[lot["id"]].ubicacion == ""
    quantity = core.stock.lotes[lot["id"]].cantidad
    confirmed = chat.ejecutar_accion_reserva("APPLY_PENDING_LOT_LOCATION")
    assert confirmed["datos"]["ui_action"] == {
        "type": "OPEN_VIEW", "target": "LOTE", "id": lot["id"], "view": "DETALLE", "label": "Abrir lote",
    }
    assert core.stock.lotes[lot["id"]].ubicacion == "Cámara 1"
    assert core.stock.lotes[lot["id"]].cantidad == quantity


def test_chat_lot_location_context_cancel_and_no_late_confirm(tmp_path):
    core, lot, chat = _chat(tmp_path)
    preview = chat.enviar("Arregla la ubicación de este lote en Cámara 1.", {"lote_id": lot["id"]})
    assert preview["tipo_mensaje"] == "CONFIRMACION"
    cancelled = chat.ejecutar_accion_reserva("DISCARD_PENDING_LOT_LOCATION")
    assert cancelled["ok"] and core.stock.lotes[lot["id"]].ubicacion == ""
    stale = chat.ejecutar_accion_reserva("APPLY_PENDING_LOT_LOCATION")
    assert stale["tipo_mensaje"] == "ADVERTENCIA"


def test_chat_lot_location_never_guesses_lot_or_location(tmp_path):
    core, lot, chat = _chat(tmp_path)
    no_context = chat.enviar("Arregla la ubicación de este lote en Cámara 1.")
    assert "único lote" in no_context["mensaje"] and core.stock.lotes[lot["id"]].ubicacion == ""
    missing_lot = chat.enviar("Pon el lote LOT-NOEXISTE en Cámara 1.")
    assert "No existe" in missing_lot["mensaje"]
    ambiguous_location = chat.enviar(f"Pon el lote {lot['id']} en Cámara.")
    assert "varias ubicaciones" in ambiguous_location["mensaje"]
    missing_location = chat.enviar(f"Pon el lote {lot['id']} en Cámara 99.")
    assert "no existe" in missing_location["mensaje"].lower()
    assert core.stock.lotes[lot["id"]].ubicacion == ""


def test_chat_lot_location_text_confirmation_does_not_reinterpret(tmp_path):
    core, lot, chat = _chat(tmp_path)
    chat.enviar(f"Pon el lote {lot['id']} en Cámara 1.")
    confirmed = chat.enviar("Sí, confirmar.")
    assert confirmed["datos"]["ui_action"]["target"] == "LOTE"
    assert core.stock.lotes[lot["id"]].ubicacion == "Cámara 1"
