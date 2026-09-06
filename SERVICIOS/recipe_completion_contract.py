from __future__ import annotations

"""Contrato público y versionado del completado masivo de recetas.

Este módulo es deliberadamente puro: no conoce repositorios, HTTP ni XLSX. Tanto
la validación de dominio como la exportación física derivan sus reglas de aquí.
"""

from copy import deepcopy
from typing import Any


CONTRACT_FORMAT = "HOSTAI_RECIPE_COMPLETION_PACKAGE"
CONTRACT_VERSION = "0.3"
SUPPORTED_CONTRACT_VERSIONS = frozenset({"0.1", "0.2", "0.3"})

RECIPE_OPERATIONAL_UNITS = frozenset({
    "kg", "g", "l", "ml", "cl", "u", "raciones", "porciones", "servicios",
    "bandejas", "cubetas", "ollas", "lotes",
})
RECIPE_INGREDIENT_UNITS = frozenset({"kg", "g", "l", "ml", "cl", "u"})


def _field(
    label: str,
    value_type: str,
    what: str,
    why: str,
    how: str,
    example: Any,
    *,
    enum: tuple[Any, ...] = (),
    units: frozenset[str] = frozenset(),
    shape: Any = None,
    no_aplica: bool = False,
    no_aplica_when: str = "",
    policy: str = "REVISION_INDIVIDUAL",
    readiness: str = "NO",
    validations: str = "No usar comodines; dejar vacío únicamente cuando no exista una estimación responsable.",
    relations: str = "",
) -> dict[str, Any]:
    return {
        "label": label,
        "type": value_type,
        "what": what,
        "why": why,
        "how": how,
        "enum": tuple(enum),
        "units": tuple(sorted(units)),
        "shape": deepcopy(shape),
        "validations": validations,
        "example": deepcopy(example),
        "allows_no_aplica": no_aplica,
        "no_aplica_when": no_aplica_when,
        "policy": policy,
        "safe": policy == "SELECCION_MASIVA",
        "critical": policy != "SELECCION_MASIVA",
        "readiness": readiness,
        "relations": relations,
    }


