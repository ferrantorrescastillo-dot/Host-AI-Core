from __future__ import annotations

from typing import Any


PRODUCTION_INPUT = {
    "type": "object",
    "properties": {
        "consulta": {
            "type": "string",
            "enum": ["pendientes", "en_curso", "hoy", "bloqueadas", "terminadas", "buscar"],
            "description": "Usa buscar para resolver un plan por nombre o por el menú que lo originó; usa los otros valores para filtrar tareas globales o del plan_id/menu_id indicado.",
        },
        "termino": {"type": "string", "description": "Nombre o identificador de plan, o nombre de menú de origen."},
        "plan_id": {"type": "string", "description": "Identificador canónico del plan ya resuelto."},
        "menu_id": {"type": "string", "description": "Identificador canónico del menú de origen, incluido el menú activo del contexto conversacional."},
        "fecha": {"type": "string"},
        "limite": {"type": "integer", "minimum": 1, "maximum": 10},
    },
    "additionalProperties": False,
}
EVENTS_INPUT = {
    "type": "object",
    "properties": {
        "consulta": {
            "type": "string",
            "enum": ["listar", "proximos", "buscar", "detalle"],
            "description": "listar/proximos para el modulo Eventos; buscar o detalle solo cuando exista un termino o evento_id concreto.",
        },
        "termino": {"type": "string", "description": "Nombre o identificador de un evento concreto."},
        "evento_id": {"type": "string", "description": "Identificador canonico de un evento ya resuelto."},
        "limite": {"type": "integer", "minimum": 1, "maximum": 10},
    },
    "additionalProperties": False,
}
RESERVATIONS_INPUT = {
    "type": "object",
    "properties": {
        "alcance": {"type": "string", "enum": ["todas", "hoy", "proximas"]},
        "q": {"type": "string", "description": "Nombre del cliente; no busca eventos, produccion ni stock reservado."},
        "fecha": {"type": "string", "description": "Fecha ISO YYYY-MM-DD."},
        "estado": {"type": "string"},
        "servicio": {"type": "string"},
        "limite": {"type": "integer", "minimum": 1, "maximum": 10},
        "reserva_id": {"type": "string", "pattern": "^RES-[A-F0-9]{12}$", "description": "Identificador canonico RES- seguido de 12 caracteres hexadecimales."},
    },
    "additionalProperties": False,
}
STOCK_INPUT = {
    "type": "object",
    "properties": {
        "consulta": {
            "type": "string",
            "enum": ["resumen", "alertas", "articulo"],
            "description": "Usa articulo siempre que la petición mencione un nombre, código o término concreto; resumen y alertas son exclusivamente globales.",
        },
        "termino": {
            "type": "string",
            "description": "Nombre o código que debe filtrarse en el catálogo. Si se informa, la consulta efectiva es articulo.",
        },
        "terminos": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1,
            "maxItems": 10,
            "description": "Hasta 10 nombres o IDs canónicos para comprobar Stock en una sola lectura batch.",
        },
    },
    "additionalProperties": False,
}
PURCHASES_INPUT = {
    "type": "object",
    "properties": {
        "consulta": {
            "type": "string",
            "enum": ["listado", "pedido"],
            "description": "listado para estado global de compras; pedido para resolver un pedido canónico por pedido_id o proveedor.",
        },
        "estado": {"type": "string"},
        "pedido_id": {"type": "string"},
        "article_id": {"type": "string"},
        "proveedor": {"type": "string"},
        "limite": {"type": "integer", "minimum": 1, "maximum": 10},
    },
    "additionalProperties": False,
}
ARTICLE_SEARCH_INPUT = {
    "type": "object",
    "properties": {
        "termino": {"type": "string", "minLength": 1},
        "terminos": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1,
            "maxItems": 10,
            "description": "Hasta 10 nombres o codigos de articulo para resolverlos independientemente en una sola lectura batch.",
        },
    },
    "oneOf": [{"required": ["termino"]}, {"required": ["terminos"]}],
    "additionalProperties": False,
}
ARTICLE_DETAIL_INPUT = {
    "type": "object",
    "properties": {"article_id": {"type": "string", "minLength": 1}},
    "required": ["article_id"], "additionalProperties": False,
}
ESCANDALLOS_INPUT = {
    "type": "object",
    "properties": {
        "consulta": {"type": "string", "enum": ["listar", "buscar", "detalle"]},
        "termino": {"type": "string"},
        "escandallo_id": {"type": "string"},
        "nombre_referencia": {"type": "string", "description": "Nombre humano asociado a una referencia histórica que no resuelva por ID."},
        "escandallo_ids": {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1, "maxItems": 50, "description": "IDs canónicos de elaboraciones para recuperar detalles en un único lote READ."},
        "limite": {"type": "integer", "minimum": 1, "maximum": 10},
        "agregacion": {"type": "string", "enum": ["MAX_COSTE_POR_RACION", "MIN_COSTE_POR_RACION", "MAX_COSTE_TOTAL", "MIN_COSTE_TOTAL", "RANK_COSTE_POR_RACION", "COUNT_COSTE_DISPONIBLE", "COUNT_COSTE_INCOMPLETO", "LIST_COSTE_INCOMPLETO", "DETAIL_COSTE_INCOMPLETO"]},
        "orden": {"type": "string", "enum": ["ASC", "DESC"]},
        "posicion": {"type": "integer", "minimum": 1, "maximum": 10},
        "estado_coste": {"type": "string", "enum": ["PARCIAL", "SIN_ESCANDALLO", "SIN_COSTE", "SIN_PRECIO", "SIN_CONVERSION", "NO_CALCULABLE"]},
        "pagina": {"type": "integer", "minimum": 1, "maximum": 10000},
    },
    "additionalProperties": False,
}
USO_ELABORACION_INPUT = {
    "type": "object",
    "properties": {
        "escandallo_id": {"type": "string"},
        "termino": {"type": "string"},
        "limite": {"type": "integer", "minimum": 1, "maximum": 10},
    },
    "additionalProperties": False,
}
MENU_INPUT = {
    "type": "object",
    "properties": {
        "consulta": {"type": "string", "enum": ["detalle", "elaboraciones"]},
        "menu_id": {"type": "string"},
        "termino": {"type": "string"},
        "limite": {"type": "integer", "minimum": 1, "maximum": 10},
    },
    "additionalProperties": False,
}
OPERATIONAL_NEEDS_INPUT = {
    "type": "object",
    "properties": {
        "menu_id": {"type": "string", "description": "Identificador canónico del menú ya resuelto."},
    },
    "required": ["menu_id"],
    "additionalProperties": False,
}
OPEN_ELABORATION_INPUT = {
    "type": "object",
    "properties": {
        "elaboracion_id": {"type": "string"},
        "vista": {"type": "string", "enum": ["receta", "escandallo"]},
    },
    "required": ["elaboracion_id", "vista"],
    "additionalProperties": False,
}
OPEN_ARTICLE_INPUT = {
    "type": "object",
    "properties": {"articulo_id": {"type": "string"}, "vista": {"type": "string", "enum": ["ficha"]}},
    "required": ["articulo_id", "vista"],
    "additionalProperties": False,
}
OPEN_MENU_INPUT = {
    "type": "object", "properties": {"menu_id": {"type": "string"}},
    "required": ["menu_id"], "additionalProperties": False,
}
OPEN_PRODUCTION_INPUT = {
    "type": "object", "properties": {"plan_id": {"type": "string"}},
    "required": ["plan_id"], "additionalProperties": False,
}
OPEN_PURCHASE_INPUT = {
    "type": "object",
    "properties": {"vista": {"type": "string", "enum": ["listado", "pedido"]}, "pedido_id": {"type": "string"}},
    "required": ["vista"], "additionalProperties": False,
}
OPEN_EVENTS_INPUT = {
    "type": "object", "properties": {}, "additionalProperties": False,
}
OPEN_RESERVATIONS_INPUT = {
    "type": "object", "properties": {}, "additionalProperties": False,
}
OPEN_RESERVATION_INPUT = {
    "type": "object", "properties": {"reserva_id": {"type": "string", "pattern": "^RES-[A-F0-9]{12}$"}},
    "required": ["reserva_id"], "additionalProperties": False,
}
CREATE_RESERVATION_INPUT = {
    "type": "object", "properties": {
        "nombre_cliente": {"type": "string", "minLength": 1}, "fecha": {"type": "string"}, "hora": {"type": "string"},
        "pax": {"type": "integer", "minimum": 1, "maximum": 10000},
        "servicio": {"type": "string", "enum": ["COMIDA", "CENA"]},
        "observaciones": {"type": "string"}, "evento_id": {"type": "string"},
        "estado": {"type": "string", "enum": ["PENDIENTE", "CONFIRMADA"]},
    }, "required": ["nombre_cliente", "fecha", "hora", "pax"], "additionalProperties": False,
}
UPDATE_RESERVATION_INPUT = {
    "type": "object", "properties": {
        "reserva_id": {"type": "string", "pattern": "^RES-[A-F0-9]{12}$"},
        "nombre_cliente": {"type": "string"}, "fecha": {"type": "string"}, "hora": {"type": "string"},
        "pax": {"type": "integer", "minimum": 1, "maximum": 10000},
        "servicio": {"type": "string", "enum": ["COMIDA", "CENA"]},
        "observaciones": {"type": "string"}, "evento_id": {"type": "string"},
    }, "required": ["reserva_id"], "additionalProperties": False,
}
TRANSITION_RESERVATION_INPUT = {
    "type": "object", "properties": {"reserva_id": {"type": "string", "pattern": "^RES-[A-F0-9]{12}$"}},
    "required": ["reserva_id"], "additionalProperties": False,
}
APPLY_RESERVATION_INPUT = {
    "type": "object", "properties": {"preview_token": {"type": "string"}},
    "required": ["preview_token"], "additionalProperties": False,
}
CREATE_EVENT_INPUT = {
    "type": "object", "properties": {
        "nombre": {"type": "string", "minLength": 1}, "fecha": {"type": "string"},
        "hora_inicio": {"type": "string"}, "pax": {"type": "integer", "minimum": 1},
        "cliente": {"type": "string"}, "tipo": {"type": "string"},
        "ubicacion": {"type": "string"}, "observaciones": {"type": "string"},
    }, "required": ["nombre", "fecha", "pax"], "additionalProperties": False,
}
CREATE_ARTICLE_INPUT = {
    "type": "object", "properties": {
        "nombre": {"type": "string", "minLength": 1}, "codigo": {"type": "string", "minLength": 1},
        "unidad_base": {"type": "string"}, "unidad_compra": {"type": "string"},
        "cantidad_formato": {"type": "number"}, "unidad_formato": {"type": "string"},
        "precio": {"type": "number", "minimum": 0}, "proveedor": {"type": "string"},
        "estado": {"type": "string"}, "observaciones": {"type": "string"},
    }, "required": ["nombre", "codigo"], "additionalProperties": False,
}
CREATE_RECIPE_INPUT = {
    "type": "object", "properties": {
        "nombre": {"type": "string", "minLength": 1}, "codigo": {"type": "string", "minLength": 1},
        "numero_raciones": {"type": "number", "exclusiveMinimum": 0},
        "ingredientes": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "cantidades": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "ingredientes_estructurados": {"type": "array", "items": {"type": "object"}},
        "elaboracion": {"type": "string", "minLength": 1}, "unidad_rendimiento": {"type": "string"},
        "conservacion": {"type": "string"}, "alergenos": {"type": "array", "items": {"type": "string"}},
        "observaciones": {"type": "string"},
    }, "required": ["nombre", "codigo", "numero_raciones", "ingredientes", "cantidades", "elaboracion"], "additionalProperties": False,
}
APPLY_CATALOG_INPUT = {"type": "object", "properties": {"preview_token": {"type": "string"}}, "required": ["preview_token"], "additionalProperties": False}
PREVIEW_ARTICLE_PRICE_INPUT = {
    "type": "object", "properties": {
        "articulo_id": {"type": "string"}, "valor": {"type": "string"},
    }, "required": ["articulo_id", "valor"], "additionalProperties": False,
}
PREVIEW_ARTICLE_CONVERSION_INPUT = {
    "type": "object", "properties": {
        "articulo_id": {"type": "string"}, "valor": {"type": "string"},
        "unidad_origen": {"type": "string", "enum": ["kg", "g", "l", "ml", "u"]},
        "unidad_destino": {"type": "string", "enum": ["kg", "g", "l", "ml", "u"]},
    }, "required": ["articulo_id", "valor", "unidad_origen", "unidad_destino"],
    "additionalProperties": False,
}
PREVIEW_ARTICLE_FORMAT_INPUT = {
    "type": "object", "properties": {
        "articulo_id": {"type": "string"}, "valor": {"type": "string"},
        "unidad_compra": {"type": "string", "enum": ["paquete", "caja", "botella", "bolsa", "bandeja", "lata", "saco"]},
        "unidad_destino": {"type": "string", "enum": ["kg", "g", "l", "ml", "u"]},
    }, "required": ["articulo_id", "valor", "unidad_compra", "unidad_destino"],
    "additionalProperties": False,
}
CONFIRM_ARTICLE_CHANGE_INPUT = {
    "type": "object", "properties": {"preview_token": {"type": "string"}},
    "required": ["preview_token"], "additionalProperties": False,
}
PREVIEW_LOT_LOCATION_INPUT = {"type": "object", "properties": {"lote_id": {"type": "string", "pattern": "^LOTE?-[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*$"}, "location_id": {"type": "string", "minLength": 1}}, "required": ["lote_id", "location_id"], "additionalProperties": False}
CONFIRM_LOT_LOCATION_INPUT = {"type": "object", "properties": {"lote_id": {"type": "string"}, "location_id": {"type": "string"}, "preview_token": {"type": "string"}}, "required": ["lote_id", "location_id", "preview_token"], "additionalProperties": False}


