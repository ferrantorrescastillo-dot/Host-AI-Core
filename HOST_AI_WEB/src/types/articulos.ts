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
  unidad_recetas?: string | null;
  iva?: number | null;
  precio_incluye_iva: boolean;
  alergenos: string[];
  conservacion?: string | null;
  stock_minimo?: number | null;
  observaciones?: string | null;
  stock_detalle: { cantidad?: number | null; unidad?: string | null; lotes: Record<string, unknown>[] };
  proveedores: Array<{ id?: string | null; nombre?: string | null; referencia?: string | null; preferente: boolean; precio?: number | null; unidad?: string | null }>;
  precios: Array<{ precio?: number | null; unidad?: string | null; proveedor?: string | null; fecha?: string | null }>;
  documentos: Record<string, unknown>[];
  ficha_tecnica: Record<string, unknown> | null;
  recetas: Record<string, unknown>[];
  escandallos: Record<string, unknown>[];
  historial: Array<{ tipo: string; fecha?: string | null; descripcion: string; precio?: number | null; proveedor?: string | null }>;
};

export type ArticuloResponse = ApiEnvelope & { articulo: ArticuloDetalle };