FIELD_CONTRACTS: dict[str, dict[str, Any]] = {
    "categoria": _field(
        "Categoría", "string", "Clasificación culinaria funcional de la receta.",
        "Permite organizar, buscar y agrupar producción y biblioteca.",
        "Inferir una categoría específica desde nombre, ingredientes y uso; no sustituir una categoría existente.",
        "ENTRANTE_FRIO", readiness="ALWAYS",
    ),
    "tipo_elaboracion": _field(
        "Tipo de elaboración", "enum", "Naturaleza operativa general de la preparación.",
        "Distingue elaboraciones, bebidas y salsas para aplicar flujos operativos adecuados.",
        "Elegir el valor cerrado que describa mejor el resultado final.", "ELABORACION",
        enum=("ELABORACION", "BEBIDA", "SALSA"), readiness="ALWAYS",
    ),
    "descripcion": _field(
        "Descripción", "string", "Resumen culinario específico de la receta.",
        "Facilita identificación, revisión y uso de la ficha técnica.",
        "Redactar una frase concreta a partir del nombre, ingredientes y contexto, sin afirmaciones sanitarias no fundadas.",
        "Crema fría de hortalizas para servicio.", policy="SELECCION_MASIVA",
    ),
    "elaboracion": _field(
        "Elaboración paso a paso", "string", "Procedimiento operativo de preparación.",
        "Convierte la receta en instrucciones ejecutables para cocina.",
        "Proponer una secuencia específica y coherente con ingredientes, tiempos y resultado.",
        "Triturar los ingredientes, ajustar textura y enfriar.", policy="SELECCION_MASIVA",
    ),
    "observaciones": _field(
        "Observaciones", "string", "Notas prácticas no cubiertas por otros campos.",
        "Conserva controles de calidad y particularidades de servicio.",
        "Añadir únicamente una nota específica y útil; no repetir el resto de la ficha.",
        "Revisar sazón y textura antes del servicio.", policy="SELECCION_MASIVA",
    ),
    "ingredientes_estructurados": _field(
        "Ingredientes estructurados", "json", "Ingredientes con identidad documental, cantidad, unidad y normalización.",
        "Alimenta stock, compras, producción y coste sin perder trazabilidad documental.",
        "Conservar cada ingrediente original por nombre/line_id; completar cantidades y añadir extras razonables solo como CANDIDATO_NUEVO.",
        [{"line_id": "LINEA-1", "nombre_original": "Tomate", "name_raw": "Tomate", "cantidad": 1, "unidad": "kg", "cantidad_normalizada": 1, "unidad_normalizada": "kg", "estado_relacion": "DOCUMENTAL", "dato_provisional": True, "procedencia_propuesta": {"origen": "IA_PROPUESTA", "confianza": 0.75, "motivo": "Estimación culinaria provisional"}}],
        units=RECIPE_INGREDIENT_UNITS,
        shape=[{"line_id": "string_unico", "nombre_original": "string_sin_cambiar", "name_raw": "string", "cantidad": "number>0", "unidad": "kg|g|l|ml|cl|u", "cantidad_normalizada": "number>0", "unidad_normalizada": "kg|l|u", "estado_relacion": "DOCUMENTAL|CANDIDATO_NUEVO", "dato_provisional": True, "procedencia_propuesta": {"origen": "IA_PROPUESTA", "confianza": "0..1", "motivo": "string"}}],
        readiness="ALWAYS",
        validations="Preservar nombres y line_id documentales; line_id únicos; sin article_id/articulo_id nuevos o modificados; candidatos no duplicados.",
        relations="Las cantidades y unidades deben corresponder al mismo ingrediente y ser compatibles con su normalización.",
    ),
    "rendimiento": _field(
        "Rendimiento", "number", "Cantidad total producida por la receta o lote.",
        "Convierte demanda en cantidad a producir y permite calcular costes unitarios.",
        "Inferir una cantidad prudente desde raciones, contexto de servicio y volumen de ingredientes.", 10,
        readiness="ALWAYS", validations="Número finito mayor que cero.",
        relations="Si unidad_rendimiento es raciones/porciones debe coincidir con numero_raciones.",
    ),
    "unidad_rendimiento": _field(
        "Unidad de rendimiento", "enum", "Unidad física o de servicio del rendimiento total.",
        "Da significado al rendimiento y conecta producción con demanda.",
        "Elegir exclusivamente una unidad publicada y coherente con el resultado final.", "raciones",
        units=RECIPE_OPERATIONAL_UNITS, readiness="ALWAYS",
        validations="Unidad cerrada; debe acompañar a rendimiento.", relations="Debe ser compatible con rendimiento y cantidad_por_racion.",
    ),
    "numero_raciones": _field(
        "Número de raciones", "number", "Número de servicios estándar que produce la receta.",
        "Conecta clientes/pax con producción y coste por ración.",
        "Estimar desde el contexto de servicio o desde rendimiento y tamaño de porción.", 10,
        readiness="ALWAYS", validations="Número finito mayor que cero.",
        relations="Debe coincidir con rendimiento cuando este se expresa en raciones/porciones.",
    ),
    "cantidad_por_racion": _field(
        "Cantidad por ración", "json", "Cantidad física servida por persona.",
        "Convierte raciones en gramos, litros o unidades necesarias.",
        "Estimar una porción culinaria prudente según categoría y servicio.",
        {"cantidad": 250, "unidad": "g"}, units=RECIPE_OPERATIONAL_UNITS,
        shape={"cantidad": "number>0", "unidad": "unidad_operativa"}, readiness="ALWAYS",
        validations="Objeto JSON con cantidad finita positiva y unidad admitida.",
        relations="cantidad × numero_raciones debe coincidir con rendimiento cuando las unidades sean comparables.",
    ),
    "rendimiento_neto": _field(
        "Rendimiento neto", "number", "Cantidad aprovechable tras pérdidas del proceso.",
        "Representa producto realmente disponible y mejora producción y coste.",
        "Estimar desde rendimiento y merma; reducir confianza si faltan mediciones.", 9.2,
        no_aplica=True, no_aplica_when="Solo si el concepto de rendimiento neto no aporta significado al tipo de receta.",
        validations="Número finito mayor que cero o NO_APLICA justificado.",
    ),
    "merma": _field(
        "Merma", "percentage", "Fracción de pérdida entre materia prima y producto útil.",
        "Ajusta compra, cantidad necesaria y rendimiento neto.",
        "Estimar prudentemente por técnica e ingrediente; usar decimal entre 0 y 1.", 0.08,
        no_aplica=True, no_aplica_when="Solo cuando no existe transformación o pérdida material relevante.",
        validations="Número finito entre 0 incluido y 1 excluido.",
    ),
    "produccion_maxima": _field(
        "Producción máxima por tanda", "number", "Capacidad máxima razonable de una tanda.",
        "Permite convertir cantidad requerida en número de tandas.",
        "Inferir un límite prudente para equipo profesional estándar; marcar imposible si depende de un equipo desconocido crítico.", 20,
        readiness="ALWAYS", validations="Número finito mayor que cero.", relations="No puede ser menor que rendimiento_por_tanda.",
    ),
    "rendimiento_por_tanda": _field(
        "Rendimiento por tanda", "number", "Cantidad obtenida en una ejecución del proceso.",
        "Permite calcular cuántas tandas necesita la producción.",
        "Estimar desde rendimiento y capacidad típica del proceso.", 10,
        readiness="ALWAYS", validations="Número finito mayor que cero.", relations="No puede superar produccion_maxima.",
    ),
    "unidad_tanda": _field(
        "Unidad de tanda", "enum", "Unidad en que se mide la capacidad de tanda.",
        "Da significado a producción máxima y rendimiento por tanda.",
        "Usar la misma dimensión operativa que rendimiento_por_tanda.", "raciones",
        units=RECIPE_OPERATIONAL_UNITS, readiness="ALWAYS",
        validations="Unidad cerrada; debe acompañar a rendimiento_por_tanda.",
    ),
    "limitacion_tanda": _field(
        "Limitación de tanda", "string", "Factor que limita el tamaño de cada tanda.",
        "Explica la capacidad y permite adaptar la planificación al equipo real.",
        "Identificar el recurso o fase limitante más probable; reducir confianza si el equipo real es desconocido.",
        "Capacidad útil del recipiente", no_aplica=True,
        no_aplica_when="Solo si el proceso no tiene una ejecución por tandas significativa.",
    ),
    "cuello_botella": _field(
        "Cuello de botella", "string", "Fase o recurso que condiciona el ritmo de producción.",
        "Permitirá optimizar secuencia, paralelismo y capacidad.",
        "Inferir la operación más lenta o el equipo compartido más limitante.", "Capacidad de triturado",
        no_aplica=True, no_aplica_when="Solo si no existe una fase o recurso limitante diferenciable.",
    ),
    "estacion_zona": _field(
        "Estación o zona", "string", "Partida o zona principal que ejecuta la receta.",
        "Distribuye trabajo y recursos entre partidas.",
        "Inferir desde técnica, temperatura y tipo de preparación.", "Cocina fría",
        no_aplica=True, no_aplica_when="Solo si el establecimiento no necesita asignación por zona para este proceso.",
    ),
    "personal_recomendado": _field(
        "Personal recomendado", "json", "Número de personas y rol principal para una tanda.",
        "Dimensiona carga laboral y coordinación de producción.",
        "Estimar para una tanda estándar según complejidad y trabajo simultáneo.",
        {"personas": 1, "rol": "cocinero"},
        shape={"personas": "number>0", "rol": "string"}, readiness="ALWAYS",
        validations="Objeto JSON con personas positivas y rol concreto.",
    ),
    "recursos_necesarios": _field(
        "Recursos necesarios", "json", "Equipos y utensilios principales requeridos.",
        "Detecta conflictos de equipo y permite planificar capacidad.",
        "Enumerar solo recursos relevantes para el proceso descrito.", ["olla", "batidora"],
        shape=["string"], readiness="ALWAYS", validations="Array JSON no vacío de nombres concretos.",
    ),
    "intervencion_activa": _field(
        "Intervención activa estimada", "boolean", "Indica si el proceso requiere trabajo humano activo relevante.",
        "Separa carga laboral de esperas y permite solapar tareas.",
        "Usar true si existe manipulación activa; false únicamente si el proceso es esencialmente autónomo.", True,
        enum=(True, False), no_aplica=True,
        no_aplica_when="Solo si la noción de intervención activa no es aplicable al registro.",
        validations="Booleano real, nunca texto ambiguo.", relations="false o NO_APLICA contradice tiempo_activo positivo.",
    ),
    "tiempo_preparacion": _field(
        "Tiempo de preparación", "duration", "Tiempo previo de mise en place de una tanda.",
        "Reserva trabajo previo y mejora el calendario.",
        "Estimar para una tanda estándar desde ingredientes y técnica.", "20 minutos",
        validations="Duración positiva completa con número y unidad.",
    ),
    "tiempo_activo": _field(
        "Tiempo activo", "duration", "Minutos de trabajo humano directo.",
        "Calcula carga laboral y necesidades de personal.",
        "Sumar las fases que requieren intervención efectiva.", "25 minutos",
        readiness="ALWAYS", validations="Duración positiva completa.", relations="No puede superar tiempo_total; requiere intervencion_activa coherente.",
    ),
    "tiempo_pasivo": _field(
        "Tiempo pasivo", "duration", "Tiempo de espera sin dedicación humana continua.",
        "Permite solapar procesos y construir un calendario realista.",
        "Sumar reposos, cocciones autónomas y enfriamientos sin trabajo continuo.", "60 minutos",
        no_aplica=True, no_aplica_when="Cuando no existe ninguna espera o fase autónoma.", readiness="ALWAYS",
        validations="Duración positiva completa o NO_APLICA justificado.", relations="No puede superar tiempo_total.",
    ),
    "tiempo_coccion": _field(
        "Tiempo de cocción o proceso", "duration", "Duración de cocción o transformación principal.",
        "Ayuda a secuenciar equipo, energía y servicio.",
        "Estimar según técnica y tamaño de tanda.", "30 minutos",
        no_aplica=True, no_aplica_when="Preparación sin cocción ni proceso temporal equivalente.",
    ),
    "tiempo_reposo": _field(
        "Tiempo de reposo", "duration", "Espera necesaria para estabilizar o desarrollar la preparación.",
        "Afecta el inicio mínimo y el solapamiento del plan.",
        "Estimar cuando la técnica requiera reposo, marinado, levado o asentamiento.", "60 minutos",
        no_aplica=True, no_aplica_when="La receta no requiere reposo, marinado, levado ni asentamiento.",
    ),
    "tiempo_enfriamiento": _field(
        "Tiempo de enfriamiento", "duration", "Tiempo necesario para alcanzar condición de conservación o servicio frío.",
        "Condiciona seguridad, cámara y momento de servicio.",
        "Estimar prudentemente según volumen y proceso; no afirmar parámetros sanitarios confirmados.", "60 minutos",
        no_aplica=True, no_aplica_when="No se enfría ni se sirve/conserva en frío.",
    ),
    "tiempo_descongelacion": _field(
        "Tiempo de descongelación", "duration", "Tiempo previsto para descongelar antes del uso.",
        "Permite anticipar producción y servicio.",
        "Estimar solo cuando la receta se congela; si no se congela usar NO_APLICA.", "12 horas",
        no_aplica=True, no_aplica_when="Obligatorio cuando puede_congelarse=false.",
        validations="Duración positiva o NO_APLICA justificado.", relations="Si puede_congelarse=true necesita una duración; si false debe ser NO_APLICA.",
    ),
    "tiempo_total": _field(
        "Tiempo total", "duration", "Tiempo transcurrido desde inicio hasta disponibilidad.",
        "Determina el calendario completo de producción.",
        "Calcular coherentemente desde fases activas y pasivas, considerando solapes reales.", "90 minutos",
        readiness="ALWAYS", validations="Duración positiva completa.", relations="Debe ser >= tiempo_activo y >= tiempo_pasivo cuando aplique.",
    ),
    "puede_refrigerarse": _field(
        "Puede refrigerarse", "boolean", "Indica si admite conservación refrigerada.",
        "Permite anticipar producción y organizar cámara.",
        "Proponer prudentemente según tipo, ingredientes y práctica culinaria; requiere revisión sanitaria.", True,
        enum=(True, False), readiness="ALWAYS", validations="Booleano real.", relations="true exige vida_util_refrigerado válida; false exige NO_APLICA.",
    ),
    "vida_util_refrigerado": _field(
        "Vida útil refrigerada", "duration", "Duración orientativa de conservación refrigerada.",
        "Ayuda a anticipar producción, rotación y servicio.",
        "Estimar de forma conservadora y marcar siempre como propuesta sanitaria pendiente de revisión.", "24 horas",
        no_aplica=True, no_aplica_when="Obligatorio cuando puede_refrigerarse=false.", readiness="IF_REFRIGERATED",
        validations="Duración positiva o NO_APLICA justificado.", relations="Debe concordar con puede_refrigerarse.",
    ),
    "puede_congelarse": _field(
        "Puede congelarse", "boolean", "Indica si admite conservación congelada.",
        "Permite anticipar producción y gestionar capacidad de congelación.",
        "Proponer prudentemente según estabilidad y calidad esperable; requiere revisión sanitaria.", False,
        enum=(True, False), readiness="ALWAYS", validations="Booleano real.", relations="Controla vida_util_congelado y tiempo_descongelacion.",
    ),
    "vida_util_congelado": _field(
        "Vida útil congelada", "duration", "Duración orientativa de conservación congelada.",
        "Planifica producción anticipada y rotación de congelados.",
        "Estimar conservadoramente solo si puede congelarse; nunca presentar como dato sanitario confirmado.", "30 días",
        no_aplica=True, no_aplica_when="Obligatorio cuando puede_congelarse=false.", readiness="IF_FROZEN",
        validations="Duración positiva o NO_APLICA justificado.", relations="Debe concordar con puede_congelarse.",
    ),
    "conservacion": _field(
        "Conservación", "string", "Condiciones operativas de conservación y etiquetado.",
        "Vincula producción anticipada con almacenamiento y servicio.",
        "Describir condiciones prudentes sin inventar límites sanitarios confirmados.",
        "Conservar refrigerado en recipiente cerrado y etiquetado.", readiness="ALWAYS",
    ),
    "regeneracion": _field(
        "Regeneración", "string", "Método para llevar la preparación conservada a condición de servicio.",
        "Permite planificar servicio, equipo y tiempos posteriores.",
        "Proponer un método coherente si se sirve regenerada; usar NO_APLICA para consumo frío o directo.",
        "Calentar suavemente antes del servicio.", no_aplica=True,
        no_aplica_when="Preparación consumida fría, a temperatura ambiente o sin regeneración posterior.", readiness="ALWAYS",
    ),
    "alergenos": _field(
        "Alérgenos", "json", "Alérgenos con fundamento explícito en ingredientes o contexto.",
        "Facilita revisión sanitaria, pero nunca sustituye la validación humana.",
        "Proponer solo una lista no vacía cuando ingredientes/contexto aporten evidencia; incluir motivo y fuente.",
        ["gluten"], shape=["string"], validations="Array JSON no vacío; motivo y fuente obligatorios; nunca inferencia genérica.",
    ),
}


