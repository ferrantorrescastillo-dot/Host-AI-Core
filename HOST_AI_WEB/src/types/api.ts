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
    eventos?: EventosModule;
    compras?: ComprasModule;
    produccion?: ProduccionModule;
    [key: string]: unknown;
  };
};

export type ProduccionTareaListItem = {
  id?: string; titulo?: string; estado?: string; prioridad?: string;
  cantidad?: number; unidad?: string; responsable?: string; bloqueo?: string;
  retraso_min?: number; progreso?: number; duracion_total_min?: number;
  incidencias?: unknown[];
};

export type ProduccionPlanListItem = {
  id?: string; nombre?: string; evento_id?: string; evento?: string;
  fecha?: string; responsable?: string; estado?: string; pax?: number;
  duracion_total_min?: number; total_tareas?: number; pendientes?: number;
  en_curso?: number; bloqueadas?: number; pausadas?: number; finalizadas?: number;
  porcentaje_completado?: number; avisos?: unknown[]; alertas?: unknown[];
  tareas?: ProduccionTareaListItem[];
};

export type ProduccionResumen = {
  planes_activos?: number; tareas?: number; pendientes?: number;
  en_curso?: number; bloqueadas?: number; pausadas?: number; alertas?: number;
};

export type ProduccionModule = {
  estado?: string; total?: number; items?: ProduccionPlanListItem[];
  planes_activos?: number; total_tareas?: number; tareas_pendientes?: number;
  tareas_en_curso?: number; tareas_bloqueadas?: number; tareas_pausadas?: number;
  total_alertas?: number; resumen?: ProduccionResumen; mensaje?: string;
};

export type EventoListItem = {
  id?: string;
  nombre?: string;
  fecha?: string;
  pax?: number;
  estado?: string;
  dias?: number;
  servicios?: number | unknown[];
  avisos?: string[];
  riesgos?: string[];
  estado_operativo?: string;
};

export type EventosResumen = {
  eventos_activos?: number;
  pax_total?: number;
  servicios?: number;
  avisos?: number;
};

export type EventosModule = {
  estado?: string;
  total?: number;
  items?: EventoListItem[];
  eventos_activos?: number;
  total_servicios?: number;
  total_avisos?: number;
  resumen?: EventosResumen;
  mensaje?: string;
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
