import type { ApiEnvelope } from "./articulos";

export type ElaboracionResumen = {
  id: string;
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  categoria?: string | null;
  tipo: string;
  estado: string;
  rendimiento?: number | null;
  unidad_rendimiento?: string | null;
  estado_rendimiento?: "IMPORTADO" | "SUGERIDO" | "CONFIRMADO" | null;
  origen_rendimiento?: RendimientoOrigen | null;
  rendimiento_neto?: RendimientoNeto | null;
  raciones?: number | null;
  coste_total?: number | null;
  coste_por_racion?: number | null;
  estado_coste?: "DISPONIBLE" | "PARCIAL" | "SIN_COSTE" | "SIN_ESCANDALLO";
  coste_completo?: boolean;
  motivo_coste_no_disponible?: string | null;
  fecha_calculo?: string | null;
  tiene_receta: boolean;
  tiene_escandallo: boolean;
  tiene_ficha_tecnica: boolean;
  tiene_fotografia: boolean;
  tiene_documentos: boolean;
  tiene_produccion: boolean;
  tiene_relaciones_menu_evento: boolean;
  completitud?: number | null;
  actualizado_en?: string | null;
  version?: number | null;
};

export type BibliotecaResponse = ApiEnvelope & {
  biblioteca: {
    estado: string;
    total_elaboraciones: number;
    sin_receta: number;
    sin_escandallo: number;
    sin_ficha_tecnica: number;
    con_documentos: number;
    capacidades: Record<string, boolean>;
  };
};