RECIPE_DOCUMENTATION_FIELDS = frozenset(FIELD_CONTRACTS)
BATCH_GROUP_REVIEW_FIELDS = frozenset({
    "categoria", "tipo_elaboracion", "rendimiento", "unidad_rendimiento",
    "numero_raciones", "cantidad_por_racion", "rendimiento_neto", "merma",
    "produccion_maxima", "rendimiento_por_tanda", "unidad_tanda",
    "limitacion_tanda", "cuello_botella", "estacion_zona",
    "personal_recomendado", "recursos_necesarios", "intervencion_activa",
    "tiempo_preparacion", "tiempo_activo", "tiempo_pasivo",
    "tiempo_coccion", "tiempo_reposo", "tiempo_total",
})
for _field_name in BATCH_GROUP_REVIEW_FIELDS:
    FIELD_CONTRACTS[_field_name]["policy"] = "REVISION_AGRUPADA_PROVISIONAL"
BATCH_MASS_SAFE_FIELDS = frozenset(
    key for key, spec in FIELD_CONTRACTS.items() if spec["safe"]
)
BATCH_INDIVIDUAL_REVIEW_FIELDS = (
    RECIPE_DOCUMENTATION_FIELDS - BATCH_MASS_SAFE_FIELDS - BATCH_GROUP_REVIEW_FIELDS
)
NO_APLICA_FIELDS = frozenset(
    key for key, spec in FIELD_CONTRACTS.items() if spec["allows_no_aplica"]
)
RECIPE_BOOLEAN_FIELDS = frozenset(
    key for key, spec in FIELD_CONTRACTS.items() if spec["type"] == "boolean"
)
RECIPE_NUMBER_FIELDS = frozenset(
    key for key, spec in FIELD_CONTRACTS.items() if spec["type"] in {"number", "percentage"}
)
RECIPE_TIME_FIELDS = frozenset(
    key for key, spec in FIELD_CONTRACTS.items() if spec["type"] == "duration"
)
RECIPE_JSON_FIELDS = frozenset(
    key for key, spec in FIELD_CONTRACTS.items() if spec["type"] == "json" and key != "alergenos"
)
RECIPE_ENUM_FIELDS = {
    key: tuple(spec["enum"]) for key, spec in FIELD_CONTRACTS.items()
    if spec["type"] == "enum" and spec["enum"]
}
RECIPE_UNIT_FIELDS = frozenset(
    key for key, spec in FIELD_CONTRACTS.items() if spec["units"] and key != "ingredientes_estructurados"
    and key != "cantidad_por_racion"
)
PRODUCTION_READINESS_BASE_FIELDS = frozenset(
    key for key, spec in FIELD_CONTRACTS.items() if spec["readiness"] == "ALWAYS"
)
PRODUCTION_READINESS_CONDITIONAL_FIELDS = {
    "puede_refrigerarse": {True: ("vida_util_refrigerado",)},
    "puede_congelarse": {True: ("vida_util_congelado", "tiempo_descongelacion")},
}


