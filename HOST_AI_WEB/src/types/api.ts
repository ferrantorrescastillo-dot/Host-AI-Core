export type ApiEnvelopeBase = {
  ok: boolean;
  version: string;
  api_version: string;
  request_id: string;
  modo_seguro: boolean;
  datos_reales_modificados: boolean;
};

export type ApiError = {
  status?: number;
  code?: string;
  message?: string;
};

export type DashboardPayload = {
  estado_general?: string;
  prioridad?: unknown;
  pendientes?: unknown[];
  riesgos?: unknown[];
  recomendaciones?: unknown[];
  evento_activo?: unknown;
  workflows?: unknown[];
  modulos?: {
    compras?: ComprasModule;
    [key: string]: unknown;
  };
};

export type CompraListItem = {
  id?: string;
  nombre?: string;
  prioridad?: number;
  estado?: string;
  fecha_necesaria?: string;
};

export type PropuestaCompraListItem = {
  id?: string;
  producto?: string;
  comprar?: number;
  unidad?: string;
  prioridad?: string;
  proveedor_sugerido?: string;
  estado?: string;
  creado_en?: string;
};

export type ProveedorCompraListItem = {
  id?: string;
  nombre?: string;
  estado?: string;
  telefono?: string;
  email?: string;
};

export type CompraHistorialListItem = {
  id?: string;
  producto?: string;
  cantidad?: number;
  unidad?: string;
  proveedor?: string;
  estado?: string;
  creado_en?: string;
};

export type ComprasModule = {
  estado?: string;
  total?: number;
  items?: CompraListItem[];
  necesidades_pendientes?: number;
  propuestas_pendientes?: number;
  propuestas?: PropuestaCompraListItem[];
  total_propuestas?: number;
  proveedores?: ProveedorCompraListItem[];
  total_proveedores?: number;
  historial?: CompraHistorialListItem[];
  total_historial?: number;
  mensaje?: string;
};

export type DashboardResponse = ApiEnvelopeBase & {
  dashboard?: DashboardPayload;
  error?: ApiError;
};

export type ChatResponse = ApiEnvelopeBase & {
  respuesta?: string;
  chat?: Record<string, unknown>;
  contexto?: Record<string, unknown>;
  error?: ApiError;
};