export type ElaboracionesResponse = ApiEnvelope & {
  elaboraciones: {
    items: ElaboracionResumen[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    filters: { estados: string[]; categorias: string[] };
    capabilities: Record<string, boolean>;
  };
};

export type IngredienteReceta = {
  tipo_componente?: "ARTICULO" | "ELABORACION" | string | null;
  articulo_id?: string | null;
  escandallo_hijo_id?: string | null;
  referencia_elaboracion?: string | null;
  articulo_codigo?: string | null;
  articulo_nombre?: string | null;
  codigo?: string | null;
  nombre_articulo?: string | null;
  unidad_base?: string | null;
  nombre_original: string;
  cantidad_texto?: string | null;
  cantidad?: number | null;
  unidad?: string | null;
  merma?: number | null;
  cantidad_neta?: number | null;
  cantidad_receta?: number | null;
  unidad_receta?: string | null;
  coste_unitario?: number | null;
  precio_unitario?: number | null;
  precio_original?: number | null;
  unidad_precio_original?: string | null;
  precio_aplicado?: number | null;
  unidad_precio_aplicado?: string | null;
  coste_linea?: number | null;
  unidad_precio?: string | null;
  origen_precio?: string | null;
  proveedor_precio?: string | null;
  fecha_precio?: string | null;
  factor_conversion?: number | null;
  tipo_conversion?: "directa" | "metrica" | "envase" | "normalizacion_heredada" | "no_disponible" | string | null;
  cantidad_utilizada?: number | null;
  cantidad_con_merma?: number | null;
  coste_con_merma?: number | null;
  estado_coste?: string | null;
  motivo_sin_coste?: string | null;
  observaciones?: string | null;
  estado_relacion: "relacionado" | "sin_relacionar" | "coincidencia_dudosa" | "elaboracion_relacionada" | "elaboracion_sin_resolver";
};

export type EscandalloElaboracion = {
  id?: string | null;
  estado?: string | null;
  estado_coste: string;
  lineas: IngredienteReceta[];
  coste_ingredientes?: number | null;
  coste_ingredientes_parcial?: number | null;
  otros_costes?: number | null;
  coste_total?: number | null;
  coste_total_parcial?: number | null;
  rendimiento?: number | null;
  coste_por_racion?: number | null;
  precio_objetivo?: number | null;
  margen?: number | null;
  fecha_calculo?: string | null;
  desactualizado: boolean;
  ingredientes_sin_coste: number;
  ingredientes_sin_conversion: number;
  incidencias: Record<string, unknown>[];
};

export type ElaboracionDetalle = ElaboracionResumen & {
  receta: {
    ingredientes: IngredienteReceta[];
    procedimiento?: string | null;
    estado_procedimiento?: "CONFIRMADO" | "PENDIENTE" | string;
    procedimiento_propuesto_ia?: string | null;
    pasos: Array<string | Record<string, unknown>>;
    observaciones?: string | null;
    tiempo_total?: string | null;
    tiempo_activo?: string | null;
    tiempo_pasivo?: string | null;
    temperaturas: Array<string | Record<string, unknown>> | null;
    tecnicas: string[] | null;
    temperaturas_propuestas_ia?: Array<string | Record<string, unknown>> | null;
    tiempos_estimados_ia?: Record<string, unknown> | string | null;
    conservacion_propuesta_ia?: string | null;
    observaciones_propuestas_ia?: string | null;
    alergenos_posibles?: string[] | null;
    ingredientes_propuestos_ia?: Array<string | Record<string, unknown>> | null;
    ingredientes_propuestos_no_registrados?: string[] | null;
    rendimiento?: number | null;
    unidad_rendimiento?: string | null;
    estado_rendimiento?: "IMPORTADO" | "SUGERIDO" | "CONFIRMADO" | null;
    origen_rendimiento?: RendimientoOrigen | null;
    rendimiento_neto?: RendimientoNeto | null;
    rendimiento_fisico_teorico?: RendimientoFisicoTeorico | null;
    raciones?: number | null;
  };
  escandallo?: EscandalloElaboracion | null;
  ficha_tecnica: {
    estado: string;
    origen: string;
    persistida: boolean;
    identificacion: Record<string, unknown>;
    descripcion?: string | null;
    fotografia?: string | null;
    ingredientes: IngredienteReceta[];
    proceso: {
      procedimiento?: string | null;
      pasos: Array<string | Record<string, unknown>>;
      observaciones?: string | null;
    };
    tiempos: Record<string, string | null>;
    temperaturas: Array<string | Record<string, unknown>>;
    rendimiento?: number | null;
    unidad_rendimiento?: string | null;
    rendimiento_fisico_teorico?: RendimientoFisicoTeorico | null;
    raciones?: number | null;
    escandallo?: EscandalloElaboracion | null;
    alergenos: string[] | null;
    conservacion?: string | null;
    caducidad?: string | null;
    regeneracion?: string | null;
    presentacion?: string | null;
    utensilios: string[];
    produccion: ProduccionElaboracion;
    documentos: DocumentoElaboracion[];
    version?: number | null;
    actualizado_en?: string | null;
    campos_pendientes: string[];
    datos_persistidos?: Record<string, unknown> | null;
  };
  alergenos: string[] | null;
  conservacion?: string | null;
  regeneracion?: string | null;
  procedencia_campos?: Record<string, { tipo?: "USUARIO" | "IA" | "WEB" | "SISTEMA" | "IMPORTADO" | string; actor_id?: string | null; fecha?: string | null; estado_revision?: string | null }>;
  historial_procedencia?: Array<Record<string, unknown>>;
  produccion: ProduccionElaboracion;
  documentos: DocumentoElaboracion[];
  imagenes: string[];
  versiones: Array<{ version?: number; fecha?: string }>;
  menus: Array<string | { menu_id: string; nombre: string; estado?: string }>;
  eventos: string[];
  historial: Record<string, unknown>[];
  pendientes: string[];
  avisos: string[];
};

export type ElaboracionResponse = ApiEnvelope & {
  elaboracion: ElaboracionDetalle;
  permisos?: { confirmar_rendimiento?: boolean };
};

export type RendimientoOrigen = {
  tipo: string;
  referencia?: string | null;
  fecha?: string | null;
  actor_id?: string | null;
};

export type RendimientoNeto = {
  cantidad: number;
  unidad: string;
  estado: "IMPORTADO" | "SUGERIDO" | "CONFIRMADO";
  origen?: RendimientoOrigen | null;
};

export type RendimientoFisicoTeorico = {
  estado: "COMPLETO" | "PARCIAL" | "NO_CALCULABLE";
  cantidad: number | null;
  unidad: "kg" | "l" | null;
  estado_confirmacion: "SUGERIDO";
  magnitudes: Partial<Record<"masa" | "volumen", { cantidad: number; unidad: "kg" | "l" }>>;
  ingredientes_incluidos: Array<{
    articulo_id?: string | null; nombre: string; cantidad_original: number;
    unidad_original: string; dimension: "masa" | "volumen";
    cantidad_normalizada: number; unidad_normalizada: "kg" | "l";
  }>;
  ingredientes_excluidos: Array<{
    articulo_id?: string | null; nombre: string; cantidad?: number | null;
    unidad?: string | null; motivo: string;
  }>;
  por_unidad?: {
    cantidad: number; unidad: string; estado_confirmacion: "SUGERIDO";
    calculo_parcial: boolean;
  } | null;
  incidencias: Array<{ codigo: string; detalle: string }>;
  datos_reales_modificados: false;
};

export type RendimientoInput = {
  cantidad: number;
  unidad: "kg" | "g" | "l" | "ml";
  modo: "TOTAL" | "POR_UNIDAD";
  referencia?: string;
  propuesta_origen?: "MANUAL" | "TEORICO_COMPLETO" | "TEORICO_PARCIAL";
  acepta_estimacion_parcial?: boolean;
};

export type RendimientoPreviewResponse = ApiEnvelope & {
  estado: "LISTO_PARA_CONFIRMAR" | "SIN_CAMBIOS";
  escandallo_id: string;
  rendimiento_declarado: { cantidad: number; unidad: string };
  rendimiento_neto_actual: RendimientoNeto | null;
  rendimiento_neto_propuesto: RendimientoNeto;
  modo_entrada: "TOTAL" | "POR_UNIDAD";
  propuesta_origen: "MANUAL" | "TEORICO_COMPLETO" | "TEORICO_PARCIAL";
  version_esperada: string;
  preview_token: string;
  requiere_confirmacion: boolean;
  incidencias: Array<{ code?: string; message?: string } | string>;
};

export type RendimientoConfirmationResponse = ApiEnvelope & {
  estado: "CONFIRMADO" | "SIN_CAMBIOS";
  escandallo_id: string;
  rendimiento_declarado: { cantidad: number; unidad: string };
  rendimiento_neto: RendimientoNeto;
  idempotente: boolean;
};

export type ProduccionElaboracion = {
  indicaciones: {
    produccion_minima?: string | number | null;
    produccion_maxima?: string | number | null;
    personal_recomendado?: string | number | null;
    recursos: string[];
    notas?: string | null;
  };
  ordenes: Record<string, unknown>[];
  necesidades: Record<string, unknown>[];
  historial: Record<string, unknown>[];
};

export type DocumentoElaboracion = {
  tipo: string;
  nombre: string;
  referencia: string;
  fecha?: string | null;
  origen?: string | null;
  descripcion?: string | null;
  estado?: string | null;
};

export type ImportProposal = {
  id: string;
  tipo: string;
  estado: "PENDIENTE_REVISION";
  confianza: { valor: number; explicacion: string };
  explicacion: string;
  titulo: string;
  origen: { importacion_id: string; nombre: string; tipo: string };
  entidad_origen: string | null;
  bloques_origen: string[];
  advertencias: string[];
  conflictos: Array<Record<string, unknown>>;
  datos_propuestos: Record<string, unknown>;
  persistida: false;
};

export type BibliotecaImportEntity = {
  id: string;
  kind: "RECETA" | "INGREDIENTE" | string;
  name: string;
  fields: {
    ingredientes_estructurados?: Array<{
      nombre_original: string;
      cantidad_texto: string;
      unidad?: string | null;
      estado_relacion: "relacionado" | "coincidencia_dudosa" | "sin_relacionar";
      articulo_id?: string | null;
    }>;
    pasos?: string[];
    estado_relacion?: "relacionado" | "coincidencia_dudosa" | "sin_relacionar";
    cantidad_texto?: string;
    unidad?: string | null;
    receta?: string;
    [key: string]: unknown;
  };
  confidence: { valor: number; explicacion: string };
};

export type BibliotecaImportSession = {
  documento: {
    id: string;
    nombre: string;
    tipo_mime: string;
    tamano: number;
    origen: string;
    clasificacion: {
      tipo: string;
      confianza: { valor: number; explicacion: string };
      evidencias: string[];
      advertencias: string[];
    };
    secciones: Array<Record<string, unknown>>;
    entidades: BibliotecaImportEntity[];
    advertencias: string[];
    contenido_almacenado: false;
  };
  analisis_restaurante?: {
    archivos: Array<{ nombre: string; tipo: string; tamano: number; estado: string; hojas: number; filas: number }>;
    hojas: Array<{ archivo: string; nombre: string; region?: string; tipo_propuesto: string; filas: number; mapping: Array<{ columna: string; destino: string; confianza: number; requiere_revision: boolean }>; fila_inicial?: number; fila_final?: number; fila_encabezado?: number | null; titulo_contexto?: string; dimensiones?: string; celdas_no_vacias?: number; merged_cells?: string[]; confianza?: number; motivo?: string }>;
    resumen: {
      archivos_analizados: number; hojas_analizadas: number; filas_analizadas: number;
      posibles_articulos: number; posibles_recetas: number; posibles_menus?: number; posibles_subelaboraciones: number;
      posibles_productos_vendibles: number; proveedores: number; relaciones_detectadas: number;
      duplicados_posibles: number; ambiguedades: number; articulos_sin_coste: number;
      warnings_tecnicos?: number; decisiones_usuario?: number;
    };
    dudas: { clasificacion: unknown[]; precio: unknown[]; duplicados: unknown[]; relaciones: unknown[] };
    regiones_ambiguas?: Array<Record<string, unknown>>;
    propuestas_ia?: Array<Record<string, unknown>>;
    warnings_tecnicos?: Array<Record<string, unknown>>;
    decisiones_usuario?: Array<Record<string, unknown>>;
    exclusiones_sesion?: Array<{ nombre?: string; tipo_origen: string; accion: "IGNORAR"; motivo: string; origen?: unknown }>;
    opciones_sesion?: { excluir_ap_antiguos?: boolean };
    perfiles_importacion?: Array<Record<string, unknown>>;
    resultado_hibrido?: Record<string, unknown>;
    coste_ia: { usada: boolean; ambiguedades_enviadas: number; layouts_reutilizados?: number; total: number };
    ai_import?: {
      used: boolean; offered?: boolean; classification?: "KNOWN" | "BASIC" | "COMPLEX";
      fingerprint?: string; cache_hit?: boolean;
      structural_summary?: { sheets?: number; regions?: number; unresolved_regions?: number; rows_sent?: number };
      usage?: Record<string, unknown>; cost_breakdown?: Record<string, unknown>;
    };
    solo_previsualizacion: true;
    datos_operativos_modificados: false;
  };
  preview_global?: {
    proveedores: Record<string, Array<{ nombre: string; accion: string; proveedor_id?: string | null }>>;
    articulos: Record<string, CatalogArticleDraft[]>;
    elaboraciones: Record<string, Array<{
      nombre: string; accion: string;
      coincidencia?: { id?: string; codigo?: string; nombre?: string; diferencias?: unknown[] } | null;
    }>>;
    relaciones: Record<string, Array<{ articulo: string; proveedor: string; accion: string }>>;
    menus?: Record<string, Array<{
      id?: string; nombre: string; accion: string; menu_id?: string | null;
      tipo?: string; lineas_resueltas?: number; lineas_pendientes?: number;
      lineas_contexto?: number; motivos?: string[];
      lineas?: Array<{ nombre: string; seccion: string; estado: "RESUELTA" | "PENDIENTE" | "CONTEXTO"; tipo_referencia?: string | null; referencia?: string | null; futura?: boolean }>;
    }>>;
    ignorados: unknown[];
    errores: unknown[];
    contadores: {
      proveedores_nuevos: number; proveedores_reutilizados: number;
      articulos_nuevos: number; articulos_reutilizados: number;
      recetas_elaboraciones: number; recetas_nuevas?: number; recetas_reutilizadas?: number;
      recetas_requieren_revision?: number; relaciones: number; pendientes: number;
      articulos_requieren_revision?: number;
      articulos_ignorados?: number;
      articulos_reclasificados_elaboracion?: number;
      relaciones_a_escribir?: number; relaciones_reutilizadas?: number; relaciones_pendientes?: number;
      ingredientes_detectados?: number; ingredientes_relacionados?: number; ingredientes_sin_relacionar?: number;
      menus_no_soportados?: number;
      menus_recibidos?: number; menus_crear?: number; menus_reutilizar?: number;
      menus_actualizar?: number; menus_pendientes?: number;
      menus_excluidos?: number;
      menu_lineas_resueltas?: number; menu_lineas_pendientes?: number; menu_lineas_contexto?: number;
      pendientes_desglose?: {
        identidad_receta: number; articulo: number; relacion: number; proveedor: number;
        documentacion: number; menu?: number; otro: number;
      };
    };
    draft_version?: number;
    draft_fingerprint?: string;
    solo_previsualizacion: true;
  };
  resolucion_identidad?: {
    recetas: {
      total: number; ya_canonicas: number; ya_conocidas_legacy: number;
      nuevas_reales: number; posibles_variantes: number; requieren_revision: number;
      grupos: {
        ya_canonicas: ImportIdentityItem[]; ya_conocidas_legacy: ImportIdentityItem[];
        nuevas_reales: ImportIdentityItem[]; posibles_variantes: ImportIdentityItem[];
        requieren_revision: ImportIdentityItem[];
      };
    };
    articulos: { total: number; ya_existentes: number; nuevos_reales: number; requieren_revision: number };
    variantes?: {
      apariciones: number; grupos: number; duplicados_exactos_colapsados: number;
      grupos_requieren_decision: number; items: VariantGroup[];
    };
  };
  resumen: {
    secciones: number;
    entidades: number;
    propuestas: number;
    incidencias: number;
    recetas_detectadas: number;
    ingredientes_detectados: number;
    ingredientes_relacionados: number;
    coincidencias_dudosas: number;
    ingredientes_sin_relacionar: number;
    ingredientes_nuevos: number;
    duplicados_detectados: number;
    estado: "PENDIENTE_REVISION";
  };
  propuestas: ImportProposal[];
  solo_previsualizacion: true;
  confirmacion_disponible: boolean;
  limitaciones: string[];
  borrador: ImportDraft;
};

export type ImportIdentityItem = {
  id: string; nombre: string; legacy_source_ids?: string[]; datos_pendientes?: boolean;
};

export type VariantGroup = {
  id: string; nombre: string;
  tipo_entidad_propuesto: "RECETA_O_ELABORACION" | "MENU_O_CONTENEDOR" | "ETIQUETA_CONTEXTO_POR_REVISAR" | string;
  apariciones: number; versiones_estructurales: number; duplicados_exactos: number; requiere_decision: boolean;
  decision?: "MISMA_RECETA" | "RECETAS_DIFERENTES" | "PENDIENTE";
  versiones: Array<{
    id: string; nombre: string; ingredientes: Array<Record<string, unknown>>;
    rendimiento?: unknown; unidad_rendimiento?: string | null; origenes: unknown[]; apariciones: number;
  }>;
  diferencias: Array<{ version: number; tipo: string; nombre?: string; antes?: unknown; despues?: unknown }>;
};

export type LegacyCanonicalizationPreviewResponse = ApiEnvelope & {
  importacion_id: string; estado: "LISTO_PARA_CONFIRMAR"; preview_token: string;
  requiere_confirmacion: boolean; canonicalizaciones: Array<{
    legacy_source_id: string; nombre: string; ingredientes?: unknown[];
    rendimiento?: number | null; unidad_rendimiento?: string | null;
  }>;
  resumen_impacto: { recetas_601: number; stock: 0; lotes: 0; movimientos_stock: 0; recepciones: 0; compras: 0 };
  datos_reales_modificados: false;
};

export type LegacyCanonicalizationConfirmationResponse = ApiEnvelope & {
  importacion_id: string; estado: "CONFIRMADO" | "SIN_CAMBIOS";
  canonicalizadas?: number; idempotente: boolean; datos_reales_modificados: boolean;
};

export type BibliotecaImportResponse = ApiEnvelope & {
  importacion: BibliotecaImportSession;
};

export type BibliotecaImportProposalsResponse = ApiEnvelope & {
  importacion_id: string;
  propuestas: ImportProposal[];
  total: number;
  solo_previsualizacion: true;
};

export type DraftIssue = {
  code: string;
  level: "ERROR" | "ADVERTENCIA" | "SUGERENCIA";
  message: string;
  field: string;
};

export type DraftValidationIssue = {
  code: string;
  level: "BLOQUEANTE" | "ADVERTENCIA";
  recipe_id: string;
  recipe_title: string;
  recipe_index: number;
  ingredient_id?: string | null;
  ingredient_index?: number | null;
  field: string;
  message: string;
};

export type ArticleCandidate = {
  articulo_id: string;
  codigo: string;
  nombre: string;
  categoria: string;
  unidad?: string | null;
  precio?: number | null;
  nivel_coincidencia: number;
  motivo: string;
  unidad_compatible: boolean;
};

export type IngredientDraft = {
  id: string;
  original_text: string;
  quantity_raw: string;
  quantity?: number | null;
  unit_raw: string;
  unit?: string | null;
  name_raw: string;
  normalized_name: string;
  observations: string;
  article_id?: string | null;
  article_candidates: ArticleCandidate[];
  relation_status: "RELACIONADO" | "COINCIDENCIA_EXACTA_PROPUESTA" | "REVISAR_COINCIDENCIA" | "SIN_RELACIONAR" | "CREAR_ARTICULO_PROPUESTO" | "IGNORADO";
  confidence: number;
  validation_errors: DraftIssue[];
};

export type RecipeDraft = {
  id: string;
  title: string;
  entity_type: "PRINCIPAL" | "SUBELABORACION" | "COMPONENTE" | "SECCION" | "DESCARTAR";
  parent_recipe_id?: string | null;
  order: number;
  description: string;
  ingredients: IngredientDraft[];
  procedure: string[];
  yield_value?: number | null;
  servings?: number | null;
  times: Record<string, unknown>;
  temperatures: unknown[];
  notes: string;
  source_blocks: Array<string | Record<string, unknown>>;
  confidence: number;
  proposed_action: string;
  identity_decision?: "MISMA_RECETA" | "VARIANTE" | "RECETA_NUEVA" | "PENDIENTE" | null;
  selected_canonical_recipe_id?: string | null;
  duplicate_candidates: Array<Record<string, unknown>>;
  validation_errors: DraftIssue[];
};

export type ImportDraft = {
  id: string;
  document_id: string;
  status: "PENDIENTE_REVISION" | "EN_REVISION" | "CONFIRMADA";
  classification: string;
  confidence: number;
  recipes: RecipeDraft[];
  warnings: DraftIssue[];
  conflicts: DraftIssue[];
  variant_decisions?: Array<{ group_id: string; decision: "MISMA_RECETA" | "RECETAS_DIFERENTES" | "PENDIENTE" }>;
  catalogo?: { articulos?: CatalogArticleDraft[]; proveedores?: Array<Record<string, unknown>>; relaciones?: Array<Record<string, unknown>> };
  article_decisions?: ArticleDraftDecision[];
  menus?: Array<Record<string, unknown>>;
  menu_decisions?: MenuDraftDecision[];
  version: number;
  draft_version: number;
  created_at: string;
  updated_at: string;
  persisted: boolean;
  confirmation_available: boolean;
  validation?: {
    valid: boolean;
    blocking_errors: DraftValidationIssue[];
    warnings: DraftValidationIssue[];
  };
};

export type MenuLineDraftDecision = {
  line_index: number;
  decision: "PENDIENTE" | "EXCLUIR" | "USAR_REFERENCIA";
  tipo_referencia?: "RECETA" | "PRODUCTO" | null;
  referencia?: string | null;
};

export type MenuDraftDecision = {
  menu_draft_id: string;
  decision: "PENDIENTE" | "CREAR_MENU" | "REUTILIZAR_MENU" | "EXCLUIR_MENU_DOCUMENTAL";
  nombre_final: string;
  menu_id?: string | null;
  line_decisions: MenuLineDraftDecision[];
};

export type CatalogArticleDraft = {
  id: string; nombre: string; accion: string; estado?: string; article_id?: string | null;
  tipo_entidad?: string; tipo_semantico?: string | null; motivo?: string; proveedor?: string | null;
  candidatos?: Array<{ article_id?: string; articulo_id?: string; nombre?: string; score?: number; evidencia?: unknown }>;
  evidencia_tipo?: unknown; evidencia_identidad?: unknown; origen?: unknown;
};

export type ArticleDraftDecision = {
  article_draft_id: string;
  decision: "REUTILIZAR_ARTICULO" | "NO_ARTICULO_COMPRA" | "ES_ELABORACION" | "PRODUCTO_VENDIBLE" | "IGNORAR" | "PENDIENTE";
  article_id?: string | null;
};

export type BibliotecaDraftResponse = ApiEnvelope & {
  importacion_id: string;
  borrador: ImportDraft;
  preview_global?: BibliotecaImportSession["preview_global"];
  resolucion_identidad?: BibliotecaImportSession["resolucion_identidad"];
  datos_reales_modificados: false;
};

export type ImportConfirmationResult = {
  estado: "COMPLETADA" | "FALLIDA";
  acciones: Array<{ tipo: string; id: string }>;
  entidades: Array<{ tipo: string; id: string; nombre: string }>;
  errores: Array<{ entidad: string; validacion: string; accion: string; mensaje: string }>;
  rollback: boolean;
  transaccion_id?: string;
};

export type BibliotecaImportConfirmationResponse = ApiEnvelope & {
  importacion_id: string;
  estado: "CONFIRMADA";
  resultado: ImportConfirmationResult;
};