PRICE_REFERENCE_COLUMNS = (
    "article_key", "article_id", "nombre_canonico", "unidad_base", "recetas_json",
    "producto_encontrado", "comercio_fuente", "marca", "precio_observado", "moneda",
    "formato_envase", "cantidad_envase", "unidad_envase", "precio_normalizado",
    "unidad_precio_normalizado", "url_fuente", "fecha_consulta", "observacion_equivalencia",
    "confianza", "price_basis", "procedencia", "estado_referencia",
)
PRICE_BASIS_VALUES = ("IVA_INCLUIDO", "IVA_EXCLUIDO", "DESCONOCIDO")
PRICE_NORMALIZED_UNITS = ("kg", "l", "u")

PRICE_FIELD_CONTRACTS = {
    "article_key": ("Identidad consolidada publicada por Host AI; no modificar.", "string", True),
    "article_id": ("ID canónico protegido; vacío para candidatos todavía no autorizados.", "string", False),
    "nombre_canonico": ("Nombre de búsqueda consolidado; no sustituye la identidad canónica.", "string", True),
    "unidad_base": ("Familia de unidad esperada para normalizar el precio.", "enum: kg|l|u", False),
    "recetas_json": ("Recetas que reutilizan esta única búsqueda consolidada.", "json[array<string>]", True),
    "producto_encontrado": ("Producto comercial comparable observado en la fuente.", "string", False),
    "comercio_fuente": ("Comercio, supermercado o distribuidor que publica la referencia.", "string", False),
    "marca": ("Marca observada cuando afecte a la comparabilidad.", "string", False),
    "precio_observado": ("Precio visible del envase o formato consultado.", "number>0", False),
    "moneda": ("Moneda ISO del precio observado; usar EUR cuando corresponda.", "string", False),
    "formato_envase": ("Descripción humana del formato comercial observado.", "string", False),
    "cantidad_envase": ("Cantidad numérica positiva contenida en el formato.", "number>0", False),
    "unidad_envase": ("Unidad del formato: g, kg, ml, l o u.", "enum: g|kg|ml|l|u", False),
    "precio_normalizado": ("Precio calculado por kg, l o unidad.", "number>0", False),
    "unidad_precio_normalizado": ("Unidad base del precio normalizado.", "enum: kg|l|u", False),
    "url_fuente": ("URL HTTP(S) directa y trazable de la observación.", "url", False),
    "fecha_consulta": ("Fecha ISO de consulta de la referencia.", "date: YYYY-MM-DD", False),
    "observacion_equivalencia": ("Razón por la que el producto es comparable o limitaciones de equivalencia.", "string", False),
    "confianza": ("Confianza prudente en la correspondencia entre 0 y 1.", "number[0,1]", False),
    "price_basis": ("Tratamiento del IVA conocido para esta referencia.", "enum: IVA_INCLUIDO|IVA_EXCLUIDO|DESCONOCIDO", False),
    "procedencia": ("Autoridad obligatoria; siempre REFERENCIA_EXTERNA.", "const: REFERENCIA_EXTERNA", True),
    "estado_referencia": ("REFERENCIA_PROPUESTA si se completó con fuente; PRECIO_REFERENCIA_PENDIENTE si no.", "enum: REFERENCIA_PROPUESTA|PRECIO_REFERENCIA_PENDIENTE", False),
}


