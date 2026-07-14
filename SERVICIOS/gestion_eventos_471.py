# Host AI 4.7.1 - Gestion de eventos y banquetes

from datetime import datetime
from pathlib import Path
import json
import re
import uuid


ESTADOS_EVENTO = {"borrador", "confirmado", "en_produccion", "servido", "cerrado", "cancelado"}


def _normalizar_texto(valor):
    return str(valor or "").strip()


def generar_id_evento(nombre, fecha=None):
    base = re.sub(r"[^a-zA-Z0-9]+", "_", _normalizar_texto(nombre).lower()).strip("_") or "evento"
    fecha_txt = _normalizar_texto(fecha).replace("-", "")[:8] or datetime.now().strftime("%Y%m%d")
    return f"EVT_{fecha_txt}_{base}_{uuid.uuid4().hex[:6].upper()}"


def crear_evento(nombre, fecha, hora=None, tipo="catering", personas=0, cliente=None, lugar=None, observaciones=None, presupuesto=None, estado="borrador"):
    if estado not in ESTADOS_EVENTO:
        estado = "borrador"
    personas = int(personas or 0)
    evento = {
        "id_evento": generar_id_evento(nombre, fecha),
        "nombre": _normalizar_texto(nombre),
        "tipo": _normalizar_texto(tipo) or "catering",
        "fecha": _normalizar_texto(fecha),
        "hora": _normalizar_texto(hora),
        "personas": personas,
        "cliente": _normalizar_texto(cliente),
        "lugar": _normalizar_texto(lugar),
        "observaciones": _normalizar_texto(observaciones),
        "presupuesto": float(presupuesto or 0),
        "estado": estado,
        "menus": [],
        "produccion": [],
        "compras": [],
        "creado_en": datetime.now().isoformat(timespec="seconds"),
    }
    return evento


def validar_evento(evento):
    errores = []
    if not evento.get("nombre"):
        errores.append("Falta nombre del evento")
    if not evento.get("fecha"):
        errores.append("Falta fecha del evento")
    if int(evento.get("personas") or 0) <= 0:
        errores.append("Falta numero de personas")
    return {"ok": not errores, "errores": errores}


def guardar_evento(evento, ruta="DATOS/db/eventos_47.json"):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    eventos = []
    if ruta.exists():
        try:
            eventos = json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            eventos = []
    eventos = [e for e in eventos if e.get("id_evento") != evento.get("id_evento")]
    eventos.append(evento)
    ruta.write_text(json.dumps(eventos, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "ruta": str(ruta), "total_eventos": len(eventos), "evento": evento}


def cargar_eventos(ruta="DATOS/db/eventos_47.json"):
    ruta = Path(ruta)
    if not ruta.exists():
        return []
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return []


def buscar_eventos(eventos, texto=None, estado=None, fecha=None):
    texto = _normalizar_texto(texto).lower()
    resultado = []
    for evento in eventos:
        if estado and evento.get("estado") != estado:
            continue
        if fecha and evento.get("fecha") != fecha:
            continue
        if texto:
            base = " ".join(str(evento.get(k, "")) for k in ("nombre", "cliente", "lugar", "tipo")).lower()
            if texto not in base:
                continue
        resultado.append(evento)
    return resultado


def cambiar_estado_evento(evento, nuevo_estado):
    if nuevo_estado not in ESTADOS_EVENTO:
        raise ValueError(f"Estado de evento no valido: {nuevo_estado}")
    copia = dict(evento)
    copia["estado"] = nuevo_estado
    copia["actualizado_en"] = datetime.now().isoformat(timespec="seconds")
    return copia
