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
    stock?: StockModule;
    [key: string]: unknown;
  };
};

export type StockLote = {
  id?: string;
  nombre?: string;
  cantidad?: number;
  unidad?: string;
  familia?: string;
  ubicacion?: string;
  proveedor?: string;
  articulo_id?: string;
  fecha_entrada?: string;
  caducidad?: string;
  coste_unitario?: number;
  creado_en?: string;
};

export type StockExistencia = {
  clave?: string;
  nombre?: string;
  articulo_id?: string;
  familia?: string;
  unidad?: string;
  cantidad?: number;
  lotes?: StockLote[];
};

export type StockMovimiento = {
  id?: string;
  tipo?: string;
  nombre?: string;
  cantidad?: number;
  unidad?: string;
  motivo?: string;
  lote_id?: string;
  articulo_id?: string;
  creado_en?: string;
  origen?: string;
  destino?: string;
  usuario?: string;
  observaciones?: string;
  referencia?: string;
  trazabilidad?: Record<string, unknown>;
};

export type StockAlerta = {
  tipo?: string;
  nivel?: string;
  mensaje?: string;
  articulo_id?: string;
  lote_id?: string;
  ubicacion?: string;
  cantidad?: number;
  unidad?: string;
};

export type StockResumen = {
  articulos?: number;
  lotes?: number;
  lotes_registrados?: number;
  movimientos?: number;
  alertas?: number;
  bajo_minimo?: number;
  caducados?: number;
  caducan_pronto?: number;
  valor_total?: number;
};

export type StockModule = {
  estado?: string;
  total?: number;
  items?: StockAlerta[];
  existencias?: StockExistencia[];
  total_existencias?: number;
  lotes?: StockLote[];
  total_lotes?: number;
  total_lotes_registrados?: number;
  movimientos?: StockMovimiento[];
  total_movimientos?: number;
  alertas?: StockAlerta[];
  total_alertas?: number;
  estado_operativo?: string;
  caducidades?: StockAlerta[];
  total_caducidades?: number;
  resumen?: StockResumen;
  mensaje?: string;
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

export type ChatUiAction = {
  type?: string;
  target?: string;
  view?: string;
  id?: string;
  label?: string;
  url?: string;
};

export type ChatNavigationRequest = {
  target_module?: string;
  filter_data?: { termino?: string; [key: string]: unknown };
};

export type ChatData = {
  ui_action?: ChatUiAction;
  ui_action_mode?: string;
  navigation_request?: ChatNavigationRequest;
  confirmation_actions?: unknown[];
  reservation_actions?: unknown[];
  economic_actions?: unknown[];
  preview?: unknown;
  purchase_groups?: ChatPurchaseGroup[];
  operational_incidents?: ChatOperationalIncident[];
  [key: string]: unknown;
};

export type ChatPurchaseItem = { articulo_id: string; nombre: string; cantidad: number; unidad: string; formato?: string | null; precio_unitario?: number | null; unidad_precio?: string | null; coste_neto?: number | null };
export type ChatPurchaseAction = { type: "OPEN_ORDER" | "PREPARE_ORDER"; label: string; pedido_id?: string; menu_id?: string };
export type ChatPurchaseRelatedLine = { articulo_id: string; nombre: string; cantidad_prevista: number | null; unidad: string; cubriria_necesidad: boolean };
export type ChatPurchaseGroup = { proveedor: string; articulos: ChatPurchaseItem[]; estado_pedido: string; pedido_relacionado?: { pedido_id: string; estado: string; lineas_relevantes: ChatPurchaseRelatedLine[] } | null; action?: ChatPurchaseAction | null };
export type ChatOperationalIncident = { articulo_id?: string; reason: string; unidad?: string };

export type ChatPayload = {
  mensaje?: string;
  datos?: ChatData;
  [key: string]: unknown;
};

export type ChatResponse = ApiEnvelopeBase & {
  respuesta?: string;
  chat?: ChatPayload;
  contexto?: Record<string, unknown>;
  session_id?: string;
  error?: ApiError;
};

export type ChatConfirmationActionId =
  | "APPLY_PENDING_RESERVATION" | "DISCARD_PENDING_RESERVATION"
  | "CONFIRM_RESERVATION" | "EDIT_RESERVATION" | "CANCEL_RESERVATION"
  | "MARK_RESERVATION_NO_SHOW" | "COMPLETE_RESERVATION" | "OPEN_RESERVATION"
  | "RESOLVE_MISSING_PRICE" | "RESOLVE_MISSING_CONVERSION"
  | "CHECK_ESCANDALLO_COST"
  | "APPLY_PENDING_ARTICLE_CHANGE" | "DISCARD_PENDING_ARTICLE_CHANGE"
  | "APPLY_PENDING_LOT_LOCATION" | "DISCARD_PENDING_LOT_LOCATION"
  | "APPLY_PENDING_CATALOG_CREATE" | "DISCARD_PENDING_CATALOG_CREATE";
export type ChatConfirmationAction = { action_id: ChatConfirmationActionId; action_context_id?: string; label: string; style: "primary" | "secondary" };

export type ArticleChangePreviewChange = { field: string; label: string; before: string; after: string };
export type ArticleChangePreviewDetail = { label: string; value: string; formula?: string; status?: string };
export type ArticleChangePreview = {
  schema: "ARTICLE_CHANGE_PREVIEW_V1";
  entity_type: "ARTICULO";
  entity_id: string;
  title: string;
  operation: "UPDATE_PRICE" | "UPDATE_CONVERSION" | "UPDATE_FORMAT";
  changes: ArticleChangePreviewChange[];
  derived: ArticleChangePreviewDetail[];
  unchanged: ArticleChangePreviewDetail[];
  notice: string;
  datos_reales_modificados: false;
};