WORKBOOK_INSTRUCTIONS = (
    ("LOTE_COMPLETO", "Procesa TODAS las recetas del libro antes de terminar; no solicites confirmación receta por receta."),
    ("IDENTIDAD", "No modifiques recipe_id, recipe_fingerprint, import_id, article_id ni valores protegidos."),
    ("SOLO_PENDIENTES", "Rellena *_propuesto únicamente cuando la clave aparezca en campos_pendientes_claves; los valores REAL/DOCUMENTO/CONFIRMADO/CALCULADO fiables están protegidos."),
    ("TRAZABILIDAD", "Cada propuesta usa metadatos_propuestas con origen=IA_PROPUESTA, confianza 0..1, motivo, fuente/contexto, modelo y estado_revision=REQUIERE_REVISION_HUMANA."),
    ("EJEMPLO_METADATOS", '{"regeneracion":{"origen":"IA_PROPUESTA","estado_campo":"NO_APLICA","confianza":0.85,"motivo":"Se sirve fría","fuente":"Nombre, ingredientes y contexto del XLSX","modelo":"modelo usado"},"tiempo_total":{"origen":"IA_PROPUESTA","confianza":0.7,"motivo":"Estimación operativa","fuente":"Contexto del XLSX","modelo":"modelo usado"}}'),
    ("NO_APLICA", "Usa el objeto estructurado de SCHEMA solo cuando el concepto genuinamente no aplique; motivo y procedencia son obligatorios."),
    ("IMPOSIBLE", "Si realmente no puede estimarse, escribe PENDIENTE_IMPOSIBLE_DE_ESTIMAR: seguido de una razón concreta; no lo uses para evitar una estimación razonable."),
    ("INGREDIENTES", "Preserva todos los ingredientes documentales por nombre/line_id, completa cantidades/unidades y añade extras solo como CANDIDATO_NUEVO sin article_id."),
    ("ALERGENOS", "Propón alérgenos solo con fundamento explícito y fuente; nunca rellenes con una lista genérica o vacía."),
    ("COHERENCIA", "Respeta las relaciones y validaciones de SCHEMA: tiempos, conservación, congelación, rendimiento, raciones y tandas deben ser objetivamente compatibles."),
    ("CONTEXTO", "Usa menús, servicio/pax, artículos, formatos, conversiones y recetas relacionadas como evidencia, nunca como permiso para sustituir valores protegidos."),
    ("SIN_COMODINES", "No uses 'Texto culinario provisional', 'Sin dato', 'Por determinar' ni una plantilla idéntica para recetas distintas."),
    ("PRECIOS", "Consolida primero ARTICULOS_PENDIENTES. Si tienes web, completa una referencia trazable por identidad en PRECIOS_REFERENCIA; reutiliza la misma referencia para todas las recetas con nombre exacto y unidad compatible."),
    ("PRECIOS_CANDIDATOS_NUEVOS", "Si añades un CANDIDATO_NUEVO no publicado, puedes añadir una fila a PRECIOS_REFERENCIA con article_key=CANDIDATO_NUEVO|nombre normalizado sin tildes|kg,l,u. No añadas article_id ni lo presentes como artículo real."),
    ("SIN_ESCRITURA", "El libro solo devuelve propuestas. Host AI validará, mostrará preview y exigirá confirmación humana antes de cualquier WRITE."),
    ("SEGURIDAD", "No añadas fórmulas, macros, enlaces internos ni columnas de propuesta desconocidas."),
)


