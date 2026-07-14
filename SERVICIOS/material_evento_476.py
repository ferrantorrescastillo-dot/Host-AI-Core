# Host AI 4.7.6 - Material inteligente para eventos

from math import ceil


MATERIAL_BASE = {
    "platos_llanos": 1.15,
    "platos_postre": 1.10,
    "cubiertos_completos": 1.15,
    "copas": 1.25,
    "vasos_agua": 1.20,
    "servilletas": 1.35,
    "sillas": 1.05,
}

MATERIAL_COCINA = {
    "cubetas_gn": 0.08,
    "cajas_isotermicas": 0.025,
    "mesas_trabajo": 0.01,
    "quemadores_paella": 0.006,
}


def calcular_material_evento(evento, menu=None, tipo_evento=None):
    personas = int(evento.get("personas") or 0)
    if personas <= 0:
        return {"ok": False, "error": "El evento no tiene personas", "material": {}}
    tipo = str(tipo_evento or evento.get("tipo") or "catering").lower()
    material = {nombre: ceil(personas * ratio) for nombre, ratio in MATERIAL_BASE.items()}
    material.update({nombre: max(1, ceil(personas * ratio)) for nombre, ratio in MATERIAL_COCINA.items()})

    platos = []
    if menu:
        platos = menu.get("platos", []) or menu.get("items", []) or []
    texto_menu = " ".join(str(p).lower() for p in platos)
    if "paella" in texto_menu or "arroz" in texto_menu or "paella" in tipo:
        material["paelleras"] = max(1, ceil(personas / 35))
        material["palas_paella"] = material["paelleras"]
    if "bbq" in tipo or "barbacoa" in texto_menu or "brasa" in texto_menu:
        material["parrillas"] = max(1, ceil(personas / 60))
        material["pinzas_brasa"] = material["parrillas"] * 2
    if "boda" in tipo or "banquete" in tipo:
        material["mesas_comensales"] = ceil(personas / 10)
        material["manteles"] = material["mesas_comensales"] + 2

    return {"ok": True, "id_evento": evento.get("id_evento"), "personas": personas, "tipo": tipo, "material": material}


def comparar_material_disponible(necesario, disponible):
    faltantes = []
    sobrantes = []
    for item, cantidad in necesario.get("material", {}).items():
        disp = int(disponible.get(item, 0))
        if disp < cantidad:
            faltantes.append({"item": item, "necesario": cantidad, "disponible": disp, "faltan": cantidad - disp})
        elif disp > cantidad:
            sobrantes.append({"item": item, "necesario": cantidad, "disponible": disp, "sobran": disp - cantidad})
    return {"ok": len(faltantes) == 0, "faltantes": faltantes, "sobrantes": sobrantes}


def resumen_material_evento(plan):
    if not plan.get("ok"):
        return "No se pudo calcular material."
    lineas = ["MATERIAL EVENTO", f"Personas: {plan.get('personas')}"]
    for item, cantidad in sorted(plan.get("material", {}).items()):
        lineas.append(f"- {item}: {cantidad}")
    return "\n".join(lineas)