def validate_arguments(schema: dict[str, Any], arguments: Any) -> tuple[bool, str]:
    if not isinstance(arguments, dict):
        return False, "arguments_must_be_object"
    properties = dict(schema.get("properties") or {})
    alternatives = list(schema.get("oneOf") or [])
    if alternatives:
        matches = sum(
            all(key in arguments for key in list(dict(option).get("required") or []))
            for option in alternatives
        )
        if matches != 1:
            return False, "required_property_choice_invalid"
    missing = [key for key in list(schema.get("required") or []) if key not in arguments]
    if missing:
        return False, f"required_property_missing:{missing[0]}"
    extra = sorted(set(arguments) - set(properties))
    if extra:
        return False, "additional_properties_not_allowed"
    for key, value in arguments.items():
        rule = dict(properties.get(key) or {})
        expected = rule.get("type")
        if expected == "string" and not isinstance(value, str):
            return False, f"invalid_type:{key}"
        if expected == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
            return False, f"invalid_type:{key}"
        if expected == "array":
            if not isinstance(value, list):
                return False, f"invalid_type:{key}"
            if len(value) < int(rule.get("minItems", 0)) or len(value) > int(rule.get("maxItems", len(value))):
                return False, f"out_of_range:{key}"
            item_rule = dict(rule.get("items") or {})
            if item_rule.get("type") == "string" and any(not isinstance(item, str) or len(item.strip()) < int(item_rule.get("minLength", 0)) for item in value):
                return False, f"invalid_type:{key}"
        if "enum" in rule and value not in rule["enum"]:
            return False, f"invalid_enum:{key}"
        if expected == "string" and rule.get("pattern"):
            import re
            if re.fullmatch(str(rule["pattern"]), value) is None:
                return False, f"invalid_pattern:{key}"
        if expected == "integer" and (value < int(rule.get("minimum", value)) or value > int(rule.get("maximum", value))):
            return False, f"out_of_range:{key}"
    return True, ""