def master_ai_prompt() -> str:
    fields = ", ".join(FIELD_CONTRACTS)
    return f"""PROMPT MAESTRO HOST AI — COMPLETADO MASIVO DE RECETAS

MISIÓN
Procesa TODAS las recetas incluidas en este libro. No solicites confirmación receta por receta, no completes una sola receta y te detengas. Devuelve el mismo XLSX con todo el lote trabajado.

OBJETIVO OPERATIVO
Host AI necesita convertir DEMANDA → RACIONES → RENDIMIENTO → CANTIDAD A PRODUCIR → TANDAS → INGREDIENTES → STOCK → COMPRAS → TIEMPOS → PERSONAL → EQUIPOS → PLAN DE PRODUCCIÓN → COSTES. Intenta completar todos los campos razonablemente inferibles usando nombre, documentación, ingredientes, cantidades, unidades, artículos, conversiones, menús, servicio/pax, valores existentes y conocimiento culinario general prudente.

REGLA PRINCIPAL
VACÍO ES EL ÚLTIMO RECURSO. Si puedes estimar responsablemente, propón. Una estimación nunca es REAL ni CONFIRMADA: usa IA_PROPUESTA con confianza, motivo, fuente/contexto, modelo y revisión humana. Si un concepto no aplica, usa exactamente el NO_APLICA estructurado de SCHEMA. Si es verdaderamente imposible, usa PENDIENTE_IMPOSIBLE_DE_ESTIMAR con razón concreta.

PROTECCIONES
No alteres IDs, fingerprints ni datos existentes protegidos. No inventes precio real, proveedor real, compra, stock, dato sanitario confirmado ni alérgeno sin fundamento. No borres ingredientes documentales. Los nuevos ingredientes son CANDIDATO_NUEVO y no crean artículos.

RECETAS
Completa exclusivamente columnas *_propuesto para claves incluidas en campos_pendientes_claves. Consulta SCHEMA para qué significa cada campo, por qué se necesita, cómo estimarlo, tipo, unidades, shape, validaciones, coherencias, política y ejemplos. Campos canónicos del lote: {fields}.

PRECIOS ORIENTATIVOS
Consolida ARTICULOS_PENDIENTES y trabaja una vez por identidad exacta, reutilizando la referencia para todas sus recetas. Si dispones de búsqueda web, intenta hallar referencias actuales y trazables en España (por ejemplo Makro, Caprabo, Carrefour, Alcampo o distribuidores horeca comparables). Completa PRECIOS_REFERENCIA con producto, comercio, formato, precio observado, precio normalizado, URL, fecha, confianza y price_basis. procedencia siempre es REFERENCIA_EXTERNA. Para un CANDIDATO_NUEVO creado en ingredientes_estructurados puedes añadir una fila con article_key=CANDIDATO_NUEVO|nombre normalizado sin tildes|kg,l,u, sin article_id. Si no tienes web o no hay fuente fiable, deja estado_referencia=PRECIO_REFERENCIA_PENDIENTE; no inventes.

ENTREGA
Conserva las hojas y columnas. No uses fórmulas. Procesa todas las recetas y referencias consolidadas antes de devolver el libro. Host AI validará después cada valor; proponer, seleccionar, previsualizar, confirmar y escribir son pasos distintos.
"""


