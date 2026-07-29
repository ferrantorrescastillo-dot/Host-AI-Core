from __future__ import annotations

import json
import tempfile
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

VERSION_MODELO_FLUJO = "1.0"

ESTADOS_FLUJO = {
    "creado",
    "activo",
    "esperando_seleccion",
    "esperando_confirmacion",
    "en_ejecucion_segura",
    "completado",
    "cancelado",
    "error",
}

ESTADOS_PASO = {
    "pendiente",
    "seleccionado",
    "esperando_confirmacion",
    "confirmado",
    "rechazado",
    "en_ejecucion_segura",
    "preparado_modo_seguro",
    "completado",
    "cancelado",
    "error",
}

ESTADOS_TERMINALES_PASO = {"completado", "preparado_modo_seguro", "cancelado", "rechazado"}
ESTADOS_NO_SELECCIONABLES = {"completado", "cancelado", "rechazado", "error", "preparado_modo_seguro"}


def ahora_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def crear_id_flujo() -> str:
    return f"flujo-{uuid4()}"


def _crear_id_paso() -> str:
    return f"paso-{uuid4()}"


def registrar_historial(
    flujo: Dict[str, Any],
    evento: str,
    detalle: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not isinstance(flujo, dict):
        raise TypeError("flujo debe ser un dict")
    copia = deepcopy(flujo)
    historial = list(copia.get("historial") or [])
    historial.append(
        {
            "fecha": ahora_iso(),
            "evento": str(evento or "evento"),
            "detalle": deepcopy(detalle or {}),
        }
    )
    copia["historial"] = historial
    copia["fecha_actualizacion"] = ahora_iso()
    return copia


def crear_paso(
    orden: int,
    codigo: str,
    nombre: str,
    modulo: str,
    accion: str,
    requiere_confirmacion: bool = False,
    modifica_datos: bool = False,
    datos: Optional[Dict[str, Any]] = None,
    id_paso: Optional[str] = None,
) -> Dict[str, Any]:
    ts = ahora_iso()
    paso = {
        "id_paso": str(id_paso or _crear_id_paso()),
        "orden": int(orden),
        "codigo": str(codigo or ""),
        "nombre": str(nombre or ""),
        "modulo": str(modulo or ""),
        "accion": str(accion or ""),
        "estado": "pendiente",
        "requiere_confirmacion": bool(requiere_confirmacion),
        "modifica_datos": bool(modifica_datos),
        "datos": deepcopy(datos or {}),
        "confirmacion": {
            "estado": "pendiente",
            "valor": None,
            "fecha": None,
            "origen": None,
        },
        "resultado": None,
        "error": None,
        "fecha_creacion": ts,
        "fecha_actualizacion": ts,
    }
    return paso


def crear_flujo(
    tipo_flujo: str,
    pasos: list[Dict[str, Any]],
    datos: Optional[Dict[str, Any]] = None,
    origen: str = "host_ai",
    id_flujo: Optional[str] = None,
) -> Dict[str, Any]:
    ts = ahora_iso()
    pasos_norm: list[Dict[str, Any]] = []
    for idx, paso in enumerate(list(pasos or []), start=1):
        p = deepcopy(paso)
        if not p.get("id_paso"):
            p["id_paso"] = _crear_id_paso()
        if not p.get("estado"):
            p["estado"] = "pendiente"
        if p.get("estado") not in ESTADOS_PASO:
            p["estado"] = "pendiente"
        p.setdefault("orden", idx)
        p.setdefault("confirmacion", {"estado": "pendiente", "valor": None, "fecha": None, "origen": None})
        p.setdefault("datos", {})
        p.setdefault("resultado", None)
        p.setdefault("error", None)
        p.setdefault("fecha_creacion", ts)
        p["fecha_actualizacion"] = ts
        pasos_norm.append(p)

    flujo = {
        "id_flujo": str(id_flujo or crear_id_flujo()),
        "version_modelo": VERSION_MODELO_FLUJO,
        "tipo_flujo": str(tipo_flujo or "operativo"),
        "estado": "creado",
        "origen": str(origen or "host_ai"),
        "datos": deepcopy(datos or {}),
        "paso_actual": None,
        "accion_seleccionada": None,
        "pasos": pasos_norm,
        "confirmaciones_especificas": {},
        "historial": [],
        "fecha_creacion": ts,
        "fecha_actualizacion": ts,
        "fecha_finalizacion": None,
    }
    flujo = registrar_historial(flujo, "flujo_creado", {"total_pasos": len(pasos_norm)})
    return flujo


def validar_flujo(flujo: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(flujo, dict):
        return {"ok": False, "estado": "flujo_invalido", "mensaje": "El flujo debe ser un diccionario."}
    faltan = [
        k
        for k in [
            "id_flujo",
            "version_modelo",
            "tipo_flujo",
            "estado",
            "pasos",
            "historial",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        if k not in flujo
    ]
    if faltan:
        return {
            "ok": False,
            "estado": "flujo_invalido",
            "mensaje": f"Faltan campos obligatorios: {', '.join(faltan)}",
        }
    if str(flujo.get("estado")) not in ESTADOS_FLUJO:
        return {
            "ok": False,
            "estado": "flujo_invalido",
            "mensaje": f"Estado de flujo no válido: {flujo.get('estado')}",
        }
    pasos = list(flujo.get("pasos") or [])
    for paso in pasos:
        if not isinstance(paso, dict):
            return {"ok": False, "estado": "flujo_invalido", "mensaje": "Cada paso debe ser un diccionario."}
        if str(paso.get("estado") or "") not in ESTADOS_PASO:
            return {
                "ok": False,
                "estado": "flujo_invalido",
                "mensaje": f"Estado de paso no válido: {paso.get('estado')}",
            }
    return {"ok": True, "estado": "flujo_valido", "flujo": deepcopy(flujo)}


def obtener_paso(flujo: Dict[str, Any], id_o_codigo: str) -> Dict[str, Any]:
    valor = str(id_o_codigo or "").strip().lower()
    for paso in list(flujo.get("pasos") or []):
        if str(paso.get("id_paso") or "").lower() == valor or str(paso.get("codigo") or "").lower() == valor:
            return {"ok": True, "estado": "paso_encontrado", "paso": deepcopy(paso)}
    return {"ok": False, "estado": "paso_no_encontrado", "mensaje": "No se encontró el paso solicitado."}


def obtener_paso_actual(flujo: Dict[str, Any]) -> Dict[str, Any]:
    actual = flujo.get("paso_actual")
    if not actual:
        return {"ok": False, "estado": "sin_paso_actual", "mensaje": "No hay paso actual seleccionado."}
    return obtener_paso(flujo, str(actual))


def _actualizar_paso_en_lista(
    pasos: list[Dict[str, Any]],
    id_o_codigo: str,
    patch: Dict[str, Any],
) -> tuple[list[Dict[str, Any]], Optional[Dict[str, Any]]]:
    nuevo: list[Dict[str, Any]] = []
    target: Optional[Dict[str, Any]] = None
    key = str(id_o_codigo or "").lower()
    for paso in pasos:
        p = deepcopy(paso)
        if (
            str(p.get("id_paso") or "").lower() == key
            or str(p.get("codigo") or "").lower() == key
        ):
            p.update(deepcopy(patch))
            p["fecha_actualizacion"] = ahora_iso()
            target = deepcopy(p)
        nuevo.append(p)
    return nuevo, target


def actualizar_estado_paso(
    flujo: Dict[str, Any],
    id_o_codigo: str,
    estado: str,
    detalle_historial: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if estado not in ESTADOS_PASO:
        return {
            "ok": False,
            "estado": "estado_paso_invalido",
            "mensaje": f"Estado de paso no válido: {estado}",
            "flujo": deepcopy(flujo),
        }
    pasos, paso = _actualizar_paso_en_lista(list(flujo.get("pasos") or []), id_o_codigo, {"estado": estado})
    if not paso:
        return {
            "ok": False,
            "estado": "paso_no_encontrado",
            "mensaje": "No se pudo actualizar porque el paso no existe.",
            "flujo": deepcopy(flujo),
        }
    nuevo = deepcopy(flujo)
    nuevo["pasos"] = pasos
    nuevo = registrar_historial(
        nuevo,
        "paso_estado_actualizado",
        {
            "id_paso": paso.get("id_paso"),
            "codigo": paso.get("codigo"),
            "estado": estado,
            **(detalle_historial or {}),
        },
    )
    return {
        "ok": True,
        "estado": "paso_actualizado",
        "flujo": nuevo,
        "paso": paso,
    }


def seleccionar_paso(flujo: Dict[str, Any], id_o_codigo: str, origen: str = "usuario") -> Dict[str, Any]:
    pasos = list(flujo.get("pasos") or [])
    res = obtener_paso(flujo, id_o_codigo)
    if not res.get("ok"):
        return {"ok": False, "estado": "paso_no_encontrado", "mensaje": res.get("mensaje"), "flujo": deepcopy(flujo)}
    paso = dict(res.get("paso") or {})
    if str(paso.get("estado") or "") in ESTADOS_NO_SELECCIONABLES:
        return {
            "ok": False,
            "estado": "paso_no_seleccionable",
            "mensaje": "No se puede seleccionar un paso ya terminal o con error.",
            "flujo": deepcopy(flujo),
            "paso": paso,
        }

    nuevo = deepcopy(flujo)
    nuevo["paso_actual"] = paso.get("id_paso")
    nuevo["accion_seleccionada"] = {
        "id_paso": paso.get("id_paso"),
        "codigo": paso.get("codigo"),
        "nombre": paso.get("nombre"),
    }

    if bool(paso.get("requiere_confirmacion")):
        upd = actualizar_estado_paso(nuevo, str(paso.get("id_paso")), "esperando_confirmacion")
        nuevo = deepcopy(upd.get("flujo") or nuevo)
        nuevo["estado"] = "esperando_confirmacion"
        nuevo = registrar_historial(
            nuevo,
            "paso_seleccionado",
            {"id_paso": paso.get("id_paso"), "codigo": paso.get("codigo"), "requiere_confirmacion": True, "origen": origen},
        )
        return {
            "ok": True,
            "estado": "paso_seleccionado_esperando_confirmacion",
            "flujo": nuevo,
            "paso": obtener_paso(nuevo, str(paso.get("id_paso"))).get("paso"),
        }

    upd = actualizar_estado_paso(nuevo, str(paso.get("id_paso")), "seleccionado")
    nuevo = deepcopy(upd.get("flujo") or nuevo)
    nuevo["estado"] = "activo"
    nuevo = registrar_historial(
        nuevo,
        "paso_seleccionado",
        {"id_paso": paso.get("id_paso"), "codigo": paso.get("codigo"), "requiere_confirmacion": False, "origen": origen},
    )
    return {
        "ok": True,
        "estado": "paso_seleccionado",
        "flujo": nuevo,
        "paso": obtener_paso(nuevo, str(paso.get("id_paso"))).get("paso"),
    }


def registrar_confirmacion(
    flujo: Dict[str, Any],
    id_o_codigo: str,
    confirmada: bool,
    origen: str = "usuario",
    valor: Optional[str] = None,
) -> Dict[str, Any]:
    paso_res = obtener_paso(flujo, id_o_codigo)
    if not paso_res.get("ok"):
        return {"ok": False, "estado": "paso_no_encontrado", "mensaje": paso_res.get("mensaje"), "flujo": deepcopy(flujo)}
    paso = dict(paso_res.get("paso") or {})

    nuevo = deepcopy(flujo)
    confirmacion = dict(paso.get("confirmacion") or {})
    confirmacion.update(
        {
            "estado": "confirmada" if confirmada else "rechazada",
            "valor": valor if valor is not None else ("si" if confirmada else "no"),
            "fecha": ahora_iso(),
            "origen": origen,
        }
    )

    estado_objetivo = "confirmado" if confirmada else "rechazado"
    pasos, paso_u = _actualizar_paso_en_lista(
        list(nuevo.get("pasos") or []),
        str(paso.get("id_paso")),
        {"estado": estado_objetivo, "confirmacion": confirmacion},
    )
    if not paso_u:
        return {
            "ok": False,
            "estado": "paso_no_encontrado",
            "mensaje": "No se pudo registrar la confirmación.",
            "flujo": deepcopy(flujo),
        }

    nuevo["pasos"] = pasos
    conf_esp = dict(nuevo.get("confirmaciones_especificas") or {})
    conf_esp[str(paso_u.get("codigo") or paso_u.get("id_paso"))] = {
        "nombre": paso_u.get("nombre"),
        "confirmada": bool(confirmada),
        "modifico_datos_reales": False,
        "fecha": confirmacion.get("fecha"),
        "origen": origen,
    }
    nuevo["confirmaciones_especificas"] = conf_esp
    nuevo["estado"] = "activo" if confirmada else "esperando_seleccion"
    if not confirmada:
        nuevo["paso_actual"] = None
        nuevo["accion_seleccionada"] = None
    nuevo = registrar_historial(
        nuevo,
        "paso_confirmacion_registrada",
        {
            "id_paso": paso_u.get("id_paso"),
            "codigo": paso_u.get("codigo"),
            "confirmada": bool(confirmada),
            "origen": origen,
        },
    )
    nuevo = actualizar_estado_general(nuevo).get("flujo") or nuevo
    return {
        "ok": True,
        "estado": "confirmacion_registrada",
        "flujo": nuevo,
        "paso": obtener_paso(nuevo, str(paso_u.get("id_paso"))).get("paso"),
    }


def registrar_resultado(
    flujo: Dict[str, Any],
    id_o_codigo: str,
    resultado: Dict[str, Any],
    estado_paso_final: str = "preparado_modo_seguro",
) -> Dict[str, Any]:
    if estado_paso_final not in ESTADOS_PASO:
        return {
            "ok": False,
            "estado": "estado_paso_invalido",
            "mensaje": f"Estado final no válido: {estado_paso_final}",
            "flujo": deepcopy(flujo),
        }
    datos_resultado = deepcopy(resultado or {})
    datos_resultado.setdefault("modo", "seguro")
    datos_resultado["datos_reales_modificados"] = False

    pasos, paso = _actualizar_paso_en_lista(
        list(flujo.get("pasos") or []),
        id_o_codigo,
        {"resultado": datos_resultado, "estado": estado_paso_final, "error": None},
    )
    if not paso:
        return {
            "ok": False,
            "estado": "paso_no_encontrado",
            "mensaje": "No se pudo registrar resultado.",
            "flujo": deepcopy(flujo),
        }

    nuevo = deepcopy(flujo)
    nuevo["pasos"] = pasos
    nuevo["estado"] = "activo"
    nuevo = registrar_historial(
        nuevo,
        "paso_resultado_registrado",
        {
            "id_paso": paso.get("id_paso"),
            "codigo": paso.get("codigo"),
            "estado_paso": estado_paso_final,
            "modo": datos_resultado.get("modo"),
            "datos_reales_modificados": False,
        },
    )
    nuevo = actualizar_estado_general(nuevo).get("flujo") or nuevo
    return {
        "ok": True,
        "estado": "resultado_registrado",
        "flujo": nuevo,
        "paso": obtener_paso(nuevo, str(paso.get("id_paso"))).get("paso"),
    }


def registrar_error(
    flujo: Dict[str, Any],
    id_o_codigo: str,
    mensaje_error: str,
    detalle: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload_error = {
        "mensaje": str(mensaje_error or "Error operativo"),
        "detalle": deepcopy(detalle or {}),
        "fecha": ahora_iso(),
    }
    pasos, paso = _actualizar_paso_en_lista(
        list(flujo.get("pasos") or []),
        id_o_codigo,
        {"estado": "error", "error": payload_error},
    )
    if not paso:
        return {
            "ok": False,
            "estado": "paso_no_encontrado",
            "mensaje": "No se pudo registrar error.",
            "flujo": deepcopy(flujo),
        }
    nuevo = deepcopy(flujo)
    nuevo["pasos"] = pasos
    nuevo["estado"] = "error"
    nuevo = registrar_historial(
        nuevo,
        "paso_error_registrado",
        {"id_paso": paso.get("id_paso"), "codigo": paso.get("codigo"), "error": payload_error},
    )
    nuevo = actualizar_estado_general(nuevo).get("flujo") or nuevo
    return {
        "ok": True,
        "estado": "error_registrado",
        "flujo": nuevo,
        "paso": obtener_paso(nuevo, str(paso.get("id_paso"))).get("paso"),
    }


def cancelar_flujo(
    flujo: Dict[str, Any],
    motivo: str = "cancelado_por_usuario",
    origen: str = "usuario",
) -> Dict[str, Any]:
    nuevo = deepcopy(flujo)
    pasos_cancelados: list[str] = []
    pasos = []
    for paso in list(nuevo.get("pasos") or []):
        p = deepcopy(paso)
        if str(p.get("estado") or "") in {"pendiente", "seleccionado", "esperando_confirmacion", "confirmado", "en_ejecucion_segura"}:
            p["estado"] = "cancelado"
            p["fecha_actualizacion"] = ahora_iso()
            pasos_cancelados.append(str(p.get("id_paso") or p.get("codigo") or ""))
        pasos.append(p)
    nuevo["pasos"] = pasos
    nuevo["estado"] = "cancelado"
    nuevo["fecha_finalizacion"] = ahora_iso()
    nuevo["paso_actual"] = None
    nuevo["accion_seleccionada"] = None
    nuevo = registrar_historial(
        nuevo,
        "flujo_cancelado",
        {"motivo": motivo, "origen": origen, "pasos_cancelados": pasos_cancelados},
    )
    return {"ok": True, "estado": "flujo_cancelado", "flujo": nuevo}


def actualizar_estado_general(flujo: Dict[str, Any]) -> Dict[str, Any]:
    nuevo = deepcopy(flujo)
    pasos = list(nuevo.get("pasos") or [])
    estados = {str(p.get("estado") or "") for p in pasos}

    estado_objetivo = str(nuevo.get("estado") or "creado")
    if "error" in estados:
        estado_objetivo = "error"
    elif pasos and all(e in ESTADOS_TERMINALES_PASO for e in estados):
        estado_objetivo = "completado"
    elif estado_objetivo == "cancelado":
        estado_objetivo = "cancelado"
    elif nuevo.get("paso_actual") and estado_objetivo in {"creado", "activo"}:
        estado_objetivo = "activo"
    elif not nuevo.get("paso_actual") and estado_objetivo == "activo":
        estado_objetivo = "esperando_seleccion"

    if estado_objetivo in {"completado", "cancelado"} and not nuevo.get("fecha_finalizacion"):
        nuevo["fecha_finalizacion"] = ahora_iso()
    if estado_objetivo not in {"completado", "cancelado"}:
        nuevo["fecha_finalizacion"] = None

    if estado_objetivo != nuevo.get("estado"):
        previo = nuevo.get("estado")
        nuevo["estado"] = estado_objetivo
        nuevo = registrar_historial(
            nuevo,
            "flujo_estado_actualizado",
            {"anterior": previo, "nuevo": estado_objetivo},
        )
    else:
        nuevo["fecha_actualizacion"] = ahora_iso()

    return {"ok": True, "estado": "estado_general_actualizado", "flujo": nuevo}


def serializar_flujo(flujo: Dict[str, Any]) -> Dict[str, Any]:
    validacion = validar_flujo(flujo)
    if not validacion.get("ok"):
        return {
            "ok": False,
            "estado": "serializacion_error",
            "mensaje": validacion.get("mensaje"),
            "flujo": deepcopy(flujo),
        }
    try:
        texto = json.dumps(flujo, ensure_ascii=False, indent=2)
    except TypeError as exc:
        return {
            "ok": False,
            "estado": "serializacion_error",
            "mensaje": f"Flujo no serializable: {exc}",
            "flujo": deepcopy(flujo),
        }
    return {"ok": True, "estado": "flujo_serializado", "flujo": deepcopy(flujo), "texto": texto}


def deserializar_flujo(texto_json: str) -> Dict[str, Any]:
    try:
        flujo = json.loads(str(texto_json or "{}"))
    except json.JSONDecodeError:
        return {
            "ok": False,
            "estado": "deserializacion_error",
            "mensaje": "El texto JSON no es válido.",
            "flujo": None,
        }
    validacion = validar_flujo(flujo)
    if not validacion.get("ok"):
        return {
            "ok": False,
            "estado": "deserializacion_error",
            "mensaje": validacion.get("mensaje"),
            "flujo": deepcopy(flujo),
        }
    return {"ok": True, "estado": "flujo_deserializado", "flujo": deepcopy(flujo)}


def guardar_flujo_json(
    flujo: Dict[str, Any],
    ruta: Optional[Path] = None,
    base_dir: Optional[Path] = None,
    overwrite: bool = False,
) -> Dict[str, Any]:
    validacion = validar_flujo(flujo)
    if not validacion.get("ok"):
        return {
            "ok": False,
            "estado": "guardar_error",
            "mensaje": validacion.get("mensaje"),
            "flujo": deepcopy(flujo),
        }

    base = Path(base_dir or Path.cwd()).resolve()
    destino = Path(ruta).resolve() if ruta else (base / "DATOS" / "flujos" / f"{flujo.get('id_flujo')}.json")
    if destino.exists() and not overwrite:
        return {
            "ok": False,
            "estado": "guardar_error",
            "mensaje": f"Ya existe un archivo para este flujo: {destino}",
            "flujo": deepcopy(flujo),
            "ruta": str(destino),
        }

    destino.parent.mkdir(parents=True, exist_ok=True)
    serial = serializar_flujo(flujo)
    if not serial.get("ok"):
        return {
            "ok": False,
            "estado": "guardar_error",
            "mensaje": serial.get("mensaje"),
            "flujo": deepcopy(flujo),
            "ruta": str(destino),
        }

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=destino.parent, suffix=".tmp") as tmp:
        tmp.write(str(serial.get("texto") or "{}"))
        temp_path = Path(tmp.name)
    temp_path.replace(destino)

    return {
        "ok": True,
        "estado": "flujo_guardado",
        "flujo": deepcopy(flujo),
        "ruta": str(destino),
    }


def cargar_flujo_json(ruta: Path) -> Dict[str, Any]:
    destino = Path(ruta).resolve()
    if not destino.exists():
        return {
            "ok": False,
            "estado": "carga_error",
            "mensaje": f"No existe el archivo de flujo: {destino}",
            "flujo": None,
            "ruta": str(destino),
        }
    try:
        texto = destino.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "ok": False,
            "estado": "carga_error",
            "mensaje": f"No se pudo leer el archivo: {exc}",
            "flujo": None,
            "ruta": str(destino),
        }

    res = deserializar_flujo(texto)
    if not res.get("ok"):
        return {
            "ok": False,
            "estado": "carga_error",
            "mensaje": res.get("mensaje"),
            "flujo": deepcopy(res.get("flujo")),
            "ruta": str(destino),
        }

    return {
        "ok": True,
        "estado": "flujo_cargado",
        "flujo": deepcopy(res.get("flujo")),
        "ruta": str(destino),
    }


__all__ = [
    "VERSION_MODELO_FLUJO",
    "ESTADOS_FLUJO",
    "ESTADOS_PASO",
    "ahora_iso",
    "crear_id_flujo",
    "crear_paso",
    "crear_flujo",
    "validar_flujo",
    "obtener_paso",
    "obtener_paso_actual",
    "seleccionar_paso",
    "actualizar_estado_paso",
    "registrar_confirmacion",
    "registrar_resultado",
    "registrar_error",
    "cancelar_flujo",
    "actualizar_estado_general",
    "registrar_historial",
    "serializar_flujo",
    "deserializar_flujo",
    "guardar_flujo_json",
    "cargar_flujo_json",
]