__all__ = [
    "PRODUCTION_INPUT", "EVENTS_INPUT", "RESERVATIONS_INPUT", "STOCK_INPUT", "PURCHASES_INPUT", "ESCANDALLOS_INPUT", "USO_ELABORACION_INPUT", "MENU_INPUT", "OPERATIONAL_NEEDS_INPUT",
    "ARTICLE_SEARCH_INPUT", "ARTICLE_DETAIL_INPUT", "OPEN_ELABORATION_INPUT", "OPEN_ARTICLE_INPUT", "OPEN_MENU_INPUT",
    "OPEN_PRODUCTION_INPUT", "OPEN_PURCHASE_INPUT", "OPEN_EVENTS_INPUT", "OPEN_RESERVATIONS_INPUT", "OPEN_RESERVATION_INPUT",
    "CREATE_RESERVATION_INPUT", "UPDATE_RESERVATION_INPUT", "TRANSITION_RESERVATION_INPUT", "APPLY_RESERVATION_INPUT",
    "PREVIEW_ARTICLE_PRICE_INPUT", "PREVIEW_ARTICLE_CONVERSION_INPUT", "PREVIEW_ARTICLE_FORMAT_INPUT", "CONFIRM_ARTICLE_CHANGE_INPUT", "PREVIEW_LOT_LOCATION_INPUT", "CONFIRM_LOT_LOCATION_INPUT",
    "validate_arguments",
]