ERROR_MESSAGES = {
    "missing_no_aplica_reason": "NO_APLICA necesita motivo/evidencia en sus metadatos o en el objeto estructurado.",
    "ingredient_count_mismatch": "Conserve todos los ingredientes documentales y añada los nuevos al final como CANDIDATO_NUEVO.",
    "ingredient_original_missing": "Falta al menos un ingrediente documental; conserve su nombre_original sin cambios.",
    "ingredient_identity_changed": "El nombre de un ingrediente documental no se puede cambiar.",
    "ingredient_line_id_changed": "Conserve el line_id documental original de cada ingrediente.",
    "duplicate_ingredient_line_id": "Cada ingrediente necesita un line_id único dentro de la receta.",
    "ingredient_article_link_unauthorized": "No incluya ni cambie article_id/articulo_id; el alta y enlace requiere autorización en Host AI.",
    "invalid_new_ingredient_candidate": "Un ingrediente nuevo necesita nombre, cantidad y unidad; quedará como CANDIDATO_NUEVO.",
    "duplicate_ingredient_candidate": "El candidato duplica otro ingrediente; conserve una única línea por identidad normalizada.",
    "EXISTING_VALUE": "El campo ya tiene un valor; deje vacía su columna *_propuesto.",
    "EMPTY_VALUE": "Una lista u objeto vacío no constituye una propuesta; deje la celda vacía.",
    "no_aplica_no_permitido": "Este campo no admite NO_APLICA; proponga un valor o deje la celda vacía.",
    "invalid_boolean": "Use true o false para este campo booleano.",
    "invalid_number": "Use un número finito mayor que cero.",
    "invalid_percentage": "Use una merma numérica entre 0 incluido y 1 excluido.",
    "invalid_duration": "Use número y unidad temporal, por ejemplo '30 minutos'.",
    "invalid_enum": "Use uno de los valores publicados en enum_permitidos_json de SCHEMA.",
    "invalid_unit": "Use una unidad publicada en unidades_admitidas_json de SCHEMA.",
    "invalid_ingredient_unit": "Use kg, g, l, ml, cl o u; la unidad normalizada debe ser kg, l o u.",
    "invalid_structured_value": "Use JSON válido con el shape indicado en SCHEMA.",
    "invalid_structured_shape": "El JSON no cumple el shape indicado en SCHEMA.",
    "invalid_string": "Use un texto específico para este campo.",
    "empty_allergen_list": "Una lista vacía no demuestra ausencia de alérgenos; deje la celda vacía.",
    "invalid_allergen_list": "Use una lista JSON no vacía de alérgenos concretos.",
    "insufficient_allergen_provenance": "Los alérgenos necesitan motivo y fuente explícitos.",
    "placeholder_value": "El texto es un comodín y no cuenta como dato operativo.",
    "contradiction_active_intervention": "intervencion_activa=false/NO_APLICA contradice un tiempo_activo positivo.",
    "contradiction_total_below_active": "tiempo_total no puede ser menor que tiempo_activo.",
    "contradiction_total_below_passive": "tiempo_total no puede ser menor que tiempo_pasivo.",
    "contradiction_refrigerated_life": "puede_refrigerarse=false exige vida_util_refrigerado=NO_APLICA.",
    "contradiction_refrigerated_no_aplica": "puede_refrigerarse=true necesita vida útil refrigerada válida.",
    "contradiction_vida_util_congelado": "puede_congelarse=false exige vida_util_congelado=NO_APLICA.",
    "contradiction_vida_util_congelado_no_aplica": "puede_congelarse=true necesita vida útil congelada válida.",
    "contradiction_tiempo_descongelacion": "puede_congelarse=false exige tiempo_descongelacion=NO_APLICA.",
    "contradiction_tiempo_descongelacion_no_aplica": "puede_congelarse=true necesita tiempo de descongelación válido.",
    "contradiction_yield_portions": "rendimiento en raciones/porciones debe coincidir con numero_raciones.",
    "contradiction_portion_quantity_yield": "cantidad_por_racion × numero_raciones debe coincidir con rendimiento cuando sean comparables.",
    "contradiction_batch_above_maximum": "rendimiento_por_tanda no puede superar produccion_maxima.",
    "ALERGENOS_EMBEBIDOS": "La descripción afirma alérgenos; use el campo estructurado y revisión individual.",
    "ALERGENOS_TRAZAS_EMBEBIDOS": "El texto afirma trazas/presencia de alérgenos y requiere revisión individual.",
    "DATOS_COMERCIALES_EMBEBIDOS": "El texto incluye precio, proveedor, stock o lote; use el campo estructurado.",
    "CONTENIDO_CRITICO_REQUIERE_REVISION": "Hay afirmaciones críticas que requieren revisión individual.",
    "ARTICLE_KEY_DESCONOCIDA": "article_key no pertenece a ARTICULOS_PENDIENTES.",
    "REFERENCIA_DUPLICADA": "Solo se admite una referencia por article_key consolidada.",
    "ARTICLE_ID_MODIFICADO": "article_id es una identidad protegida y no puede modificarse.",
    "NOMBRE_CANONICO_MODIFICADO": "nombre_canonico identifica la búsqueda publicada y no puede modificarse.",
    "UNIDAD_BASE_MODIFICADA": "unidad_base es contexto protegido y no puede modificarse.",
    "invalid_price_reference": "Complete producto, comercio, URL y fecha para proponer una referencia.",
    "invalid_price_authority": "procedencia debe ser exactamente REFERENCIA_EXTERNA; nunca REAL o CONFIRMADO.",
    "invalid_price_reference_state": "Use REFERENCIA_PROPUESTA o deje la fila en PRECIO_REFERENCIA_PENDIENTE.",
    "invalid_price_basis": "Use IVA_INCLUIDO, IVA_EXCLUIDO o DESCONOCIDO.",
    "invalid_price_unit": "Use g, kg, ml, l o u y normalice respectivamente a kg, l o u.",
    "inconsistent_normalized_price": "precio_normalizado no coincide con precio_observado y cantidad_envase.",
    "invalid_confidence": "confianza debe ser un número finito entre 0 y 1.",
    "invalid_source": "url_fuente debe ser una URL HTTP(S) trazable.",
    "invalid_reference_date": "fecha_consulta debe usar YYYY-MM-DD.",
    "invalid_price": "Los precios y cantidades deben ser números finitos mayores que cero.",
}


