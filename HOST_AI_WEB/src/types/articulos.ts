export type ApiEnvelope = {
  ok: boolean;
  version: string;
  api_version: string;
  request_id: string;
  modo_seguro: boolean;
  datos_reales_modificados: boolean;
};

export type ArticuloResumen = {
  id: string;
  codigo: string;
  nombre: string;
  tipo_entidad?: "ARTICULO_COMPRADO" | "ELABORACION_INTERNA" | "SUBELABORACION" | "PRODUCTO_VENDIBLE";
  elaboracion_id?: string | null;
  origen_coste?: "COSTE_COMPRA" | "COSTE_DERIVADO_ELABORACION";
  familia?: string | null;
  subfamilia?: string | null;
  marca?: string | null;
  proveedor?: string | null;
  precio?: number | null;
  unidad?: string | null;
  estado: string;
  stock?: number | null;
  unidad_stock?: string | null;
  con_stock: boolean;
  actualizado_en?: string | null;
  tiene_ficha_tecnica: boolean;
};

export type CatalogoResponse = ApiEnvelope & {
  catalogo: {
    items: ArticuloResumen[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
    filtros: { familias: string[]; proveedores: string[]; estados: string[] };
    capacidades: Record<string, boolean>;
  };
};

export type ArticuloDetalle = ArticuloResumen & {
  referencia_proveedor?: string | null;
  unidad_compra?: string | null;
  cantidad_formato?: number | null;
  unidad_base?: string | null;
  unidad_base_sugerida?: boolean;
  estado_unidad_base?: "SUGERIDA_PENDIENTE_REVISION" | "CONFIRMADA";
  conversion_unidades?: string | null;
  unidad_recetas?: string | null;
  iva?: number | null;
  precio_incluye_iva: boolean;
  alergenos: string[];
  conservacion?: string | null;
  stock_minimo?: number | null;
  observaciones?: string | null;
  unidad_formato?: string | null;
  procedencia_campos?: Record<string, { tipo?: string; actor_id?: string; fecha?: string; estado_revision?: string }>;
  historial_procedencia?: Record<string, unknown>[];
  precios_referencia?: PrecioReferencia[];
  stock_detalle: { cantidad?: number | null; unidad?: string | null; lotes: Record<string, unknown>[] };
  proveedores: Array<{ id?: string | null; nombre?: string | null; referencia?: string | null; preferente: boolean; precio?: number | null; unidad?: string | null }>;
  precios: Array<{ precio?: number | null; unidad?: string | null; proveedor?: string | null; fecha?: string | null }>;
  documentos: Record<string, unknown>[];
  ficha_tecnica: Record<string, unknown> | null;
  recetas: Record<string, unknown>[];
  escandallos: Record<string, unknown>[];
  historial: Array<{ tipo: string; fecha?: string | null; descripcion: string; precio?: number | null; proveedor?: string | null }>;
  operatividad: { stock: boolean; compras: boolean; escandallos: boolean };
  edicion: { unidades_base: string[]; proveedores: Array<{ id?: string | null; nombre: string }> };
};

export type PrecioReferencia = { tipo: string; origen: string; producto?: string; tienda_referencia?: string; precio_comercial: number; moneda?: string; cantidad_formato: number; unidad_formato: string; formato_comercial?: string; precio_normalizado: number; unidad_normalizada: string; url?: string; consultado_en?: string; evidencia?: string; confianza?: number | null; modelo_busqueda?: string; fuente_verificada?: boolean; autoridad: string; actor_id?: string; registrado_en?: string };
export type AICostItem = { provider?: string; model?: string; tool?: string | null; quantity?: number; input_tokens?: number; cached_input_tokens?: number; cache_write_tokens?: number; output_tokens?: number; reasoning_tokens?: number; total_tokens?: number; cost_usd: string };
export type AICostBreakdown = { operation_id: string; operation_type?: string; items: AICostItem[]; total_cost_usd: string; incremental_cost_usd?: string; currency: "USD"; pricing_version?: string; cache_hit?: boolean; label?: string };
export type ArticleDocumentationResponse = ApiEnvelope & { datos_propuestos_ia?: Record<string, unknown>; campos_sin_datos?: string[]; cambios_seleccionados?: Record<string, unknown>; preview_token?: string; articulo?: ArticuloDetalle; lectura_posterior_verificada?: boolean; cost_breakdown?: AICostBreakdown };

export type ArticleCulinaryContext = {
  ingrediente_original?: string;
  receta_nombre?: string;
  receta_id?: string;
  uso_culinario?: string;
  cantidad_receta?: number | string;
  unidad_receta?: string;
  procedimiento_receta?: string;
};
export type ManualPriceResponse = ApiEnvelope & { referencia_propuesta?: PrecioReferencia; preview_token?: string; referencia?: PrecioReferencia; articulo?: ArticuloDetalle; precio_real_modificado?: boolean; proveedor_real_modificado?: boolean };
export type ArticuloSinPrecio = { article_id: string; codigo: string; articulo: string; tipo_entidad?: "ARTICULO_COMPRADO" | "PRODUCTO_VENDIBLE"; unidad_base?: string | null; unidad_compra?: string | null; cantidad_formato?: number | null; unidad_formato?: string | null; recetas: string[]; usado_en_recetas: number; precio_real: null; proveedor_real?: string | null; referencia?: PrecioReferencia | null; estado: string };
export type ArticuloCosteDerivado = { article_id: string; articulo: string; tipo_entidad: "ELABORACION_INTERNA" | "SUBELABORACION" | "PRODUCTO_VENDIBLE"; elaboracion_id: string; origen_coste: "COSTE_DERIVADO_ELABORACION"; estado: "COSTE_DERIVADO_ESCANDALLO" | "ESCANDALLO_PENDIENTE"; coste_total?: number | null; coste_por_racion?: number | null };
export type ReclassificationCandidate = { article_id: string; articulo: string; registro_actual: Record<string, unknown>; coincidencias: Array<{ elaboracion_id: string; nombre: string }>; senales: string[]; estado: "REQUIERE_REVISION"; acciones_permitidas: string[] };
export type ReclassificationPreview = ApiEnvelope & { propuestas: Array<{ article_id: string; registro_actual: Record<string, unknown>; propuesto: { tipo_entidad: string; elaboracion_id?: string | null; origen_coste: string }; valor_legado_sin_clasificar?: number | null; consecuencias: string[] }>; preview_token: string; requiere_confirmacion: true };
export type ReferenciaImportPreviewRow = { fila: number; article_id: string; articulo: string; precio_real_actual?: number | null; proveedor_real_actual?: string | null; referencia: PrecioReferencia; preview_token: string; incluir: boolean };
export type ReferenciasImportPreview = ApiEnvelope & { formato_detectado: "JSON" | "CSV" | "TSV" | "MARKDOWN" | "VACIO"; listas: ReferenciaImportPreviewRow[]; ambiguas: Record<string, unknown>[]; invalidas: Record<string, unknown>[]; resumen: { listas: number; ambiguas: number; invalidas: number }; requiere_confirmacion: true; precio_real_modificado?: false; proveedor_real_modificado?: false; coste_ia_usd: string };
export type ReferenciasImportWorkflow = { estado: "LISTO_PARA_CONFIRMAR" | "CONFIRMADO"; preview: ReferenciasImportPreview; confirmacion?: { confirmadas: number; lectura_posterior_verificada: boolean; datos_reales_modificados: boolean }; updated_at: string };

export type ArticuloResponse = ApiEnvelope & { articulo: ArticuloDetalle };
export type ArticuloUpdateInput = { nombre: string; familia?: string; unidad_base: string; unidad_compra?: string; cantidad_formato?: number | null; proveedor_preferente?: string; precio?: number | null; referencia_proveedor?: string; marca?: string; conservacion?: string; alergenos?: string[]; observaciones?: string };