def public_field_contract(field: str) -> dict[str, Any]:
    return deepcopy(FIELD_CONTRACTS[field])


__all__ = [
    "CONTRACT_FORMAT", "CONTRACT_VERSION", "SUPPORTED_CONTRACT_VERSIONS",
    "FIELD_CONTRACTS", "RECIPE_DOCUMENTATION_FIELDS", "BATCH_MASS_SAFE_FIELDS",
    "BATCH_GROUP_REVIEW_FIELDS",
    "BATCH_INDIVIDUAL_REVIEW_FIELDS", "NO_APLICA_FIELDS", "RECIPE_BOOLEAN_FIELDS",
    "RECIPE_NUMBER_FIELDS", "RECIPE_TIME_FIELDS", "RECIPE_JSON_FIELDS",
    "RECIPE_ENUM_FIELDS", "RECIPE_UNIT_FIELDS", "RECIPE_OPERATIONAL_UNITS",
    "RECIPE_INGREDIENT_UNITS", "PRODUCTION_READINESS_BASE_FIELDS",
    "PRODUCTION_READINESS_CONDITIONAL_FIELDS", "PRICE_REFERENCE_COLUMNS", "PRICE_FIELD_CONTRACTS",
    "PRICE_BASIS_VALUES", "PRICE_NORMALIZED_UNITS", "WORKBOOK_INSTRUCTIONS",
    "ERROR_MESSAGES", "master_ai_prompt", "public_field_contract",
]
